#performans_tahmin_V2.py:
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import json
import os
import joblib
import shap

from sklearn.model_selection import train_test_split, RandomizedSearchCV, KFold
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, RobustScaler
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from xgboost import XGBRegressor
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import set_config

set_config(transform_output="pandas")

# --- 1. ÖZEL DÖNÜŞTÜRÜCÜLER (PIPELINE İÇİN) ---

class OutlierCapper(BaseEstimator, TransformerMixin):
    """
    Aykırı değerleri (Outliers) IQR yöntemiyle alt ve üst sınırlara baskılar.
    Modelin uç değerlerden (örn: günde 25 saat ders) sapmasını engeller.
    """

    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        # Sadece sayısal sütunlara uygulanır
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        X_ = X.copy()
        for col in self.columns_to_cap:
            if col in X_.columns:
                Q1 = X_[col].quantile(0.25)
                Q3 = X_[col].quantile(0.75)
                IQR = Q3 - Q1
                self.lower_bounds_[col] = Q1 - self.factor * IQR
                self.upper_bounds_[col] = Q3 + self.factor * IQR
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        for col, lower in self.lower_bounds_.items():
            if col in X_.columns:
                upper = self.upper_bounds_[col]
                X_[col] = np.clip(X_[col], lower, upper)
        return X_


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Ham verilerden modelin daha iyi anlayacağı 'Zeka Dolu' özellikler türetir.
    V2 GÜNCELLEMESİ: Yeni etkileşim terimleri eklendi.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()

        # --- Temel Türetimler (V1) ---
        X_['total_distraction_hours'] = X_['social_media_hours'] + X_['netflix_hours']
        # 0'a bölme hatasını önlemek için +1 ekliyoruz
        X_['focus_ratio'] = X_['study_hours_per_day'] / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = X_['sleep_hours'] / (X_['study_hours_per_day'] + 1)
        X_['study_efficiency'] = X_['study_hours_per_day'] * X_['mental_health_rating']
        X_['academic_engagement'] = X_['attendance_percentage'] * X_['study_hours_per_day']
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        # --- İleri Seviye Türetimler (V2) ---

        # 1. Zindelik Skoru (Vitality): Uyku kalitesi ile egzersizin sinerjisi
        # Egzersiz yapan ve iyi uyuyan öğrenci daha dinçtir.
        X_['vitality_score'] = (X_['sleep_hours'] ** 1.2) * (X_['exercise_frequency'] + 1)

        # 2. Tükenmişlik Riski (Burnout Risk):
        # Part-time çalışıp çok ders çalışan öğrenci yorgun düşebilir.
        part_time_val = np.where(X_['part_time_job'] == 'Yes', 1.5, 1.0)
        X_['burnout_risk'] = X_['study_hours_per_day'] * part_time_val

        # 3. Adanmışlık (Dedication):
        # Okul dışı aktiviteye katılıp devamsızlığı az olan öğrenci "sosyal inektir".
        extra_curr_val = np.where(X_['extracurricular_participation'] == 'Yes', 1.2, 1.0)
        X_['dedication_level'] = X_['attendance_percentage'] * extra_curr_val

        return X_

