import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_project.settings')
django.setup()

from screening.resume_parser import extract_text_from_file, parse_resume_text
from screening.ml_models import predict_candidate

class DummyFile:
    def __init__(self, f):
        self.f = f
        self.name = 'test_resume.pdf'
    def read(self, *args, **kwargs):
        return self.f.read(*args, **kwargs)
    def seek(self, *args, **kwargs):
        return self.f.seek(*args, **kwargs)
    def tell(self, *args, **kwargs):
        return self.f.tell(*args, **kwargs)

with open('test_resume.pdf', 'rb') as f:
    dummy = DummyFile(f)
    text = extract_text_from_file(dummy)
    print("--- EXTRACTED TEXT ---")
    print(text)
    
    parsed = parse_resume_text(text)
    print("--- PARSED DATA ---")
    print(parsed)
    
    result = predict_candidate(
        parsed['skills'], 
        parsed['experience'], 
        parsed['education'], 
        parsed['projects_count']
    )
    print("--- PREDICTION ---")
    print(result)
