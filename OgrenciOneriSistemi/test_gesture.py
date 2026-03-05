import cv2
import time
import numpy as np
import unittest
import csv
from gesture_control import PomodoroGestureController, GESTURE_LIBRARY


class TestPomodoroAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Test ortamını başlat."""
        cls.controller = PomodoroGestureController()
        cls.test_results = []

    def test_angle_logic(self):
        """Postür analizindeki açı hesaplama algoritmasını doğrula."""
        # Senaryo 1: Tam dik duruş (0 derece)
        p1 = (100, 200)  # Omuz
        p2 = (100, 100)  # Burun
        angle = self.controller._calculate_angle(p1, p2)
        self.assertAlmostEqual(angle, 0.0, delta=1.0)

        # Senaryo 2: 30 derece eğilme
        # Tan 30 = x/100 -> x yaklasik 57
        p3 = (157, 100)
        angle_30 = self.controller._calculate_angle(p1, p3)
        self.assertAlmostEqual(angle_30, 30.0, delta=2.0)
        print("✅ Açı Hesaplama Mantığı: Doğrulandı.")

    def test_system_latency(self):
        """Sistemin kare başına işlem süresini (Gecikme) ölç."""
        print("\n--- Performans Analizi Başlatılıyor ---")
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        latencies = []

        for i in range(50):  # 50 kare üzerinden örneklem
            start_time = time.time()
            # Postür ve El analizi beraber çalıştırılıyor
            _, _, _ = self.controller.detect_action(dummy_frame)
            end_time = time.time()
            latencies.append((end_time - start_time) * 1000)  # ms

        avg_latency = np.mean(latencies)
        fps = 1000 / avg_latency

        print(f"Ortalama Gecikme: {avg_latency:.2f} ms")
        print(f"Teorik FPS: {fps:.2f}")

        self.test_results.append(["Gecikme (ms)", f"{avg_latency:.2f}"])
        self.test_results.append(["FPS", f"{fps:.2f}"])
        self.assertLess(avg_latency, 100, "Sistem gerçek zamanlı çalışma sınırının altında!")


def run_realtime_benchmark():
    """Rapor için doğruluk oranlarını manuel test etme aracı."""
    cap = cv2.VideoCapture(0)
    controller = PomodoroGestureController()

    print("\n--- MANUEL DOĞRULAMA MODU ---")
    print("Test etmek istediğiniz jesti yapın ve sistemin tepkisini gözlemleyin.")
    print("'q' tuşuna basarak bitirin.")

    stats = {"total_frames": 0, "gesture_detected": 0, "posture_warnings": 0}

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        start = time.time()
        frame, cmd, warn = controller.detect_action(frame)
        end = time.time()

        stats["total_frames"] += 1
        if cmd != "NO_ACTION": stats["gesture_detected"] += 1
        if warn: stats["posture_warnings"] += 1

        cv2.putText(frame, f"FPS: {1 / (end - start):.1f}", (10, 30), 1, 1, (0, 255, 0), 2)
        cv2.imshow("Bulgular Test Paneli", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Rapor için özet veriler
    print("\n--- RAPOR İÇİN BULGULAR ---")
    print(f"Toplam Analiz Edilen Kare: {stats['total_frames']}")
    print(f"Tespit Edilen Komut Sayısı: {stats['gesture_detected']}")
    print(f"Postür Uyarısı Sayısı: {stats['posture_warnings']}")


if __name__ == "__main__":
    # Önce otomatik unit testler
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPomodoroAI)
    unittest.TextTestRunner(verbosity=2).run(suite)

    # Sonra manuel veri toplama
    run_realtime_benchmark()