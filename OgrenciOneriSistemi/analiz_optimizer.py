import numpy as np
import time
from optimizer import AcademicOptimizer, MUTABLE_FEATURES


# ==========================================
# 🎭 MOCK ADVISOR (Taklit Danışman)
# ==========================================
# Gerçek XGBoost modelini taklit eden, sonucu formüle dayalı basit bir sınıf.
# Amacımız algoritmanın mantığını test etmek, modelin kendisini değil.
class MockAdvisor:
    def _calculate_derived(self, data: dict) -> dict:
        """Türetilmiş özellikleri hesaplar (Basit passthrough)"""
        return data.copy()

    def predict(self, data: dict) -> float:
        """
        Basit Formül:
        Puan = 40 + (Ders*4) + (Uyku*3) - (Sosyal*1.5) - (Netflix*1) + (Katılım*0.1)
        Zombi Cezası: Uyku < 6 ise -20 Puan.
        """
        study = data.get('study_hours_per_day', 0)
        sleep = data.get('sleep_hours', 0)
        social = data.get('social_media_hours', 0)
        netflix = data.get('netflix_hours', 0)
        attendance = data.get('attendance_percentage', 0)

        score = 40.0 + (study * 4.0) + (sleep * 3.0) - (social * 1.5) - (netflix * 1.0) + (attendance * 0.1)

        # Zombi Cezası (Modelin davranışını simüle ediyoruz)
        if sleep < 6.0:
            score -= 20.0

        return max(0.0, min(100.0, score))


# ==========================================
# 🧪 ANALİZ MOTORU
# ==========================================
class OptimizerAnalyzer:
    def __init__(self):
        self.mock_advisor = MockAdvisor()
        self.optimizer = AcademicOptimizer(self.mock_advisor)

    def _check_time_conservation(self, original, optimized):
        """Fizik kurallarını (24 saat) kontrol eder."""
        added = 0
        removed = 0

        # Giderler (Eklenenler)
        added += max(0, optimized['study_hours_per_day'] - original['study_hours_per_day'])
        added += max(0, optimized['sleep_hours'] - original['sleep_hours'])

        # Okul Süresi (Varsayım: %100 = 6 saat)
        orig_school = (original['attendance_percentage'] / 100.0) * 6.0
        opt_school = (optimized['attendance_percentage'] / 100.0) * 6.0
        added += max(0, opt_school - orig_school)

        # Gelirler (Kısılanlar)
        removed += max(0, original['social_media_hours'] - optimized['social_media_hours'])
        removed += max(0, original['netflix_hours'] - optimized['netflix_hours'])

        # Fark (Eklenen - Kısılan)
        return added - removed

    def run_stress_test(self, scenario_name, student_profile, target_score, frozen_features=[], iterations=20):
        print(f"\n🔬 SENARYO: {scenario_name}")
        print("=" * 65)
        start_score = self.mock_advisor.predict(student_profile)
        print(f"   Başlangıç: {start_score:.2f} -> Hedef: {target_score}")
        print(f"   Kısıtlamalar (Frozen): {frozen_features}")
        print("-" * 65)

        results = []
        start_time = time.time()

        metrics = {
            "success": 0,
            "zombie_fixed": 0,
            "physics_violation": 0,
            "constraint_violation": 0  # Kısıt ihlali
        }

        for _ in range(iterations):
            # Genetik Algoritmayı Çalıştır (Daha az step ile test edelim)
            res = self.optimizer.find_optimal_path(
                student_profile,
                target_score,
                frozen_features=frozen_features,
                population_size=15,  # Test için biraz düşürdük
                generations=20
            )

            if res['status'] == 'Success':
                metrics["success"] += 1
                opt_data = res['optimized_data']
                results.append(opt_data)

                # 1. Zombi Kontrolü
                was_zombie = student_profile['sleep_hours'] < 6.0
                is_zombie = opt_data['sleep_hours'] < 6.0
                if was_zombie and not is_zombie:
                    metrics["zombie_fixed"] += 1
                elif not was_zombie:
                    metrics["zombie_fixed"] += 1  # Zaten zombi değildi, başarılı sayılır

                # 2. Fizik Kontrolü (Tolerans 0.5 saat)
                time_diff = self._check_time_conservation(student_profile, opt_data)
                if time_diff > 0.6:
                    metrics["physics_violation"] += 1

                # 3. Kısıt (Frozen) Kontrolü
                for feat in frozen_features:
                    if abs(opt_data[feat] - student_profile[feat]) > 0.01:
                        metrics["constraint_violation"] += 1

        duration = time.time() - start_time

        # --- RAPORLAMA ---
        print(f"✅ Başarı Oranı         : %{(metrics['success'] / iterations) * 100:.1f}")

        # Sadece başarı durumunda anlamlı metrikler
        if metrics['success'] > 0:
            zombie_rate = (metrics['zombie_fixed'] / metrics['success']) * 100
            print(f"🧟 Zombi Kurtarma       : %{zombie_rate:.1f}")
            print(f"⚖️ Fizik İhlali (Bug)   : {metrics['physics_violation']} adet")
            print(f"🔒 Kısıt İhlali (Bug)   : {metrics['constraint_violation']} adet")

            # Ortalama Değerler
            avg_sleep = np.mean([r['sleep_hours'] for r in results])
            avg_study = np.mean([r['study_hours_per_day'] for r in results])
            print(f"📊 Ortalama Sonuç      : Uyku={avg_sleep:.1f}s, Ders={avg_study:.1f}s")

        print(f"⏱️ Ort. İşlem Süresi    : {(duration / iterations) * 1000:.2f} ms")

        if metrics['success'] == 0:
            print("❌ HİÇBİR ÇÖZÜM BULUNAMADI! (Hedef çok yüksek veya kısıtlar çok katı)")


