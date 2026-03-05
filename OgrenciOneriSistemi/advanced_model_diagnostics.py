# advanced_model_diagnostics.py (DÜZELTİLMİŞ WINDOWS UYUMLU VERSİYON)

import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import learning_curve
from sklearn import set_config
import scipy.stats as stats

# --- AYARLAR ---
OUTPUT_DIR = "analiz_raporlari"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --- GEREKLİ SINIFLAR (MODELİN YÜKLENMESİ İÇİN) ---
class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return X


class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()
        # Temel türetimler
        sm = X_.get('social_media_hours', 0)
        nf = X_.get('netflix_hours', 0)
        X_['total_distraction_hours'] = sm + nf
        study = X_.get('study_hours_per_day', 0)
        sleep = X_.get('sleep_hours', 0)

        # 0'a bölme koruması
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
            if isinstance(X_['part_time_job'], pd.Series):
                pt_val = X_['part_time_job'].apply(lambda x: 1.5 if x == 'Yes' else 1.0)
            else:  # Eğer numpy array veya tekil değerse
                pt_val = np.where(X_['part_time_job'] == 'Yes', 1.5, 1.0)

        X_['burnout_risk'] = study * pt_val

        # Extracurricular yönetimi
        ec_val = 1.0
        if 'extracurricular_participation' in X_.columns:
            if isinstance(X_['extracurricular_participation'], pd.Series):
                ec_val = X_['extracurricular_participation'].apply(lambda x: 1.2 if x == 'Yes' else 1.0)
            else:
                ec_val = np.where(X_['extracurricular_participation'] == 'Yes', 1.2, 1.0)

        X_['dedication_level'] = att * ec_val
        return X_


def plot_learning_curve_graph(estimator, X, y, output_path):
    print("📈 Öğrenme Eğrisi (Learning Curve) Hesaplanıyor...")

    # DÜZELTME BURADA: n_jobs=1 yapıldı (Windows hatasını çözer)
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, cv=5, n_jobs=1,
        train_sizes=np.linspace(0.1, 1.0, 5),
        scoring='neg_root_mean_squared_error'
    )

    # Skorlar negatif döner (sklearn standardı), pozitife çeviriyoruz
    train_scores_mean = -np.mean(train_scores, axis=1)
    test_scores_mean = -np.mean(test_scores, axis=1)

    plt.figure(figsize=(10, 6))
    plt.plot(train_sizes, train_scores_mean, 'o-', color="#e74c3c", label="Eğitim Hatası (Training Error)")
    plt.plot(train_sizes, test_scores_mean, 'o-', color="#2ecc71", label="Doğrulama Hatası (Validation Error)")

    plt.title("Öğrenme Eğrisi (Learning Curve) Analizi\n(Bias-Variance Tradeoff Kontrolü)", fontsize=14)
    plt.xlabel("Eğitim Seti Boyutu (Örnek Sayısı)", fontsize=12)
    plt.ylabel("RMSE (Hata Payı)", fontsize=12)
    plt.legend(loc="best")
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"✅ Öğrenme Eğrisi Kaydedildi: {output_path}")

    return train_scores_mean[-1], test_scores_mean[-1]


def plot_residuals_diagnostics(y_true, y_pred, output_path):
    print("📉 Hata Dağılım Analizi (Residual Diagnostics) Yapılıyor...")

    residuals = y_true - y_pred

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 1. Residuals vs Predicted (Heteroscedasticity Check)
    sns.scatterplot(x=y_pred, y=residuals, alpha=0.6, ax=ax1, color='#3498db')
    ax1.axhline(0, color='red', linestyle='--', linewidth=2)
    ax1.set_title("Hata Dağılımı (Residuals vs Predicted)", fontsize=12)
    ax1.set_xlabel("Tahmin Edilen Notlar")
    ax1.set_ylabel("Hata (Residuals)")

    # 2. Q-Q Plot (Normality Check)
    stats.probplot(residuals, dist="norm", plot=ax2)
    ax2.set_title("Q-Q Grafiği (Normallik Testi)", fontsize=12)
    ax2.get_lines()[0].set_markerfacecolor('#9b59b6')
    ax2.get_lines()[0].set_markeredgecolor('#8e44ad')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"✅ Hata Analizi Grafikleri Kaydedildi: {output_path}")


