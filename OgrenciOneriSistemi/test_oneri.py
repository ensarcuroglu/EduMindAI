import pandas as pd
import numpy as np
import sys
import os
import joblib
from sklearn.base import BaseEstimator, TransformerMixin

# Mevcut dizini path'e ekle
sys.path.append(os.getcwd())


# =============================================================================
# KRİTİK DÜZELTME: MODELİN YÜKLENEBİLMESİ İÇİN GEREKLİ SINIFLAR
# =============================================================================
# Joblib modeli yüklerken bu sınıfları __main__ içinde aradığı için
# bunları buraya eklemek ZORUNDAYIZ.
# =============================================================================

class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            return X
        X_ = X.copy()
        if hasattr(self, 'lower_bounds_') and self.lower_bounds_:
            for col, lower in self.lower_bounds_.items():
                if col in X_.columns:
                    upper = self.upper_bounds_.get(col, np.inf)
                    X_[col] = np.clip(X_[col], lower, upper)
        return X_


class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            print("⚠️ FeatureEngineer Uyarısı: Girdi verisi Pandas DataFrame değil. İşlem atlanıyor.")
            return X

        X_ = X.copy()

        sm = X_.get('social_media_hours', 0)
        nf = X_.get('netflix_hours', 0)
        X_['total_distraction_hours'] = sm + nf

        study = X_.get('study_hours_per_day', 0)
        sleep = X_.get('sleep_hours', 0)

        X_['focus_ratio'] = study / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = sleep / (study + 1)

        mh = X_.get('mental_health_rating', 5)
        X_['study_efficiency'] = study * mh

        att = X_.get('attendance_percentage', 0)
        X_['academic_engagement'] = att * study
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        ex = X_.get('exercise_frequency', 0)
        X_['vitality_score'] = sleep * (ex + 1)

        pt_job = X_.get('part_time_job', 'No')
        pt_multiplier = 1.5 if hasattr(pt_job, 'lower') and pt_job == 'Yes' else 1.0
        if hasattr(pt_job, 'apply'):
            pt_multiplier = pt_job.apply(lambda x: 1.5 if x == 'Yes' else 1.0)

        X_['burnout_risk'] = study * pt_multiplier

        ec_part = X_.get('extracurricular_participation', 'No')
        ec_multiplier = 1.2 if hasattr(ec_part, 'lower') and ec_part == 'Yes' else 1.0
        if hasattr(ec_part, 'apply'):
            ec_multiplier = ec_part.apply(lambda x: 1.2 if x == 'Yes' else 1.0)

        X_['dedication_level'] = att * ec_multiplier

        return X_


# =============================================================================
# SMART ADVISOR İÇE AKTARMA
# =============================================================================
try:
    from oneri_motoru_V2 import SmartAdvisor
except ImportError:
    print("❌ HATA: 'oneri_motoru_V2.py' dosyası bu dizinde bulunamadı.")
    sys.exit(1)


# =============================================================================
# TEST KONFİGÜRASYONU VE RENKLER
# =============================================================================
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Color.HEADER}{'=' * 60}\n{text}\n{'=' * 60}{Color.ENDC}")


def print_result(test_name, status, msg=""):
    color = Color.OKGREEN if status else Color.FAIL
    symbol = "✅ BAŞARILI" if status else "❌ BAŞARISIZ"
    print(f"{Color.BOLD}[{test_name}]{Color.ENDC} -> {color}{symbol}{Color.ENDC} {msg}")


# =============================================================================
# SENARYOLAR (PERSONA TANIMLARI)
# =============================================================================
def get_test_personas():
    return {
        "THE_ZOMBIE": {  # Uykusuz, Düşük Performans
            "student_id": "TEST_001", "age": 20, "study_hours_per_day": 6.0,
            "sleep_hours": 4.5, "social_media_hours": 2.0, "netflix_hours": 1.0,
            "attendance_percentage": 80, "mental_health_rating": 3,
            "exercise_frequency": 0, "parental_education_level": "High School",
            # EKSİK KOLONLAR EKLENDİ
            "internet_quality": "Average",
            "gender": "Male",
            "part_time_job": "No",
            "diet_quality": "Poor",
            "extracurricular_participation": "No"
        },
        "THE_SLACKER": {  # Çok Sosyal, Az Ders
            "student_id": "TEST_002", "age": 21, "study_hours_per_day": 1.0,
            "sleep_hours": 8.0, "social_media_hours": 5.0, "netflix_hours": 4.0,
            "attendance_percentage": 60, "mental_health_rating": 8,
            "exercise_frequency": 2, "parental_education_level": "Bachelor",
            # EKSİK KOLONLAR EKLENDİ
            "internet_quality": "High",
            "gender": "Female",
            "part_time_job": "No",
            "diet_quality": "Average",
            "extracurricular_participation": "Yes"
        },
        "THE_OVERACHIEVER": {  # Zaten Yüksek, Tükenmişlik Sınırında
            "student_id": "TEST_003", "age": 22, "study_hours_per_day": 9.0,
            "sleep_hours": 6.5, "social_media_hours": 1.0, "netflix_hours": 0.5,
            "attendance_percentage": 95, "mental_health_rating": 6,
            "exercise_frequency": 1, "parental_education_level": "Master",
            # EKSİK KOLONLAR EKLENDİ
            "internet_quality": "High",
            "gender": "Female",
            "part_time_job": "Yes",
            "diet_quality": "Healthy",
            "extracurricular_participation": "Yes"
        }
    }


