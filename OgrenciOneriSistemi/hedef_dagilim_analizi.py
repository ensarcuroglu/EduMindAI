import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm

# --- AYARLAR ---
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'sans-serif' # Türkçe karakter sorunu yaşamamak için

# --- 1. VERİ YÜKLEME ---
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

# Hedef Değişken
target = df['exam_score']

# --- 2. GRAFİK OLUŞTURMA ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# --- SOL GRAFİK: Orijinal Dağılım ---
sns.histplot(target, kde=True, color='#87CEEB', edgecolor='white', bins=20, ax=axes[0])
# Normal dağılım eğrisini ekle (karşılaştırma için)
mu, std = norm.fit(target)
xmin, xmax = axes[0].get_xlim()
x = np.linspace(xmin, xmax, 100)
p = norm.pdf(x, mu, std)
# Ölçeklendirme (Histogramın yüksekliğine uydurmak için)
# Bu sadece görsel bir referanstır, y ekseni count olduğu için pdf'i ölçekliyoruz
axes[0].plot(x, p * len(target) * (xmax - xmin) / 20, 'r--', linewidth=2, label='Normal Dağılım (Teorik)')

axes[0].set_title('Orijinal Hedef Değişken (Exam Score)', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Not Dağılımı', fontsize=11)
axes[0].set_ylabel('Frekans (Count)', fontsize=11)
axes[0].legend()

# --- SAĞ GRAFİK: Logaritmik Dönüşüm Sonrası ---
# Log1p Dönüşümü Uygula
target_log = np.log1p(target)

sns.histplot(target_log, kde=True, color='#2ECC71', edgecolor='white', bins=20, ax=axes[1])

# Normal dağılım eğrisini ekle (Log veri için)
mu_log, std_log = norm.fit(target_log)
xmin_log, xmax_log = axes[1].get_xlim()
x_log = np.linspace(xmin_log, xmax_log, 100)
p_log = norm.pdf(x_log, mu_log, std_log)
axes[1].plot(x_log, p_log * len(target_log) * (xmax_log - xmin_log) / 20, 'r--', linewidth=2, label='Normal Dağılım (Teorik)')

axes[1].set_title('Logaritmik Dönüşüm Sonrası (Log1p)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Log(Not + 1)', fontsize=11)
axes[1].set_ylabel('Frekans (Count)', fontsize=11)
axes[1].legend()

# --- BAŞLIK VE KAYDETME ---
plt.suptitle('Şekil 3.3: Hedef Değişken (Sınav Notu) Dönüşüm Öncesi ve Sonrası Dağılım Analizi', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()

# Yüksek çözünürlüklü kaydet
plt.savefig('Hedef_Degisken_Dagitimi_V5.png', dpi=300, bbox_inches='tight')
print("📊 Grafik kaydedildi: Hedef_Degisken_Dagitimi_V5.png")
plt.show()