if __name__ == "__main__":

    # --- 2. VERİ YÜKLEME ---
    try:
        # Veri yolunu kendi yapına göre güncelle
        df = pd.read_csv('D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv')
        print("Veri seti başarıyla yüklendi.")
    except FileNotFoundError:
        print("HATA: Veri dosyası bulunamadı.")
        raise

    TARGET_COLUMN = 'exam_score'
    if 'student_id' in df.columns:
        df = df.drop('student_id', axis=1)

    y = df[TARGET_COLUMN]
    X = df.drop(TARGET_COLUMN, axis=1)

    # --- 3. ÖZELLİK GRUPLARINI BELİRLEME ---

    # Orijinal Sayısal
    numerical_features = ['study_hours_per_day', 'exercise_frequency', 'sleep_hours',
                          'social_media_hours', 'netflix_hours', 'attendance_percentage', 'mental_health_rating']

    # Türetilmiş Sayısal (Pipeline içinde oluşacaklar)
    derived_features = ['total_distraction_hours', 'focus_ratio', 'lifestyle_balance',
                        'study_efficiency', 'academic_engagement', 'log_total_distraction',
                        'vitality_score', 'burnout_risk', 'dedication_level']

    all_numeric = numerical_features + derived_features

    nominal_features = ['gender', 'part_time_job', 'extracurricular_participation']
    ordinal_features = ['parental_education_level', 'diet_quality', 'internet_quality']

    education_levels = ['None', 'High School', 'Bachelor', 'Master', 'PhD']
    quality_levels = ['Poor', 'Average', 'Good']
    internet_levels = ['Poor', 'Average', 'Good']

    # --- 4. PIPELINE KURULUMU ---

    # Sayısal Dönüşüm: İmpute -> Outlier Capping -> Scaling
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('capper', OutlierCapper(factor=1.5)),  # V2 YENİLİK
        ('scaler', RobustScaler())
    ])

    nominal_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    ordinal_transformer = Pipeline(steps=[
        # 1. Önce NaN'ları koruyarak sayıya çevir
        ('ordinal', OrdinalEncoder(categories=[education_levels, quality_levels, internet_levels],
                                   handle_unknown='use_encoded_value', unknown_value=np.nan)),
        # 2. Sayısal boşlukları en yakın 5 komşuya bakarak doldur
        ('imputer', KNNImputer(n_neighbors=5)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, all_numeric),
            ('nom', nominal_transformer, nominal_features),
            ('ord', ordinal_transformer, ordinal_features)
        ],
        remainder='drop'
    )

    # XGBoost Modeli (Temel Ayarlar)
    xgb_base = XGBRegressor(
        random_state=42,
        n_jobs=-1,
        objective='reg:squarederror',
        booster='gbtree'
    )

    # Ana Pipeline
    # FeatureEngineer -> Preprocessor -> Model
    main_pipeline = Pipeline(steps=[
        ('feature_engineer', FeatureEngineer()),
        ('preprocessor', preprocessor),
        ('regressor', xgb_base)
    ])

    # V2 YENİLİK: TransformedTargetRegressor
    # Hedef değişkeni (Score) logaritmik ölçeğe çevirir, tahminden sonra geri çevirir.
    # Bu, hatayı normalleştirir ve performansı artırır.
    final_pipeline = TransformedTargetRegressor(
        regressor=main_pipeline,
        func=np.log1p,  # Log(y+1) uygula
        inverse_func=np.expm1  # Exp(y)-1 ile geri çevir
    )

    # --- 5. VERİ BÖLME ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- 6. HİPERPARAMETRE OPTİMİZASYONU (V3.1 - GÜVENLİ GRID SEARCH MODU) ---
    print("\n🚀 Model Eğitimi ve Optimizasyonu Başlıyor (Grid Search)...")

    from sklearn.model_selection import GridSearchCV

    # Parametre uzayını "Overfitting"i engelleyecek şekilde güncelledik.
    # Daha sığ ağaçlar (depth 3-4) ve daha yüksek gürültü filtresi (min_child_weight) kullanıyoruz.

    param_grid = {
        # Ağaç sayısı: 500 idealdir, çok artırmak bazen ezberletir
        'regressor__regressor__n_estimators': [400, 500, 600],

        # Öğrenme hızı: Düşük olması genellemeyi artırır
        'regressor__regressor__learning_rate': [0.008, 0.01, 0.012],

        # Derinlik: 6 çok riskliydi, 3 ve 4 ile sınırlandırdık (Daha basit modeller)
        'regressor__regressor__max_depth': [3, 4],

        # Gürültü Engelleme: Bu değer arttıkça model detaylarda kaybolmaz
        'regressor__regressor__min_child_weight': [7, 10, 15],

        # Rassallık: Her ağaçta verinin %60-70'ini görsün
        'regressor__regressor__subsample': [0.6, 0.7],
        'regressor__regressor__colsample_bytree': [0.6, 0.7],

        # Regularization (L1/L2): Cezalandırmayı artırdık
        'regressor__regressor__reg_alpha': [0.05, 0.1],
        'regressor__regressor__reg_lambda': [1.5, 2.0, 3.0]
    }

    # GridSearchCV: Halving gibi adayları elemez, hepsini dener.
    # 1000 satırlık veri için en güvenilir yöntem budur.
    search = GridSearchCV(
        estimator=final_pipeline,
        param_grid=param_grid,
        cv=10,  # 10 Katlı CV ile sonucun şans eseri olmadığından emin olacağız
        scoring='neg_mean_squared_error',
        verbose=1,
        n_jobs=-1
    )

    start_time = time.time()
    search.fit(X_train, y_train)
    elapsed_time = time.time() - start_time

    print(f"\n✅ Grid Search Optimizasyonu tamamlandı ({elapsed_time:.1f} sn).")

    # Değişken ismini koruyoruz ki alt satırlar bozulmasın
    random_search = search

    best_model_wrapper = random_search.best_estimator_
    # İçteki pipeline'a erişim (metrics json için)
    best_pipeline = best_model_wrapper.regressor_
    best_xgb = best_pipeline.named_steps['regressor']

    print("\n--- EN İYİ HİPERPARAMETRELER ---")
    print(random_search.best_params_)


    # --- 7. PERFORMANS DEĞERLENDİRME ---
    print("\n--- MODEL PERFORMANS METRİKLERİ ---")

    # Eğitim seti skoru
    y_train_pred = best_model_wrapper.predict(X_train)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_r2 = r2_score(y_train, y_train_pred)

    # Test seti skoru
    y_test_pred = best_model_wrapper.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)

    print(f"Eğitim Seti RMSE : {train_rmse:.4f}")
    print(f"Eğitim Seti R2   : {train_r2:.4f}")
    print("-" * 30)
    print(f"TEST SETİ RMSE   : {test_rmse:.4f}")
    print(f"TEST SETİ MAE    : {test_mae:.4f}")
    print(f"TEST SETİ R2     : {test_r2:.4f}")

    # Overfitting kontrolü
    if (train_r2 - test_r2) > 0.10:
        print("⚠️ UYARI: Modelde overfitting (ezberleme) riski var.")
    else:
        print("✅ Model kararlı ve genelleştirilebilir görünüyor.")

    # --- 8. GRAFİKLER ---

    # Tahmin vs Gerçek
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_test, y=y_test_pred, alpha=0.6, color='#2980b9')
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], '--r', linewidth=2)
    plt.title(f'Gerçek vs Tahmin (R2: {test_r2:.3f}) - V2 Model')
    plt.xlabel('Gerçek Notlar')
    plt.ylabel('Tahmin Edilen Notlar')
    plt.tight_layout()
    plt.show()

    # --- 9. SHAP ANALİZİ (V2 UYUMLU) ---
    # TransformedTargetRegressor kullandığımız için SHAP'e veriyi verirken dikkatli olmalıyız.
    # Ham modeli ve transform edilmiş veriyi alacağız.

    print("\nSHAP analizi hazırlanıyor...")

    # 1. Pipeline'ın içinden ön işleyici ve modeli çıkar
    preprocessor_step = best_pipeline.named_steps['preprocessor']
    feature_engineer_step = best_pipeline.named_steps['feature_engineer']
    final_regressor = best_pipeline.named_steps['regressor']

    # 2. Test verisini modele girdiği hale getir (Feature Eng -> Preprocess)
    X_test_eng = feature_engineer_step.transform(X_test)
    X_test_processed = preprocessor_step.transform(X_test_eng)

    # 3. Özellik isimlerini al
    try:
        ohe_names = preprocessor_step.named_transformers_['nom']['onehot'].get_feature_names_out(nominal_features)
        feature_names = all_numeric + list(ohe_names) + ordinal_features
    except:
        feature_names = [f"Feature_{i}" for i in range(X_test_processed.shape[1])]

    # 4. SHAP Hesapla
    explainer = shap.TreeExplainer(final_regressor)
    shap_values = explainer.shap_values(X_test_processed)

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test_processed, feature_names=feature_names, show=False)
    plt.title("SHAP Özellik Önem Haritası (V2)")
    plt.tight_layout()
    plt.show()

    # --- 10. MODEL KAYDETME ---
    os.makedirs("artifacts", exist_ok=True)

    # ÖNEMLİ: API'nin kullanacağı pipeline 'best_pipeline' dır.
    # TransformedTargetRegressor wrapper'ı API'de kullanmak zordur (inverse_func vs).
    # Bu yüzden içindeki ana pipeline'ı kaydediyoruz.
    # Ancak log dönüşümü yapıldığı için API tarafında da log dönüşümünü hesaba katmalıyız
    # YA DA direkt wrapper'ı kaydedip API'de onu kullanırız (En temiz yöntem wrapper'ı kaydetmektir).

    model_save_path = "artifacts/student_score_xgb_pipeline_v2.joblib"
    joblib.dump(best_model_wrapper, model_save_path)

    # Metrikleri kaydet
    metrics = {
        "version": "V2.0",
        "algorithm": "XGBoost + TargetTransform + OutlierCapping",
        "test_rmse": float(test_rmse),
        "test_r2": float(test_r2),
        "best_params": random_search.best_params_,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open("artifacts/metrics_and_params.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Model kaydedildi: {model_save_path}")
    print("Tebrikler! V2 Modeliniz servise hazır.")