namespace OgrenciPerformansArayuz.Models
{
    public class LearningStyleInputModel
    {
        // Kişisel Veriler
        public int Age { get; set; }
        public int Gender { get; set; } // 0: Kadın, 1: Erkek

        // Akademik Veriler
        /// <summary>
        /// Veri setinde bu değer HAFTALIKTIR (Ortalama ~20).
        /// Frontend'den günlük geliyorsa 7 ile çarpılmalıdır.
        /// </summary>
        public double StudyHours { get; set; }

        public double Attendance { get; set; } // 0-100 arası
        public double AssignmentCompletion { get; set; } // 0-100 arası

        // 0-20 arası sayısal değer (Veri seti ortalaması ~10)
        public int OnlineCourses { get; set; }

        // Kategorik Değerler
        public int Resources { get; set; }      // 0: Düşük, 1: Orta, 2: Yüksek (Veri seti max: 2)

        // DÜZELTME: Veri setinde max değer 1. Sadece Var/Yok olmalı.
        public int Extracurricular { get; set; } // 0: Yok, 1: Var

        // DÜZELTME: Veri setinde max değer 2. (0, 1, 2)
        public int Motivation { get; set; }     // 0: Düşük, 1: Orta, 2: Yüksek

        public int StressLevel { get; set; }    // 0: Az, 1: Orta, 2: Çok

        // Boolean Değerler (0 veya 1)
        public int Internet { get; set; }
        public int Discussions { get; set; }
        public int EduTech { get; set; }
    }
}