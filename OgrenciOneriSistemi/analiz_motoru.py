import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from tqdm import tqdm  # İlerleme çubuğu için (yoksa: pip install tqdm)

# --- IMPORT KONTROLÜ ---
try:
    import oneri_motoru_V2
    from oneri_motoru_V2 import SmartAdvisor, FeatureEngineer, OutlierCapper

    # --- KRİTİK DÜZELTME: Sınıfları __main__ uzayına kopyalıyoruz ---
    # Bu satırlar, joblib'in modeli yüklerken "Sınıfı bulamadım" hatasını engeller.
    sys.modules['__main__'].FeatureEngineer = FeatureEngineer
    sys.modules['__main__'].OutlierCapper = OutlierCapper

except ImportError:
    print("❌ HATA: 'oneri_motoru_V2.py' dosyası bulunamadı.")
    sys.exit(1)

# Çıktı Ayarları
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
sns.set_theme(style="whitegrid", palette="muted")


class EngineAnalyzer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.advisor = SmartAdvisor()
        self.df = None
        self.results = []
        self.recommendation_stats = []

        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Veri yok: {self.data_path}")
        self.df = pd.read_csv(self.data_path)
        # ID yoksa oluştur
        if 'student_id' not in self.df.columns:
            self.df['student_id'] = range(1, len(self.df) + 1)

    def run_batch_analysis(self, sample_size=None):
        """Toplu analiz çalıştırır."""
        print(f"\n🚀 MOTOR ANALİZİ BAŞLIYOR...")

        # Eğer model yüklenemediyse çalışmayı durdur
        if self.advisor.model is None:
            print("❌ KRİTİK HATA: Model (joblib) yüklenemediği için analiz yapılamıyor.")
            return

        # --- KRİTİK DÜZELTME: EKSİK VERİLERİ TEMİZLE ---
        # Analiz için sadece verisi tam olan öğrencileri alıyoruz.
        initial_count = len(self.df)
        target_df = self.df.dropna()
        final_count = len(target_df)

        print(f"🧹 Veri Temizliği: {initial_count - final_count} eksik verili öğrenci analiz dışı bırakıldı.")
        print(f"📊 Analiz Edilecek Net Öğrenci Sayısı: {final_count}")

        if sample_size and sample_size < final_count:
            target_df = target_df.sample(sample_size)

        for _, row in tqdm(target_df.iterrows(), total=len(target_df), desc="Analiz Ediliyor"):
            try:
                student_dict = row.to_dict()

                # Motoru çalıştır
                advice = self.advisor.generate_advice(student_dict)

                # Sonuçları kaydet
                res = {
                    'student_id': student_dict.get('student_id'),
                    'current_score': advice['current_score'],
                    'potential_score': advice['potential_score'],
                    'uplift': advice['potential_score'] - advice['current_score'],
                    'rec_count': len(advice['recommendations']),
                    'total_time_cost': advice['time_budget_used'],
                    'sleep_hours': row['sleep_hours'],  # Analiz için kritik
                    'study_hours': row['study_hours_per_day']
                }
                self.results.append(res)

                # Öneri detaylarını kaydet
                for rec in advice['recommendations']:
                    self.recommendation_stats.append({
                        'category': rec.get('category', 'Unknown'),
                        'impact': rec.get('calculated_impact', 0),
                        'feature': rec['simulation']['feature']
                    })
            except Exception as e:
                continue

        self.res_df = pd.DataFrame(self.results)
        self.rec_df = pd.DataFrame(self.recommendation_stats)
        print("✅ Analiz tamamlandı.")

    def print_executive_summary(self):
        """Yönetici özeti basar."""
        if not self.results:
            print("⚠️ Analiz sonucu boş.")
            return

        print("\n" + "=" * 50)
        print("📋 SİSTEM PERFORMANS RAPORU (EXECUTIVE SUMMARY)")
        print("=" * 50)

        avg_uplift = self.res_df['uplift'].mean()
        max_uplift = self.res_df['uplift'].max()
        avg_time = self.res_df['total_time_cost'].mean()

        print(f"Ortalama Puan Artışı : +{avg_uplift:.2f} Puan")
        print(f"Maksimum Puan Artışı : +{max_uplift:.2f} Puan")
        print(f"Ortalama Ekstra Süre : {avg_time:.2f} Saat/Gün")
        print("-" * 50)

        # Kritik Uyku Modu Analizi
        zombies = self.res_df[self.res_df['sleep_hours'] < 6]
        print(f"Tespit Edilen 'Zombi' Öğrenci Sayısı: {len(zombies)}")
        if not zombies.empty:
            # Zombilere verilen ortalama süre maliyeti (0 olması lazım)
            zombie_cost = zombies['total_time_cost'].mean()
            print(f"Zombilere Yüklenen Ekstra Ders Saati : {zombie_cost:.2f} (Hedef: 0.0)")

            # Tolerans (Float hataları için < 0.1)
            if zombie_cost < 0.1:
                print("✅ TEST GEÇİLDİ: Sistem uykusuzları koruyor.")
            else:
                print("❌ TEST KALDI: Sistem uykusuzlara ders yüklüyor!")
        else:
            print("ℹ️ Analiz grubunda hiç uykusuz öğrenci yok.")

    def plot_insights(self):
        """Görsel analizleri oluşturur."""
        if not self.results: return
        if not os.path.exists("analiz_cikti"): os.mkdir("analiz_cikti")

        plt.figure(figsize=(18, 12))

        # 1. Puan Artış Dağılımı
        plt.subplot(2, 2, 1)
        sns.histplot(self.res_df['uplift'], kde=True, color='green', bins=30)
        plt.title('Sistemin Vadettiği Puan Artışları (Uplift Distribution)')
        plt.xlabel('Puan Artışı')

        # 2. Öneri Kategorileri
        plt.subplot(2, 2, 2)
        if not self.rec_df.empty:
            cat_counts = self.rec_df['category'].value_counts()
            plt.pie(cat_counts, labels=cat_counts.index, autopct='%1.1f%%', startangle=140,
                    colors=sns.color_palette("pastel"))
            plt.title('Öneri Kategorilerinin Dağılımı')

        # 3. Mevcut Puan vs Potansiyel (Scatter)
        plt.subplot(2, 2, 3)
        sns.scatterplot(x='current_score', y='potential_score', data=self.res_df, hue='uplift', palette='viridis',
                        size='uplift')
        plt.plot([0, 100], [0, 100], 'r--', lw=2)  # Referans çizgisi
        plt.title('Mevcut vs Potansiyel Puan')
        plt.xlabel('Şu Anki Tahmin')
        plt.ylabel('Potansiyel (Önerilerle)')

        # 4. En Çok Önerilen Aksiyonlar
        plt.subplot(2, 2, 4)
        if not self.rec_df.empty:
            top_features = self.rec_df['feature'].value_counts().head(5)
            sns.barplot(x=top_features.values, y=top_features.index, palette="mako")
            plt.title('En Sık Müdahale Edilen Özellikler')

        plt.tight_layout()
        plt.savefig("analiz_cikti/motor_analiz_dashboard.png")
        print("\n📊 Grafik kaydedildi: analiz_cikti/motor_analiz_dashboard.png")
        plt.show()


if __name__ == "__main__":
    # Yol ayarı
    DATA_PATH = "data/student_habits_performance.csv"
    if os.path.exists(r"D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv"):
        DATA_PATH = r"D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv"

    analyzer = EngineAnalyzer(DATA_PATH)

    # Tüm veri setini analiz et (None = Hepsi)
    analyzer.run_batch_analysis(sample_size=300)

    analyzer.print_executive_summary()
    analyzer.plot_insights()