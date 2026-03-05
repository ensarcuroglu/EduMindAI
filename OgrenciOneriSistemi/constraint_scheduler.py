#constraint_scheduler.py:
import math
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum
import statistics
import random
import sys

# PuLP Kontrolü
try:
    import pulp

    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False


# --- 1. KONFİGÜRASYON VE VERİ YAPILARI ---

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 5


class UserProfile(Enum):
    STANDARD = 1  # 09:00 - 17:00
    EARLY_BIRD = 2  # 06:00 - 14:00
    NIGHT_OWL = 3  # 16:00 - 02:00
    POWER_GRINDER = 4  # Dayanıklı


@dataclass
class TimeSlotConfig:
    slot_duration_minutes: int = 15
    slots_per_hour: int = 4
    slots_per_day: int = 96
    horizon_days: int = 7

    @property
    def total_slots(self):
        return self.slots_per_day * self.horizon_days


@dataclass
class StudyTask:
    id: str
    name: str
    duration_minutes: int
    difficulty: int  # 1-10
    category: str
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline_day: Optional[int] = None
    fixed_start_slot: Optional[int] = None
    prerequisites: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    chunk_index: int = 0

    # Durumlar
    is_previously_failed: bool = False
    postpone_count: int = 0
    is_fear_task: bool = False

    # Pedagojik Özellikler
    is_new_topic: bool = False
    repetition_count: int = 0
    is_reward_task: bool = False


@dataclass
class UserHistory:
    last_week_completion_rate: float = 1.0
    failed_task_ids: List[str] = field(default_factory=list)
    actual_work_hours: List[int] = field(default_factory=list)
    manual_override_hotspots: Dict[int, List[int]] = field(default_factory=dict)
    consecutive_lazy_days: int = 0

    # Geri Besleme Verileri
    early_finish_accumulated_minutes: int = 0
    cancelled_slots: List[int] = field(default_factory=list)
    manual_override_days: Set[int] = field(default_factory=set)
    previous_week_schedule: Dict[str, int] = field(default_factory=dict)


@dataclass
class SchedulerConfig:
    # --- İnsan Biyolojisi ---
    max_daily_minutes: int = 360
    max_weekly_minutes: int = 1800
    burnout_threshold_minutes: int = 240
    min_daily_minutes: int = 90
    pomodoro_chunk_minutes: int = 45

    # --- Gelecek Nesil Özellikler ---
    lazy_mode: bool = False
    user_mood_score: int = 5
    enable_gamification: bool = True

    # --- Kısıtlar ---
    is_exam_week: bool = False
    min_empty_days: int = 1
    project_spread_threshold: int = 180
    max_hard_blocks_per_day: int = 3
    consecutive_work_limit: int = 6
    soft_consecutive_limit: bool = True
    max_consecutive_subject_days: int = 2
    max_blocks_per_cat_day: int = 2
    spaced_repetition_min_hours: int = 24
    spaced_repetition_max_hours: int = 72

    # --- Zaman Algısı ---
    late_night_start_hour: float = 21.5
    late_night_penalty_factor: float = 1.3
    max_short_tasks_per_day: int = 2
    fragmentation_threshold: int = 3

    # OPTİMİZASYON 1: Grid çözünürlüğünü 4 yaptık (Hız için kritik)
    time_grid_resolution: int = 4

    # --- AI Karakter & Motivasyon (YENİ) ---
    enable_coach_mode: bool = True
    penalty_drop_critical: int = 1000000
    penalty_drop_high: int = 50000
    penalty_drop_medium: int = 8000
    penalty_drop_low: int = 4000

    # --- Solver Cezaları ---
    weight_bio_friction: int = 60
    weight_day_usage: int = 1500
    weight_deadline: int = 2500
    weight_difficulty_match: int = 250
    weight_category_spread: int = 400
    weight_after_school_fatigue: int = 600
    weight_sunday_fatigue: int = 1000
    weight_abstract_evening: int = 500
    weight_monday_motivation: float = 0.7
    weight_morning_momentum: int = -50
    weight_robotic_packing: int = 200
    weight_fragmentation: int = 2000
    weight_pedagogy_match: int = -100
    weight_avoidance_zone: int = 2000
    weight_similarity_penalty: int = 50

    weight_cumulative_fatigue_base: int = 20
    diversity_noise_factor: float = 0.05


# --- 2. TAKVİM VE BİYORİTİM SERVİSİ ---

