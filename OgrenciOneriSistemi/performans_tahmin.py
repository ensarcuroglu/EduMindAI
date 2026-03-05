import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, RobustScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor
from sklearn.base import BaseEstimator, TransformerMixin
import shap  # *** YENİ İMPORT ***

# --- 1. VERİ YÜKLEME VE HAZIRLIK ---
try:
    df = pd.read_csv('D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv')
except FileNotFoundError:
    print("HATA: Dosya bulunamadı. Lütfen 'student_habits_performance.csv' dosyasının doğru yolda olduğundan emin olun.")
    raise

TARGET_COLUMN = 'exam_score'
if 'student_id' in df.columns:
    df = df.drop('student_id', axis=1)

y = df[TARGET_COLUMN]
X = df.drop(TARGET_COLUMN, axis=1)

# --- 2. ÖZELLİK GRUPLARINI BELİRLEME (BUDANMIŞ) ---

# A. Orijinal Sayısal Özellikler (Korunanlar)
numerical_features = [
    'age',
    'study_hours_per_day',
    'exercise_frequency'
]

# B. Yeni (Türetilmiş) Sayısal Özellikler
new_numerical_features = [
    'total_distraction_hours',
    'focus_ratio',
    'lifestyle_balance',
    'study_efficiency',
    'academic_engagement',
    'log_total_distraction'
]

all_numerical_features = numerical_features + new_numerical_features

# C. Nominal (Sırasız) Kategorik Özellikler
nominal_features = [
    'gender', 'part_time_job', 'extracurricular_participation'
]

# D. Ordinal (Sıralı) Kategorik Özellikler
ordinal_features = [
    'parental_education_level', 'diet_quality', 'internet_quality'
]

education_levels = ['None', 'High School', 'Bachelor', 'Master', 'PhD']
quality_levels = ['Poor', 'Average', 'Good']
internet_levels = ['Poor', 'Average', 'Good']


# --- 3. ÖZEL DÖNÜŞTÜRÜCÜ VE ÖN İŞLEME PIPLINES ---

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

numerical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', RobustScaler())
])

nominal_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

ordinal_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('ordinal', OrdinalEncoder(categories=[education_levels, quality_levels, internet_levels],
                                handle_unknown='use_encoded_value',
                                unknown_value=-1))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, all_numerical_features),
        ('nom', nominal_transformer, nominal_features),
        ('ord', ordinal_transformer, ordinal_features)
    ],
    remainder='drop' # Budama burada yapılıyor
)


# --- 4. VERİ BÖLME VE MODEL TANIMLAMA ---

X_train_full, X_test, y_train_full, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X_train_fit, X_train_eval, y_train_fit, y_train_eval = train_test_split(
    X_train_full, y_train_full, test_size=0.2, random_state=42
)

xgb_model = XGBRegressor(random_state=42, n_jobs=-1, early_stopping_rounds=10)

full_pipeline = Pipeline(steps=[
    ('feature_engineer', FeatureEngineer()),
    ('preprocessor', preprocessor),
    ('regressor', xgb_model)
])


# --- 5. HİPERPARAMETRE OPTİMİZASYONU (XGBOOST) ---

print("XGBoost Hiperparametre Optimizasyonu (RandomizedSearchCV) başlıyor...")

param_dist_xgb = {
    'regressor__n_estimators': [100, 200, 300, 500],
    'regressor__learning_rate': [0.01, 0.05, 0.1, 0.2],
    'regressor__max_depth': [3, 5, 7, 10],
    'regressor__subsample': [0.7, 0.8, 0.9, 1.0],
    'regressor__colsample_bytree': [0.7, 0.8, 0.9, 1.0]
}

random_search = RandomizedSearchCV(
    estimator=full_pipeline,
    param_distributions=param_dist_xgb,
    n_iter=60,
    scoring='neg_mean_squared_error',
    cv=5,
    verbose=2,
    n_jobs=-1,
    random_state=42
)

# eval_set için ön işleme
preprocessing_pipeline = Pipeline(steps=[
    ('feature_engineer', FeatureEngineer()),
    ('preprocessor', preprocessor)
])
X_train_fit_processed = preprocessing_pipeline.fit_transform(X_train_fit, y_train_fit)
X_train_eval_processed = preprocessing_pipeline.transform(X_train_eval)
eval_set = [(X_train_eval_processed, y_train_eval)]

