from typing import Iterable
from django.db import models
from .extractor import TextExtractor
from elasticsearch import Elasticsearch
from .search import DocumentIndex

es = Elasticsearch('http://localhost:9200')

class Documents(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    url = models.URLField(null=True, blank=True)      
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        extractor = TextExtractor()
        if self.url:
            print("executed")
            self.text = extractor.fromUrl(self.url)
            self.title = self.url
        else:
            file = self.file
            image_file_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp']
            document_file_extensions = ['docx']
            name, extension = file.name.rsplit('.', 1)
            if extension in image_file_extensions:
                self.text = extractor.fromImageFileEasyOCR(file)
            elif extension == 'pdf':
                self.text = extractor.fromPDFFile(file)
            elif extension == 'txt':
                self.text = extractor.fromTextFile(file)
            elif extension == 'html':
                self.text = extractor.fromHTMLFile(file)
            elif extension in document_file_extensions:
                self.text = extractor.fromWordFile(file)  

            self.title = self.file.name

        
        super().save(*args, **kwargs)
        if(es.ping()):
            if self.url:
                doc = DocumentIndex(title=self.url, content=self.text, id=self.id)
            else:
                doc = DocumentIndex(title=self.file.name, content=self.text, id=self.id)

            doc = doc.save(using=es)

    @property
    def get_url(self):
        if self.url:
            return self.url
        else:
            return "http://localhost:8000" + self.file.url

    @property
    def get_extension(self):
        return self.file.name.split('.')[-1]

    @staticmethod
    def count_pdf(self):
        return Documents.objects.filter(file__icontains='pdf').count()
    
    @staticmethod
    def count_text(self):
        return Documents.objects.filter(file__icontains='txt').count()
    
    @staticmethod
    def count_html(self):
        return Documents.objects.filter(file__icontains='html').count()
    
    @staticmethod
    def count_image(self):
        instance =  Documents.objects.exclude(file__icontains='pdf').exclude(file__icontains='txt').exclude(file__icontains='html')
        instance = instance.exclude(url__isnull=False).count()
        # print(instance)
        return instance
    
    @staticmethod
    def count_word_doc(self):
        return Documents.objects.filter(file__icontains='docx').count()
    
    @staticmethod
    def count_url(self):
        return Documents.objects.filter(url__isnull=False).count()

    def __str__(self):
        return self.title