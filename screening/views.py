"""
Views for the resume screening application.
"""
import io
import csv
import logging

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .forms import CandidateForm, BulkUploadForm, ResumeUploadForm
from .ml_models import predict_candidate, get_edu_encoder
from .resume_parser import extract_text_from_file, parse_resume_text

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def form_view(request):
    """Render the candidate screening form."""
    form = CandidateForm()
    bulk_form = BulkUploadForm()
    resume_form = ResumeUploadForm()
    return render(request, 'screening/form.html', {
        'form': form,
        'bulk_form': bulk_form,
        'resume_form': resume_form,
    })


@require_http_methods(["POST"])
def predict_view(request):
    """Handle form submission and return prediction results."""
    form = CandidateForm(request.POST)

    if not form.is_valid():
        bulk_form = BulkUploadForm()
        resume_form = ResumeUploadForm()
        return render(request, 'screening/form.html', {
            'form': form,
            'bulk_form': bulk_form,
            'resume_form': resume_form,
            'errors': form.errors,
        })

    try:
        skills = form.cleaned_data['skills']
        experience = form.cleaned_data['experience']
        education = form.cleaned_data['education']
        projects_count = form.cleaned_data['projects_count']

        result = predict_candidate(skills, experience, education, projects_count)

        context = {
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'skills': skills,
            'experience': experience,
            'education': education,
            'projects_count': projects_count,
            'is_hired': result['prediction'] == 'Hire',
        }
        return render(request, 'screening/result.html', context)

    except Exception as e:
        logger.error("Prediction failed: %s", e, exc_info=True)
        messages.error(request, f"Prediction failed: {str(e)}")
        bulk_form = BulkUploadForm()
        resume_form = ResumeUploadForm()
        return render(request, 'screening/form.html', {
            'form': form,
            'bulk_form': bulk_form,
            'resume_form': resume_form,
        })


@require_http_methods(["POST"])
def bulk_upload_view(request):
    """Handle CSV upload with multiple candidates, rank and display results."""
    bulk_form = BulkUploadForm(request.POST, request.FILES)

    if not bulk_form.is_valid():
        form = CandidateForm()
        resume_form = ResumeUploadForm()
        messages.error(request, "Please upload a valid CSV file.")
        return render(request, 'screening/form.html', {
            'form': form,
            'bulk_form': bulk_form,
            'resume_form': resume_form,
        })

    try:
        csv_file = request.FILES['csv_file']

        # Validate file type
        if not csv_file.name.endswith('.csv'):
            raise ValueError("Only CSV files are accepted.")

        # Read CSV
        decoded = csv_file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(decoded))

        # Strip column names
        df.columns = df.columns.str.strip()

        # Validate required columns
        required_cols = {'Skills', 'Experience (Years)', 'Education', 'Projects Count'}
        actual_cols = set(df.columns)
        missing = required_cols - actual_cols
        if missing:
            raise ValueError(
                f"Missing required columns: {', '.join(missing)}. "
                f"Found columns: {', '.join(actual_cols)}"
            )

        # Get valid education values
        valid_edu = set(get_edu_encoder().classes_)

        results = []
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed + header
            try:
                skills = str(row['Skills']).strip()
                experience = float(row['Experience (Years)'])
                education = str(row['Education']).strip()
                projects_count = int(row['Projects Count'])

                if not skills:
                    raise ValueError("Skills field is empty")
                if education not in valid_edu:
                    raise ValueError(f"Invalid education: '{education}'. Must be one of: {', '.join(sorted(valid_edu))}")
                if experience < 0:
                    raise ValueError("Experience cannot be negative")
                if projects_count < 0:
                    raise ValueError("Projects count cannot be negative")

                result = predict_candidate(skills, experience, education, projects_count)
                results.append({
                    'row': row_num,
                    'name': row.get('Name', f'Candidate {row_num - 1}'),
                    'skills': skills,
                    'experience': experience,
                    'education': education,
                    'projects_count': projects_count,
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'hire_prob': result['probabilities'].get('Hire', 0),
                    'is_hired': result['prediction'] == 'Hire',
                })
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        # Sort by hire probability descending (ranking)
        results.sort(key=lambda x: x['hire_prob'], reverse=True)

        # Add rank
        for i, r in enumerate(results, 1):
            r['rank'] = i

        context = {
            'results': results,
            'total': len(results),
            'hired_count': sum(1 for r in results if r['is_hired']),
            'rejected_count': sum(1 for r in results if not r['is_hired']),
            'errors': errors,
            'filename': csv_file.name,
        }
        return render(request, 'screening/bulk_result.html', context)

    except Exception as e:
        logger.error("Bulk upload failed: %s", e, exc_info=True)
        messages.error(request, f"Bulk upload failed: {str(e)}")
        form = CandidateForm()
        bulk_form = BulkUploadForm()
        resume_form = ResumeUploadForm()
        return render(request, 'screening/form.html', {
            'form': form,
            'bulk_form': bulk_form,
            'resume_form': resume_form,
        })

@require_http_methods(["POST"])
def resume_upload_view(request):
    """Handle resume upload (PDF/DOCX/TXT), parse and predict."""
    resume_form = ResumeUploadForm(request.POST, request.FILES)

    if not resume_form.is_valid():
        form = CandidateForm()
        bulk_form = BulkUploadForm()
        messages.error(request, "Please upload a valid resume file.")
        return render(request, 'screening/form.html', {
            'form': form,
            'bulk_form': bulk_form,
            'resume_form': resume_form,
        })

    try:
        resume_file = request.FILES['resume_file']
        text = extract_text_from_file(resume_file)
        parsed = parse_resume_text(text)

        skills = parsed['skills']
        experience = parsed['experience']
        education = parsed['education']
        projects_count = parsed['projects_count']

        result = predict_candidate(skills, experience, education, projects_count)

        context = {
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'skills': "Extracted from Resume" if len(skills) > 100 else skills,
            'experience': experience,
            'education': education,
            'projects_count': projects_count,
            'is_hired': result['prediction'] == 'Hire',
        }
        return render(request, 'screening/result.html', context)

    except Exception as e:
        logger.error("Resume parsing failed: %s", e, exc_info=True)
        messages.error(request, f"Resume processing failed: {str(e)}")
        form = CandidateForm()
        bulk_form = BulkUploadForm()
        return render(request, 'screening/form.html', {
            'form': form,
            'bulk_form': bulk_form,
            'resume_form': resume_form,
        })

