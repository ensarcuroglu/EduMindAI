import unittest
import os
import joblib
import pandas as pd
import numpy as np
import warnings

# Test sırasında gereksiz uyarıları kapatmak için
warnings.filterwarnings("ignore")

# Test edilecek modülden fonksiyonları içe aktarıyoruz
from learning_style_predictor import train_and_predict_learning_style, predict_new_student


class TestLearningStyleModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Tüm testlerden önce bir kez çalışır.
        Modelin varlığını kontrol eder, yoksa eğitir ve test ortamını hazırlar.
        """
        print("\n=== TEST ORTAMI BAŞLATILIYOR ===")
        cls.save_dir = 'artifacts/models'
        cls.model_path = os.path.join(cls.save_dir, 'rf_learning_style_model.joblib')
        cls.features_path = os.path.join(cls.save_dir, 'model_features.joblib')

        # Model dosyaları yoksa eğitimi tetikle
        if not os.path.exists(cls.model_path) or not os.path.exists(cls.features_path):
            print("UYARI: Model dosyaları bulunamadı. Test için geçici eğitim başlatılıyor...")
            cls.model, cls.features = train_and_predict_learning_style()
        else:
            print("BİLGİ: Mevcut model dosyaları diskten yükleniyor...")
            cls.model = joblib.load(cls.model_path)
            cls.features = joblib.load(cls.features_path)

    def test_01_model_files_exist(self):
        """Adım 1: Model ve özellik dosyalarının diskte başarıyla oluşturulduğunu doğrular."""
        self.assertTrue(os.path.exists(self.model_path), "HATA: Model dosyası (.joblib) bulunamadı.")
        self.assertTrue(os.path.exists(self.features_path), "HATA: Özellik dosyası (.joblib) bulunamadı.")
        print("✓ Dosya bütünlüğü testi başarılı.")

    def test_02_model_loading(self):
        """Adım 2: Modelin belleğe düzgün yüklendiğini doğrular."""
        self.assertIsNotNone(self.model, "Model None olarak yüklendi.")
        self.assertIsNotNone(self.features, "Özellik listesi None olarak yüklendi.")
        # Özellik sayısının doğruluğunu kontrol et (FinalGrade/ExamScore/LearningStyle hariç 13 özellik olmalı)
        self.assertEqual(len(self.features), 13, f"Beklenen özellik sayısı 13, alınan {len(self.features)}")
        print("✓ Model yükleme testi başarılı.")

    def test_03_prediction_output_structure(self):
        """Adım 3: Tahmin fonksiyonunun çıktı formatını ve veri tiplerini kontrol eder."""
        # Rastgele geçerli değerlerle standart bir öğrenci profili
        test_student = [
            20,  # StudyHours
            80,  # Attendance
            1,  # Resources
            0,  # Extracurricular
            1,  # Motivation
            1,  # Internet
            0,  # Gender
            22,  # Age
            5,  # OnlineCourses
            1,  # Discussions
            75,  # AssignmentCompletion
            1,  # EduTech
            1  # StressLevel
        ]

        # Fonksiyonu çalıştır
        print("\n-- Tahmin Fonksiyonu Test Ediliyor --")
        results = predict_new_student(self.model, self.features, test_student)

        # Kontroller
        self.assertIsNotNone(results, "Tahmin sonucu boş döndü.")
        self.assertIsInstance(results, list, "Sonuç bir liste olmalı.")
        self.assertEqual(len(results), 4, "4 farklı öğrenme stili için sonuç dönmeli.")

        # İçerik kontrolü (Stil Adı, Yüzde)
        first_result = results[0]
        self.assertIsInstance(first_result, tuple, "Liste elemanları tuple olmalı.")
        self.assertIsInstance(first_result[0], str, "Stil adı string olmalı.")
        self.assertIsInstance(first_result[1], float, "Olasılık değeri float olmalı.")
        print("✓ Çıktı yapısı testi başarılı.")

    def test_04_probability_math_check(self):
        """Adım 4: Olasılıkların toplamının %100 olduğunu doğrular."""
        # Düşük profilli bir öğrenci örneği
        test_student = [5, 60, 0, 0, 0, 0, 1, 18, 0, 0, 50, 0, 2]

        results = predict_new_student(self.model, self.features, test_student)

        total_percentage = sum([score for _, score in results])

        # Float hassasiyeti nedeniyle tam 100.0 olmayabilir, küçük bir sapma payı (delta) ile kontrol ediyoruz
        self.assertAlmostEqual(total_percentage, 100.0, delta=0.01,
                               msg="Olasılıklar toplamı 100 olmalıdır.")

        # Hiçbir olasılık negatif veya 100'den büyük olamaz
        for style, percentage in results:
            self.assertTrue(0 <= percentage <= 100, "Olasılık değeri 0-100 aralığı dışında.")

        print("✓ Matematiksel tutarlılık testi başarılı.")

    def test_05_input_dimension_error(self):
        """Adım 5: Eksik veri girildiğinde sistemin hata verip vermediğini kontrol eder."""
        # 13 yerine 10 özellikli eksik veri
        incomplete_data = [20, 80, 1, 0, 1, 1, 0, 22, 5, 1]

        # ValueError bekle (Sklearn özellik sayısı tutmadığında hata fırlatır)
        with self.assertRaises(ValueError):
            predict_new_student(self.model, self.features, incomplete_data)
        print("✓ Hata yönetimi testi başarılı (Eksik veriye karşı dirençli).")

    def test_06_consistency(self):
        """Adım 6: Determinizm testi - Aynı girdi her zaman aynı çıktıyı vermelidir."""
        input_data = [30, 90, 2, 1, 2, 1, 1, 25, 10, 1, 90, 1, 0]

        result1 = predict_new_student(self.model, self.features, input_data)
        result2 = predict_new_student(self.model, self.features, input_data)

        self.assertEqual(result1, result2, "Aynı girdiler farklı sonuçlar üretti!")
        print("✓ Kararlılık testi başarılı.")


if __name__ == '__main__':
    unittest.main(verbosity=2)