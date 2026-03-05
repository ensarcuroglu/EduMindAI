# constraint_scheduler.py dosyasının eski genetik algoritma ile deneme hali (ESKİ)
import random
import json
import statistics
from deap import base, creator, tools, algorithms

# --- GLOBAL DEAP SETUP ---
if not hasattr(creator, "FitnessMax"):
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
if not hasattr(creator, "Individual"):
    creator.create("Individual", list, fitness=creator.FitnessMax)

# --- SABİTLER VE VARSAYILAN AYARLAR ---
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_MAP = {day: i for i, day in enumerate(DAYS)}

DEFAULT_CONFIG = {
    # --- ZAMAN AYARLARI ---
    "SLOT_SIZE": 60,
    "DAY_START_HOUR": 8,
    "DAY_END_HOUR": 23,

    # --- GENETİK ALGORİTMA PARAMETRELERİ ---
    "POP_SIZE": 400,
    "NGEN": 200,
    "CXPB": 0.8,  # Çaprazlama olasılığı
    "MUTPB": 0.35,  # Mutasyon olasılığı
    "INDPB": 0.05,  # Bireysel gen mutasyon olasılığı
    "TOURNSIZE": 6,

    # --- HARD CONSTRAINTS (AĞIR CEZALAR) ---
    "PENALTY_OVERLAP": 5000,
    "PENALTY_SCHOOL_CONFLICT": 5000,
    "PENALTY_BARRIER": 20000,  # Hard constraint ihlali varsa düşülecek taban puan

    # --- SOFT CONSTRAINTS (KALİTE AYARLARI) ---
    # 1. Denge
    "BALANCE_MIN_WEEKDAY_RATIO": 0.35,
    "PENALTY_BALANCE_POOR": 3000,
    "REWARD_BALANCE_GOOD": 1000,

    # 2. Yayılım (Scattering)
    "PENALTY_SCATTERING": 600,  # Ders gereğinden fazla güne yayılmışsa

    # 3. Blok / Ardışıklık
    "PENALTY_ORPHAN_SLOT": 400,  # Tek kalan ders saati cezası
    "REWARD_BLOCK": 800,  # Blok ders ödülü
    "PENALTY_BLOCK_BREAK": 1000,  # Blok olması gerekirken kopuk ders cezası

    # 4. Boşluklar (Gaps)
    "PENALTY_GAP": 600,
    "REWARD_NO_GAP": 300,

    # 5. Günlük Limitler
    "LIMIT_WEEKEND": 7,
    "LIMIT_WEEKDAY": 4,
    "PENALTY_LIMIT_EXCESS_MULTIPLIER": 800,  # (Aşım karesi * bu değer)

    # 6. Biyoritim / Yorgunluk
    "PENALTY_LATE_GENERAL": 1000,  # Hafta içi 22:00+
    "PENALTY_LATE_WEEKEND": 1000,  # Hafta sonu 23:00+

    # Zorluk Bazlı Cezalar
    "PENALTY_LATE_DIFFICULT": 2500,  # Zor ders, Hafta içi 20:00+
    "PENALTY_TIRED_DIFFICULT": 500,  # Zor ders, Hafta içi 18:00+
    "PENALTY_LATE_MEDIUM": 1000  # Orta zorluk, Hafta içi 21:00+
}


