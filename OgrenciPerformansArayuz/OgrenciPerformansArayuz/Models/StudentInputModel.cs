using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace OgrenciPerformansArayuz.Models
{
    public class StudentInputModel
    {
        // Python tarafı "student_id" bekliyor
        [JsonPropertyName("student_id")]
        public string StudentId { get; set; } = "Ogrenci_" + DateTime.Now.Ticks.ToString().Substring(10);

        // --- Adım 1: Kimlik & Çevre ---
        [Required(ErrorMessage = "Yaş alanı zorunludur.")]
        [Range(10, 100, ErrorMessage = "Yaş 10-100 arasında olmalıdır.")]
        [JsonPropertyName("age")]
        public int Age { get; set; }

        [Required]
        [JsonPropertyName("gender")]
        public string Gender { get; set; } // Male, Female

        [JsonPropertyName("parental_education_level")]
        public string ParentalEducationLevel { get; set; } // High School, Bachelor...

        [JsonPropertyName("internet_quality")]
        public string InternetQuality { get; set; } // Poor, Average, Good

        // --- Adım 2: Akademik ---
        [Required]
        [Range(0, 24)]
        [JsonPropertyName("study_hours_per_day")]
        public double StudyHoursPerDay { get; set; }

        [Range(0, 100)]
        [JsonPropertyName("attendance_percentage")]
        public double AttendancePercentage { get; set; }

        [JsonPropertyName("extracurricular_participation")]
        public string ExtracurricularParticipation { get; set; } // Yes, No

        [JsonPropertyName("part_time_job")]
        public string PartTimeJob { get; set; } // Yes, No

        // --- Adım 3: Yaşam & Sağlık ---
        [Range(0, 24)]
        [JsonPropertyName("social_media_hours")]
        public double SocialMediaHours { get; set; }

        [Range(0, 24)]
        [JsonPropertyName("netflix_hours")]
        public double NetflixHours { get; set; }

        [Required]
        [Range(0, 24)]
        [JsonPropertyName("sleep_hours")]
        public double SleepHours { get; set; }

        [Range(0, 7)]
        [JsonPropertyName("exercise_frequency")]
        public int ExerciseFrequency { get; set; }

        [JsonPropertyName("diet_quality")]
        public string DietQuality { get; set; } // Poor, Average, Good

        [Range(1, 10)]
        [JsonPropertyName("mental_health_rating")]
        public int MentalHealthRating { get; set; }
    }
}