random_search.fit(X_train_fit, y_train_fit,
                  regressor__eval_set=eval_set,
                  regressor__verbose=False)


print("Optimizasyon tamamlandı.")
best_model = random_search.best_estimator_
best_params = random_search.best_params_

print("\n--- OPTİMİZASYON SONUÇLARI (XGBOOST) ---")
print(f"En İyi Parametreler: {best_params}")
best_cv_score = np.sqrt(-random_search.best_score_)
print(f"Çapraz Doğrulama En İyi RMSE: {best_cv_score:.2f}")


# --- 6. FİNAL MODEL DEĞERLENDİRME ---

print("\nEn iyi model tüm eğitim verisiyle yeniden eğitiliyor...")
best_model.set_params(regressor__early_stopping_rounds=None)
best_model.fit(X_train_full, y_train_full)

print("\n--- FİNAL MODEL DEĞERLENDİRME (TEST SETİ) ---")
y_pred = best_model.predict(X_test)
final_mse = mean_squared_error(y_test, y_pred)
final_rmse = np.sqrt(final_mse)
final_r2 = r2_score(y_test, y_pred)

print(f"Test Veri Seti Boyutu: {len(X_test)}")
print(f"Kök Ortalama Karesel Hata (RMSE): {final_rmse:.2f}")
print(f"R-Kare (R2 Score): {final_r2:.4f}")
print("--------------------------------------------------")


# --- 7. ÖZELLİK ÖNEMİ ANALİZİ (FİNAL MODEL) ---

xgb_regressor = best_model.named_steps['regressor']
feature_importances = xgb_regressor.feature_importances_

try:
    ohe_feature_names = list(best_model.named_steps['preprocessor']
                             .named_transformers_['nom']
                             .named_steps['onehot']
                             .get_feature_names_out(nominal_features))
except AttributeError:
    ohe_feature_names = list(best_model.named_steps['preprocessor']
                             .named_transformers_['nom']
                             .named_steps['onehot']
                             .get_feature_names(nominal_features))

ord_feature_names = ordinal_features
all_feature_names = all_numerical_features + ohe_feature_names + ord_feature_names

importance_df = pd.DataFrame({
    'Feature': all_feature_names,
    'Importance': feature_importances
})
importance_df = importance_df.sort_values(by='Importance', ascending=False)

print("\n--- XGBOOST İLE ÖZELLİK ÖNEMİ (TOP 10 FAKTÖR) ---")
print(importance_df.head(10).to_string(index=False))


# --- 7.5. SHAP İLE MODEL YORUMLAMA ---
print("\nSHAP analiz grafikleri oluşturuluyor...")

# Adım 1: Pipeline'dan 'regressor' (XGBoost) ve 'preprocessor' (işlemci) adımlarını al
xgb_regressor = best_model.named_steps['regressor']
# Veriyi dönüştürmek için 'feature_engineer' ve 'preprocessor' adımlarını al
# Not: best_model.fit() çağrıldığı için bu adımlar zaten eğitilmiştir.
preprocessing_pipeline = Pipeline(steps=[
    ('feature_engineer', best_model.named_steps['feature_engineer']),
    ('preprocessor', best_model.named_steps['preprocessor'])
])

# Adım 2: Test verisini (X_test) modele girdiği formatta işle
# SHAP, modelin gördüğü son formatta (ölçeklenmiş, kodlanmış) veriye ihtiyaç duyar
X_test_transformed = preprocessing_pipeline.transform(X_test)

# Adım 3: SHAP Explainer'ı (Açıklayıcı) ve SHAP değerlerini oluştur
# TreeExplainer, XGBoost gibi ağaç tabanlı modeller için en hızlısıdır
explainer = shap.TreeExplainer(xgb_regressor)
shap_values = explainer.shap_values(X_test_transformed)

# Adım 4: Grafikleri Çizdirme

