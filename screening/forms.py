"""
Django forms for resume screening input validation.
"""
from django import forms


EDUCATION_CHOICES = [
    ('', 'Select Education Level'),
    ('B.Sc', 'B.Sc'),
    ('B.Tech', 'B.Tech'),
    ('M.Tech', 'M.Tech'),
    ('MBA', 'MBA'),
    ('PhD', 'PhD'),
]


class CandidateForm(forms.Form):
    """Form for single candidate screening."""

    skills = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'id': 'skills-input',
            'class': 'form-input',
            'placeholder': 'e.g. Python, Machine Learning, SQL, Deep Learning',
            'autocomplete': 'off',
        }),
        help_text='Enter comma-separated skills',
    )

    experience = forms.FloatField(
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'id': 'experience-input',
            'class': 'form-input',
            'placeholder': 'Years of experience',
            'step': '0.5',
        }),
    )

    education = forms.ChoiceField(
        choices=EDUCATION_CHOICES,
        widget=forms.Select(attrs={
            'id': 'education-input',
            'class': 'form-input',
        }),
    )

    projects_count = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'id': 'projects-input',
            'class': 'form-input',
            'placeholder': 'Number of projects',
        }),
    )


class BulkUploadForm(forms.Form):
    """Form for uploading CSV with multiple candidates."""

    csv_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'id': 'csv-upload-input',
            'class': 'form-input file-input',
            'accept': '.csv',
        }),
        help_text='Upload a CSV with columns: Skills, Experience (Years), Education, Projects Count',
    )


class ResumeUploadForm(forms.Form):
    """Form for uploading a single resume file to parse and evaluate."""

    resume_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'id': 'resume-upload-input',
            'class': 'form-input file-input',
            'accept': '.pdf,.docx,.txt',
        }),
        help_text='Upload a resume (.pdf, .docx, .txt) to automatically extract details and evaluate.',
    )
