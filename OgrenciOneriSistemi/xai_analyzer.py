import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib
import warnings
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

# --- ÖNEMLİ: Web Sunucusu İçin Backend Ayarı ---
matplotlib.use('Agg')
warnings.filterwarnings('ignore')

# Grafik Stili: Modern ve Akademik
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'

try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("❌ HATA: 'shap' kütüphanesi yüklü değil.")


# =============================================================================
# 1. OUTLIER CAPPER (Performans Tahmin V2 ile BİREBİR AYNI)
# =============================================================================

class OutlierCapper(BaseEstimator, TransformerMixin):
    """
    Aykırı değerleri (Outliers) IQR yöntemiyle alt ve üst sınırlara baskılar.
    Modelin uç değerlerden (örn: günde 25 saat ders) sapmasını engeller.
    """

    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        # Not: Pipeline içinde fit edildiğinde bu değerler öğrenilir.
        # Ancak joblib ile yüklendiğinde öğrenilmiş değerler (lower_bounds_) zaten nesne içinde gelir.
        return self

    def transform(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            return X
        X_ = X.copy()
        # Eğer modelden yüklenen sınırlar varsa onları kullan
        if hasattr(self, 'lower_bounds_') and self.lower_bounds_:
            for col, lower in self.lower_bounds_.items():
                if col in X_.columns:
                    upper = self.upper_bounds_.get(col, np.inf)
                    X_[col] = np.clip(X_[col], lower, upper)
        return X_


# =============================================================================
# 2. FeatureEngineer (Performans Tahmin V2 ile BİREBİR AYNI)
# =============================================================================

class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Ham verilerden modelin daha iyi anlayacağı 'Zeka Dolu' özellikler türetir.
    V2 GÜNCELLEMESİ İLE SENKRONİZE EDİLDİ.
    """

    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            return X

        X_ = X.copy()

        # Güvenli erişim için get kullanalım ama formüller V2 ile aynı olsun
        study = X_.get('study_hours_per_day', 0)
        sleep = X_.get('sleep_hours', 0)
        social = X_.get('social_media_hours', 0)
        netflix = X_.get('netflix_hours', 0)
        attendance = X_.get('attendance_percentage', 0)
        mental = X_.get('mental_health_rating', 5)
        exercise = X_.get('exercise_frequency', 0)

        # --- Temel Türetimler (V1) ---
        X_['total_distraction_hours'] = social + netflix
        X_['focus_ratio'] = study / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = sleep / (study + 1)
        X_['study_efficiency'] = study * mental
        X_['academic_engagement'] = attendance * study
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        # --- İleri Seviye Türetimler (V2 - Senkronize) ---

        # 1. Zindelik Skoru (Vitality): (Uyku ^ 1.2) * (Egzersiz + 1)
        X_['vitality_score'] = (sleep ** 1.2) * (exercise + 1)

        # 2. Tükenmişlik Riski (Burnout Risk)
        # Part-time iş kontrolü (V2'deki np.where mantığı)
        pt_val = 1.0
        pt_col = X_.get('part_time_job')
        if pt_col is not None:
            if isinstance(pt_col, pd.Series):
                pt_val = np.where(pt_col == 'Yes', 1.5, 1.0)
            elif isinstance(pt_col, str) and pt_col == 'Yes':
                pt_val = 1.5
        X_['burnout_risk'] = study * pt_val

        # 3. Adanmışlık (Dedication)
        ec_val = 1.0
        ec_col = X_.get('extracurricular_participation')
        if ec_col is not None:
            if isinstance(ec_col, pd.Series):
                ec_val = np.where(ec_col == 'Yes', 1.2, 1.0)
            elif isinstance(ec_col, str) and ec_col == 'Yes':
                ec_val = 1.2
        X_['dedication_level'] = attendance * ec_val

        return X_


# =============================================================================
# 3. XAI VISUALIZATION ENGINE
# =============================================================================

from oneri_motoru_V2 import SmartAdvisor


class XAI_Analyzer:
    def __init__(self, advisor_instance: SmartAdvisor):
        self.advisor = advisor_instance
        self.output_dir = "wwwroot/xai_outputs"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # SmartAdvisor zaten yüklü modeli ve pipeline'ı taşıyor.
        self.explainer = advisor_instance.explainer
        self.prep_pipeline = advisor_instance.prep_pipeline

    def _preprocess_data(self, raw_data_dict):
        """
        Veriyi SHAP analizine hazırlar.
        ÖNEMLİ: Model pipeline'ı 'FeatureEngineer' adımını zaten içerdiği için
        burada sadece ham veriyi DataFrame'e çevirip pipeline'a veriyoruz.
        Manuel zenginleştirme (advisor._calculate_derived) yapmıyoruz, çünkü pipeline bunu tekrar yapacak.
        """
        df = pd.DataFrame([raw_data_dict])

        # Pipeline'ın transform metodunu kullan (FeatureEngineer -> Preprocessor)
        if self.prep_pipeline:
            return self.prep_pipeline.transform(df)
        return df

    def generate_waterfall_plot(self, student_data, filename="shap_waterfall.png"):
        """
        Neden-Sonuç Analizi (Waterfall).
        """
        if not self.explainer or not SHAP_AVAILABLE:
            return None

        try:
            # 1. Veriyi hazırla (Ham veri -> Pipeline -> İşlenmiş Veri)
            X_processed = self._preprocess_data(student_data)

            # 2. SHAP değerlerini hesapla
            shap_values = self.explainer.shap_values(X_processed)

            # Boyut kontrolü
            values = shap_values[0] if isinstance(shap_values, list) else shap_values
            if hasattr(values, 'shape') and len(values.shape) > 1:
                values = values[0]

            # Özellik isimlerini pipeline'dan veya veriden çek
            feature_names = X_processed.columns.tolist() if hasattr(X_processed, 'columns') else [f"Feature {i}" for i
                                                                                                  in range(len(values))]

            # Base value
            base_value = self.explainer.expected_value
            if isinstance(base_value, np.ndarray): base_value = base_value[0]

            explanation = shap.Explanation(
                values=values,
                base_values=base_value,
                data=X_processed.values[0] if hasattr(X_processed, 'values') else X_processed[0],
                feature_names=feature_names
            )

            # Gerçek skor (Predict fonksiyonu da pipeline'ı kullandığı için sonuç tutarlı olacak)
            real_score = self.advisor.predict(student_data)

            plt.figure(figsize=(10, 6))
            shap.plots.waterfall(explanation, max_display=10, show=False)

            plt.title(f"Puanın Anatomisi | Tahmini Skor: {real_score:.1f}",
                      fontsize=14, fontweight='bold', pad=20)

            save_path = os.path.join(self.output_dir, filename)
            plt.savefig(save_path, bbox_inches='tight', dpi=100)
            plt.close()

            return save_path
        except Exception as e:
            print(f"❌ [XAI] Waterfall Hatası: {e}")
            return None

    def generate_what_if_curve(self, student_data, feature_name, min_val, max_val, step=0.5, filename="what_if.png"):
        """
        Sweet Spot Analizi (Simülasyon).
        """
        try:
            values = np.arange(min_val, max_val + step, step)
            scores = []
            temp_data = student_data.copy()
            current_val = temp_data.get(feature_name, 0)

            for v in values:
                temp_data[feature_name] = v
                # Burada predict'e HAM SÖZLÜK veriyoruz.
                # Predict fonksiyonu da bunu pipeline'a sokuyor.
                score = self.advisor.predict(temp_data)
                scores.append(score)

            # Analiz
            max_score = max(scores)
            max_idx = scores.index(max_score)
            optimal_val = values[max_idx]
            current_score = self.advisor.predict(student_data)

            # Grafik
            plt.figure(figsize=(10, 5))
            sns.lineplot(x=values, y=scores, linewidth=3, color="#2c3e50", label="Potansiyel Başarı")
            plt.fill_between(values, scores, alpha=0.1, color="#3498db")

            plt.scatter([current_val], [current_score], color='#e74c3c', s=120, zorder=5,
                        edgecolor='white', linewidth=2, label=f"Mevcut ({current_val}h)")

            if abs(optimal_val - current_val) > 0.5 and max_score > current_score + 1:
                plt.scatter([optimal_val], [max_score], color='#27ae60', s=150, zorder=5, marker='*',
                            edgecolor='white', linewidth=1, label=f"Önerilen ({optimal_val}h)")
                plt.annotate(f"Maksimum Verim\n+{max_score - current_score:.1f} Puan",
                             xy=(optimal_val, max_score), xytext=(optimal_val, max_score - 10),
                             arrowprops=dict(facecolor='#27ae60', shrink=0.05),
                             horizontalalignment='center', color='#27ae60', fontweight='bold')

            clean_name = feature_name.replace('_', ' ').title()
            plt.title(f"Simülasyon: {clean_name} Değişimi", fontsize=14, fontweight='bold')
            plt.xlabel(f"{clean_name} (Değer)", fontsize=11)
            plt.ylabel("Tahmini Puan", fontsize=11)
            plt.legend(loc='lower right')
            plt.grid(True, linestyle='--', alpha=0.6)

            save_path = os.path.join(self.output_dir, filename)
            plt.savefig(save_path, dpi=100)
            plt.close()

            insight = ""
            if current_val < optimal_val:
                insight = f"💡 Tavsiye: {current_val} -> {optimal_val} artışı puanını {max_score:.1f} yapabilir."
            elif current_val > optimal_val:
                insight = f"⚠️ Uyarı: Fazla yüklenme verimsiz. {optimal_val} seviyesi daha iyi."
            else:
                insight = "✅ Mükemmel denge!"

            return {"path": save_path, "insight": insight}

        except Exception as e:
            print(f"❌ [XAI] What-If Hatası: {e}")
            return None

    def generate_radar_comparison(self, student_data, filename="radar_chart.png"):
        """
        Radar Grafiği: İdeal profil kıyaslaması.
        """
        try:
            metrics = ['study_hours_per_day', 'sleep_hours', 'attendance_percentage', 'social_media_hours']
            labels = ['Ders\nÇalışma', 'Uyku\nDüzeni', 'Derse\nKatılım', 'Sosyal\nMedya (Ters)']
            ideal_profile = [6.0, 8.0, 95.0, 1.0]
            student_vals = [student_data.get(m, 0) for m in metrics]
            max_vals = [8.0, 10.0, 100.0, 6.0]

            student_norm = []
            ideal_norm = []

            for i, metric in enumerate(metrics):
                val_s = student_vals[i]
                val_i = ideal_profile[i]
                max_v = max_vals[i]
                if metric == 'social_media_hours':
                    s_n = max(0, 1 - (val_s / max_v))
                    i_n = max(0, 1 - (val_i / max_v))
                else:
                    s_n = min(1, val_s / max_v)
                    i_n = min(1, val_i / max_v)
                student_norm.append(s_n)
                ideal_norm.append(i_n)

            angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
            student_norm += [student_norm[0]]
            ideal_norm += [ideal_norm[0]]
            angles += [angles[0]]
            labels += [labels[0]]

            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
            ax.plot(angles, ideal_norm, color='#2ecc71', linewidth=1, linestyle='--', label='Hedef')
            ax.fill(angles, ideal_norm, color='#2ecc71', alpha=0.1)
            ax.plot(angles, student_norm, color='#3498db', linewidth=2, label='Sen')
            ax.fill(angles, student_norm, color='#3498db', alpha=0.25)

            ax.set_yticklabels([])
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels[:-1], size=10, fontweight='bold')
            plt.title("Yetenek Dengesi", size=14, y=1.05, fontweight='bold')
            plt.legend(loc='lower right', bbox_to_anchor=(1.1, 0.1))

            save_path = os.path.join(self.output_dir, filename)
            plt.savefig(save_path, dpi=100, bbox_inches='tight')
            plt.close()
            return save_path
        except Exception as e:
            print(f"❌ [XAI] Radar Hatası: {e}")
            return None


# =============================================================================
# TEST (Doğrudan çalıştırılırsa)
# =============================================================================
if __name__ == "__main__":
    print("🔬 XAI Analiz Modülü Test Ediliyor...")

    # Ana motordan advisor'ı çağır
    advisor = SmartAdvisor()
    analyzer = XAI_Analyzer(advisor)

    # Test Verisi (Ham veri - Feature Engineering'siz)
    sample_student = {
        'student_id': 'TEST_USER', 'age': 20, 'gender': 'Male',
        'study_hours_per_day': 2.0, 'social_media_hours': 4.0,
        'netflix_hours': 2.0, 'attendance_percentage': 60.0,
        'sleep_hours': 5.0, 'part_time_job': 'Yes', 'exam_score': 0,
        'exercise_frequency': 1, 'extracurricular_participation': 'No',
        'parental_education_level': 'High School', 'mental_health_rating': 5,
        'internet_quality': 'Good', 'diet_quality': 'Average'
    }

    print("\n--- Grafikler Oluşturuluyor ---")
    wf_path = analyzer.generate_waterfall_plot(sample_student)
    print(f"1. Waterfall: {wf_path}")

    wi_res = analyzer.generate_what_if_curve(sample_student, 'study_hours_per_day', 0, 10, filename="test_whatif.png")
    if wi_res:
        print(f"2. What-If: {wi_res['path']} | Insight: {wi_res['insight']}")

    rd_path = analyzer.generate_radar_comparison(sample_student)
    print(f"3. Radar: {rd_path}")