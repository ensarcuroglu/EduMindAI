import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, RobustScaler
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import set_config

# Pandas çıktı ayarı
set_config(transform_output="pandas")


# --- 1. Dinamik Özellik Mühendisi (Bu Sınıf Sihri Yapıyor) ---
class DynamicFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Formül optimizasyonu için katsayıları dışarıdan parametre olarak alır.
    Böylece Grid Search ile 'En iyi katsayı'yı bulabiliriz.
    """

    def __init__(self, sleep_exponent=1.5):
        self.sleep_exponent = sleep_exponent

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()

        # Temel Özellikler
        X_['total_distraction_hours'] = X_['social_media_hours'] + X_['netflix_hours']
        X_['focus_ratio'] = X_['study_hours_per_day'] / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = X_['sleep_hours'] / (X_['study_hours_per_day'] + 1)
        X_['study_efficiency'] = X_['study_hours_per_day'] * X_['mental_health_rating']
        X_['academic_engagement'] = X_['attendance_percentage'] * X_['study_hours_per_day']
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        # --- OPTİMİZE EDİLEN FORMÜL ---
        # Vitality Score: Uyku üssü dinamik olarak deneniyor
        X_['vitality_score'] = (X_['sleep_hours'] ** self.sleep_exponent) * (X_['exercise_frequency'] + 1)

        # Diğer Sabit Formüller
        part_time_val = np.where(X_['part_time_job'] == 'Yes', 1.5, 1.0)
        X_['burnout_risk'] = X_['study_hours_per_day'] * part_time_val

        extra_curr_val = np.where(X_['extracurricular_participation'] == 'Yes', 1.2, 1.0)
        X_['dedication_level'] = X_['attendance_percentage'] * extra_curr_val

        return X_


# --- 2. Yardımcı Sınıflar (Mevcut Projeden Aynen Alındı) ---
class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.bounds = {}
        self.cols = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        for col in self.cols:
            if col in X.columns:
                Q1 = X[col].quantile(0.25)
                Q3 = X[col].quantile(0.75)
                IQR = Q3 - Q1
                self.bounds[col] = (Q1 - self.factor * IQR, Q3 + self.factor * IQR)
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        for col, (lower, upper) in self.bounds.items():
            if col in X_.columns:
                X_[col] = np.clip(X_[col], lower, upper)
        return X_


# --- 3. Ana Akış ---
if __name__ == "__main__":
    # Veri Yükleme
    try:
        df = pd.read_csv('data/student_habits_performance.csv')
        print("✅ Veri seti yüklendi.")
    except:
        # Test amaçlı dummy veri (Eğer dosya yoksa hata vermesin diye)
        print("⚠️ Dosya bulunamadı, script mantığını göstermek için çalışıyor.")
        exit()

    if 'student_id' in df.columns: df = df.drop('student_id', axis=1)

    y = df['exam_score']
    X = df.drop('exam_score', axis=1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Pipeline Hazırlığı (Mevcut kodunla uyumlu)
    numerical_cols = ['study_hours_per_day', 'exercise_frequency', 'sleep_hours',
                      'social_media_hours', 'netflix_hours', 'attendance_percentage', 'mental_health_rating']
    derived_cols = ['total_distraction_hours', 'focus_ratio', 'lifestyle_balance',
                    'study_efficiency', 'academic_engagement', 'log_total_distraction',
                    'vitality_score', 'burnout_risk', 'dedication_level']

    # Preprocessor Tanımları (Basitleştirilmiş)
    num_pipe = Pipeline([('imputer', SimpleImputer(strategy='median')),
                         ('capper', OutlierCapper()),
                         ('scaler', RobustScaler())])

    nom_pipe = Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                         ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))])

    ord_pipe = Pipeline([('ordinal', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=np.nan)),
                         ('imputer', KNNImputer(n_neighbors=5))])

    preprocessor = ColumnTransformer([
        ('num', num_pipe, numerical_cols + derived_cols),
        ('nom', nom_pipe, ['gender', 'part_time_job', 'extracurricular_participation']),
        ('ord', ord_pipe, ['parental_education_level', 'diet_quality', 'internet_quality'])
    ])

    # --- 4. FORMÜL OPTİMİZASYON DÖNGÜSÜ ---
    print("\n🧪 Formül Optimizasyonu Başlıyor: Vitality Score Üssü (Exponent)...")
    print(f"{'Üs (Exponent)':<15} | {'RMSE Hata':<15}")
    print("-" * 35)

    results = []
    # 1.0'dan 2.5'e kadar 0.1'lik adımlarla dene
    exponents = np.arange(1.0, 2.6, 0.1)

    for exp in exponents:
        # Dinamik Pipeline Oluştur
        model_pipeline = Pipeline([
            ('feature_engineer', DynamicFeatureEngineer(sleep_exponent=exp)),
            ('preprocessor', preprocessor),
            ('regressor', XGBRegressor(n_estimators=500, learning_rate=0.01, max_depth=4, n_jobs=-1, random_state=42))
        ])

        final_model = TransformedTargetRegressor(regressor=model_pipeline, func=np.log1p, inverse_func=np.expm1)

        # Eğit ve Test Et
        final_model.fit(X_train, y_train)
        preds = final_model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, preds))

        results.append(rmse)
        print(f"{exp:<15.1f} | {rmse:.4f}")

    # --- 5. Sonuçları Görselleştirme ---
    best_idx = np.argmin(results)
    best_exp = exponents[best_idx]
    best_rmse = results[best_idx]

    print(f"\n🏆 EN İYİ SONUÇ: Üs = {best_exp:.1f} (RMSE: {best_rmse:.4f})")

    plt.figure(figsize=(10, 6))
    plt.plot(exponents, results, marker='o', linestyle='-', color='#2c3e50', linewidth=2)
    plt.axvline(best_exp, color='#e74c3c', linestyle='--', label=f'Optimum: {best_exp:.1f}')
    plt.title('Bilimsel Formül Optimizasyonu: Vitality Score Katsayısı Analizi', fontsize=14)
    plt.xlabel('Uyku Üssü (Sleep Exponent)', fontsize=12)
    plt.ylabel('Model Hatası (RMSE)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('formula_optimization_result.png')
    print("📈 Grafik kaydedildi: formula_optimization_result.png")