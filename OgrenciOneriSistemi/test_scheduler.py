import time
import statistics
# DÜZELTME: SLOT_SIZE kaldırıldı, DEFAULT_CONFIG eklendi
from genetic_scheduler import AdvancedScheduler, DAYS, DEFAULT_CONFIG


# --- RENKLENDİRME ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class ScheduleValidator:
    def __init__(self, schedule, input_data, test_name, config_override=None):
        self.schedule = schedule
        self.input = input_data
        self.name = test_name
        self.config = config_override or {}

        self.errors = []
        self.warnings = []
        self.infos = []

        # Talep edilen slot sayısı (Yuvarlama mantığı dahil)
        self.requested_slots = 0

        # DÜZELTME: Varsayılan değeri DEFAULT_CONFIG'den al
        default_slot_size = DEFAULT_CONFIG["SLOT_SIZE"]
        slot_size = self.config.get("SLOT_SIZE", default_slot_size)

        for s in input_data['subjects']:
            self.requested_slots += max(1, round(s['total_minutes'] / slot_size))

    def _print_grid(self):
        """Konsola haftalık program tablosu çizer"""
        print(f"\n{Colors.CYAN}📅 {self.name} - GÖRSEL TABLO{Colors.ENDC}")
        headers = [d[:3] for d in DAYS]
        print("      " + " ".join([f"{h:>5}" for h in headers]))
        print("     " + "-" * 48)

        # Config'den gün sınırlarını al (Varsayılanlar DEFAULT_CONFIG'den)
        start_h = self.config.get("DAY_START_HOUR", DEFAULT_CONFIG["DAY_START_HOUR"])
        end_h = self.config.get("DAY_END_HOUR", DEFAULT_CONFIG["DAY_END_HOUR"])

        grid = {h: {d: ".." for d in DAYS} for h in range(start_h, end_h + 1)}

        for item in self.schedule:
            h = int(item['start'].split(':')[0])
            d = item['day']
            if start_h <= h <= end_h:
                grid[h][d] = item['title'][:5]

        for h in range(start_h, end_h + 1):
            row_str = f"{h:02d}:00 |"
            for d in DAYS:
                val = grid[h][d]
                color = Colors.GREEN if val != ".." else Colors.ENDC

                # Zor dersleri kırmızı yap
                if val != "..":
                    subj = next((s for s in self.input['subjects'] if s['name'].startswith(val)), None)
                    if subj and subj['difficulty'] >= 4: color = Colors.FAIL

                row_str += f" {color}{val:>5}{Colors.ENDC} |"
            print(row_str)

    def analyze(self):
        print(f"\n{Colors.HEADER}🔍 ANALİZ RAPORU: {self.name}{Colors.ENDC}")

        if not self.schedule:
            print(f"{Colors.FAIL}❌ KRİTİK: Çizelge boş döndü!{Colors.ENDC}")
            return

        total_scheduled = len(self.schedule)

        # 1. Doluluk Oranı
        if total_scheduled < self.requested_slots:
            missing = self.requested_slots - total_scheduled
            self.errors.append(f"KAYIP DERS: {missing} saat ders yerleştirilemedi (Kapasite yetersiz).")
        elif total_scheduled > self.requested_slots:
            self.warnings.append(f"FAZLA DERS: İstenenden {total_scheduled - self.requested_slots} saat fazla.")

        # Veri Hazırlığı
        day_loads = {d: 0 for d in DAYS}
        slots_occupied = set()
        subject_days = {}  # Dersin hangi günlerde olduğu
        daily_subjects = {d: [] for d in DAYS}  # Günlük ders listesi (sıralı)

        school_data = self.input['student_info'].get('school_schedule', {})
        school_days = school_data.get('days', [])
        school_start = school_data.get('start', 8)
        school_end = school_data.get('end', 15)

        for item in self.schedule:
            d = item['day']
            h = int(item['start'].split(':')[0])
            subj = item['title']
            slot_key = f"{d}-{h}"

            day_loads[d] += 1
            if subj not in subject_days: subject_days[subj] = set()
            subject_days[subj].add(d)
            daily_subjects[d].append((h, subj))

            # 2. Hard Constraint: Çakışma
            if slot_key in slots_occupied:
                self.errors.append(f"ÇAKIŞMA: {d} {h}:00'da birden fazla ders var!")
            slots_occupied.add(slot_key)

            # 3. Hard Constraint: Okul Saati
            if d in school_days and school_start <= h < school_end:
                self.errors.append(f"OKUL ÇAKIŞMASI: {d} {h}:00.")

        # 4. Soft Constraint: Gravity (Dağılma) Kontrolü
        for subj, days in subject_days.items():
            if len(days) > 4:
                self.warnings.append(
                    f"DAĞINIK DERS: {subj} dersi {len(days)} farklı güne yayılmış (Gravity başarısız).")

        # 5. Bloklama Kalitesi (Popcorn Effect Check)
        for d in DAYS:
            daily_items = sorted(daily_subjects[d], key=lambda x: x[0])
            if not daily_items: continue

            # Gün içindeki ders değişim sayısını ölç
            switches = 0
            for k in range(len(daily_items) - 1):
                curr_s = daily_items[k][1]
                next_s = daily_items[k + 1][1]
                if curr_s != next_s:
                    switches += 1

            # Eğer günde 5 ders var ama 4 kere ders değişiyorsa -> Popcorn
            if len(daily_items) > 4 and switches >= len(daily_items) - 1:
                self.warnings.append(f"POPCORN ETKİSİ: {d} gününde dersler çok parçalı (Sürekli ders değişimi).")

        # Rapor Yazdır
        if not self.errors and not self.warnings:
            print(f"{Colors.GREEN}✅ MÜKEMMEL SONUÇ{Colors.ENDC}")
        else:
            for e in self.errors: print(f"{Colors.FAIL}❌ {e}{Colors.ENDC}")
            for w in self.warnings: print(f"{Colors.WARNING}⚠️ {w}{Colors.ENDC}")

        print(
            f"{Colors.BLUE}ℹ️  Doluluk: {total_scheduled}/{self.requested_slots} Slot ({total_scheduled / self.requested_slots * 100:.0f}%){Colors.ENDC}")
        self._print_grid()

        # --- ÖZET TABLOSU ---
        print(f"\n{Colors.HEADER}📊 {self.name} - ÖZET İSTATİSTİKLER{Colors.ENDC}")
        print(f"   • Durum:     {'❌ FAIL' if self.errors else ('⚠️ WARN' if self.warnings else '✅ PASS')}")
        print(
            f"   • Kapasite:  %{int(total_scheduled / self.requested_slots * 100) if self.requested_slots else 0} ({total_scheduled}/{self.requested_slots})")
        print(f"   • Hata/Uyarı: {len(self.errors)} / {len(self.warnings)}")
        print(f"   • Gün Yayılımı: {sum(1 for d in day_loads.values() if d > 0)}/7 gün")
        print("-" * 50 + "\n")


