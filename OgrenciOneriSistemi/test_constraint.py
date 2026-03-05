import unittest
import re
from typing import List, Dict

# constraint_scheduler.py dosyasının aynı klasörde olduğunu varsayıyoruz
try:
    from constraint_scheduler import (
        FluxScheduler, StudyTask, TimeSlotConfig, CalendarService,
        SchedulerConfig, UserProfile, UserHistory, TaskPriority
    )

    PULP_AVAILABLE = True
except ImportError as e:
    PULP_AVAILABLE = False
    print(
        f"KRİTİK HATA: Modüller yüklenemedi. 'constraint_scheduler.py' dosyasının adının doğru olduğundan ve 'pulp' kütüphanesinin yüklü olduğundan emin olun.\nHata: {e}")


class TestFluxScheduler(unittest.TestCase):

    def setUp(self):
        if not PULP_AVAILABLE:
            self.skipTest("Gerekli kütüphaneler eksik.")

        # --- 1. Temel Konfigürasyon ---
        self.time_cfg = TimeSlotConfig(
            slot_duration_minutes=15,
            slots_per_hour=4,
            slots_per_day=96,
            horizon_days=7
        )

        # --- 2. Takvim ve Kısıtlar ---
        self.calendar = CalendarService(self.time_cfg)

        # Kullanıcının "başka hiçbir kısıt eklemedim" dediği senaryo.
        # Ancak sistem varsayılan olarak öğrenci kısıtlarını (Okul: H.İçi 09-17) uyguluyor olabilir.
        # Bunu simüle ediyoruz:
        self.calendar.apply_student_constraints()

        # --- 3. Kullanıcı Profili ---
        # Arayüzdeki varsayılan veya muhtemel profil
        self.user_profile = UserProfile.NIGHT_OWL
        self.calendar.apply_dynamic_sleep(self.user_profile)

        # Geçmiş Verisi (Varsayılan / Nötr)
        self.history = UserHistory(
            last_week_completion_rate=1.0,  # Nötr
            failed_task_ids=[],
            actual_work_hours=[]
        )

        # --- 4. Görev Havuzu (KULLANICI GİRDİLERİ) ---
        # Matematik(Zorluk: 8), Fizik(Zorluk: 9), Kimya(Zorluk: 6), Biyoloji(Zorluk: 4) - Hepsi 120dk
        self.tasks = [
            StudyTask(id="task_math", name="Matematik",
                      duration_minutes=120, difficulty=8, category="MATH",
                      priority=TaskPriority.HIGH),

            StudyTask(id="task_physics", name="Fizik",
                      duration_minutes=120, difficulty=9, category="SCI",
                      priority=TaskPriority.HIGH),

            StudyTask(id="task_chem", name="Kimya",
                      duration_minutes=120, difficulty=6, category="SCI",
                      priority=TaskPriority.MEDIUM),

            StudyTask(id="task_bio", name="Biyoloji",
                      duration_minutes=120, difficulty=4, category="SCI",
                      priority=TaskPriority.MEDIUM)
        ]

        # --- 5. Scheduler Ayarları ---
        self.scheduler_config = SchedulerConfig(
            user_mood_score=5,  # Nötr
            enable_coach_mode=True,
            max_daily_minutes=360  # Standart
        )

    def test_run_scheduler_and_analyze(self):
        """Kullanıcının bildirdiği 'Hafta Sonu Yığılması' sorununu analiz eder."""
        print("\n\n" + "=" * 60)
        print("🧪 KULLANICI SENARYOSU: 4 Ders (120dk) - Dağılım Analizi")
        print("=" * 60)

        scheduler = FluxScheduler(
            self.tasks,
            self.calendar,
            self.scheduler_config,
            self.time_cfg,
            self.user_profile,
            self.history
        )

        schedule = scheduler.solve()

        if not schedule:
            print("❌ Çizelge oluşturulamadı (Infeasible).")
            return

        # --- ÇIKTIYI YAZDIR ---
        print(f"\n📅 PLANLANAN GÖREV SAYISI: {len(schedule)}")
        print("-" * 80)
        print(f"{'GÜN':<15} | {'SAAT':<12} | {'GÖREV':<35} | {'SÜRE'}")
        print("-" * 80)

        days_active = set()
        day_loads: Dict[str, int] = {}

        for item in schedule:
            # Süre Hesabı
            h_s, m_s = map(int, item['start_fmt'].split(':'))
            h_e, m_e = map(int, item['end_fmt'].split(':'))
            dur = (h_e * 60 + m_e) - (h_s * 60 + m_s)

            print(f"{item['day']:<15} | {item['start_fmt']}-{item['end_fmt']:<5} | {item['task']:<35} | {dur} dk")

            day_name = item['day'].split(" ")[0]
            days_active.add(day_name)
            day_loads[day_name] = day_loads.get(day_name, 0) + dur

        # --- DETAYLI ANALİZ RAPORU ---
        print("\n" + "=" * 60)
        print("📊 SENARYO ANALİZ RAPORU")
        print("=" * 60)

        # 1. HAFTA İÇİ vs HAFTA SONU KULLANIMI
        weekdays = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        weekend = ["Cumartesi", "Pazar"]

        used_weekdays = [d for d in days_active if d in weekdays]
        used_weekend = [d for d in days_active if d in weekend]

        print(f"🔹 Hafta İçi Kullanılan Günler ({len(used_weekdays)}/5): {', '.join(used_weekdays)}")
        print(f"🔹 Hafta Sonu Kullanılan Günler ({len(used_weekend)}/2): {', '.join(used_weekend)}")

        if len(used_weekdays) <= 1 and len(used_weekend) == 2:
            print("\n⚠️ TESPİT: 'Hafta Sonu Savaşçısı' Sendromu Mevcut.")
            print("   Analiz: Model, hafta içi akşamlarını kullanmak yerine (yüksek ceza?),")
            print("   tüm yükü boş olan hafta sonuna ve Cuma akşamına yığıyor.")
        else:
            print("\n✅ TESPİT: Dengeli dağılım görünüyor.")

        # 2. GÜNLÜK YÜK ANALİZİ
        print("\n🔹 Günlük Yük Dağılımı:")
        for d, load in day_loads.items():
            print(f"   - {d}: {load} dakika")
            if load >= 180:
                print("     ⚠️ Yoğunluk Uyarısı: 3 saat veya üzeri blok.")

        # 3. MANTIKSAL AÇIKLAMA (AI Rationale)
        print("\n🔹 AI Mantığı (Neden böyle yaptı?):")
        for r in scheduler.ai_rationale:
            print(f"   - {r}")


if __name__ == '__main__':
    unittest.main()