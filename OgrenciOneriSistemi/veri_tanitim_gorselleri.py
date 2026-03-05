import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

# ---------------------------------------------------------
# 1. VERİ YÜKLEME VE HAZIRLIK
# ---------------------------------------------------------
file_path = 'data/student_habits_performance.csv'

try:
    df = pd.read_csv(file_path)
    print(f"Veri seti yüklendi: {df.shape}")
except FileNotFoundError:
    print("Dosya bulunamadı! Lütfen dosya yolunu kontrol edin.")
    exit()

# Sütun İsimlerini Türkçeleştirme (Rapor için şık görünsün)
column_map = {
    'student_id': 'Öğrenci ID',
    'age': 'Yaş',
    'gender': 'Cinsiyet',
    'study_hours_per_day': 'Günlük Çalışma (Saat)',
    'social_media_hours': 'Sosyal Medya (Saat)',
    'netflix_hours': 'Netflix (Saat)',
    'part_time_job': 'Yarı Zamanlı İş',
    'attendance_percentage': 'Devam Oranı (%)',
    'sleep_hours': 'Uyku Süresi (Saat)',
    'diet_quality': 'Beslenme Kalitesi',
    'exercise_frequency': 'Egzersiz Sıklığı',
    'parental_education_level': 'Ebeveyn Eğitim',
    'internet_quality': 'İnternet Kalitesi',
    'mental_health_rating': 'Ruh Sağlığı Puanı',
    'extracurricular_participation': 'Kulüp Üyeliği',
    'exam_score': 'Sınav Puanı'
}

df_tr = df.rename(columns=column_map).copy()

# Eksik Verileri Doldurma
if 'Ebeveyn Eğitim' in df_tr.columns:
    df_tr['Ebeveyn Eğitim'] = df_tr['Ebeveyn Eğitim'].fillna('Belirtilmemiş')

# Stil Ayarları (Profesyonel Dergi Stili)
sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

# ---------------------------------------------------------
# GÖRSEL 1: DEMOGRAFİK PROFİL (Dashboard Tarzı)
# ---------------------------------------------------------
fig = plt.figure(figsize=(15, 10))
gs = GridSpec(2, 3, figure=fig)

# 1.1 Cinsiyet Dağılımı
ax1 = fig.add_subplot(gs[0, 0])
gender_counts = df_tr['Cinsiyet'].value_counts()
colors = ['#ff9999', '#66b3ff', '#99ff99']
ax1.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%',
        colors=colors, startangle=90, wedgeprops={'edgecolor': 'white'})
ax1.set_title('Cinsiyet Dağılımı', fontsize=14, fontweight='bold')

# 1.2 Ebeveyn Eğitim Durumu
ax2 = fig.add_subplot(gs[0, 1:])
sns.countplot(y='Ebeveyn Eğitim', data=df_tr, ax=ax2, palette='viridis',
              order=df_tr['Ebeveyn Eğitim'].value_counts().index)
ax2.set_title('Ebeveyn Eğitim Seviyesi', fontsize=14, fontweight='bold')
ax2.set_xlabel('Öğrenci Sayısı')
ax2.set_ylabel('')

# 1.3 İş ve Sosyal Aktivite Durumu
ax3 = fig.add_subplot(gs[1, :])
cross_data = pd.crosstab(df_tr['Yarı Zamanlı İş'], df_tr['Kulüp Üyeliği'])
cross_data.plot(kind='bar', ax=ax3, color=['#e74c3c', '#2ecc71'], rot=0)
ax3.set_title('Çalışma Durumu ve Kulüp Üyeliği İlişkisi', fontsize=14, fontweight='bold')
ax3.set_xlabel('Yarı Zamanlı Bir İşte Çalışıyor mu?')
ax3.set_ylabel('Öğrenci Sayısı')
ax3.legend(title='Kulüp Üyeliği')
ax3.set_xticklabels(['Hayır', 'Evet'])

plt.tight_layout()
plt.savefig('Rapor_1_Demografik_Profil.png', bbox_inches='tight')
print("-> Grafik 1 (Demografik Profil) oluşturuldu.")

# ---------------------------------------------------------
# GÖRSEL 2: AKADEMİK ALIŞKANLIKLARIN DAĞILIMI
# ---------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
features = ['Günlük Çalışma (Saat)', 'Uyku Süresi (Saat)',
            'Sosyal Medya (Saat)', 'Devam Oranı (%)']
colors = ['#3498db', '#9b59b6', '#e67e22', '#27ae60']

