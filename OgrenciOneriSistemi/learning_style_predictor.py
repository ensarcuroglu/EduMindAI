import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, log_loss


# ---------------------------------------------------------
# YARDIMCI FONKSİYON: ÖZELLİK MÜHENDİSLİĞİ (AYNI KALIYOR)
# ---------------------------------------------------------
def engineer_features(df):
    """
    Ham verilerden öğrenme stiline yönelik türetilmiş özellikler oluşturur.
    """
    df_eng = df.copy()

    # 1. Tech_Score (Görsel Potansiyeli)
    df_eng['Tech_Score'] = df_eng['OnlineCourses'] * (1 + df_eng['EduTech'])

    # 2. Social_Score (İşitsel Potansiyeli)
    df_eng['Social_Score'] = df_eng['Discussions'] * df_eng['Attendance']

    # 3. Traditional_Score (Okuma/Yazma Potansiyeli)
    df_eng['Traditional_Score'] = df_eng['Resources'] * df_eng['AssignmentCompletion']

    # 4. Active_Score (Kinestetik Potansiyeli)
    df_eng['Active_Score'] = df_eng['Extracurricular'] * (1 + df_eng['Motivation'])

    return df_eng


# ---------------------------------------------------------
# YENİ: NEDENSEL ETKİ HESAPLAYICI (CAUSAL INFERENCE ENGINE)
# ---------------------------------------------------------
def calculate_causal_effect(df, treatment_col, outcome_col, target_class, confounders):
    """
    Propensity Score Weighting (IPW) yöntemini kullanarak nedensel etkiyi hesaplar.
    """
    # 1. Hazırlık: Treatment'ı (Müdahale) Binary Yap
    threshold = df[treatment_col].median()
    df_causal = df.copy()
    df_causal['is_treated'] = (df_causal[treatment_col] > threshold).astype(int)

    # Hedef sonucu Binary Yap
    df_causal['outcome_binary'] = (df_causal[outcome_col] == target_class).astype(int)

    # 2. Propensity Score Tahmini
    ps_model = LogisticRegression(solver='lbfgs', max_iter=1000)
    ps_model.fit(df_causal[confounders], df_causal['is_treated'])
    df_causal['ps_score'] = ps_model.predict_proba(df_causal[confounders])[:, 1]

    # 3. Ağırlıklandırma (IPW)
    df_causal['ps_score'] = df_causal['ps_score'].clip(0.05, 0.95)

    df_causal['weight'] = np.where(
        df_causal['is_treated'] == 1,
        1 / df_causal['ps_score'],
        1 / (1 - df_causal['ps_score'])
    )

    # 4. ATE Hesaplama
    weighted_mean_treated = np.average(
        df_causal[df_causal['is_treated'] == 1]['outcome_binary'],
        weights=df_causal[df_causal['is_treated'] == 1]['weight']
    )

    weighted_mean_control = np.average(
        df_causal[df_causal['is_treated'] == 0]['outcome_binary'],
        weights=df_causal[df_causal['is_treated'] == 0]['weight']
    )

    ate = weighted_mean_treated - weighted_mean_control
    return ate * 100


