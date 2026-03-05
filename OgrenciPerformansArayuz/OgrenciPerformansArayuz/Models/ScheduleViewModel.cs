using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace OgrenciPerformansArayuz.Models
{
    // Python tarafındaki TaskInput modeline karşılık gelir
    public class TaskInputModel
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = System.Guid.NewGuid().ToString();

        [JsonPropertyName("name")]
        public string Name { get; set; }

        [JsonPropertyName("duration_minutes")]
        public int DurationMinutes { get; set; }

        [JsonPropertyName("difficulty")]
        public int Difficulty { get; set; } // 1-10 arası

        [JsonPropertyName("category")]
        public string Category { get; set; }

        [JsonPropertyName("priority")]
        public string Priority { get; set; } = "MEDIUM"; // LOW, MEDIUM, HIGH, CRITICAL

        [JsonPropertyName("deadline_day")]
        public int? DeadlineDay { get; set; }

        [JsonPropertyName("fixed_start_slot")]
        public int? FixedStartSlot { get; set; }

        [JsonPropertyName("prerequisites")]
        public List<string> Prerequisites { get; set; } = new List<string>();

        // Yeni Pedagojik Özellikler
        [JsonPropertyName("is_new_topic")]
        public bool IsNewTopic { get; set; } = false;

        [JsonPropertyName("repetition_count")]
        public int RepetitionCount { get; set; } = 0;

        [JsonPropertyName("postpone_count")]
        public int PostponeCount { get; set; } = 0;
    }

    // Python tarafındaki BusyInterval modeline karşılık gelir
    public class BusyIntervalModel
    {
        [JsonPropertyName("day_idx")]
        public int DayIndex { get; set; }

        [JsonPropertyName("start_hour")]
        public float StartHour { get; set; }

        [JsonPropertyName("end_hour")]
        public float EndHour { get; set; }
    }

    // Python tarafındaki SchedulerHistoryInput modeline karşılık gelir
    public class SchedulerHistoryInputModel
    {
        [JsonPropertyName("last_week_completion_rate")]
        public float LastWeekCompletionRate { get; set; } = 1.0f;

        [JsonPropertyName("failed_task_ids")]
        public List<string> FailedTaskIds { get; set; } = new List<string>();

        [JsonPropertyName("actual_work_hours")]
        public List<int> ActualWorkHours { get; set; } = new List<int>();

        [JsonPropertyName("consecutive_lazy_days")]
        public int ConsecutiveLazyDays { get; set; } = 0;

        [JsonPropertyName("early_finish_accumulated_minutes")]
        public int EarlyFinishAccumulatedMinutes { get; set; } = 0;

        [JsonPropertyName("cancelled_slots")]
        public List<int> CancelledSlots { get; set; } = new List<int>();
    }

    // Python API'ye gidecek ana istek modeli (SchedulerRequest)
    public class SchedulerRequestModel
    {
        [JsonPropertyName("tasks")]
        public List<TaskInputModel> Tasks { get; set; } = new List<TaskInputModel>();

        [JsonPropertyName("user_profile")]
        public string UserProfile { get; set; } = "STANDARD"; // STANDARD, EARLY_BIRD, NIGHT_OWL, POWER_GRINDER

        [JsonPropertyName("busy_intervals")]
        public List<BusyIntervalModel> BusyIntervals { get; set; } = new List<BusyIntervalModel>();

        [JsonPropertyName("user_history")]
        public SchedulerHistoryInputModel UserHistory { get; set; }

        // Durumlar
        [JsonPropertyName("is_exam_week")]
        public bool IsExamWeek { get; set; } = false;

        [JsonPropertyName("lazy_mode")]
        public bool LazyMode { get; set; } = false;

        [JsonPropertyName("user_mood_score")]
        public int UserMoodScore { get; set; } = 5;

        [JsonPropertyName("horizon_days")]
        public int HorizonDays { get; set; } = 7;
    }

    // ---------------------------------------------------------
    // API'den Dönecek Yanıt Modelleri
    // ---------------------------------------------------------

    public class ScheduledTaskItem
    {
        [JsonPropertyName("day")]
        public string Day { get; set; }

        [JsonPropertyName("task")]
        public string TaskName { get; set; }

        [JsonPropertyName("category")]
        public string Category { get; set; }

        [JsonPropertyName("start_fmt")]
        public string StartFormatted { get; set; } // Örn: "09:00"

        [JsonPropertyName("end_fmt")]
        public string EndFormatted { get; set; }   // Örn: "10:30"

        [JsonPropertyName("duration")]
        public int Duration { get; set; }

        [JsonPropertyName("difficulty")]
        public int Difficulty { get; set; }

        [JsonPropertyName("energy_match")]
        public string EnergyMatch { get; set; } // "🔥 Flow", "✅ İyi" vb.

        [JsonPropertyName("tags")]
        public string Tags { get; set; }
    }

    public class SchedulerResponseModel
    {
        [JsonPropertyName("status")]
        public string Status { get; set; }

        [JsonPropertyName("message")]
        public string Message { get; set; }

        [JsonPropertyName("schedule")]
        public List<ScheduledTaskItem> Schedule { get; set; }

        [JsonPropertyName("coach_notes")]
        public List<string> CoachNotes { get; set; }

        [JsonPropertyName("ai_rationale")]
        public List<string> AiRationale { get; set; }

        [JsonPropertyName("profile_used")]
        public string ProfileUsed { get; set; }

        [JsonPropertyName("total_tasks_scheduled")]
        public int TotalTasksScheduled { get; set; }
    }
}