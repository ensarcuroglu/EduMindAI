#analiz_log.py:
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import sys
import scipy.stats as stats
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, median_absolute_error
from sklearn import set_config

# --- GÜVENLİK VE IMPORT ---
try:
    from performans_tahmin_V2 import OutlierCapper, FeatureEngineer
except ImportError:
    print("❌ HATA: 'performans_tahmin_V2.py' dosyası bulunamadı.")
    sys.exit(1)

set_config(transform_output="pandas")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
# Görselleştirme Teması
sns.set_theme(style="whitegrid", context="talk", palette="viridis")


class ProfessionalValidator:
    def __init__(self, model_path, data_path, output_dir="analiz_raporlari"):
        self.model_path = model_path
        self.data_path = data_path
        self.output_dir = output_dir
        self.model = None
        self.df = None
        self.X = None
        self.y = None
        self.predictions = None
        self.residuals = None
        self.analysis_df = None
        self.report_buffer = []  # Rapor metinlerini burada biriktireceğiz

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self._load_resources()

    def _log(self, message):
        """Hem konsola hem rapora yazar."""
        print(message)
        self.report_buffer.append(message)

    def _load_resources(self):
        if not os.path.exists(self.model_path): raise FileNotFoundError(f"Model yok: {self.model_path}")
        if not os.path.exists(self.data_path): raise FileNotFoundError(f"Veri yok: {self.data_path}")

        print(f"📥 Kaynaklar yükleniyor...")
        self.model = joblib.load(self.model_path)
        self.df = pd.read_csv(self.data_path)

        # Veri Hazırlığı
        if 'exam_score' not in self.df.columns: raise ValueError("Hedef sütun eksik.")
        self.y = self.df['exam_score']
        self.X = self.df.drop(columns=['exam_score', 'student_id'], errors='ignore')

    def run_prediction(self):
        print("🤖 Model çalıştırılıyor...")
        self.predictions = self.model.predict(self.X)
        self.residuals = self.y - self.predictions

        # Detaylı Analiz DataFrame'i
        self.analysis_df = self.X.copy()
        self.analysis_df['Actual'] = self.y
        self.analysis_df['Predicted'] = self.predictions
        self.analysis_df['Error'] = self.residuals
        self.analysis_df['Abs_Error'] = self.residuals.abs()
        self.analysis_df['Error_Pct'] = (self.analysis_df['Abs_Error'] / self.analysis_df['Actual']) * 100

    def analyze_metrics_pro(self):
        """Gelişmiş metrik analizi."""
        rmse = np.sqrt(mean_squared_error(self.y, self.predictions))
        mae = mean_absolute_error(self.y, self.predictions)
        med_ae = median_absolute_error(self.y, self.predictions)  # Outlier'lardan etkilenmez
        r2 = r2_score(self.y, self.predictions)

        # Confidence Interval (95%)
        std_dev = np.std(self.residuals)
        margin_of_error = 1.96 * std_dev

        self._log("\n" + "█" * 50)
        self._log("📊 PROFESYONEL PERFORMANS RAPORU")
        self._log("█" * 50)
        self._log(f"► R2 (Açıklayıcılık) : {r2:.4f} " + ("✅ Mükemmel" if r2 > 0.9 else "⚠️ İyileştirilebilir"))
        self._log(f"► RMSE (Hata Karekök) : {rmse:.2f}")
        self._log(f"► MAE (Ort. Mutlak Hata): {mae:.2f}")
        self._log(f"► MedAE (Medyan Hata)   : {med_ae:.2f} (Bu değer MAE'den düşükse, hata uç değerlerden kaynaklıdır)")
        self._log(f"► Güven Aralığı (%95)   : +/- {margin_of_error:.2f} Puan")
        self._log("-" * 50)

    def check_fairness_and_bias(self):
        """Kategorik değişkenlere göre modelin adil olup olmadığını ölçer."""
        self._log("\n⚖️ ADALET VE ÖNYARGI ANALİZİ (FAIRNESS CHECK)")
        self._log("-" * 50)

        cat_cols = self.X.select_dtypes(include=['object']).columns

        for col in cat_cols:
            # Gruplara göre Ortalama Mutlak Hata (MAE)
            group_errors = self.analysis_df.groupby(col)['Abs_Error'].mean().sort_values()
            max_diff = group_errors.max() - group_errors.min()

            self._log(f"📌 {col.upper()} Bazlı Hata Analizi:")
            for cat, err in group_errors.items():
                self._log(f"   - {cat:<25}: {err:.2f} MAE")

            if max_diff > 3.0:
                self._log(f"   ⚠️ UYARI: Model '{col}' özelliğinde taraf tutuyor olabilir! (Fark: {max_diff:.2f})")
            else:
                self._log(f"   ✅ Dengeli dağılım.")
            self._log("")

    def analyze_corner_cases_pro(self, n=5):
        """En kötü ve en iyi tahminleri analiz eder."""
        self._log("\n🚨 UÇ NOKTA ANALİZİ (CORNER CASES)")
        self._log("-" * 50)

        # En büyük hatalar (Overestimation & Underestimation)
        worst_over = self.analysis_df.sort_values('Error', ascending=False).head(n)  # Tahmin > Gerçek
        worst_under = self.analysis_df.sort_values('Error', ascending=True).head(n)  # Tahmin < Gerçek

        cols = ['Actual', 'Predicted', 'Error', 'study_hours_per_day', 'sleep_hours', 'attendance_percentage']

        self._log("🔻 MODELİN AŞIRI İYİMSER OLDUĞU DURUMLAR (Tahmin > Gerçek):")
        self._log(worst_over[cols].to_string(index=False))
        self._log("\n🔻 MODELİN AŞIRI KÖTÜMSER OLDUĞU DURUMLAR (Tahmin < Gerçek):")
        self._log(worst_under[cols].to_string(index=False))

    def generate_dashboard(self):
        """4'lü Profesyonel Dashboard Çizer."""
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(2, 2)

        # 1. Gerçek vs Tahmin (Regresyon Çizgisiyle)
        ax1 = fig.add_subplot(gs[0, 0])
        sns.regplot(x=self.y, y=self.predictions, ax=ax1, scatter_kws={'alpha': 0.5, 'color': '#2c3e50'},
                    line_kws={'color': '#e74c3c'})
        ax1.set_title('Doğruluk: Gerçek vs Tahmin', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Gerçek Not')
        ax1.set_ylabel('Tahmin Edilen Not')

        # 2. Residuals vs Predicted (Heteroscedasticity)
        ax2 = fig.add_subplot(gs[0, 1])
        sns.scatterplot(x=self.predictions, y=self.residuals, ax=ax2, alpha=0.6, color='#2980b9', edgecolor='w', s=80)
        ax2.axhline(0, color='black', linestyle='--', lw=2)
        ax2.set_title('Hata Dağılımı (Homojenlik Kontrolü)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Tahmin Edilen Not')
        ax2.set_ylabel('Hata Miktarı')

        # 3. Distribution Overlap (KDE)
        ax3 = fig.add_subplot(gs[1, 0])
        sns.kdeplot(self.y, fill=True, color="green", label="Gerçek", ax=ax3, alpha=0.3)
        sns.kdeplot(self.predictions, fill=True, color="blue", label="Tahmin", ax=ax3, alpha=0.3)
        ax3.set_title('Not Dağılımı Karşılaştırması', fontsize=14, fontweight='bold')
        ax3.legend()

        # 4. Q-Q Plot (Normallik Testi - Bilimsel Kanıt)
        ax4 = fig.add_subplot(gs[1, 1])
        stats.probplot(self.residuals, dist="norm", plot=ax4)
        ax4.get_lines()[0].set_markerfacecolor('#8e44ad')
        ax4.get_lines()[0].set_markeredgecolor('w')
        ax4.get_lines()[1].set_color('black')
        ax4.set_title('Q-Q Plot (Hata Normallik Testi)', fontsize=14, fontweight='bold')

        plt.tight_layout()
        save_path = os.path.join(self.output_dir, "Model_Dashboard_Pro.png")
        plt.savefig(save_path, dpi=300)
        print(f"\n📊 Dashboard kaydedildi: {save_path}")
        plt.show()

    def save_text_report(self):
        """Tüm logları dosyaya yazar."""
        path = os.path.join(self.output_dir, "Model_Analiz_Raporu.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.report_buffer))
        print(f"📄 Metin raporu kaydedildi: {path}")


# --- MAIN BLOCK ---
if __name__ == "__main__":
    MODEL_PATH = "artifacts/student_score_xgb_pipeline_v2.joblib"

    # Veri yolu bulucu (Windows/Mac uyumlu)
    DATA_PATH = "data/student_habits_performance.csv"
    if os.path.exists(r"D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv"):
        DATA_PATH = r"D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv"

    try:
        validator = ProfessionalValidator(MODEL_PATH, DATA_PATH)
        validator.run_prediction()

        # Analiz Adımları
        validator.analyze_metrics_pro()
        validator.check_fairness_and_bias()
        validator.analyze_corner_cases_pro()

        # Görselleştirme ve Kayıt
        validator.generate_dashboard()
        validator.save_text_report()

    except Exception as e:
        print(f"\n❌ KRİTİK HATA: {e}")
        import traceback

        traceback.print_exc()