class CalendarService:
    def __init__(self, time_cfg: TimeSlotConfig):
        self.cfg = time_cfg
        self.availability = [1] * self.cfg.total_slots

    def block_interval(self, day_idx: int, start_hour: float, end_hour: float):
        start_slot = int(day_idx * self.cfg.slots_per_day + start_hour * self.cfg.slots_per_hour)
        end_slot = int(day_idx * self.cfg.slots_per_day + end_hour * self.cfg.slots_per_hour)
        start_slot = max(0, start_slot)
        end_slot = min(self.cfg.total_slots, end_slot)
        for i in range(start_slot, end_slot):
            self.availability[i] = 0

    def block_social_activity(self, day_idx: int, start_hour: float, end_hour: float):
        print(f"🧘 Koç Notu: {day_idx}. gün {start_hour}-{end_hour} arasına dokunmuyorum, sosyalleşmek de ihtiyaçtır.")
        self.block_interval(day_idx, start_hour, end_hour)

    def block_untouchable_days(self, days: Set[int]):
        pass  # Logic handled in solver

    def apply_dynamic_sleep(self, user_profile: UserProfile):
        for d in range(self.cfg.horizon_days):
            if user_profile == UserProfile.EARLY_BIRD:
                self.block_interval(d, 22, 24)
                self.block_interval(d, 0, 5)
            elif user_profile == UserProfile.NIGHT_OWL:
                self.block_interval(d, 2, 10)
            elif user_profile == UserProfile.POWER_GRINDER:
                self.block_interval(d, 1, 6)
            else:
                self.block_interval(d, 23.5, 24)
                self.block_interval(d, 0, 7.5)

    def apply_student_constraints(self):
        for d in range(5):
            self.block_interval(d, 0, 17)  # Okul
            self.block_interval(d, 23, 24)  # Gece

    def get_bio_cost(self, slot_idx: int, user_profile: UserProfile) -> float:
        hour = (slot_idx % self.cfg.slots_per_day) / self.cfg.slots_per_hour
        if 18.5 <= hour < 19.5: return 3.0

        cost = 1.0
        if user_profile == UserProfile.EARLY_BIRD:
            if 5 <= hour < 10:
                cost = 0.1
            elif 10 <= hour < 14:
                cost = 0.4
            elif 14 <= hour < 18:
                cost = 3.0
            else:
                cost = 15.0
        elif user_profile == UserProfile.NIGHT_OWL:
            if 20 <= hour < 26:
                cost = 0.1
            elif 16 <= hour < 20:
                cost = 0.5
            elif 10 <= hour < 16:
                cost = 3.0
            else:
                cost = 15.0
        elif user_profile == UserProfile.POWER_GRINDER:
            if 6 <= hour < 23:
                cost = 0.3
            else:
                cost = 5.0
        else:  # STANDARD
            if 9 <= hour < 12:
                cost = 0.2
            elif 13 <= hour < 17:
                cost = 0.6
            elif 17 <= hour < 22:
                cost = 2.0
            else:
                cost = 8.0
        return cost


# --- 3. CORE SOLVER: PuLP (MOTIVATION & COACH EDITION) ---

