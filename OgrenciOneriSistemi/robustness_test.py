# robustness_test.py (GÜNCEL VERSİYON)
# Amaç: Modelin gürültüye karşı dayanıklılığını test eder ve raporlar.

import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import set_config

# --- 1. AYARLAR VE KLASÖR KURULUMU ---
OUTPUT_DIR = "analiz_raporlari"
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"📂 Çıktı klasörü hazır: {OUTPUT_DIR}/")


# --- 2. GEREKLİ SINIFLAR (MODELİN YÜKLENMESİ İÇİN ŞART) ---
# Bu sınıflar, eğitilmiş model (.joblib) yüklenirken hafızada bulunmalıdır.
# Ayrıca FeatureEngineer, gürültü eklendiğinde türetilmiş özellikleri (focus_ratio vb.)
# güncellemeli ki analiz doğru çıksın.

class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        # Analiz sırasında veriyi kırpmıyoruz, olduğu gibi geçsin.
        return X


class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()

        # --- ÖZELLİK TÜRETİM MANTIĞI (Model ile aynı olmalı) ---
        sm = X_.get('social_media_hours', 0)
        nf = X_.get('netflix_hours', 0)
        X_['total_distraction_hours'] = sm + nf

        study = X_.get('study_hours_per_day', 0)
        sleep = X_.get('sleep_hours', 0)

        # +1 ekleyerek 0'a bölme hatasını önlüyoruz
        X_['focus_ratio'] = study / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = sleep / (study + 1)

        mh = X_.get('mental_health_rating', 5)
        X_['study_efficiency'] = study * mh

        att = X_.get('attendance_percentage', 0)
        X_['academic_engagement'] = att * study

        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        ex = X_.get('exercise_frequency', 0)
        X_['vitality_score'] = (sleep ** 1.2) * (ex + 1)

        # Part-time job yönetimi
        pt_val = 1.0
        if 'part_time_job' in X_.columns:
            # Vektörize işlem (Hızlı)
            if X_['part_time_job'].dtype == 'object':
                pt_val = np.where(X_['part_time_job'] == 'Yes', 1.5, 1.0)
            else:
                pt_val = 1.0
        X_['burnout_risk'] = study * pt_val

        # Extracurricular yönetimi
        ec_val = 1.0
        if 'extracurricular_participation' in X_.columns:
            if X_['extracurricular_participation'].dtype == 'object':
                ec_val = np.where(X_['extracurricular_participation'] == 'Yes', 1.2, 1.0)
        X_['dedication_level'] = att * ec_val

        return X_


# --- 3. GÜRÜLTÜ ENJEKSİYON MOTORU ---
def inject_noise(df, column, noise_level=0.10):
    """
    Belirtilen sütuna standart sapmasının %10'u kadar rastgele gürültü ekler.
    """
    temp_df = df.copy()
    if column not in temp_df.columns:
        return temp_df

    sigma = temp_df[column].std() * noise_level
    noise = np.random.normal(0, sigma, temp_df.shape[0])

    temp_df[column] = temp_df[column] + noise

    # Mantıksız değerleri (Negatif saat vb.) engelle
    if 'hours' in column:
        temp_df[column] = temp_df[column].clip(lower=0, upper=24)
    if 'percentage' in column:
        temp_df[column] = temp_df[column].clip(lower=0, upper=100)
    if 'rating' in column:
        temp_df[column] = temp_df[column].clip(lower=1, upper=10)

    return temp_df