# ==========================================
# 🔥 EKSTREM SENARYOLAR
# ==========================================

# 1. "THE SWISS CHEESE" (İsviçre Peyniri)
test_cheese = {
    "student_info": {
        "school_schedule": {"days": ["Monday", "Wednesday", "Friday"], "start": 10, "end": 18}
    },
    "subjects": [
        {"name": "Fizik", "total_minutes": 300, "difficulty": 5},  # 5 saat
        {"name": "Kimya", "total_minutes": 300, "difficulty": 4},
        {"name": "Bio", "total_minutes": 300, "difficulty": 3},
        {"name": "Mat", "total_minutes": 300, "difficulty": 5},
    ]
}

# 2. "THE MATH OLYMPIAN" (Tek Ders Yüklemesi)
test_olympian = {
    "student_info": {
        "school_schedule": {"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "start": 8, "end": 15}},
    "subjects": [
        {"name": "OLIMPIYAT_MAT", "total_minutes": 1800, "difficulty": 5, "color": "#ff0000"}  # 30 Saat!
    ]
}

# 3. "THE INSOMNIAC" (Gece Kuşu - Config Override)
test_insomniac = {
    "student_info": {
        "school_schedule": {"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "start": 9, "end": 17}},
    "subjects": [
        {"name": "Gece_Fizigi", "total_minutes": 600, "difficulty": 5},  # 10 saat
        {"name": "Gece_Kodu", "total_minutes": 600, "difficulty": 4},  # 10 saat
        {"name": "Uyku_Yok", "total_minutes": 600, "difficulty": 3}  # 10 saat
    ]
}

# 4. "MISSION IMPOSSIBLE" (Kapasite Aşımı)
test_impossible = {
    "student_info": {
        "school_schedule": {"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "start": 8, "end": 16}},
    "subjects": [
        {"name": "AŞIRI_YÜK_1", "total_minutes": 3000, "difficulty": 3},  # 50 saat
        {"name": "AŞIRI_YÜK_2", "total_minutes": 3000, "difficulty": 3},  # 50 saat
        {"name": "AŞIRI_YÜK_3", "total_minutes": 3000, "difficulty": 3},  # 50 saat
    ]
}


def run_stress_tests():
    print(f"{Colors.BOLD}🚀 GENETIC SCHEDULER: ULTIMATE STRESS TEST{Colors.ENDC}\n")

    # SENARYO 1
    print("--- 1. MATH OLYMPIAN (GRAVITY TEST) ---")
    s1 = AdvancedScheduler(test_olympian)
    r1 = s1.run()
    v1 = ScheduleValidator(r1, test_olympian, "OLYMPIAN")
    v1.analyze()

    # SENARYO 2
    print("\n--- 2. INSOMNIAC (CONFIG OVERRIDE TEST) ---")
    # Config'i eziyoruz: Gece 02:00'ye kadar izin ver
    insomniac_config = {
        "DAY_END_HOUR": 26,  # 24 + 2 = 02:00
        "PENALTY_LATE_GENERAL": 0,  # Gece cezasını kaldır
        "PENALTY_LATE_WEEKEND": 0
    }
    s2 = AdvancedScheduler(test_insomniac, config=insomniac_config)
    r2 = s2.run()
    # Validator'a da config veriyoruz ki tabloyu ona göre çizsin
    v2 = ScheduleValidator(r2, test_insomniac, "INSOMNIAC (02:00 AM)", config_override=insomniac_config)
    v2.analyze()

    # SENARYO 3
    print("\n--- 3. MISSION IMPOSSIBLE (FAIL GRACEFULLY TEST) ---")
    s3 = AdvancedScheduler(test_impossible)
    r3 = s3.run()
    v3 = ScheduleValidator(r3, test_impossible, "IMPOSSIBLE")
    v3.analyze()

    print("\n🏁 Testler tamamlandı.")


if __name__ == "__main__":
    run_stress_tests()