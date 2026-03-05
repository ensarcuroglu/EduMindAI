# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import pandas as pd
import numpy as np
# Sklearn sınıflarını eklememiz şart
from sklearn.base import BaseEstimator, TransformerMixin


# =============================================================================
# JOBBLIB İÇİN GEREKLİ SINIF
# =============================================================================
class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        X_['total_distraction_hours'] = X_['social_media_hours'] + X_['netflix_hours']
        X_['focus_ratio'] = X_['study_hours_per_day'] / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = X_['sleep_hours'] / (X_['study_hours_per_day'] + 1)
        X_['study_efficiency'] = X_['study_hours_per_day'] * X_['mental_health_rating']
        X_['academic_engagement'] = X_['attendance_percentage'] * X_['study_hours_per_day']
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])
        return X_


# =============================================================================

from oneri_motoru import SmartAdvisor

app = FastAPI()
advisor = SmartAdvisor()


# --- YENİ EKLENEN TEMİZLEME FONKSİYONU ---
def convert_numpy_to_python(obj):
    """
    Numpy veri tiplerini (float32, int64, ndarray) standart Python
    tiplerine (float, int, list) çevirir. JSON hatasını önler.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(i) for i in obj]
    else:
        return obj


class StudentData(BaseModel):
    student_id: str = "Unknown"
    age: int
    gender: str
    study_hours_per_day: float
    social_media_hours: float
    netflix_hours: float
    attendance_percentage: float
    sleep_hours: float
    diet_quality: str
    mental_health_rating: int
    internet_quality: str
    parental_education_level: str
    exercise_frequency: int
    part_time_job: str
    extracurricular_participation: str


@app.get("/")
def home():
    return {"message": "Student AI Advisor API is running"}


@app.post("/predict")
def predict_performance(data: StudentData):
    try:
        student_dict = data.dict()

        # 1. Analizi yap
        raw_result = advisor.generate_advice(student_dict)

        # 2. Sonucu temizle (Numpy -> Python dönüşümü)
        clean_result = convert_numpy_to_python(raw_result)

        return clean_result
    except Exception as e:
        print(f"HATA OLUŞTU: {str(e)}")
        # Hatayı daha detaylı görmek için traceback ekleyebiliriz
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)