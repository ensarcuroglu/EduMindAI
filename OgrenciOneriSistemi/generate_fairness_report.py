# generate_fairness_report.py (DÜZELTİLMİŞ VERSİYON)

import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import set_config


# --- 1. GEREKLİ SINIFLAR (MODELİN BEKLEDİĞİ GERÇEK MANTIK) ---
# Joblib modeli yüklerken bu sınıfların hafızada "dolu" olmasını bekler.

class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        # Rapor alırken outlier'ları baskılamasak da olur, hata vermesin yeter.
        return X


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Modelin eğitimde kullandığı özellik türetme mantığının aynısı.
    Bu olmazsa 'Missing Columns' hatası alırız.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()

        # --- Temel Türetimler ---
        # Get ile güvenli çekim yapıyoruz, yoksa 0 kabul ediyoruz
        sm = X_.get('social_media_hours', 0)
        nf = X_.get('netflix_hours', 0)
        X_['total_distraction_hours'] = sm + nf

        study = X_.get('study_hours_per_day', 0)
        sleep = X_.get('sleep_hours', 0)

        # 0'a bölünme hatasını engellemek için +1
        X_['focus_ratio'] = study / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = sleep / (study + 1)

        mh = X_.get('mental_health_rating', 5)
        X_['study_efficiency'] = study * mh

        att = X_.get('attendance_percentage', 0)
        X_['academic_engagement'] = att * study

        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        # --- İleri Seviye Türetimler (V2) ---
        ex = X_.get('exercise_frequency', 0)
        X_['vitality_score'] = (sleep ** 1.2) * (ex + 1)

        # Part-time job dönüşümü
        pt_job = X_.get('part_time_job', 'No')
        # Pandas Series gelirse apply kullan, düz değerse direkt if
        if isinstance(pt_job, pd.Series):
            pt_val = pt_job.apply(lambda x: 1.5 if x == 'Yes' else 1.0)
        else:
            pt_val = 1.5 if pt_job == 'Yes' else 1.0
        X_['burnout_risk'] = study * pt_val

        # Extracurricular dönüşümü
        ec_part = X_.get('extracurricular_participation', 'No')
        if isinstance(ec_part, pd.Series):
            ec_val = ec_part.apply(lambda x: 1.2 if x == 'Yes' else 1.0)
        else:
            ec_val = 1.2 if ec_part == 'Yes' else 1.0
        X_['dedication_level'] = att * ec_val

        return X_


# --- 2. RAPORLAMA MOTORU ---
def generate_report():
    print("📊 ADALET RAPORU OLUŞTURULUYOR...")

    # AYARLAR
    MODEL_PATH = "artifacts/student_score_xgb_pipeline_v2.joblib"

    # Veri setini bul
    csv_paths = [
        "student_habits_performance.csv",
        "data/student_habits_performance.csv",
        r"D:\Ensar Dosya\OgrenciOneriSistemi\student_habits_performance.csv",
        r"D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv"
    ]

    DATA_PATH = None
    for p in csv_paths:
        if os.path.exists(p):
            DATA_PATH = p
            break

    if not DATA_PATH:
        print("❌ HATA: Veri seti bulunamadı!")
        return

    # MODELİ VE VERİYİ YÜKLE
    try:
        model = joblib.load(MODEL_PATH)
        df = pd.read_csv(DATA_PATH)
        print(f"✅ Model yüklendi. Veri: {DATA_PATH}")
    except Exception as e:
        print(f"❌ Yükleme Hatası: {e}")
        return

    # Pandas çıktısı ayarı
    set_config(transform_output="pandas")

    X = df.drop('exam_score', axis=1, errors='ignore')
    y_true = df['exam_score']

    print("🤖 Tahminler ve Özellik Mühendisliği yapılıyor...")

    try:
        # Pipeline'ı tetikle (FeatureEngineer burada çalışacak)
        y_pred = model.predict(X)
    except Exception as e:
        print(f"❌ Tahmin Hatası: {e}")
        print("İpucu: FeatureEngineer sınıfı modelin beklediği sütunları üretemiyor olabilir.")
        return

    # Residuals Hesapla
    df['residuals'] = y_true - y_pred

    # RAPORU YAZDIR (TXT)
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("🎓 AI STUDENT COACH - ADİLLİK DENETİM RAPORU (BASELINE)")
    report_lines.append("=" * 60)
    report_lines.append(f"Analiz Tarihi: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append(f"Model: XGBoost Hibrit V2.0")
    report_lines.append("-" * 60)
    report_lines.append("METRİK AÇIKLAMASI (BIAS):")
    report_lines.append("Bias = Gerçek Not - Tahmin Edilen Not")
    report_lines.append(" (+) Pozitif Bias: Model eksik tahmin etmiş (Öğrenci Mağdur).")
    report_lines.append(" (-) Negatif Bias: Model fazla tahmin etmiş (Öğrenci Avantajlı).")
    report_lines.append("-" * 60)

    sensitive_features = ['internet_quality', 'gender', 'part_time_job', 'parental_education_level']
    plot_data = []

    for feature in sensitive_features:
        if feature not in df.columns: continue

        report_lines.append(f"\n📌 {feature.upper().replace('_', ' ')}")
        groups = df.groupby(feature)['residuals'].mean().sort_values(ascending=False)

        for group_name, bias_val in groups.items():
            # Durum belirteci
            status = "✅ ADİL"
            if bias_val > 1.0: status = "⚠️ MAĞDUR"
            if bias_val < -1.0: status = "⚠️ AVANTAJLI"

            line = f"   • {str(group_name).ljust(15)} : {bias_val:+.4f} Puan  [{status}]"
            report_lines.append(line)

            plot_data.append({'Feature': feature, 'Group': group_name, 'Bias': bias_val})

    # TXT Kaydet
    with open("fairness_audit_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print("✅ Rapor Kaydedildi: fairness_audit_report.txt")

    # PNG Kaydet
    if plot_data:
        try:
            plot_df = pd.DataFrame(plot_data)
            plt.figure(figsize=(12, 7))
            sns.set_theme(style="whitegrid")

            # Renklendirme
            colors = ['#e74c3c' if x > 0.5 else ('#3498db' if x < -0.5 else '#95a5a6') for x in plot_df['Bias']]

            sns.barplot(x='Group', y='Bias', hue='Feature', data=plot_df, palette='viridis')

            plt.axhline(0, color='black', linewidth=1.5)
            plt.axhline(0.2, color='red', linestyle='--', linewidth=0.8, alpha=0.5, label='Hassasiyet Eşiği (+)')
            plt.axhline(-0.2, color='blue', linestyle='--', linewidth=0.8, alpha=0.5, label='Hassasiyet Eşiği (-)')

            plt.title("Adalet Analizi: Gruplara Göre Model Hatası", fontsize=14, fontweight='bold')
            plt.ylabel("Ortalama Hata Payı (Puan)\n(Yukarı: Mağduriyet | Aşağı: İltimas)", fontsize=11)
            plt.xlabel("Sosyo-Demografik Gruplar", fontsize=11)
            plt.legend(title="Kategoriler", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)
            plt.tight_layout()

            plt.savefig("fairness_bias_chart.png", dpi=300)
            print("✅ Grafik Kaydedildi: fairness_bias_chart.png")
        except Exception as e:
            print(f"⚠️ Grafik çizilirken hata oluştu: {e}")


if __name__ == "__main__":
    generate_report()