# =============================================================================
# TEST FONKSİYONLARI
# =============================================================================

def test_simulation_logic(advisor):
    """
    Simülasyon motorunun zamanı doğru yönetip yönetmediğini test eder.
    Ders saati artırıldığında, eğlence zamanından kesiyor mu?
    """
    print_header("TEST 1: SİMÜLASYON MANTIĞI (ZAMAN YÖNETİMİ)")

    student = get_test_personas()["THE_SLACKER"]
    initial_social = student['social_media_hours']

    # Senaryo: Derse 2 saat ekle
    recs = [{
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 2.0}
    }]

    # Simülasyonu çalıştır
    simulated_data = advisor.apply_smart_simulation(student, recs)

    final_study = simulated_data['study_hours_per_day']
    final_social = simulated_data['social_media_hours']
    final_netflix = simulated_data['netflix_hours']

    # Kontroller
    print(f"   Önceki Ders: {student['study_hours_per_day']}, Sonraki Ders: {final_study}")
    print(f"   Önceki Sosyal: {initial_social}, Sonraki Sosyal: {final_social}")

    # Mantık: Ders arttıysa, sosyal medya veya netflix azalmalı (Zaman borcu tahsili)
    total_distraction_initial = initial_social + student['netflix_hours']
    total_distraction_final = final_social + final_netflix

    if total_distraction_final < total_distraction_initial:
        print_result("Time Debt Collection", True,
                     f"Eğlence zamanı {total_distraction_initial - total_distraction_final:.2f} saat azaldı.")
    else:
        print_result("Time Debt Collection", False,
                     "Ders saati arttı ama eğlence zamanından düşülmedi! (Fizik kurallarına aykırı)")


def test_sleep_crisis_veto(advisor):
    """
    Uykusuz öğrenciye (The Zombie) ders çalışma önerisi veriliyor mu?
    Beklenen: Akademik önerilerin bloke edilmesi veya 'Sleep Fix'in en üstte olması.
    """
    print_header("TEST 2: UYKU KRİZİ VE VETO MEKANİZMASI")

    student = get_test_personas()["THE_ZOMBIE"]
    result = advisor.generate_advice(student)

    if not result['recommendations']:
        print_result("Zombie Protection", False, "Hiçbir öneri üretilemedi!")
        return

    top_rec = result['recommendations'][0]
    print(f"   En Üst Öneri Kategorisi: {top_rec.get('category')}")
    print(f"   Öneri Metni: {top_rec.get('text')}")

    if top_rec.get('simulation', {}).get('feature') == 'sleep_hours':
        print_result("Zombie Protection", True, "Sistem uykusuzluğu fark etti ve önceliklendirdi.")
    else:
        print_result("Zombie Protection", False, "UYARI: Uykusuz öğrenciye öncelikle uyku önerilmedi!")

    # Veto Kontrolü: Akademik öneri var mı?
    academic_recs = [r for r in result['recommendations'] if r.get('category') == 'Academic']
    if len(academic_recs) == 0:
        print_result("Academic Veto", True, "Uykusuz öğrenciye ders yükü bindirilmedi (Veto başarılı).")
    else:
        print(f"   ⚠️ Bulunan Akademik Öneri: {academic_recs[0]['text']}")
        print_result("Academic Veto", False, "Uykusuz öğrenciye ders çalışma önerildi! (Riskli)")


def test_diminishing_returns(advisor):
    """
    Sweet Spot Analizi: Çok çalışan birine daha da çalış demenin etkisi azalıyor mu?
    """
    print_header("TEST 3: AZALAN VERİM (DIMINISHING RETURNS)")

    student = get_test_personas()["THE_OVERACHIEVER"]  # Zaten 9 saat çalışıyor

    # 9 saatten 14 saate kadar çıkararak puanı izle
    current_val = student['study_hours_per_day']
    scores = []

    print(f"   Baseline ({current_val} saat): {advisor.predict(student):.2f}")

    for add in [1.0, 2.0, 3.0, 5.0]:
        temp_student = student.copy()
        temp_student['study_hours_per_day'] += add
        # OutlierCapper ve FeatureEngineer mantığı devreye girsin diye derived hesapla
        enriched = advisor._calculate_derived(temp_student)
        score = advisor.predict(enriched)
        uplift = score - advisor.predict(student)
        scores.append((current_val + add, score, uplift))
        print(f"   +{add} Saat (Top: {current_val + add}) -> Puan: {score:.2f} (Artış: {uplift:+.2f})")

    # Analiz: 14 saat çalışınca puan düşüşe geçmeli veya artış durmalı
    if len(scores) > 1:
        last_uplift = scores[-1][2]
        first_uplift = scores[0][2]

        if last_uplift < first_uplift:
            print_result("Burnout Simulation", True, "Aşırı çalışmada verim artışı yavaşladı/düştü.")
        else:
            print_result("Burnout Simulation", False,
                         "DİKKAT: Model sürekli doğrusal artış veriyor olabilir (Gerçekçi değil).")
    else:
        print_result("Burnout Simulation", False, "Yeterli veri noktası oluşturulamadı.")


