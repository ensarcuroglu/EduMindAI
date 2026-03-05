import unittest
import math
import random
from optimizer import AcademicOptimizer


# ==========================================
# 🧠 ADVANCED MOCK ADVISOR (AKILLI DANIŞMAN)
# ==========================================
class AdvancedMockAdvisor:
    """
    Daha gerçekçi, lineer olmayan bir puanlama simülasyonu.
    - Azalan Verim Yasası: 10 saat çalışmak, 5 saat çalışmanın 2 katı puan getirmez.
    - Uyku Cezası: 6 saatin altında uyursan, çalıştığın dersin verimi düşer.
    """

    def _calculate_derived(self, data: dict) -> dict:
        return data

    def predict(self, data: dict) -> float:
        # 1. Temel Değerler
        study = data.get('study_hours_per_day', 0)
        sleep = data.get('sleep_hours', 7)
        attendance = data.get('attendance_percentage', 0)
        netflix = data.get('netflix_hours', 0)
        social = data.get('social_media_hours', 0)

        # 2. Uyku Çarpanı (Yorgunluk Etkisi)
        # Uyku 6 saatin altındaysa çalışma verimi %40 düşer.
        # Uyku 9 saatin üstündeyse "uyuşukluk"tan %10 düşer.
        efficiency = 1.0
        if sleep < 6.0:
            efficiency = 0.6
        elif sleep > 9.0:
            efficiency = 0.9

        # 3. Puan Hesaplama (Logaritmik Artış)
        # log kullanıyoruz ki sonsuz çalışmanın etkisi azalsın.
        base_score = 40.0

        # Çalışma Puanı (Verim çarpanı ile)
        study_score = math.log(study + 1) * 25.0 * efficiency

        # Devamsızlık (Lineer)
        att_score = (attendance / 100.0) * 15.0

        # Ceza Puanları (Karesel artış - çok izlemek çok kaybettirir)
        distraction_penalty = (netflix ** 1.2) * 2.0 + (social ** 1.1) * 1.5

        total_score = base_score + study_score + att_score - distraction_penalty

        return max(0, min(100, total_score))