# ==========================================
# 🏁 MAIN TEST
# ==========================================
if __name__ == "__main__":
    analyzer = OptimizerAnalyzer()

    # 1. SENARYO: NETFLIX BAĞIMLISI (KISIT TESTİ)
    # Öğrenci: "Puanımı artır ama Netflix'ime (4 saat) dokunma!"
    # Beklenti: Netflix 4.0 kalmalı, Sosyal Medya ve Uyku değişmeli.
    netflix_addict = {
        'study_hours_per_day': 1.0, 'social_media_hours': 4.0, 'netflix_hours': 4.0,
        'sleep_hours': 7.0, 'attendance_percentage': 70.0, 'diet_quality': 'Fair'
    }
    # Mock puanı ~50. Hedef: 75
    analyzer.run_stress_test(
        "NETFLIX BAĞIMLISI (Locking Test)",
        netflix_addict,
        target_score=75,
        frozen_features=['netflix_hours']
    )

    # 2. SENARYO: ZOMBİ KURTARMA (GENETİK EVRİM)
    # Zombi (4.5 saat uyku) ve Hedef yüksek.
    # Beklenti: Genetik algoritma "Zombi Cezasını" aşmak için uykuyu 6.0'a çekmeli.
    zombie_student = {
        'study_hours_per_day': 5.0, 'social_media_hours': 2.0, 'netflix_hours': 2.0,
        'sleep_hours': 4.5, 'attendance_percentage': 80.0, 'diet_quality': 'Fair'
    }
    analyzer.run_stress_test(
        "ZOMBİ EVRİMİ (Survival Test)",
        zombie_student,
        target_score=80
    )

    # 3. SENARYO: İMKANSIZ GÖREV (FİZİK SINIRI)
    # Zaten iyi bir öğrenci, imkansız puan istiyor.
    # Beklenti: Başarısızlık (%0 veya çok düşük başarı).
    # Çünkü Genetik Algoritma da olsa zamanı bükemez.
    good_student = {
        'study_hours_per_day': 6.0, 'social_media_hours': 1.0, 'netflix_hours': 0.0,
        'sleep_hours': 7.5, 'attendance_percentage': 95.0, 'diet_quality': 'Good'
    }
    analyzer.run_stress_test(
        "İMKANSIZ HEDEF (Physics Test)",
        good_student,
        target_score=99.9
    )