import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin

# --- AYARLAR ---
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'sans-serif'


# --- 1. GEREKLİ SINIF: Özellik Mühendisliği ---
class DynamicFeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self, sleep_exponent=1.2):  # Bilimsel Optimize Katsayı
        self.sleep_exponent = sleep_exponent

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()

        # Focus Ratio Hesabı (Ana Oyuncu)
        X_['total_distraction_hours'] = X_['social_media_hours'] + X_['netflix_hours']
        # Paydaya +1 ekleyerek sıfıra bölünmeyi önlüyoruz
        X_['focus_ratio'] = X_['study_hours_per_day'] / (X_['total_distraction_hours'] + 1)

        return X_


# --- 2. VERİ YÜKLEME ---
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

if 'student_id' in df.columns:
    df = df.drop('student_id', axis=1)

# --- 3. ÖZELLİK TÜRETME ---
engineer = DynamicFeatureEngineer()
df_eng = engineer.transform(df)

# --- 4. GRAFİK OLUŞTURMA ---
plt.figure(figsize=(11, 7))

# Scatter Plot (Saçılım Grafiği)
# Hue (Renk) ve Size (Boyut) -> Focus Ratio'ya göre değişir
scatter = sns.scatterplot(
    data=df_eng,
    x='study_hours_per_day',
    y='exam_score',
    hue='focus_ratio',
    size='focus_ratio',
    sizes=(20, 200),  # Daire boyut aralığı
    palette='viridis_r',  # Renk paleti (Koyu renk yüksek odak olsun diye _r ekledik veya silebilirsin)
    alpha=0.7,  # Saydamlık
    edgecolor='black',  # Daire kenarlıkları
    linewidth=0.5
)

# --- GÖRSEL DÜZENLEMELER ---
plt.title('Şekil 3.4: Çalışma Saati ve Odaklanma Oranının Başarı Üzerindeki Bileşik Etkisi', fontsize=14,
          fontweight='bold', pad=20)
plt.xlabel('Günlük Ders Çalışma Saati', fontsize=12)
plt.ylabel('Sınav Notu (Başarı)', fontsize=12)

# Lejantı (Açıklama Kutusunu) Düzenle
plt.legend(title='Odaklanma Oranı\n(Focus Ratio)', bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)

# Izgara ve Sınırlar
plt.grid(True, alpha=0.3, linestyle='--')
plt.tight_layout()

# --- KAYDETME ---
plt.savefig('Bilesik_Etki_Analizi_V5.png', dpi=300, bbox_inches='tight')
print("📊 Grafik kaydedildi: Bilesik_Etki_Analizi_V5.png")
plt.show()