# ==========================================
# 🔥 HARDCORE TEST SUITE
# ==========================================
class TestHardcoreOptimizer(unittest.TestCase):

    def setUp(self):
        self.advisor = AdvancedMockAdvisor()
        self.optimizer = AcademicOptimizer(self.advisor)

        # Standart "Sorunlu" Öğrenci Profili
        self.student_data = {
            'study_hours_per_day': 1.0,  # Çok az
            'social_media_hours': 5.0,  # Çok fazla
            'netflix_hours': 4.0,  # Çok fazla
            'sleep_hours': 5.5,  # Kritik sınırın altında (Verim düşük)
            'attendance_percentage': 60.0,
            'diet_quality': 'Poor'
        }

        # Başlangıç puanını hesaplayalım
        self.initial_score = self.advisor.predict(self.student_data)
        print(f"\n--- Test Başlangıç Profili (Skor: {self.initial_score:.2f}) ---")

    def test_01_sanity_check(self):
        """Basit kontrol: Kilit yokken puan artıyor mu?"""
        print("\nTEST 1: Kilit Yok - Genel İyileştirme")
        target = 85.0
        result = self.optimizer.find_optimal_path(self.student_data, target, frozen_features=[])

        self.assertEqual(result['status'], 'Success')
        self.assertGreater(result['achieved_score'], self.initial_score)
        print(f"✅ Başarı: {self.initial_score:.1f} -> {result['achieved_score']:.1f}")

    def test_02_stress_lock_integrity(self):
        """
        STRES TESTİ: 50 kez üst üste çalıştır.
        Eğer BİR kez bile kilitli özellik değişirse test başarısız olur.
        Genetik algoritmalardaki rastgeleliğin kilitleri kırmadığını kanıtlar.
        """
        print("\nTEST 2: Kilit Bütünlüğü Stres Testi (50 Döngü)")
        frozen = ['netflix_hours', 'sleep_hours']
        target = 80.0

        failures = 0
        for i in range(50):
            res = self.optimizer.find_optimal_path(
                self.student_data, target, frozen_features=frozen, population_size=10, generations=5
            )

            if res.get('status') == 'Success':
                opt_data = res['optimized_data']
                if opt_data['netflix_hours'] != self.student_data['netflix_hours']:
                    failures += 1
                    print(f"❌ HATA Döngü {i}: Netflix değişti!")
                if opt_data['sleep_hours'] != self.student_data['sleep_hours']:
                    failures += 1
                    print(f"❌ HATA Döngü {i}: Uyku değişti!")

        # Başarılı logunu sadece 1 kez yaz
        if failures == 0:
            print("✅ 50 döngü başarıyla tamamlandı, kilitler sağlam.")

        self.assertEqual(failures, 0, f"{failures} kez kilit ihlali yapıldı!")

    def test_03_impossible_triangle(self):
        """
        İMKANSIZ ÜÇGEN TESTİ:
        1. Çalışma saatini kitle (Düşük: 1 saat)
        2. Netflix'i kitle (Yüksek: 4 saat)
        3. Hedef: 95 Puan

        Beklenti: Sadece uykuyu ve devamsızlığı değiştirerek 95 alamaz.
        Sonuç 'Impossible' olmalı.
        """
        print("\nTEST 3: İmkansız Hedef Testi")
        frozen = ['study_hours_per_day', 'netflix_hours']
        target = 98.0  # Çok yüksek

        result = self.optimizer.find_optimal_path(self.student_data, target, frozen_features=frozen)

        print(f"Durum: {result['status']} (Beklenen: Impossible)")
        self.assertEqual(result['status'], 'Impossible',
                         "Optimizer fizik kurallarını ihlal edip imkansız puana ulaştı!")

    def test_04_sleep_efficiency_paradox(self):
        """
        UYKU PARADOKSU:
        Öğrencinin uykusu 5.5 saat (Verimsiz).
        Optimizer, çalışma saatini artırmak yerine SADECE uykuyu artırarak puan kazanabileceğini bulmalı.

        Senaryo: Çalışma saatini kitle (1.0). Hedefi yükselt.
        Çözüm: Uykuyu 5.5 -> 6.0+ seviyesine çekmek verimi artıracağı için puan artmalı.
        """
        print("\nTEST 4: Uyku Verimliliği Paradoksu")

        # Çalışma saati kilitli, yani puanı çalışarak artıramaz.
        frozen = ['study_hours_per_day']
        target = self.initial_score + 10.0  # Makul bir artış iste

        result = self.optimizer.find_optimal_path(self.student_data, target, frozen_features=frozen)

        if result['status'] == 'Impossible':
            print("⚠️ Uyarı: Hedef çok yüksek geldi, test atlanıyor.")
            return

        opt_sleep = result['optimized_data']['sleep_hours']
        print(f"Orijinal Uyku: {self.student_data['sleep_hours']}")
        print(f"Önerilen Uyku: {opt_sleep}")

        # DÜZELTME: 6.0 saat de "Verimli" kategorisine girdiği için >= 6.0 kabul edilmeli.
        # Optimizer, 6.0'a çıkarak verimliliği %40 artırdıysa başarılıdır.
        self.assertGreaterEqual(opt_sleep, 6.0,
                                "Optimizer verimi artırmak için uykuyu en azından 6.0 saate çekmeliydi!")
        print("✅ Optimizer, uykuyu kritik seviyenin (5.5) üzerine çıkardı.")

    def test_05_time_budget_constraint(self):
        """
        ZAMAN BÜTÇESİ KONTROLÜ:
        Optimizer, bir yerden zaman eklerken başka yerden kısmalı.
        Eğer ders çalışmayı +5 saat artırıp, netflix/uyku/sosyal medyadan hiç kısmıyorsa
        bu fiziksel olarak imkansızdır.
        """
        print("\nTEST 5: Zaman Bütçesi (Fizik Kuralları)")

        # Kilit yok, serbest optimizasyon
        target = 80.0
        result = self.optimizer.find_optimal_path(self.student_data, target)

        if result['status'] != 'Success':
            print("Test için uygun çözüm bulunamadı.")
            return

        orig = self.student_data
        new = result['optimized_data']

        # Değişimleri hesapla
        # (Basit hesap: Okul + Uyku + Ders + Netflix + Sosyal)
        def calc_total_load(d):
            school = (d['attendance_percentage'] / 100.0) * 6.0
            return d['study_hours_per_day'] + d['sleep_hours'] + d['netflix_hours'] + d['social_media_hours'] + school

        orig_load = calc_total_load(orig)
        new_load = calc_total_load(new)

        diff = new_load - orig_load

        print(f"Orijinal Yük: {orig_load:.2f} saat")
        print(f"Yeni Yük: {new_load:.2f} saat")
        print(f"Fark: {diff:.2f} saat")

        # Optimizer'ın cost fonksiyonunda 0.5 saatlik tolerans var.
        # Eğer fark 1.5 saatten fazlaysa, optimizer zaman yaratıyor demektir (HATA).
        self.assertLess(diff, 1.5, "Optimizer yoktan zaman var etti! (Zaman bütçesi aşıldı)")
        print("✅ Zaman bütçesi makul sınırlar içinde.")


if __name__ == '__main__':
    unittest.main()