# --- 4. ANA ANALİZ FONKSİYONU ---
def run_robustness_test():
    print("🛡️  DAYANIKLILIK VE DUYARLILIK ANALİZİ BAŞLATILIYOR...")

    # A. Dosyaları Bul ve Yükle
    MODEL_PATH = "artifacts/student_score_xgb_pipeline_v2.joblib"

    csv_paths = [
        "student_habits_performance.csv",
        "data/student_habits_performance.csv",
        r"D:\Ensar Dosya\OgrenciOneriSistemi\student_habits_performance.csv"
    ]
    DATA_PATH = next((p for p in csv_paths if os.path.exists(p)), None)

    if not DATA_PATH:
        print("❌ Veri dosyası (csv) bulunamadı.")
        return
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model dosyası bulunamadı: {MODEL_PATH}")
        return

    try:
        model = joblib.load(MODEL_PATH)
        df = pd.read_csv(DATA_PATH)
        print(f"✅ Model ve Veri Yüklendi. ({len(df)} kayıt)")
    except Exception as e:
        print(f"❌ Yükleme Hatası: {e}")
        return

    # Pandas çıktısı ayarı
    set_config(transform_output="pandas")

    # Hedef sütunu çıkar
    X = df.drop('exam_score', axis=1, errors='ignore')

    # B. Baz (Baseline) Tahmin
    print("🤖 Baz tahminler hesaplanıyor...")
    try:
        base_preds = model.predict(X)
    except:
        # Eski versiyon uyumluluğu
        base_preds = model.predict(X.values)

    mean_base_score = base_preds.mean()

    # C. Stres Testi Döngüsü
    features_to_test = [
        'study_hours_per_day',
        'sleep_hours',
        'social_media_hours',
        'attendance_percentage',
        'mental_health_rating'
    ]

    NOISE_LEVEL = 0.10  # %10 Gürültü
    results = []

    print(f"\n⚡ Stres Testi Başlıyor (Gürültü Oranı: %{int(NOISE_LEVEL * 100)})...")

    for feat in features_to_test:
        if feat not in X.columns: continue

        # 1. Gürültü Ekle
        X_noisy = inject_noise(X, feat, noise_level=NOISE_LEVEL)

        # 2. Tekrar Tahmin Et (FeatureEngineer otomatik çalışır)
        try:
            noisy_preds = model.predict(X_noisy)
        except:
            noisy_preds = model.predict(X_noisy.values)

        # 3. Sapmayı Hesapla (Mean Absolute Deviation)
        diff = np.abs(noisy_preds - base_preds).mean()

        # 4. Yüzdesel Etki (Sensitivity)
        sensitivity = (diff / mean_base_score) * 100

        print(f"   👉 {feat.ljust(25)} bozulunca ortalama sapma: {diff:.2f} Puan")

        results.append({
            'Feature': feat,
            'Mean_Deviation': diff,
            'Sensitivity_Percent': sensitivity,
            'Max_Change': np.max(np.abs(noisy_preds - base_preds))
        })

    # D. Veriyi Düzenle
    res_df = pd.DataFrame(results).sort_values(by='Mean_Deviation', ascending=False)

    # --- 5. RAPORLAMA (TXT ÇIKTISI) ---
    txt_path = os.path.join(OUTPUT_DIR, "robustness_analiz_raporu.txt")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("🛡️  AI STUDENT COACH - DUYARLILIK VE KARARLILIK RAPORU\n")
        f.write("=" * 60 + "\n")
        f.write(f"Analiz Tarihi: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Uygulanan Gürültü (Noise) Oranı: %{int(NOISE_LEVEL * 100)}\n")
        f.write(f"Test Edilen Model: XGBoost Hibrit V2.0\n")
        f.write("-" * 60 + "\n")
        f.write("METRİK AÇIKLAMASI:\n")
        f.write("• Mean Deviation (Ort. Sapma): Girdi hatalı olduğunda notun kaç puan şaştığı.\n")
        f.write("• Sensitivity (Duyarlılık): Sapmanın toplam nota oranı (%).\n")
        f.write("• Robustness (Kararlılık): Sapma ne kadar düşükse, model o kadar kararlıdır.\n")
        f.write("-" * 60 + "\n\n")

        f.write(f"{'ÖZELLİK (FEATURE)':<30} | {'SAPMA (PUAN)':<15} | {'DUYARLILIK (%)':<15}\n")
        f.write("-" * 66 + "\n")

        for index, row in res_df.iterrows():
            f.write(f"{row['Feature']:<30} | {row['Mean_Deviation']:<15.4f} | %{row['Sensitivity_Percent']:<14.2f}\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("📋 AKADEMİK YORUM VE SONUÇ:\n")

        most_sensitive = res_df.iloc[0]
        f.write(
            f"1. En Yüksek Duyarlılık: Model, '{most_sensitive['Feature']}' değişkenindeki değişimlere en fazla tepkiyi vermektedir.\n")
        f.write(
            f"2. Kararlılık Testi: %10'luk veri bozulmasında ortalama sapma {most_sensitive['Mean_Deviation']:.2f} puanda kalmıştır.\n")

        if most_sensitive['Mean_Deviation'] < 5.0:
            f.write(
                "3. SONUÇ: Model Gürültüye Karşı 'DAYANIKLIDIR' (Robust). Sapma marjı kabul edilebilir sınırlar (5 puan) altındadır.\n")
        else:
            f.write(
                "3. SONUÇ: Model bazı değişkenlere karşı 'HASSASDIR'. Veri girişinde doğrulama yapılması önerilir.\n")

    print(f"\n✅ Rapor yazıldı: {txt_path}")

    # --- 6. GÖRSELLEŞTİRME (PNG ÇIKTISI) ---
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")

    # Renk Paleti: Duyarlılık arttıkça renk koyulaşsın
    colors = sns.color_palette("rocket", len(res_df))

    ax = sns.barplot(x='Mean_Deviation', y='Feature', data=res_df, palette=colors)

    plt.title(f"Model Duyarlılık Analizi (Tornado Plot)\n(Girdi %{int(NOISE_LEVEL * 100)} Bozulduğunda Puan Sapması)",
              fontsize=12, fontweight='bold')
    plt.xlabel("Ortalama Puan Sapması (Mean Deviation)", fontsize=10)
    plt.ylabel("Test Edilen Özellik", fontsize=10)

    # Çubukların ucuna değerleri yaz
    for i, v in enumerate(res_df['Mean_Deviation']):
        ax.text(v + 0.02, i, f"+{v:.2f}", color='black', va='center', fontweight='bold', fontsize=9)

    plt.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, "robustness_tornado_plot.png")
    plt.savefig(png_path, dpi=300)

    print(f"✅ Grafik kaydedildi: {png_path}")
    print("\n🎉 İŞLEM TAMAMLANDI.")


if __name__ == "__main__":
    run_robustness_test()