# GRAFİK 1: Özet Grafiği (Beeswarm)
# Bu, en önemli grafiktir. Özelliklerin önemini, etkisinin yönünü (pozitif/negatif)
# ve o etkinin büyüklüğünü tek seferde gösterir.
print("SHAP Özet Grafiği (Beeswarm) oluşturuluyor...")
plt.figure(figsize=(10, 8)) # SHAP için bir figür alanı ayarla
shap.summary_plot(
    shap_values,
    X_test_transformed,
    feature_names=all_feature_names,
    show=False, # Grafiği hemen gösterme
    max_display=15 # En önemli 15 özelliği göster
)
plt.title("SHAP Özellik Etki Özeti")
plt.tight_layout()
plt.show() # Grafiği şimdi göster


# GRAFİK 2: Bağımlılık Grafiği (Dependence Plot)
# En önemli özelliğinizin (örn: 'focus_ratio') skoru nasıl etkilediğini detaylıca gösterir.
print("SHAP Bağımlılık Grafiği (focus_ratio) oluşturuluyor...")
plt.figure() # Yeni bir figür alanı
top_feature = importance_df.iloc[0]['Feature'] # En önemli özelliği al ('focus_ratio')
shap.dependence_plot(
    top_feature,
    shap_values,
    X_test_transformed,
    feature_names=all_feature_names,
    interaction_index=None, # Otomatik olarak en iyi etkileşimi bul
    show=False
)
plt.title(f"SHAP Bağımlılık Grafiği - {top_feature}")
plt.tight_layout()
plt.show()



# --- 7.6. SHAP İLE BİREYSEL TAHMİN ANALİZİ ---
print("\nSHAP Bireysel Analiz Grafiği (Waterfall) oluşturuluyor...")

# Analiz etmek için test setinden bir öğrenci seçelim (örn. ilk öğrenci, index 0)
student_index = 0
student_transformed_data = X_test_transformed[student_index]
student_shap_values = shap_values[student_index]
base_value = explainer.expected_value

# 'base_value' modelin ortalama tahminidir.
# Waterfall plot, bu ortalamadan başlayarak özelliklerin skoru nasıl
# 'final_prediction'a (base_value + sum(shap_values)) getirdiğini gösterir.
plt.figure()
shap.waterfall_plot(
    shap.Explanation(
        values=student_shap_values,
        base_values=base_value,
        data=student_transformed_data,
        feature_names=all_feature_names
    ),
    max_display=10, # En etkili 10 faktörü göster
    show=True
)

# --- 8. GRAFİKSEL GÖSTERİM (Devam) ---
print("\nDiğer grafikler oluşturuluyor...")

# Özellik Önemi Grafiği (XGBoost'un kendi)
plt.figure(figsize=(10, 7))
sns.barplot(x='Importance', y='Feature', data=importance_df.head(10), hue='Feature', palette='viridis', legend=False)
plt.title('Öğrenci Performansı Tahmininde En Önemli 10 Özellik (XGBoost)')
plt.xlabel('Özellik Önemi (Normalized)')
plt.ylabel('Özellik Adı')
plt.tight_layout()
plt.show() # Grafiği göster

# Hata Dağılımı Grafiği (Gerçek vs Tahmin)
plt.figure(figsize=(10, 6))
sns.scatterplot(x=y_test, y=y_pred, alpha=0.6)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], '--r', linewidth=2)
plt.title('Gerçek Notlar vs. Tahmin Edilen Notlar')
plt.xlabel('Gerçek Not (y_test)')
plt.ylabel('Tahmin Edilen Not (y_pred)')
plt.tight_layout()
plt.show() # Grafiği göster


print("\n--- İŞLEM TAMAMLANDI ---")
print(f"Geliştirilen en iyi model: Optimize Edilmiş XGBoost Regressor (Budanmış Özellikler ile)")
print(f"Final Performans: RMSE = {final_rmse:.2f}, R2 = {final_r2:.4f}")

import joblib, json, time, os

os.makedirs("artifacts", exist_ok=True)

# 1) Model (tüm pipeline)
model_path = f"artifacts/student_score_xgb_pipeline.joblib"
joblib.dump(best_model, model_path)

# 2) En iyi parametreler ve metrikler
meta = {
    "best_params": best_params,
    "cv_rmse": float(best_cv_score),
    "test_rmse": float(final_rmse),
    "test_r2": float(final_r2),
    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "code_version": "v1.0"  # kendi versiyonun
}
with open("artifacts/metrics_and_params.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"Model kaydedildi: {model_path}")