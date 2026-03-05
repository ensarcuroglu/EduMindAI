import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# *** UI/UX STİL AYARLARI ***
plt.style.use('default')
sns.set_context("notebook", font_scale=1.1)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.family'] = 'sans-serif'

# Renk Paleti
COLOR_PERFORMANCE = '#E74C3C'  # Kırmızı/Turuncu tonu
COLOR_STUDY = '#3498DB'        # Mavi tonu
COLOR_DIET = '#2ECC71'         # Yeşil tonu
COLOR_SLEEP = '#9B59B6'        # Mor tonu
BACKGROUND_COLOR = '#F9F9F9'
TEXT_COLOR = '#2C3E50'

# Veri setini yükle
try:
    df = pd.read_csv('D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv')
except FileNotFoundError:
    print("HATA: Dosya bulunamadı. Lütfen dosya adını veya yolunu kontrol edin.")
    exit()

print("--- Öğrenci Performansı Temel Analiz Tablosu ---")

# Figür ve Alt Grafikleri Oluştur (2x2 Grid)
fig, axes = plt.subplots(2, 2, figsize=(15, 12), facecolor=BACKGROUND_COLOR)
fig.suptitle('Öğrenci Alışkanlıkları ve Sınav Skoru Arasındaki Temel İlişkiler',
             fontsize=20, color=TEXT_COLOR, y=1.02, fontweight='bold')

# Grafik Başlıkları ve Etiketleri İçin Yardımcı Fonksiyon
def set_labels(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=14, color=TEXT_COLOR, pad=10)
    ax.set_xlabel(xlabel, fontsize=12, color=TEXT_COLOR)
    ax.set_ylabel(ylabel, fontsize=12, color=TEXT_COLOR)
    ax.spines[['right', 'top']].set_visible(False)
    ax.set_facecolor('white')

# =========================================================================
# 1. GRAFİK: Sınav Skoru Dağılımı (Histogram)
# =========================================================================
ax1 = axes[0, 0]
sns.histplot(df['exam_score'], kde=True, bins=20, ax=ax1,
             color=COLOR_PERFORMANCE, edgecolor='white', alpha=0.8)

# Medyan çizgisini ekle
median_score = df['exam_score'].median()
ax1.axvline(median_score, color='black', linestyle='--', linewidth=1.5, label=f'Medyan: {median_score:.1f}')
ax1.legend(fontsize=10)

set_labels(ax1, '1. Sınav Skoru Genel Dağılımı', 'Sınav Skoru', 'Öğrenci Sayısı (Frekans)')

# =========================================================================
# 2. GRAFİK: Çalışma Saati vs. Sınav Skoru (Serpilme Grafiği)
# =========================================================================
ax2 = axes[0, 1]
sns.scatterplot(x='study_hours_per_day', y='exam_score', data=df, ax=ax2,
                alpha=0.6, color=COLOR_STUDY, edgecolor='w', s=50)
sns.regplot(x='study_hours_per_day', y='exam_score', data=df, ax=ax2,
            scatter=False, color=COLOR_STUDY, line_kws={'linestyle': '--', 'linewidth': 2}) # Regresyon doğrusu

set_labels(ax2, '2. Günlük Çalışma Saati vs. Performans (Korelasyon)',
           'Günlük Çalışma Saati (Saat)', 'Sınav Skoru')

# =========================================================================
# 3. GRAFİK: Beslenme Kalitesi vs. Sınav Skoru (Kutu Grafiği)
# =========================================================================
ax3 = axes[1, 0]
# Medyana göre sıralama
order_diet = df.groupby('diet_quality')['exam_score'].median().sort_values(ascending=False).index
sns.boxplot(x='diet_quality', y='exam_score', data=df, ax=ax3, order=order_diet,
            palette=[COLOR_DIET, '#88C0A6', '#C7E9C0'], width=0.5)

ax3.set_xticklabels(['İyi', 'Orta', 'Kötü']) # Etiketleri Türkçeleştir
set_labels(ax3, '3. Beslenme Kalitesinin Sınav Skoru Dağılımına Etkisi',
           'Beslenme Kalitesi', 'Sınav Skoru')

# =========================================================================
# 4. GRAFİK: Uyku Saati vs. Sınav Skoru (Serpilme Grafiği)
# =========================================================================
ax4 = axes[1, 1]
sns.scatterplot(x='sleep_hours', y='exam_score', data=df, ax=ax4,
                alpha=0.6, color=COLOR_SLEEP, edgecolor='w', s=50)

set_labels(ax4, '4. Uyku Saati vs. Sınav Skoru İlişkisi',
           'Günlük Uyku Saati (Saat)', 'Sınav Skoru')

# Grafikler arasında yeterli boşluk bırak
plt.tight_layout(rect=[0, 0, 1, 0.98])
plt.show()

print("\n--- Analiz Tablosu Hazır. ---")