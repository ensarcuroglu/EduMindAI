import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin


# --- 1. GEREKLİ SINIF: Özellik Mühendisliği (Senin Modelinden) ---
class DynamicFeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self, sleep_exponent=1.2):  # Optimize edilmiş katsayı
        self.sleep_exponent = sleep_exponent

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        # Temel Türetimler
        X_['total_distraction_hours'] = X_['social_media_hours'] + X_['netflix_hours']
        X_['focus_ratio'] = X_['study_hours_per_day'] / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = X_['sleep_hours'] / (X_['study_hours_per_day'] + 1)
        X_['study_efficiency'] = X_['study_hours_per_day'] * X_['mental_health_rating']
        X_['academic_engagement'] = X_['attendance_percentage'] * X_['study_hours_per_day']

        # Optimize Edilmiş Formül
        X_['vitality_score'] = (X_['sleep_hours'] ** self.sleep_exponent) * (X_['exercise_frequency'] + 1)

        # Kategorik veriden sayısal türetim (Korelasyon için önemli)
        part_time_val = np.where(X_['part_time_job'] == 'Yes', 1.5, 1.0)
        X_['burnout_risk'] = X_['study_hours_per_day'] * part_time_val

        extra_curr_val = np.where(X_['extracurricular_participation'] == 'Yes', 1.2, 1.0)
        X_['dedication_level'] = X_['attendance_percentage'] * extra_curr_val

        return X_


# --- 2. VERİ YÜKLEME VE HAZIRLIK ---
try:
    df = pd.read_csv('student_habits_performance.csv')
    print("✅ Veri seti yüklendi.")
except:
    try:
        df = pd.read_csv('data/student_habits_performance.csv')
        print("✅ Veri seti 'data' klasöründen yüklendi.")
    except:
        print("❌ HATA: student_habits_performance.csv dosyası bulunamadı!")
        exit()

# Gereksiz sütunları at
if 'student_id' in df.columns:
    df = df.drop('student_id', axis=1)

# --- 3. ÖZELLİKLERİ TÜRETME ---
engineer = DynamicFeatureEngineer(sleep_exponent=1.2)
df_eng = engineer.transform(df)

# --- 4. KORELASYON HESAPLAMA ---
# Sadece sayısal sütunları al
numeric_df = df_eng.select_dtypes(include=[np.number])

# Hedef değişken (exam_score) ile korelasyonları hesapla
correlations = numeric_df.corrwith(numeric_df['exam_score']).sort_values(ascending=False)

# Hedef değişkenin kendisini (1.0) listeden çıkar
correlations = correlations.drop('exam_score')

# --- 5. GRAFİK OLUŞTURMA (Rapor Formatına Uygun) ---
plt.figure(figsize=(12, 7))
sns.set_style("whitegrid")

# Renk Paleti: Pozitifler Mavi, Negatifler Kırmızı
colors = ['#4e79a7' if x > 0 else '#e15759' for x in correlations.values]

# Bar Plot Çizimi
ax = sns.barplot(x=correlations.index, y=correlations.values, palette=colors)

# Görsel Düzenlemeler
plt.title('Özniteliklerin Akademik Başarı (Exam Score) ile Pearson Korelasyonu', fontsize=15, fontweight='bold', pad=20)
plt.ylabel('Pearson Korelasyon Katsayısı (r)', fontsize=12)
plt.xlabel('Değişkenler', fontsize=12)
plt.axhline(0, color='black', linewidth=1)  # Sıfır çizgisi
plt.xticks(rotation=45, ha='right', fontsize=10)  # Yazıları eğik yaz
plt.grid(axis='y', alpha=0.3)

# Çubukların üzerine değerleri yaz
for i, v in enumerate(correlations.values):
    offset = 0.02 if v > 0 else -0.05
    ax.text(i, v + offset, f"{v:.2f}", ha='center', fontsize=9, color='black')

# Kaydet ve Göster
plt.tight_layout()
plt.savefig('Korelasyon_Analizi_V5.png', dpi=300)
print("📊 Grafik kaydedildi: Korelasyon_Analizi_V5.png")
plt.show()