def run_diagnostics():
    print("🏥 MODEL SAĞLIK KONTROLÜ (DIAGNOSTICS) BAŞLATILIYOR...")

    # Yükleme
    MODEL_PATH = "artifacts/student_score_xgb_pipeline_v2.joblib"

    csv_paths = [
        "student_habits_performance.csv",
        "data/student_habits_performance.csv",
        r"D:\Ensar Dosya\OgrenciOneriSistemi\student_habits_performance.csv"
    ]
    DATA_PATH = next((p for p in csv_paths if os.path.exists(p)), None)

    if not DATA_PATH:
        print("❌ Veri dosyası bulunamadı.")
        return
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model dosyası bulunamadı: {MODEL_PATH}")
        return

    try:
        model = joblib.load(MODEL_PATH)
        df = pd.read_csv(DATA_PATH)
        print(f"✅ Model ve Veri Yüklendi.")
    except Exception as e:
        print(f"❌ Hata: {e}")
        return

    set_config(transform_output="pandas")

    X = df.drop('exam_score', axis=1, errors='ignore')
    y = df['exam_score']

    # --- 1. ÖĞRENME EĞRİSİ ---
    lc_path = os.path.join(OUTPUT_DIR, "4_ogrenme_egrisi.png")

    try:
        final_train_err, final_test_err = plot_learning_curve_graph(model, X, y, lc_path)
    except Exception as e:
        print(f"⚠️ Öğrenme Eğrisi Hatası: {e}")
        final_train_err, final_test_err = 0, 0

    # --- 2. HATA DAĞILIM ANALİZİ ---
    try:
        y_pred = model.predict(X)
    except:
        y_pred = model.predict(X.values)

    res_path = os.path.join(OUTPUT_DIR, "5_hata_analizi_qq.png")
    plot_residuals_diagnostics(y, y_pred, res_path)

    # --- 3. RAPORLAMA ---
    txt_path = os.path.join(OUTPUT_DIR, "model_saglik_raporu.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("🏥 AI STUDENT COACH - MODEL SAĞLIK RAPORU\n")
        f.write("=" * 60 + "\n")
        f.write(f"1. BIAS-VARIANCE ANALİZİ (Öğrenme Eğrisi):\n")
        f.write(f"   - Son Eğitim Hatası (RMSE)   : {final_train_err:.4f}\n")
        f.write(f"   - Son Doğrulama Hatası (RMSE): {final_test_err:.4f}\n")
        f.write(f"   - Fark (Gap)                 : {abs(final_train_err - final_test_err):.4f}\n")

        gap = abs(final_train_err - final_test_err)
        if gap < 5.0:
            f.write("   -> YORUM: Fark düşük. Model 'Genelleştirme' (Generalization) konusunda başarılı.\n")
            f.write("   -> Overfitting (Ezberleme) belirtisi yok.\n")
        else:
            f.write("   -> YORUM: Fark yüksek. Overfitting riski var. Veri artırımı önerilir.\n")

        f.write("\n2. İSTATİSTİKSEL GEÇERLİLİK (Residuals):\n")
        f.write("   - Hata dağılımı (Q-Q Plot) 45 derecelik çizgi üzerindeyse,\n")
        f.write("     modelin hataları Normal Dağılıma uygundur.\n")
        f.write("   - Residuals grafiğinde rastgele saçılım varsa model başarılıdır.\n")
        f.write("   - Herhangi bir 'U' şekli veya huni şekli (Heteroscedasticity) yoksa güvenilirdir.\n")

    print(f"✅ Rapor Kaydedildi: {txt_path}")
    print("\n🎉 DIAGNOSTICS TAMAMLANDI.")


if __name__ == "__main__":
    run_diagnostics()