def test_damping_factor(advisor):
    """
    Hayali yüksek puanları engelleme (Damping) testi.
    """
    print_header("TEST 4: PUAN SÖNÜMLEME (REALISM CHECK)")

    student = get_test_personas()["THE_SLACKER"]
    result = advisor.generate_advice(student)

    raw_uplift = 0
    # Ham upliftleri topla
    for rec in result['recommendations']:
        raw_uplift += rec.get('calculated_impact', 0)

    reported_uplift = result['potential_score'] - result['current_score']

    print(f"   Toplam Ham Etki (Önerilerin Toplamı): {raw_uplift:.2f}")
    print(f"   Raporlanan Nihai Artış: {reported_uplift:.2f}")

    if reported_uplift < raw_uplift:
        ratio = reported_uplift / raw_uplift if raw_uplift > 0 else 0
        print_result("Damping Logic", True, f"Puan sönümleme aktif. (Oran: %{ratio * 100:.1f})")
    else:
        # Eğer raw_uplift çok küçükse damping devreye girmeyebilir, bunu başarısızlık saymayalım
        if raw_uplift < 1.0:
            print_result("Damping Logic", True, "Uplift çok küçük olduğu için damping uygulanmadı (Normal).")
        else:
            print_result("Damping Logic", False, "Puanlar direkt toplanıyor, abartılı sonuç çıkabilir.")


def test_optimizer_integration(advisor):
    """
    Genetic Algorithm (AcademicOptimizer) entegrasyon testi.
    """
    print_header("TEST 5: OPTİMİZASYON ALGORİTMASI TESTİ")
    try:
        from optimizer import AcademicOptimizer
        opt = AcademicOptimizer(advisor)
        student = get_test_personas()["THE_SLACKER"]
        target_score = advisor.predict(student) + 10  # 10 puan artış iste

        print(f"   Hedef: +10 Puan (Mevcut: {advisor.predict(student):.2f})")

        # Netflix'i kitle (Değiştirme)
        plan = opt.find_optimal_path(student, target_score, frozen_features=['netflix_hours'])

        if plan['status'] == 'Success':
            optimized_data = plan['optimized_data']
            # Kontrol: Netflix değişmiş mi?
            if optimized_data['netflix_hours'] == student['netflix_hours']:
                print_result("Constraint Check", True, "Netflix saati sabit tutuldu (Kısıtlama çalışıyor).")
            else:
                print_result("Constraint Check", False,
                             f"Netflix değiştirildi! ({student['netflix_hours']} -> {optimized_data['netflix_hours']})")

            print(f"   Ulaşılan Skor: {plan['achieved_score']:.2f}")
            print(f"   Önerilen Değişiklikler: {len(plan['changes'])} adet")
        else:
            # Optimizasyonun başarısız olması kodun bozuk olduğu anlamına gelmez,
            # sadece hedefe ulaşılamadığını gösterir.
            print_result("Optimizer Run", False, f"Optimizasyon hedefi yakalayamadı: {plan.get('msg')}")

    except ImportError:
        print(f"{Color.WARNING}optimizer.py bulunamadı, bu test atlanıyor.{Color.ENDC}")
    except Exception as e:
        print(f"{Color.FAIL}Optimizasyon hatası: {e}{Color.ENDC}")


# =============================================================================
# MAIN RUNNER
# =============================================================================
if __name__ == "__main__":
    print_header("🔍 ONERI MOTORU V2 - SİSTEM SAĞLIK TARAMASI")

    # 1. Advisor'ı Başlat
    # Not: Sınıfları yukarıda tanımladığımız için artık model yüklenebilir olmalı.
    print("Advisor başlatılıyor...")
    try:
        advisor = SmartAdvisor()
    except Exception as e:
        print(f"{Color.FAIL}CRITICAL ERROR: Advisor başlatılamadı: {e}{Color.ENDC}")
        sys.exit(1)

    if advisor.model is None:
        print(
            f"{Color.WARNING}UYARI: Model dosyası (.joblib) yüklenemedi. Tahminler 0 dönecek, testler tam doğrulanamaz.{Color.ENDC}")
        # Test için dummy predict fonksiyonu atayalım (Eğer model yoksa)
        advisor.predict = lambda x: 50.0 + (x.get('study_hours_per_day', 0) * 2) + (x.get('sleep_hours', 0) * 1)
    else:
        print(f"{Color.OKBLUE}Model başarıyla yüklendi!{Color.ENDC}")

    # 2. Testleri Çalıştır
    test_simulation_logic(advisor)
    test_sleep_crisis_veto(advisor)
    test_diminishing_returns(advisor)
    test_damping_factor(advisor)
    test_optimizer_integration(advisor)

    print_header("TEST TAMAMLANDI")