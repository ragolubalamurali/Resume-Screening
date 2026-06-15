# Intelligent Resume Screening and Candidate Shortlisting System

## 1. Project Overview

The **Intelligent Resume Screening and Candidate Shortlisting System** is a robust web application built using the Django framework. Its primary objective is to streamline the recruitment process by leveraging Machine Learning (ML) and Large Language Models (LLMs) to automatically evaluate and shortlist candidates based on their resumes, skills, experience, and educational background.

The system replaces manual screening with an automated, objective, and efficient pipeline that provides a "Hire" or "Reject" prediction along with a confidence score.

---

## 2. Core Features

### 2.1. Individual Candidate Evaluation
A manual entry form where recruiters can input specific candidate details:
- **Skills**: Comma-separated list of technical and soft skills.
- **Experience**: Total years of professional experience.
- **Education**: Highest educational degree (e.g., B.Sc, B.Tech, M.Tech, MBA, PhD).
- **Projects Count**: Number of projects completed by the candidate.
The system processes this input through the pre-trained ML model and instantly returns a Hire/Reject prediction.

### 2.2. Bulk Candidate Upload (CSV)
For large-scale recruitment drives, the system supports uploading a CSV file containing multiple candidates.
- Validates data integrity (required columns, negative values, valid education levels).
- Processes all candidates sequentially.
- Returns a comprehensive dashboard with candidates **ranked by their probability of being hired**, making it easy to prioritize top talent.

### 2.3. Intelligent AI Resume Parsing (PDF, DOCX, TXT)
Recruiters can directly upload a candidate's resume document.
- **Text Extraction**: Uses `PyPDF2` for PDFs, `python-docx` for Word documents, and standard decoding for text files.
- **LLM Integration (Google Gemini)**: The application utilizes the `gemini-2.5-flash` model to intelligently extract structured data (skills, experience, education, and project count) directly from the unstructured resume text.
- **Regex Fallback**: In the event the Gemini API is unavailable or fails, the system automatically falls back to a custom Regular Expression (Regex) parsing engine to heuristically estimate the required metrics.

---

## 3. Technology Stack

- **Backend Framework**: Django (Python)
- **Machine Learning**: `scikit-learn` (Random Forest Classifier), `numpy`, `pandas`
- **Natural Language Processing (NLP)**: TF-IDF Vectorization for skills evaluation
- **LLM API**: `google-generativeai` (Google Gemini)
- **Document Processing**: `PyPDF2` (PDFs), `python-docx` (DOCX)
- **Frontend**: Django Templates (HTML/CSS), Bootstrap/Custom CSS (presumed for UI)
- **Database**: SQLite (Default Django DB)

---

## 4. Architecture and Directory Structure

The project follows a standard Django architecture with a primary application called `screening`.

```text
c:\projects\resume-shortlisting\
├── manage.py                  # Django CLI utility
├── requirements.txt           # Python dependencies
├── resume_project/            # Main Django project configuration directory
│   ├── settings.py            # Global settings, API keys (GEMINI_API_KEY)
│   ├── urls.py                # Global URL routing
│   └── wsgi.py / asgi.py      # Server entry points
└── screening/                 # Primary App Directory
    ├── models.py              # Database schemas (if any)
    ├── forms.py               # Django forms (CandidateForm, BulkUploadForm, ResumeUploadForm)
    ├── views.py               # Business logic, request handling, file validations
    ├── urls.py                # App-specific URL routing
    ├── resume_parser.py       # Gemini API integration and Regex fallback logic
    ├── ml_models/             # Machine Learning Artifacts
    │   ├── __init__.py        # Lazy loading module for ML models to prevent repetitive I/O
    │   ├── model.pkl          # Trained Random Forest Classifier
    │   ├── tfidf.pkl          # TF-IDF Vectorizer for skills
    │   ├── edu.pkl            # LabelEncoder for Education levels
    │   └── target.pkl         # LabelEncoder for Target labels (Hire/Reject)
    ├── templates/screening/   # HTML Templates (form.html, result.html, bulk_result.html)
    └── static/                # CSS, JS, and image assets
```

---

## 5. Machine Learning Pipeline

The ML component is fully decoupled from the active training code, relying on serialized artifacts (`.pkl` files) to ensure rapid inference.

### Data Flow during Prediction:
1. **Input Reception**: Skills, Experience, Education, Projects Count.
2. **Text Vectorization**: The `skills` string is transformed into a numerical array using the pre-fitted TF-IDF Vectorizer (`tfidf.pkl`).
3. **Categorical Encoding**: The `education` string is transformed into an integer using the pre-fitted Label Encoder (`edu.pkl`).
4. **Feature Concatenation**: The TF-IDF array is combined with Experience, encoded Education, and Projects Count to form a single, unified feature vector (`np.hstack`).
5. **Inference**: The feature vector is passed to the trained Random Forest Classifier (`model.pkl`).
6. **Output Decoding**: The numeric prediction is translated back into 'Hire' or 'Reject' using the Target Label Encoder (`target.pkl`). The model also provides the calculated probability/confidence score.

---

## 6. Setup and Installation

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Installation Steps

1. **Clone/Navigate to the repository:**
   ```bash
   cd c:\projects\resume-shortlisting
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   To enable AI Resume Parsing, you must configure the Gemini API key. Add it to your environment variables or directly inside `resume_project/settings.py` (for local development only).
   ```python
   # In settings.py or via os.environ
   GEMINI_API_KEY = "your_google_gemini_api_key"
   ```

5. **Apply Database Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
   The application will be accessible at `http://127.0.0.1:8000/`.

---

## 7. Future Enhancements

- **Database Integration**: Currently, predictions are stateless. Storing uploaded candidate details and predictions in the database (`models.py`) would allow for historical tracking and auditing.
- **Asynchronous Processing**: Implement Celery/Redis for bulk CSV uploads and heavy resume parsing to prevent HTTP timeouts on massive datasets.
- **Expanded File Support**: Add support for `.rtf` and image-based PDFs using OCR (Optical Character Recognition).
- **Role-Based Access Control**: Implement Django Authentication to separate Recruiter and Admin views.
