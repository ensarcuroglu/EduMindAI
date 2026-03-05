# metrics_report.py

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import set_config

# --- AYARLAR ---
OUTPUT_DIR = "analiz_raporlari"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --- GEREKLİ SINIFLAR (Modeli yüklemek için) ---
class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None): return self

    def transform(self, X, y=None): return X


class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        # Temel türetimler
        sm = X_.get('social_media_hours', 0)
        nf = X_.get('netflix_hours', 0)
        X_['total_distraction_hours'] = sm + nf
        study = X_.get('study_hours_per_day', 0)
        sleep = X_.get('sleep_hours', 0)
        X_['focus_ratio'] = study / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = sleep / (study + 1)
        mh = X_.get('mental_health_rating', 5)
        X_['study_efficiency'] = study * mh
        att = X_.get('attendance_percentage', 0)
        X_['academic_engagement'] = att * study
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])
        ex = X_.get('exercise_frequency', 0)
        X_['vitality_score'] = (sleep ** 1.2) * (ex + 1)
        pt_val = 1.0
        if 'part_time_job' in X_.columns:
            pt_val = np.where(X_['part_time_job'] == 'Yes', 1.5, 1.0) if X_['part_time_job'].dtype == 'object' else 1.0
        X_['burnout_risk'] = study * pt_val
        ec_val = 1.0
        if 'extracurricular_participation' in X_.columns:
            ec_val = np.where(X_['extracurricular_participation'] == 'Yes', 1.2, 1.0) if X_[
                                                                                             'extracurricular_participation'].dtype == 'object' else 1.0
        X_['dedication_level'] = att * ec_val
        return X_


def generate_performance_report():
    print("📊 MODEL PERFORMANS METRİKLERİ HESAPLANIYOR...")

    # 1. Yükleme
    MODEL_PATH = "artifacts/student_score_xgb_pipeline_v2.joblib"
    csv_paths = ["student_habits_performance.csv", "data/student_habits_performance.csv",
                 r"D:\Ensar Dosya\OgrenciOneriSistemi\student_habits_performance.csv"]
    DATA_PATH = next((p for p in csv_paths if os.path.exists(p)), None)

    if not DATA_PATH or not os.path.exists(MODEL_PATH):
        print("❌ Dosyalar eksik.")
        return

    model = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)
    set_config(transform_output="pandas")

    # 2. Veri Bölme (Eğitim sırasındaki seed ile aynı olmalı: random_state=42)
    X = df.drop('exam_score', axis=1, errors='ignore')
    y = df['exam_score']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Tahminler
    print("🤖 Tahminler yapılıyor...")
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    # 4. Metrik Hesaplama
    metrics = {
        "Train": {
            "RMSE": np.sqrt(mean_squared_error(y_train, y_train_pred)),
            "MAE": mean_absolute_error(y_train, y_train_pred),
            "R2": r2_score(y_train, y_train_pred)
        },
        "Test": {
            "RMSE": np.sqrt(mean_squared_error(y_test, y_test_pred)),
            "MAE": mean_absolute_error(y_test, y_test_pred),
            "R2": r2_score(y_test, y_test_pred)
        }
    }

    # 5. Ekrana Yazdırma (Tablo Formatı)
    print("\n" + "=" * 50)
    print(f"{'METRİK':<10} | {'EĞİTİM (TRAIN)':<15} | {'TEST (TEST)':<15}")
    print("-" * 50)
    print(f"{'RMSE':<10} | {metrics['Train']['RMSE']:<15.4f} | {metrics['Test']['RMSE']:<15.4f}")
    print(f"{'MAE':<10} | {metrics['Train']['MAE']:<15.4f} | {metrics['Test']['MAE']:<15.4f}")
    print(f"{'R²':<10} | {metrics['Train']['R2']:<15.4f} | {metrics['Test']['R2']:<15.4f}")
    print("=" * 50 + "\n")

    # 6. Dosyaya Kaydetme
    txt_path = os.path.join(OUTPUT_DIR, "model_performance_metrics.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Tablo 4.1. XGBoost Modeli Performans Metrikleri\n")
        f.write("=" * 60 + "\n")
        f.write(f"{'Metrik':<15} | {'Eğitim Seti (Train)':<20} | {'Test Seti (Test)':<20}\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'RMSE':<15} | {metrics['Train']['RMSE']:<20.4f} | {metrics['Test']['RMSE']:<20.4f}\n")
        f.write(f"{'MAE':<15} | {metrics['Train']['MAE']:<20.4f} | {metrics['Test']['MAE']:<20.4f}\n")
        f.write(f"{'R² (R-Kare)':<15} | {metrics['Train']['R2']:<20.4f} | {metrics['Test']['R2']:<20.4f}\n")
        f.write("-" * 60 + "\n")

        diff_r2 = metrics['Train']['R2'] - metrics['Test']['R2']
        f.write(f"\nGenelleştirme Farkı (Train R2 - Test R2): {diff_r2:.4f}\n")
        if diff_r2 < 0.05:
            f.write("SONUÇ: Modelde aşırı öğrenme (Overfitting) yoktur. Kararlıdır.\n")
        else:
            f.write("SONUÇ: Modelde hafif aşırı öğrenme eğilimi olabilir.\n")

    print(f"✅ Rapor dosyaya kaydedildi: {txt_path}")


if __name__ == "__main__":
    generate_performance_report()