def train_and_predict_learning_style():
    # ---------------------------------------------------------
    # 1. VERİ YÜKLEME VE HAZIRLIK
    # ---------------------------------------------------------
    print("Veri seti yükleniyor...")
    try:
        df = pd.read_csv('data/student_performance.csv')
    except FileNotFoundError:
        print("HATA: 'data/student_performance.csv' bulunamadı.")
        return None, None

    # Hedef Sızıntısı Önleme
    df_model = df.drop(columns=['FinalGrade', 'ExamScore'])

    # X ve y ayrımı
    X_raw = df_model.drop(columns=['LearningStyle'])
    y = df_model['LearningStyle']

    # --- ÖZELLİK MÜHENDİSLİĞİ ---
    print("Özellik mühendisliği uygulanıyor...")
    X_engineered = engineer_features(X_raw)

    # --- SÜTUN ELEME (V2 Stratejisi) ---
    cols_to_drop = [
        'OnlineCourses', 'EduTech',
        'Discussions', 'Attendance',
        'Resources', 'AssignmentCompletion',
        'Extracurricular', 'Motivation'
    ]
    X_final = X_engineered.drop(columns=cols_to_drop)

    # Eğitim ve Test seti ayrımı
    X_train, X_test, y_train, y_test = train_test_split(
        X_final, y, test_size=0.2, random_state=42, stratify=y
    )

    # ---------------------------------------------------------
    # 2. HİBRİT MODEL MİMARİSİ (GELİŞMİŞ ENSEMBLE)
    # ---------------------------------------------------------
    print("Gelişmiş Hibrit Model (SOTA Ensemble) hazırlanıyor...")

    # Model 1: Random Forest (Benchmark & Stability)
    rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=42)
    calibrated_rf = CalibratedClassifierCV(rf, method='isotonic', cv=5)

    # Model 2: Gaussian Naive Bayes (ÇIKARILDI)
    # Analiz Sonucu: Engineered özellikler (örn: Social_Score) normal dağılıma uymadığı için
    # GNB ensemble performansını aşağı çekme riski taşıyor.

    # Model 3: Logistic Regression (Smooth Decision Boundaries)
    lr = LogisticRegression(solver='lbfgs', max_iter=2000)

    # Model 4: HistGradientBoosting (Modern SOTA - LightGBM Style)
    hgb = HistGradientBoostingClassifier(random_state=42)
    calibrated_hgb = CalibratedClassifierCV(hgb, method='isotonic', cv=5)

    # --- Voting Classifier (Optimize Edilmiş Komite) ---
    # GNB çıkarıldı, artık daha sağlam 3'lü yapı var.
    ensemble_model = VotingClassifier(
        estimators=[
            ('rf', calibrated_rf),
            ('lr', lr),
            ('hgb', calibrated_hgb)
        ],
        voting='soft'
    )

    print("Ensemble Model eğitiliyor (RF + LR + GradientBoosting)...")
    ensemble_model.fit(X_train, y_train)

    # ---------------------------------------------------------
    # 3. PERFORMANS DEĞERLENDİRME
    # ---------------------------------------------------------
    print("\n--- PERFORMANS METRİKLERİ ---")
    y_pred = ensemble_model.predict(X_test)
    y_prob = ensemble_model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"Gelişmiş Ensemble Doğruluk Oranı: %{accuracy * 100:.2f}")

    model_log_loss = log_loss(y_test, y_prob)
    print(f"Log Loss (Dağılım Hatası): {model_log_loss:.4f}")

    print("-" * 40)
    print("Sınıflandırma Raporu:")
    print(classification_report(y_test, y_pred))

    # Özellik Önem Düzeyleri (Referans Model üzerinden)
    try:
        # Benchmark olması için saf RF kullanıyoruz
        print("\nBenchmark Model (Saf Random Forest) ile özellik analizi yapılıyor...")
        ref_rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=42)
        ref_rf.fit(X_train, y_train)

        feature_importance = pd.DataFrame({
            'Özellik': X_final.columns,
            'Önem': ref_rf.feature_importances_
        }).sort_values(by='Önem', ascending=False)

        print("\nÖğrenme Stilini Etkileyen En Önemli 5 Faktör (Referans):")
        print(feature_importance.head(5))
    except Exception as e:
        print(f"Önem analizi hatası: {e}")

    # ---------------------------------------------------------
    # 4. NEDENSEL DOĞRULAMA (CAUSAL VALIDATION)
    # ---------------------------------------------------------
    print("\n--- NEDENSEL ETKİ ANALİZİ ---")

    analysis_df = X_engineered.copy()
    analysis_df['LearningStyle'] = y
    confounders = ['Age', 'Gender', 'StudyHours']

    # Test 1: Tech -> Visual
    effect_tech = calculate_causal_effect(analysis_df, 'Tech_Score', 'LearningStyle', 0, confounders)
    print(f"1. Tech_Score -> Görsel Stil Etkisi (ATE): %{effect_tech:.2f}")

    # Test 2: Social -> Auditory
    effect_social = calculate_causal_effect(analysis_df, 'Social_Score', 'LearningStyle', 1, confounders)
    print(f"2. Social_Score -> İşitsel Stil Etkisi (ATE): %{effect_social:.2f}")

    # ---------------------------------------------------------
    # 5. MODELİ KAYDETME
    # ---------------------------------------------------------
    save_dir = 'artifacts/models'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    model_path = os.path.join(save_dir, 'sota_ensemble_learning_style_model.joblib')
    features_path = os.path.join(save_dir, 'model_features.joblib')

    joblib.dump(ensemble_model, model_path)
    joblib.dump(X_final.columns, features_path)

    return ensemble_model, X_final.columns


# ---------------------------------------------------------
# 6. YENİ ÖĞRENCİ TAHMİN FONKSİYONU
# ---------------------------------------------------------
def predict_new_student(model, feature_names_trained, student_data_raw):
    """
    Yeni öğrenci tahmin fonksiyonu (Değişmedi)
    """
    raw_columns = [
        'StudyHours', 'Attendance', 'Resources', 'Extracurricular',
        'Motivation', 'Internet', 'Gender', 'Age', 'OnlineCourses',
        'Discussions', 'AssignmentCompletion', 'EduTech', 'StressLevel'
    ]

    if len(student_data_raw) != len(raw_columns):
        raise ValueError(f"Eksik veri! Beklenen: {len(raw_columns)}, Gelen: {len(student_data_raw)}")

    student_df = pd.DataFrame([student_data_raw], columns=raw_columns)
    student_df_engineered = engineer_features(student_df)
    student_df_final = student_df_engineered[feature_names_trained]

    probabilities = model.predict_proba(student_df_final)[0]

    style_names = {
        0: 'Görsel (Visual)',
        1: 'İşitsel (Auditory)',
        2: 'Okuma/Yazma (Read/Write)',
        3: 'Kinestetik (Kinesthetic)'
    }

    print("\n--- GÜÇLENDİRİLMİŞ ENSEMBLE ANALİZİ ---")
    results = []
    for i, prob in enumerate(probabilities):
        percentage = prob * 100
        style_name = style_names.get(i, f"Stil {i}")
        results.append((style_name, percentage))
        print(f"{style_name}: %{percentage:.1f}")

    dominant_style = max(results, key=lambda x: x[1])
    print(f"\n>> Baskın Öğrenme Stili: {dominant_style[0]} (%{dominant_style[1]:.1f})")

    return results


if __name__ == "__main__":
    trained_model, feature_cols = train_and_predict_learning_style()

    if trained_model:
        # Örnek Test
        new_student = [25, 90, 2, 1, 2, 1, 0, 21, 3, 1, 95, 1, 1]
        predict_new_student(trained_model, feature_cols, new_student)