class AdvancedScheduler:
    def __init__(self, input_data, config=None):
        self.data = input_data
        self.student_info = input_data.get('student_info', {})
        self.subjects = input_data.get('subjects', [])

        # Konfigürasyonu yükle (Varsayılanların üzerine yaz)
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

        self.school_hours = self._parse_school_schedule()

        # Hangi genin hangi derse ait olduğunu tutan harita
        self.subject_indices = {}
        self.genes = []

        self._prepare_genes()

        self.toolbox = base.Toolbox()
        self._setup_toolbox()

    def _parse_school_schedule(self):
        schedule = {}
        raw_sched = self.student_info.get('school_schedule', {})
        days = raw_sched.get('days', [])
        start = raw_sched.get('start', 8)
        end = raw_sched.get('end', 15)

        for day in DAYS:
            schedule[day] = set()
            if day in days:
                for h in range(start, end):
                    schedule[day].add(h)
        return schedule

    def _prepare_genes(self):
        current_idx = 0
        slot_size = self.config["SLOT_SIZE"]

        for subj in self.subjects:
            total_slots = max(1, round(subj['total_minutes'] / slot_size))
            subj_name = subj['name']

            if subj_name not in self.subject_indices:
                self.subject_indices[subj_name] = []

            while total_slots > 0:
                if total_slots >= 2:
                    duration = 2
                    total_slots -= 2
                else:
                    duration = 1
                    total_slots -= 1

                self.genes.append({
                    "name": subj_name,
                    "difficulty": subj['difficulty'],
                    "color": subj.get('color', '#3788d8'),
                    "duration": duration
                })

                self.subject_indices[subj_name].append(current_idx)
                current_idx += 1

    def _setup_toolbox(self):
        self.toolbox.register("attr_gene", self._random_time_slot, duration=1)
        self.toolbox.register("individual", self._create_feasible_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        self.toolbox.register("evaluate", self._evaluate_schedule)
        self.toolbox.register("mate", tools.cxTwoPoint)

        # Config'den mutasyon oranını al
        self.toolbox.register("mutate", self._smart_mutation, indpb=self.config["INDPB"])

        self.toolbox.register("select", tools.selTournament, tournsize=self.config["TOURNSIZE"])

        self.toolbox.decorate("mate", self._wrap_repair)
        self.toolbox.decorate("mutate", self._wrap_repair)

    def _wrap_repair(self, func):
        def wrapper(*args, **kwargs):
            offspring = func(*args, **kwargs)
            for child in offspring:
                repaired = self._repair_schedule(child)
                for i in range(len(child)):
                    child[i] = repaired[i]
            return offspring

        return wrapper

    def _create_feasible_individual(self):
        individual = [None] * len(self.genes)
        occupied_slots = set()

        indices = list(range(len(self.genes)))
        random.shuffle(indices)

        day_start = self.config["DAY_START_HOUR"]
        day_end = self.config["DAY_END_HOUR"]

        for idx in indices:
            gene = self.genes[idx]
            duration = gene['duration']

            valid_starts = []

            for day in DAYS:
                for h in range(day_start, day_end - duration + 1):
                    is_valid = True
                    for offset in range(duration):
                        check_h = h + offset
                        if (day, check_h) in occupied_slots:
                            is_valid = False
                            break
                        if check_h in self.school_hours.get(day, set()):
                            is_valid = False
                            break

                    if is_valid:
                        valid_starts.append((day, h))

            if valid_starts:
                chosen = random.choice(valid_starts)
                individual[idx] = chosen
                for offset in range(duration):
                    occupied_slots.add((chosen[0], chosen[1] + offset))
            else:
                individual[idx] = self._random_time_slot(duration)

        return creator.Individual(individual)

    def _random_time_slot(self, duration=1, preferred_days=None):
        if preferred_days and random.random() < 0.7:
            candidates = list(preferred_days)
            random.shuffle(candidates)
            target_day = candidates[0]
        else:
            target_day = random.choice(DAYS)

        day_start = self.config["DAY_START_HOUR"]
        day_end = self.config["DAY_END_HOUR"]

        valid_starts = []
        for h in range(day_start, day_end - duration + 1):
            is_valid = True
            for offset in range(duration):
                if (h + offset) in self.school_hours.get(target_day, set()):
                    is_valid = False
                    break

            if is_valid:
                valid_starts.append(h)

        if valid_starts:
            hour = random.choice(valid_starts)
        else:
            hour = random.randint(day_start, day_end - duration)

        return (target_day, hour)

    def _smart_mutation(self, individual, indpb):
        for i in range(len(individual)):
            if random.random() < indpb:
                subj_name = self.genes[i]['name']
                duration = self.genes[i]['duration']

                preferred_days = set()
                if subj_name in self.subject_indices:
                    for other_idx in self.subject_indices[subj_name]:
                        if other_idx != i:
                            day = individual[other_idx][0]
                            preferred_days.add(day)

                individual[i] = self._random_time_slot(duration, preferred_days)
        return individual,

    def _evaluate_schedule(self, individual):
        score = 0
        schedule_map = {day: set() for day in DAYS}
        full_schedule_map = {day: {} for day in DAYS}
        daily_subject_hours = {day: {} for day in DAYS}

        overlap_penalty = 0
        school_penalty = 0

        # Config kısayolları
        cfg = self.config

        # --- DECODING & HARD CONSTRAINTS ---
        for i, (day, start_hour) in enumerate(individual):
            subj_data = self.genes[i]
            duration = subj_data['duration']
            subj_name = subj_data['name']

            for offset in range(duration):
                current_hour = start_hour + offset

                if current_hour in schedule_map[day]:
                    overlap_penalty += cfg["PENALTY_OVERLAP"]
                else:
                    schedule_map[day].add(current_hour)
                    full_schedule_map[day][current_hour] = subj_data

                    if subj_name not in daily_subject_hours[day]:
                        daily_subject_hours[day][subj_name] = []
                    daily_subject_hours[day][subj_name].append(current_hour)

                if current_hour in self.school_hours.get(day, set()):
                    school_penalty += cfg["PENALTY_SCHOOL_CONFLICT"]

        # --- SOFT CONSTRAINTS ---
        total_slots = sum([g['duration'] for g in self.genes])
        weekday_slots = sum([len(schedule_map[d]) for d in DAYS[:5]])

        # A) Hafta İçi / Hafta Sonu Dengesi
        if total_slots > 8:
            ratio = weekday_slots / total_slots
            if ratio < cfg["BALANCE_MIN_WEEKDAY_RATIO"]:
                score -= cfg["PENALTY_BALANCE_POOR"]
            else:
                score += cfg["REWARD_BALANCE_GOOD"]

        # B) Konu Yayılımı Cezası (Dynamic)
        subject_days_count = {}
        subject_total_duration = {}

        for d in DAYS:
            for h, subj_data in full_schedule_map[d].items():
                s_name = subj_data['name']
                if s_name not in subject_days_count:
                    subject_days_count[s_name] = set()
                    subject_total_duration[s_name] = 0

                subject_days_count[s_name].add(d)
                subject_total_duration[s_name] += 1

        for s_name, days_set in subject_days_count.items():
            day_count = len(days_set)
            total_h = subject_total_duration[s_name]
            ideal_days = max(1, round(total_h / 2.5))

            if day_count > ideal_days + 1:
                excess = day_count - (ideal_days + 1)
                score -= (excess * cfg["PENALTY_SCATTERING"])

        # C) Gün Bazlı Kontroller
        for day in DAYS:
            hours = sorted(list(schedule_map[day]))
            if not hours: continue

            daily_lessons_count = len(hours)

            # 1. Ardışıklık ve Blok Bütünlüğü
            for subj_name, subj_hours in daily_subject_hours[day].items():
                subj_hours.sort()
                count = len(subj_hours)

                if count == 1 and total_slots > 10:
                    score -= cfg["PENALTY_ORPHAN_SLOT"]

                if count > 1:
                    for k in range(count - 1):
                        diff = subj_hours[k + 1] - subj_hours[k]
                        if diff == 1:
                            score += cfg["REWARD_BLOCK"]
                        else:
                            score -= cfg["PENALTY_BLOCK_BREAK"]

            # 2. Gün İçi Boşluk (Gap) Cezası
            day_span = hours[-1] - hours[0] + 1
            gaps = day_span - daily_lessons_count

            if gaps > 0:
                score -= (gaps * cfg["PENALTY_GAP"])
            else:
                score += cfg["REWARD_NO_GAP"]

            # 3. Günlük Limit Aşımı
            limit = cfg["LIMIT_WEEKEND"] if day in ["Saturday", "Sunday"] else cfg["LIMIT_WEEKDAY"]
            if daily_lessons_count > limit:
                excess = daily_lessons_count - limit
                score -= (excess ** 2) * cfg["PENALTY_LIMIT_EXCESS_MULTIPLIER"]

            # 4. Bilişsel Yorgunluk
            for h in hours:
                subj = full_schedule_map[day][h]
                difficulty = subj['difficulty']
                is_weekend = day in ["Saturday", "Sunday"]

                if not is_weekend:
                    if h >= 22: score -= cfg["PENALTY_LATE_GENERAL"]
                    if difficulty >= 4:
                        if h >= 20:
                            score -= cfg["PENALTY_LATE_DIFFICULT"]
                        elif h >= 18:
                            score -= cfg["PENALTY_TIRED_DIFFICULT"]
                    elif difficulty == 3 and h >= 21:
                        score -= cfg["PENALTY_LATE_MEDIUM"]
                else:
                    if h >= 23: score -= cfg["PENALTY_LATE_WEEKEND"]

        # --- PUANLAMA BİRLEŞTİRME ---
        if overlap_penalty > 0 or school_penalty > 0:
            score -= cfg["PENALTY_BARRIER"]
            score -= overlap_penalty
            score -= school_penalty

        return (score,)

    def run(self):
        cfg = self.config

        pop = self.toolbox.population(n=cfg["POP_SIZE"])
        hof = tools.HallOfFame(1)

        stats = tools.Statistics(lambda ind: ind.fitness.values[0])
        stats.register("avg", statistics.mean)
        stats.register("max", max)

        algorithms.eaSimple(pop, self.toolbox,
                            cxpb=cfg["CXPB"],
                            mutpb=cfg["MUTPB"],
                            ngen=cfg["NGEN"],
                            halloffame=hof, stats=stats, verbose=False)

        if not hof:
            return []

        return self._format_output(hof[0])

    def _repair_schedule(self, individual):
        repaired_individual = list(individual)
        calendar = set()
        unplaced_indices = []

        day_start = self.config["DAY_START_HOUR"]
        day_end = self.config["DAY_END_HOUR"]

        # 1. Adım
        for i, (day, start_h) in enumerate(repaired_individual):
            duration = self.genes[i]['duration']
            is_valid = True
            for offset in range(duration):
                current_h = start_h + offset
                if (day, current_h) in calendar:
                    is_valid = False
                    break
                if current_h in self.school_hours.get(day, set()):
                    is_valid = False
                    break

            if is_valid:
                for offset in range(duration):
                    calendar.add((day, start_h + offset))
            else:
                unplaced_indices.append(i)

        # 2. Adım
        for i in unplaced_indices:
            subj_name = self.genes[i]['name']
            duration = self.genes[i]['duration']

            existing_days = set()
            if subj_name in self.subject_indices:
                for idx in self.subject_indices[subj_name]:
                    if idx != i:
                        existing_days.add(repaired_individual[idx][0])

            all_possible_slots = []
            for d in DAYS:
                for h in range(day_start, day_end - duration + 1):
                    is_valid = True
                    for offset in range(duration):
                        if (h + offset) in self.school_hours.get(d, set()):
                            is_valid = False
                            break

                    if is_valid:
                        all_possible_slots.append((d, h))

            random.shuffle(all_possible_slots)
            all_possible_slots.sort(key=lambda x: 0 if x[0] in existing_days else 1)

            placed = False
            for (d, h) in all_possible_slots:
                fits = True
                for offset in range(duration):
                    if (d, h + offset) in calendar:
                        fits = False
                        break

                if fits:
                    repaired_individual[i] = (d, h)
                    for offset in range(duration):
                        calendar.add((d, h + offset))
                    placed = True
                    break

            if not placed:
                pass

        return repaired_individual

    def _format_output(self, individual):
        individual = self._repair_schedule(individual)
        final_schedule = []

        for i, (day, start_hour) in enumerate(individual):
            subj = self.genes[i]
            duration = subj['duration']

            for offset in range(duration):
                current_hour = start_hour + offset

                final_schedule.append({
                    "title": subj['name'],
                    "day": day,
                    "start": f"{current_hour:02d}:00",
                    "end": f"{current_hour + 1:02d}:00",
                    "color": subj['color'],
                    "difficulty": subj['difficulty']
                })

        final_schedule.sort(key=lambda x: (DAY_MAP[x['day']], x['start']))
        return final_schedule