class FluxScheduler:
    def __init__(self, tasks: List[StudyTask],
                 calendar: CalendarService,
                 config: SchedulerConfig,
                 time_config: TimeSlotConfig,
                 user_profile: UserProfile = UserProfile.STANDARD,
                 user_history: Optional[UserHistory] = None):
        self.original_tasks = tasks
        self.calendar = calendar
        self.config = config
        self.time_cfg = time_config
        self.user_profile = user_profile
        self.history = user_history or UserHistory()
        self.scheduled_tasks = []
        self.dropped_tasks = []
        self.coach_notes = []
        self.ai_rationale = []

        random.seed()

        self._check_lazy_abuse()
        self._learn_from_history()
        self._analyze_mood_and_energy()
        self._analyze_and_adapt()

    def _check_lazy_abuse(self):
        if self.config.lazy_mode:
            if self.history.consecutive_lazy_days >= 2:
                print("🛑 KOÇ MÜDAHALESİ: Üst üste 3. gün 'Lazy Mode'a izin veremem.")
                self.config.lazy_mode = False
                self.config.max_daily_minutes = int(self.config.max_daily_minutes * 0.4)
                self.coach_notes.append("İki gün dinlendin, bugün 'Mikro Başarı Günü'.")
            else:
                self.history.consecutive_lazy_days += 1
        else:
            self.history.consecutive_lazy_days = 0

    def _learn_from_history(self):
        if self.history.early_finish_accumulated_minutes > 60:
            reduction = min(60, self.history.early_finish_accumulated_minutes // 2)
            self.config.max_daily_minutes -= reduction
            self.coach_notes.append(f"Geçen hafta harikaydın! Ödül olarak günlük yükünü {reduction} dk hafiflettim. 🏆")

        if self.history.cancelled_slots:
            self.coach_notes.append("Daha önce iptal ettiğin saatleri 'Riskli Bölge' olarak işaretledim.")

    def _analyze_mood_and_energy(self):
        mood = self.config.user_mood_score

        if self.config.lazy_mode:
            print("🛌 LAZY MODE: Bugün (0. Gün) Mental Sağlık Günü ilan edildi.")
            self.config.max_daily_minutes = int(self.config.max_daily_minutes * 0.8)
            self.coach_notes.append("Bugün modunda değilsin, seni zorlamadım.")
            return

        if mood < 4:
            self.config.weight_bio_friction += 150
            self.config.max_hard_blocks_per_day = 1
            self.config.burnout_threshold_minutes -= 60
            self.coach_notes.append("Enerjin düşük, programı hafiflettim.")

        elif mood > 7:
            self.config.weight_bio_friction -= 20
            self.config.max_hard_blocks_per_day += 1
            self.config.max_daily_minutes += 60
            self.coach_notes.append("Enerjin harika! Zor dersleri bugüne çektim.")

    def _analyze_and_adapt(self):
        if self.history.last_week_completion_rate < 0.50 and not self.config.lazy_mode:
            self.config.resistance_mode_active = True
            self.config.max_daily_minutes = int(self.config.max_daily_minutes * 0.7)
            self.config.min_empty_days = max(self.config.min_empty_days, 2)
            self.coach_notes.append("Geçen haftaki direncini kırmak için 'Yumuşak Başlangıç' uyguladım.")

        if self.history.actual_work_hours:
            adjusted_hours = [h if h >= 5 else h + 24 for h in self.history.actual_work_hours]
            avg_hour = statistics.mean(adjusted_hours)
            suggested_profile = None
            if avg_hour > 21.0 and self.user_profile != UserProfile.NIGHT_OWL:
                suggested_profile = UserProfile.NIGHT_OWL
            elif avg_hour < 10.0 and self.user_profile != UserProfile.EARLY_BIRD:
                suggested_profile = UserProfile.EARLY_BIRD

            if suggested_profile:
                self.user_profile = suggested_profile
                self.coach_notes.append(
                    f"Uyku düzenine uyum sağlamak için geçici olarak {suggested_profile.name} moduna geçtim.")

        for task in self.original_tasks:
            if self.history.failed_task_ids and task.id in self.history.failed_task_ids:
                task.is_previously_failed = True
            if task.postpone_count >= 2:
                task.is_fear_task = True
                self.coach_notes.append(f"'{task.name}' dersini 'Korku Dersi' ilan ettim.")

    def _prepare_tasks(self) -> List[StudyTask]:
        chunked_tasks = []
        for task in self.original_tasks:
            if task.fixed_start_slot is not None:
                chunked_tasks.append(task)
                continue

            effective_duration = task.duration_minutes
            if task.repetition_count >= 3:
                effective_duration = int(effective_duration * 0.7)

            remaining = effective_duration
            part = 1
            current_chunk_size = self.config.pomodoro_chunk_minutes

            effective_difficulty = task.difficulty
            task_prefix = ""

            if task.is_previously_failed:
                current_chunk_size = 25
                effective_difficulty = max(1, int(task.difficulty * 0.5))
                task_prefix = "👀 (Pasif) "
            elif task.is_fear_task:
                current_chunk_size = 20
                effective_difficulty = max(1, task.difficulty - 1)

            needs_reward = False
            if task.difficulty >= 8 and not task.is_fear_task:
                needs_reward = True

            while remaining > 0:
                duration = min(remaining, current_chunk_size)
                chunk_diff = effective_difficulty
                if part > 1 and task.duration_minutes > 120 and not task.is_previously_failed:
                    chunk_diff = max(3, int(effective_difficulty * 0.7))

                new_task = StudyTask(
                    id=f"{task.id}_p{part}",
                    name=f"{task_prefix}{task.name} ({part})",
                    duration_minutes=duration,
                    difficulty=chunk_diff,
                    category=task.category,
                    priority=task.priority,
                    deadline_day=task.deadline_day,
                    fixed_start_slot=task.fixed_start_slot,
                    prerequisites=task.prerequisites,
                    parent_id=task.id,
                    chunk_index=part,
                    is_previously_failed=task.is_previously_failed,
                    is_fear_task=task.is_fear_task,
                    is_new_topic=task.is_new_topic
                )
                chunked_tasks.append(new_task)

                if needs_reward:
                    reward_task = StudyTask(
                        id=f"{task.id}_reward_{part}",
                        name="🎉 Zihinsel Ödül",
                        duration_minutes=15,
                        difficulty=1,
                        category="REWARD",
                        priority=TaskPriority.HIGH,
                        parent_id=task.id,
                        is_reward_task=True
                    )
                    chunked_tasks.append(reward_task)
                    needs_reward = False

                remaining -= duration
                part += 1
        return chunked_tasks

    def _get_noise(self):
        return random.uniform(1.0 - self.config.diversity_noise_factor, 1.0 + self.config.diversity_noise_factor)

    def _generate_rationale_report(self, solved_model, x, processing_tasks, valid_starts):
        days_usage = [0] * 7
        total_minutes_per_day = [0] * 7

        for t_idx, s in valid_starts:
            if pulp.value(x[(t_idx, s)]) == 1:
                d = s // self.time_cfg.slots_per_day
                days_usage[d] += 1
                total_minutes_per_day[d] += processing_tasks[t_idx].duration_minutes

        if any(days_usage):
            max_day = days_usage.index(max(days_usage))
            days_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            self.ai_rationale.append(
                f"📌 {days_names[max_day]} en yoğun günün çünkü biyolojik saatin o gün zirve yapıyor.")

        active_days_indices = [i for i, m in enumerate(total_minutes_per_day) if m > 0]
        if active_days_indices:
            easy_win_day_idx = min(active_days_indices, key=lambda i: total_minutes_per_day[i])
            self.config.easy_win_day_idx = easy_win_day_idx
            self.ai_rationale.append(
                f"🎯 {days_names[easy_win_day_idx]} günü 'Kolay Kazanım Günü'. Yükü hafif tuttum, keyfini çıkar.")

        empty_days = [days_names[i] for i, u in enumerate(days_usage) if u == 0]
        if empty_days:
            self.ai_rationale.append(f"🧘 {', '.join(empty_days)} günleri 'Mental Reset' için tamamen boş.")

    def solve(self):
        if not PULP_AVAILABLE:
            print("⚠️ UYARI: PuLP eksik.")
            return []

        print(f"🧠 AI Koç Hesaplıyor... (Profil: {self.user_profile.name})")

        processing_tasks = self._prepare_tasks()
        num_tasks = len(processing_tasks)
        total_slots = self.time_cfg.total_slots
        num_days = self.time_cfg.horizon_days
        slots_per_day = self.time_cfg.slots_per_day

        task_durations = [math.ceil(t.duration_minutes / self.time_cfg.slot_duration_minutes) for t in processing_tasks]
        hard_task_indices = [i for i, t in enumerate(processing_tasks) if t.difficulty >= 8]
        short_task_indices = [i for i, t in enumerate(processing_tasks) if t.duration_minutes < 30]

        parent_ids = list(set(t.parent_id for t in processing_tasks if t.parent_id))
        categories = list(set(t.category for t in processing_tasks))
        abstract_subjects = ['MATH', 'PHYSICS', 'CHEM', 'SCI', 'CS', 'PHILOSOPHY']
        concrete_subjects = ['HIST', 'LIT', 'LANG', 'ART', 'READING', 'GEO']

        prob = pulp.LpProblem("Motivation_Scheduler", pulp.LpMinimize)

        # OPTİMİZASYON 2: Biyo-Maliyetleri Önceden Hesapla (Caching)
        bio_costs_cache = [self.calendar.get_bio_cost(s, self.user_profile) for s in range(total_slots)]

        # --- TOTAL COST DEĞİŞKENİNİ BURADA BAŞLAT ---
        total_cost = 0

        # --- KARAR DEĞİŞKENLERİ ---
        x = {}
        valid_starts = []
        for t_idx in range(num_tasks):
            task_dur = task_durations[t_idx]
            deadline_slot = (processing_tasks[t_idx].deadline_day + 1) * slots_per_day if processing_tasks[
                                                                                              t_idx].deadline_day is not None else total_slots

            is_fear_restricted = processing_tasks[t_idx].is_fear_task
            step = self.config.time_grid_resolution
            search_range = range(0, total_slots, step) if processing_tasks[t_idx].fixed_start_slot is None else [
                processing_tasks[t_idx].fixed_start_slot]

            for s in search_range:
                day_idx = s // slots_per_day
                if day_idx in self.history.manual_override_days:
                    continue

                if s + task_dur <= deadline_slot and s + task_dur <= total_slots:
                    is_feasible = True
                    # Basitleştirilmiş feasible kontrolü
                    for k in range(s, s + task_dur):
                        if self.calendar.availability[k] == 0:
                            is_feasible = False
                            break
                    if is_feasible:
                        current_day = s // slots_per_day
                        hour_start = (s % slots_per_day) / 4.0

                        if self.config.lazy_mode and current_day == 0:
                            if processing_tasks[t_idx].difficulty > 3 or task_dur > 2:
                                continue

                        if current_day < 5 and 17.0 <= hour_start < 18.0 and processing_tasks[t_idx].difficulty > 5:
                            continue

                        if is_fear_restricted and hour_start >= 12.0:
                            continue

                        x[(t_idx, s)] = pulp.LpVariable(f"x_{t_idx}_{s}", 0, 1, pulp.LpBinary)
                        valid_starts.append((t_idx, s))

        is_dropped = pulp.LpVariable.dicts("DropTask", range(num_tasks), 0, 1, pulp.LpBinary)
        y = pulp.LpVariable.dicts("DayActive", range(num_days), 0, 1, pulp.LpBinary)
        parent_day_vars = pulp.LpVariable.dicts("ParentDay", [(pid, d) for pid in parent_ids for d in range(num_days)],
                                                0, 1, pulp.LpBinary)
        cat_day_vars = pulp.LpVariable.dicts("CatDay", [(c, d) for c in categories for d in range(num_days)], 0, 1,
                                             pulp.LpBinary)
        overload_vars = pulp.LpVariable.dicts("DayOverload", range(num_days), 0, self.config.max_daily_minutes,
                                              pulp.LpContinuous)
        is_high_load = pulp.LpVariable.dicts("IsHighLoad", range(num_days), 0, 1, pulp.LpBinary)
        consecutive_violation_vars = {}
        fragmentation_vars = pulp.LpVariable.dicts("Fragmentation", range(num_days), 0, 10, pulp.LpContinuous)

        slot_is_active_expr = [[] for _ in range(total_slots)]
        slot_is_blocked_expr = [[] for _ in range(total_slots)]

        for t_idx, s in valid_starts:
            task_dur = task_durations[t_idx]
            for k in range(s, s + task_dur):
                if k < total_slots:
                    slot_is_active_expr[k].append(x[(t_idx, s)])
            for k in range(s, min(total_slots, s + task_dur + 1)):
                if k < total_slots:
                    slot_is_blocked_expr[k].append(x[(t_idx, s)])

        # --- KISITLAMALAR ---
        for t_idx in range(num_tasks):
            prob += pulp.lpSum([x[(t_idx, s)] for s in range(total_slots) if (t_idx, s) in x]) == 1 - is_dropped[t_idx]

        for s in range(total_slots):
            if slot_is_blocked_expr[s]:
                prob += pulp.lpSum(slot_is_blocked_expr[s]) <= 1

        M = 1000
        high_load_threshold = self.config.max_daily_minutes * 0.75
        weekly_load_expr = []

        for d in range(num_days):
            day_start = d * slots_per_day
            day_end = (d + 1) * slots_per_day
            total_duration_expr = pulp.lpSum(
                [x[(t_idx, s)] * task_durations[t_idx] * self.time_cfg.slot_duration_minutes
                 for t_idx, s in valid_starts if day_start <= s < day_end])
            weekly_load_expr.append(total_duration_expr)
            starts_in_day_expr = pulp.lpSum([x[(t_idx, s)] for t_idx, s in valid_starts if day_start <= s < day_end])

            prob += starts_in_day_expr <= M * y[d]
            if not (self.config.lazy_mode and d == 0):
                prob += total_duration_expr >= self.config.min_daily_minutes * y[d]
            prob += overload_vars[d] >= total_duration_expr - self.config.burnout_threshold_minutes
            prob += total_duration_expr - high_load_threshold <= M * is_high_load[d]
            prob += fragmentation_vars[d] >= starts_in_day_expr - self.config.fragmentation_threshold

            short_starts = pulp.lpSum([x[(t_idx, s)] for t_idx, s in valid_starts
                                       if t_idx in short_task_indices and day_start <= s < day_end])
            prob += short_starts <= self.config.max_short_tasks_per_day

        prob += pulp.lpSum(weekly_load_expr) <= self.config.max_weekly_minutes

        for d in range(num_days - 2):
            prob += is_high_load[d] + is_high_load[d + 1] + is_high_load[d + 2] <= 2

        if self.config.min_empty_days > 0 and not self.config.lazy_mode:
            prob += pulp.lpSum([y[d] for d in range(num_days)]) <= num_days - self.config.min_empty_days

        window = self.config.consecutive_work_limit + 1
        for s in range(total_slots - window + 1):
            if self.calendar.availability[s] == 1:
                window_sum = []
                for k in range(s, s + window):
                    window_sum.extend(slot_is_active_expr[k])
                if window_sum:
                    expr = pulp.lpSum(window_sum)
                    limit = self.config.consecutive_work_limit
                    if self.config.soft_consecutive_limit:
                        slack_var = pulp.LpVariable(f"ConsecSlack_{s}", 0, 10, pulp.LpContinuous)
                        consecutive_violation_vars[s] = slack_var
                        prob += slack_var >= expr - limit
                    else:
                        prob += expr <= limit

        for d in range(num_days):
            day_start = d * slots_per_day
            day_end = (d + 1) * slots_per_day
            hard_in_day = []
            for t_idx in hard_task_indices:
                for s in range(day_start, day_end):
                    if (t_idx, s) in x: hard_in_day.append(x[(t_idx, s)])
            if hard_in_day: prob += pulp.lpSum(hard_in_day) <= self.config.max_hard_blocks_per_day

        for t1 in hard_task_indices:
            dur1 = task_durations[t1]
            for s1 in range(total_slots):
                if (t1, s1) in x:
                    end_slot = s1 + dur1 + 1
                    if end_slot < total_slots:
                        next_hards = []
                        for t2 in hard_task_indices:
                            if t1 != t2 and (t2, end_slot) in x: next_hards.append(x[(t2, end_slot)])
                        if next_hards: prob += x[(t1, s1)] + pulp.lpSum(next_hards) <= 1

        for pid in parent_ids:
            for t_idx in range(num_tasks):
                task = processing_tasks[t_idx]
                if task.parent_id == pid:
                    for s in range(total_slots):
                        if (t_idx, s) in x:
                            d = s // slots_per_day
                            prob += x[(t_idx, s)] <= parent_day_vars[(pid, d)]
            for d in range(num_days - 2):
                prob += parent_day_vars[(pid, d)] + parent_day_vars[(pid, d + 1)] + parent_day_vars[
                    (pid, d + 2)] <= self.config.max_consecutive_subject_days

        for c in categories:
            for d in range(num_days):
                total_cost += cat_day_vars[(c, d)] * self.config.weight_category_spread

        for t_idx, task in enumerate(processing_tasks):
            if "tekrar" in task.name.lower() or "revision" in task.name.lower():
                if task.prerequisites:
                    prereq_id = task.prerequisites[0]
                    prereq_indices = [i for i, t in enumerate(processing_tasks) if
                                      t.parent_id == prereq_id or t.id == prereq_id]
                    if prereq_indices:
                        start_time_revision = pulp.lpSum(
                            [s * x[(t_idx, s)] for s in range(total_slots) if (t_idx, s) in x])
                        last_prereq_idx = prereq_indices[-1]
                        start_time_prereq = pulp.lpSum(
                            [s * x[(last_prereq_idx, s)] for s in range(total_slots) if (last_prereq_idx, s) in x])
                        duration_prereq_slots = task_durations[last_prereq_idx]
                        min_gap_slots = (
                                                self.config.spaced_repetition_min_hours * 60) / self.time_cfg.slot_duration_minutes
                        max_gap_slots = (
                                                self.config.spaced_repetition_max_hours * 60) / self.time_cfg.slot_duration_minutes
                        M_time = total_slots
                        prob += start_time_revision >= start_time_prereq + duration_prereq_slots + min_gap_slots - M_time * \
                                is_dropped[t_idx]
                        prob += start_time_revision <= start_time_prereq + duration_prereq_slots + max_gap_slots + M_time * \
                                is_dropped[t_idx]

            if task.is_new_topic:
                current_id = task.parent_id if task.parent_id else task.id
                for t_other_idx, t_other in enumerate(processing_tasks):
                    if current_id in t_other.prerequisites:
                        start_time_new = pulp.lpSum([s * x[(t_idx, s)] for s in range(total_slots) if (t_idx, s) in x])
                        start_time_followup = pulp.lpSum(
                            [s * x[(t_other_idx, s)] for s in range(total_slots) if (t_other_idx, s) in x])
                        min_gap_slots = (24 * 60) / self.time_cfg.slot_duration_minutes
                        prob += start_time_followup >= start_time_new + min_gap_slots - M * is_dropped[t_idx]

        # --- YENİ KISIT: KRONOLOJİK PARÇA SIRALAMASI ---
        tasks_by_parent = {}
        for idx, t in enumerate(processing_tasks):
            if t.parent_id:
                if t.parent_id not in tasks_by_parent:
                    tasks_by_parent[t.parent_id] = []
                tasks_by_parent[t.parent_id].append(idx)

        for pid, indices in tasks_by_parent.items():
            indices.sort(key=lambda i: processing_tasks[i].chunk_index)

            for i in range(len(indices) - 1):
                curr_idx = indices[i]
                next_idx = indices[i + 1]

                curr_start = pulp.lpSum([s * x[(curr_idx, s)] for s in range(total_slots) if (curr_idx, s) in x])
                next_start = pulp.lpSum([s * x[(next_idx, s)] for s in range(total_slots) if (next_idx, s) in x])

                curr_dur_slots = task_durations[curr_idx]

                prob += next_start >= curr_start + curr_dur_slots - (M * is_dropped[curr_idx]) - (
                        M * is_dropped[next_idx])

        # --- AMAÇ FONKSİYONU ---

        # OPTİMİZASYON 3: Gürültüyü döngü dışında görev bazlı hesapla
        task_noise = {t_idx: self._get_noise() for t_idx in range(num_tasks)}

        for t_idx in range(num_tasks):
            task = processing_tasks[t_idx]
            penalty = self.config.penalty_drop_low
            if task.priority == TaskPriority.CRITICAL:
                penalty = self.config.penalty_drop_critical
            elif task.priority == TaskPriority.HIGH:
                penalty = self.config.penalty_drop_high
            elif task.priority == TaskPriority.MEDIUM:
                penalty = self.config.penalty_drop_medium
            total_cost += is_dropped[t_idx] * penalty

        for t_idx, s in valid_starts:
            task = processing_tasks[t_idx]
            dur = task_durations[t_idx]
            current_day = s // slots_per_day
            hour_in_day = (s % slots_per_day) / 4.0

            # OPTİMİZASYON 4: Cache'den oku
            avg_bio = sum(bio_costs_cache[k] for k in range(s, s + dur)) / dur

            fatigue_factor = 1.0
            if hour_in_day > 12:
                base_fatigue = (hour_in_day - 12) * (self.config.weight_cumulative_fatigue_base / 100.0)
                fatigue_factor = 1.0 + (base_fatigue ** 1.8)

            after_school_penalty = 0
            sunday_penalty = 0
            if current_day == 6 and task.difficulty > 4: sunday_penalty = self.config.weight_sunday_fatigue

            late_night_penalty = 0
            if hour_in_day >= self.config.late_night_start_hour:
                fatigue_factor *= self.config.late_night_penalty_factor

            urgency_discount = 1.0
            last_minute_penalty = 0
            if task.deadline_day is not None:
                days_left = task.deadline_day - current_day
                if days_left <= 1: urgency_discount = 0.1
                if days_left == 0: last_minute_penalty = self.config.weight_deadline * 2.0

            priority_multiplier = 1.0
            if task.priority == TaskPriority.CRITICAL and urgency_discount > 0.5:
                priority_multiplier = 10.0
            elif task.priority == TaskPriority.LOW:
                priority_multiplier = 0.2

            difficulty_multiplier = 1.0
            if task.difficulty >= 8 or task.category in abstract_subjects:
                difficulty_multiplier = 2.5
            elif task.difficulty <= 4:
                difficulty_multiplier = 0.6

            bio_penalty = avg_bio * (task.difficulty ** 1.2) * self.config.weight_bio_friction * \
                          difficulty_multiplier * priority_multiplier * urgency_discount * fatigue_factor

            # OPTİMİZASYON 5: Görev bazlı gürültü kullan
            noise = task_noise[t_idx]

            similarity_penalty = 0
            prev_slot = self.history.previous_week_schedule.get(task.category)
            if prev_slot is not None and abs(prev_slot - s) < 4:
                similarity_penalty = self.config.weight_similarity_penalty

            avoidance_penalty = 0
            if s in self.history.cancelled_slots:
                avoidance_penalty = self.config.weight_avoidance_zone

            pedagogy_bonus = 0
            if task.category in concrete_subjects and hour_in_day > 16.0:
                pedagogy_bonus = self.config.weight_pedagogy_match

            if task.is_reward_task:
                bio_penalty = 0
                last_minute_penalty = 0

            total_cost += x[(t_idx, s)] * (
                    bio_penalty + last_minute_penalty + after_school_penalty + sunday_penalty + pedagogy_bonus + similarity_penalty + avoidance_penalty) * noise

        for d in range(num_days):
            total_cost += y[d] * self.config.weight_day_usage * self._get_noise()
            total_cost += overload_vars[d] * 2500
            total_cost += fragmentation_vars[d] * self.config.weight_fragmentation

        for c in categories:
            for d in range(num_days):
                total_cost += cat_day_vars[(c, d)] * self.config.weight_category_spread

        if self.config.soft_consecutive_limit:
            for s in consecutive_violation_vars:
                total_cost += consecutive_violation_vars[s] * 5000

        prob += total_cost

        # OPTİMİZASYON 6: Solver Ayarları (KRİTİK DÜZELTME)
        # threads=4 KALDIRILDI: Windows üzerinde kilitlenmeye (Deadlock) sebep oluyor.
        # msg=1 EKLENDİ: Arka planda solver'ın çalışıp çalışmadığını görmek için.
        # gapRel=0.05 KORUNDU: En iyi sonuca %5 yaklaşınca durması için.
        # timeLimit=60 EKLENDİ: Sonsuz döngü sigortası olarak (Kaliteyi bozmaz, sadece donmayı önler).
        prob.solve(pulp.PULP_CBC_CMD(msg=1, gapRel=0.05, timeLimit=60))

        # SONUÇ
        if pulp.LpStatus[prob.status] == "Optimal":
            days_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

            self._generate_rationale_report(prob, x, processing_tasks, valid_starts)

            for t_idx, s in valid_starts:
                if pulp.value(x[(t_idx, s)]) == 1:
                    task = processing_tasks[t_idx]
                    start_min = (s % slots_per_day) * 15
                    end_min = start_min + task.duration_minutes
                    day_idx = s // slots_per_day

                    # Cache'den okuma (Performance)
                    bio_val = bio_costs_cache[s]

                    match_desc = "🔥 Flow" if bio_val <= 0.5 else ("✅ İyi" if bio_val <= 2.0 else "⚠️ Zorlama")

                    extra_tags = ""
                    if task.is_previously_failed: extra_tags += " (İyileştirme)"
                    if task.is_fear_task: extra_tags += " (Korku Yüzleşmesi 🛡️)"
                    if task.is_reward_task: extra_tags += " (ÖDÜL 🏆)"

                    motivation_msg = ""
                    if task.priority == TaskPriority.CRITICAL:
                        motivation_msg = " | 🚀 Game Changer!"
                    elif task.chunk_index == 1 and task.parent_id:
                        motivation_msg = " | 🏁 Güçlü Başlangıç"

                    day_label = ""
                    if hasattr(self.config, 'easy_win_day_idx') and day_idx == self.config.easy_win_day_idx:
                        day_label = " [🟢 Kolay Kazanım Günü]"

                    self.scheduled_tasks.append({
                        "day": days_names[day_idx % 7] + day_label,
                        "task": task.name,
                        "category": task.category,
                        "start_fmt": f"{int(start_min // 60):02d}:{int(start_min % 60):02d}",
                        "end_fmt": f"{int(end_min // 60):02d}:{int(end_min % 60):02d}",
                        "duration": task.duration_minutes,
                        "raw_start": s,
                        "difficulty": task.difficulty,
                        "energy_match": match_desc,
                        "tags": extra_tags + motivation_msg
                    })

            for t_idx in range(num_tasks):
                if pulp.value(is_dropped[t_idx]) == 1:
                    self.dropped_tasks.append(processing_tasks[t_idx])
                    if self.config.enable_coach_mode:
                        self.coach_notes.append(
                            f"Mental sağlığını korumak için '{processing_tasks[t_idx].name}' görevini bu haftalık eledim.")

            self.scheduled_tasks.sort(key=lambda x: x['raw_start'])
            return self.scheduled_tasks
        else:
            print(f"⚠️ Optimize edilemedi: {pulp.LpStatus[prob.status]}")
            return []


if __name__ == "__main__":
    time_cfg = TimeSlotConfig()
    cal = CalendarService(time_cfg)
    cal.apply_student_constraints()

    user_prof = UserProfile.STANDARD
    cal.apply_dynamic_sleep(user_prof)
    cal.block_social_activity(1, 19, 21)

    # TEST: Kolay Kazanım Günü ve Motivasyon Mesajları
    history = UserHistory(last_week_completion_rate=0.95, early_finish_accumulated_minutes=45)

    tasks = [
        StudyTask("t1", "Lineer Cebir", 120, 9, "MATH", priority=TaskPriority.CRITICAL, deadline_day=2),
        StudyTask("t2", "İnkılap Tarihi", 90, 3, "HIST", repetition_count=3),
        StudyTask("t3", "Kuantum Fiziği (Yeni)", 90, 9, "SCI", is_new_topic=True),
        StudyTask("t4", "Büyük Proje", 240, 7, "CS", deadline_day=5),
    ]

    config = SchedulerConfig(is_exam_week=False)
    scheduler = FluxScheduler(tasks, cal, config, time_cfg, user_prof, user_history=history)
    res = scheduler.solve()

    if res:
        print(f"\n--- 🧠 AI YAŞAM KOÇU ({user_prof.name}) ---")
        current_day = ""
        total_days = 0
        for item in res:
            if item['day'] != current_day:
                print(f"\n📅 {item['day']}")
                current_day = item['day']
                total_days += 1
            print(f"   ⏰ {item['start_fmt']}-{item['end_fmt']} | {item['task']}{item['tags']}")

        if scheduler.ai_rationale:
            print("\n🤖 NEDEN BU PLAN?:")
            for note in scheduler.ai_rationale:
                print(f"   ► {note}")

        if scheduler.coach_notes:
            print("\n🧘 KOÇ TAVSİYELERİ:")
            for note in scheduler.coach_notes:
                print(f"   • {note}")