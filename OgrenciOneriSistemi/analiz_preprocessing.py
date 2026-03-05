# analiz_preprocessing.py
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
from scipy.stats import skew

# 1. VERİ YÜKLEME
DATA_PATH = "data/student_habits_performance.csv"
if os.path.exists(r"D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv"):
    DATA_PATH = r"D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv"

df = pd.read_csv(DATA_PATH)
if 'student_id' in df.columns:
    # Analiz için ID'yi saklayalım, sonra gerekirse drop ederiz
    student_ids = df['student_id']
    df_model = df.drop('student_id', axis=1)
else:
    df_model = df.copy()
    student_ids = pd.Series(range(1, len(df) + 1), name='student_id')

print("="*60)
print("🔎 VERİ KALİTESİ VE ANOMALİ RAPORU")
print("="*60)

# ====================================================
# A. MANTIKSAL ANOMALİ KONTROLLERİ (YENİ BÖLÜM)
# ====================================================
print("\n[A] MANTIKSAL TUTARLILIK KONTROLÜ")
print("-" * 40)

anomalies = []

# Kural 1: Yaş ve Eğitim Seviyesi Uyuşmazlığı
# Lise: <19, Lisans: 17-25, Master: >21, PhD: >23 (Kabaca)
# 17 Yaşında Master veya PhD olması çok şüphelidir.
if 'parental_education_level' in df.columns:
    # Not: Veri setinde bu sütun bazen 'education_level' olabilir, kontrol et.
    # Senin veri setinde 'parental_education_level' var ama öğrencinin kendi seviyesi yok.
    # EĞER öğrencinin seviyesi yoksa bu kontrolü yapamayız.
    # ANCAK senin analiz çıktında "17 Yaş | Master" görünüyor. Demek ki bir yerde bu bilgi var.
    # Varsayalım ki bu bilgi 'education_level' veya benzeri bir sütunda.
    # Eğer yoksa ve 'parental...' ailenin eğitimiyse, 17 yaşındaki çocuğun ailesinin Master yapması normaldir.
    # *DİKKAT:* Önceki analizde "17 Yaş | Master" gördük. Bu öğrencinin kendisi mi ailesi mi?
    # Veri setindeki sütun 'parental_education_level' (Aile Eğitimi).
    # O zaman analiz raporundaki başlık YANILTICI olabilir. "17 Yaş | Ailesi Master" demek istemiş olabilir.
    # Ama yine de biz genel mantık hatalarına bakalım.
    pass

# Kural 2: Zaman Bükülmesi (Günde 24 Saatten Fazla Aktivite)
# Uyku + Ders + Sosyal Medya + Netflix > 24 Olamaz.
df['total_hours'] = df.get('study_hours_per_day', 0) + \
                    df.get('sleep_hours', 0) + \
                    df.get('social_media_hours', 0) + \
                    df.get('netflix_hours', 0)

time_travelers = df[df['total_hours'] > 24]
if not time_travelers.empty:
    print(f"🚨 ZAMAN YOLCULARI TESPİT EDİLDİ: {len(time_travelers)} öğrenci günde 24 saatten fazla yaşıyor!")
    print(time_travelers[['total_hours']].head())
else:
    print("✅ Zaman bütçesi hatası yok (Toplam saatler < 24).")

# Kural 3: İmkansız Değerler (Negatif veya Aşırı Uç)
impossible_conditions = [
    (df['sleep_hours'] < 0, "Negatif Uyku"),
    (df['sleep_hours'] > 16, "Kış Uykusu (>16s)"),
    (df['study_hours_per_day'] < 0, "Negatif Ders"),
    (df['exam_score'] < 0, "Eksi Not"),
    (df['exam_score'] > 100, "100 Üzeri Not")
]

for condition, label in impossible_conditions:
    count = condition.sum()
    if count > 0:
        print(f"🚨 {label}: {count} kayıt bulundu.")
        # Örnek göster
        print(df[condition].head(3))
    else:
        print(f"✅ {label} sorunu yok.")

# Kural 4: Genç Profesörler (Yaş Kontrolü)
# Eğer öğrencinin eğitim seviyesi sütunu varsa (Örn: 'education_level')
if 'education_level' in df.columns:
    young_masters = df[(df['age'] < 20) & (df['education_level'].isin(['Master', 'PhD']))]
    if not young_masters.empty:
        print(f"\n🚨 DAHİ ÇOCUKLAR: {len(young_masters)} kişi 20 yaş altı Master/PhD yapıyor.")
        print(young_masters[['age', 'education_level']].head())
else:
    print("\nℹ️ Öğrencinin kendi eğitim seviyesi sütunu bulunamadı (Sadece Aile Eğitimi var).")
    print("   Not: Analiz raporunda '17 Yaş | Master' yazıyorsa, bu 'Ailesi Master Mezunu' anlamına geliyor olabilir.")

# ====================================================
# B. İSTATİSTİKSEL KONTROLLER (MEVCUT KOD)
# ====================================================
print("\n[B] İSTATİSTİKSEL ANALİZ")
print("-" * 40)

# 1. EKSİK VERİ ANALİZİ
missing = df_model.isnull().sum()
missing = missing[missing > 0]
print("\n1. EKSİK VERİLER:")
if missing.empty:
    print("✅ Eksik değer yok.")
else:
    print(missing)

# 2. KATEGORİK DEĞİŞKEN ANALİZİ
cat_cols = df_model.select_dtypes(include=['object']).columns
print("\n2. NADİR SINIFLAR (%1 Altı):")
found_rare = False
for col in cat_cols:
    counts = df_model[col].value_counts(normalize=True) * 100
    rares = counts[counts < 1.0] # %1'den az
    if not rares.empty:
        found_rare = True
        print(f"⚠️ {col}: {rares.index.tolist()} (Gürültü olabilir)")

if not found_rare: print("✅ Nadir sınıf sorunu yok.")

# 3. KORELASYON
print("\n3. HEDEF DEĞİŞKEN (exam_score) İLE KORELASYON:")
num_cols = df_model.select_dtypes(include=['number']).columns
if 'exam_score' in num_cols:
    corr = df_model[num_cols].corr()['exam_score'].sort_values(ascending=False)
    print(corr)
else:
    print("⚠️ 'exam_score' sütunu bulunamadı.")

# Grafik
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
sns.histplot(df['total_hours'], kde=True, color='orange')
plt.axvline(24, color='red', linestyle='--')
plt.title("Günlük Toplam Aktivite Saati")

plt.subplot(1, 2, 2)
if 'exam_score' in df.columns:
    sns.scatterplot(x='study_hours_per_day', y='exam_score', data=df, alpha=0.5)
    plt.title("Ders Saati vs Not")

plt.tight_layout()
plt.show()