for i, feature in enumerate(features):
    row, col = i // 2, i % 2
    sns.histplot(df_tr[feature], kde=True, ax=axes[row, col],
                 color=colors[i], edgecolor='white', bins=20)
    mean_val = df_tr[feature].mean()
    axes[row, col].axvline(mean_val, color='red', linestyle='--', label=f'Ort: {mean_val:.1f}')
    axes[row, col].set_title(f'{feature} Dağılımı', fontweight='bold')
    axes[row, col].legend()

plt.suptitle('Öğrenci Alışkanlıkları Analizi', fontsize=16, y=1.02)
plt.tight_layout()
plt.savefig('Rapor_2_Aliskanlik_Dagilimi.png', bbox_inches='tight')
print("-> Grafik 2 (Alışkanlık Analizi) oluşturuldu.")

# ---------------------------------------------------------
# GÖRSEL 3: BAŞARIYI ETKİLEYEN FAKTÖRLER (Korelasyon)
# ---------------------------------------------------------
plt.figure(figsize=(12, 10))
numeric_cols = ['Yaş', 'Günlük Çalışma (Saat)', 'Sosyal Medya (Saat)',
                'Netflix (Saat)', 'Uyku Süresi (Saat)', 'Devam Oranı (%)',
                'Sınav Puanı']
corr_matrix = df_tr[numeric_cols].corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f", cmap='RdBu_r',
            center=0, square=True, linewidths=.5, cbar_kws={"shrink": .8})
plt.title('Faktörler Arası İlişki ve Sınav Puanına Etkisi', fontsize=16, pad=20)
plt.savefig('Rapor_3_Korelasyon_Matrisi.png', bbox_inches='tight')
print("-> Grafik 3 (Korelasyon) oluşturuldu.")

# ---------------------------------------------------------
# GÖRSEL 4: SINAV PUANI vs ÇALIŞMA (Detaylı Scatter)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=df_tr, x='Günlük Çalışma (Saat)', y='Sınav Puanı',
    hue='İnternet Kalitesi', style='Yarı Zamanlı İş',
    palette='deep', s=100, alpha=0.7
)
plt.title('Çalışma Saati ve Başarı İlişkisi (İnternet ve İş Durumuna Göre)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig('Rapor_4_Detayli_Basari_Analizi.png', bbox_inches='tight')
print("-> Grafik 4 (Başarı Analizi) oluşturuldu.")

# ---------------------------------------------------------
# GÖRSEL 5: VERİ SETİNDEN ÖRNEK (TABLO) - TÜM SÜTUNLAR
# ---------------------------------------------------------
print("-> Grafik 5 (Veri Tablosu - Tam Set) hazırlanıyor...")


def render_mpl_table(data, col_width=3.8, row_height=0.8, font_size=10,
                     header_color='#2c3e50', row_colors=['#ecf0f1', 'white'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        # Dinamik boyutlandırma: Sütun sayısına göre genişliği ayarla
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in mpl_table.get_celld().items():
        cell.set_edgecolor(edge_color)
        # Metinleri hem yatay hem dikey ortala
        cell.set_text_props(ha='center', va='center')

        if k[0] == 0:  # Başlık satırı
            cell.set_text_props(weight='bold', color='w', ha='center', va='center')
            cell.set_facecolor(header_color)
        else:  # Veri satırları
            cell.set_facecolor(row_colors[k[0] % len(row_colors)])

    return ax


# Tüm sütunları al (Seçilen sütun filtresini kaldırdık, tüm df_tr kullanılıyor)
# İlk 5 satırı al ve sayısal değerleri yuvarla
tablo_verisi = df_tr.head(5).round(2)

# Tabloyu oluştur - Geniş sütunlar ve okunabilir font
render_mpl_table(tablo_verisi, header_color='#2980b9', row_colors=['#d6eaf8', 'white'])

plt.savefig('Rapor_5_Ilk_5_Satir_Tablo.png', bbox_inches='tight', dpi=300)
print("-> Grafik 5 (Tam Veri Seti Tablosu) oluşturuldu.")

# ---------------------------------------------------------
# GEMINI İÇİN METİN ÇIKTISI
# ---------------------------------------------------------
print("\n" + "=" * 80)
print("GEMINI İÇİN VERİ ÇIKTISI (LÜTFEN AŞAĞIDAKİ TABLOYU KOPYALAYIN)")
print("=" * 80)
# Pandas tablosunu string formatına çevirip yazdırıyoruz
print(df_tr.head(5).to_string())
print("=" * 80)

print("\n----------------------------------------------")
print("TÜM GÖRSELLER BAŞARIYLA OLUŞTURULDU.")
print("Raporunuz için dosyalar kaydedildi.")
print("----------------------------------------------")