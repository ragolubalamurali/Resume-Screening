"""
ML Model loader module.

Loads the trained model and preprocessing artifacts once at module import time
to avoid repeated disk I/O on every request.
"""
import pickle
import logging
import warnings
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Suppress scikit-learn version mismatch warnings
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

# Resolve paths relative to this file
_MODEL_DIR = Path(__file__).resolve().parent

# Lazy-loaded singletons
_model = None
_tfidf = None
_le_edu = None
_le_target = None
_loaded = False


def _load_artifacts():
    """Load all .pkl artifacts from disk (called once)."""
    global _model, _tfidf, _le_edu, _le_target, _loaded

    if _loaded:
        return

    artifacts = {
        'model': _MODEL_DIR / 'model.pkl',
        'tfidf': _MODEL_DIR / 'tfidf.pkl',
        'edu': _MODEL_DIR / 'edu.pkl',
        'target': _MODEL_DIR / 'target.pkl',
    }

    # Verify all files exist before loading
    for name, path in artifacts.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Required ML artifact '{name}.pkl' not found at: {path}"
            )

    try:
        with open(artifacts['model'], 'rb') as f:
            _model = pickle.load(f)
        with open(artifacts['tfidf'], 'rb') as f:
            _tfidf = pickle.load(f)
        with open(artifacts['edu'], 'rb') as f:
            _le_edu = pickle.load(f)
        with open(artifacts['target'], 'rb') as f:
            _le_target = pickle.load(f)
        _loaded = True
        logger.info("ML artifacts loaded successfully from %s", _MODEL_DIR)
    except Exception as e:
        logger.error("Failed to load ML artifacts: %s", e)
        raise


def get_model():
    """Return the trained RandomForestClassifier."""
    _load_artifacts()
    return _model


def get_tfidf():
    """Return the fitted TfidfVectorizer."""
    _load_artifacts()
    return _tfidf


def get_edu_encoder():
    """Return the fitted LabelEncoder for Education."""
    _load_artifacts()
    return _le_edu


def get_target_encoder():
    """Return the fitted LabelEncoder for target (Hire/Reject)."""
    _load_artifacts()
    return _le_target


def predict_candidate(skills: str, experience: float, education: str, projects_count: int):
    """
    Run prediction for a single candidate.

    Args:
        skills: Comma-separated skills string.
        experience: Years of experience.
        education: Education level (B.Sc, B.Tech, M.Tech, MBA, PhD).
        projects_count: Number of projects completed.

    Returns:
        dict with 'prediction' (str), 'confidence' (float),
        'probabilities' (dict of class->prob).
    """
    model = get_model()
    tfidf = get_tfidf()
    le_edu = get_edu_encoder()
    le_target = get_target_encoder()

    # Transform skills via TF-IDF (same as training)
    skills_vector = tfidf.transform([skills]).toarray()

    # Encode education level
    edu_encoded = le_edu.transform([education])

    # Combine features: [tfidf_features, experience, education_encoded, projects_count]
    # This matches the training pipeline: np.hstack((skills_matrix, other_features))
    # where other_features = df[['Experience (Years)', 'Education', 'Projects Count']].values
    final_features = np.hstack((
        skills_vector,
        [[experience, edu_encoded[0], projects_count]]
    ))

    # Predict
    prediction_encoded = model.predict(final_features)
    prediction_label = le_target.inverse_transform(prediction_encoded)[0]

    # Confidence via predict_proba
    probabilities = model.predict_proba(final_features)[0]
    class_labels = le_target.inverse_transform(model.classes_)
    prob_dict = {label: round(float(prob) * 100, 2) for label, prob in zip(class_labels, probabilities)}

    # Confidence is the probability of the predicted class
    confidence = prob_dict[prediction_label]

    return {
        'prediction': prediction_label,
        'confidence': confidence,
        'probabilities': prob_dict,
    }
