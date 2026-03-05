import cv2
import mediapipe as mp
import numpy as np
import time
from datetime import datetime


class AIProctor:
    def __init__(self):
        # MediaPipe Kurulumu
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            refine_landmarks=True
        )

        # Durum Değişkenleri
        self.warning_given = False
        self.violation_start_time = None
        self.violation_logs = []
        self.exam_start_time = datetime.now()  # Sınav başlangıç saati

        # --- HASSASİYET AYARLARI ---
        self.SUSPICION_THRESHOLD_SECONDS = 0.8
        self.HEAD_YAW_LIMIT = 6.0
        self.HEAD_PITCH_LIMIT = -6.0
        self.EYE_RATIO_LEFT_SAFE = 0.44
        self.EYE_RATIO_RIGHT_SAFE = 0.56

    def log_violation(self, violation_type):
        """İhlal tespiti ve log listesine ekleme"""
        if self.violation_start_time is None:
            return None, 0

        duration = time.time() - self.violation_start_time
        progress = min(duration / self.SUSPICION_THRESHOLD_SECONDS, 1.0)

        if duration > self.SUSPICION_THRESHOLD_SECONDS:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Aksiyon tipini belirle
            action_type = "SILENT_LOG"
            alert_msg = "LOGLANDI"

            if not self.warning_given:
                self.warning_given = True
                action_type = "WARNING_POPUP"
                alert_msg = "UYARI: EKRANA ODAKLAN!"
                # Anlık konsol uyarısı (opsiyonel, rapor zaten sonda verilecek)
                print(f"\n!!! {alert_msg} ({violation_type}) !!!")

            # Log listesine ekle
            log_entry = {
                "time": timestamp,
                "type": violation_type,
                "duration": f"{duration:.2f}",
                "action": action_type
            }
            self.violation_logs.append(log_entry)

            return alert_msg, progress

        return None, progress

    def print_final_report(self):
        """Sınav sonunda raporu KONSOLA yazar"""
        exam_end_time = datetime.now()

        print("\n" + "=" * 60)
        print(f"{'SINAV GÜVENLİK VE TAKİP RAPORU':^60}")
        print("=" * 60)
        print(f"Tarih: {self.exam_start_time.strftime('%d.%m.%Y')}")
        print(f"Baslangic: {self.exam_start_time.strftime('%H:%M:%S')}")
        print(f"Bitis:     {exam_end_time.strftime('%H:%M:%S')}")
        print(f"Toplam Ihlal Sayisi: {len(self.violation_logs)}")
        print("=" * 60 + "\n")

        if not self.violation_logs:
            print("TEBRIKLER! Hicbir supheli hareket tespit edilmedi.\n")
        else:
            print(f"{'ZAMAN':<10} | {'IHLAL TURU':<15} | {'SURE (sn)':<10} | {'DURUM'}")
            print("-" * 60)
            for log in self.violation_logs:
                print(f"{log['time']:<10} | {log['type']:<15} | {log['duration']:<10} | {log['action']}")
        print("\n" + "=" * 60 + "\n")

    def get_gaze_ratio(self, eye_points, landmarks, frame):
        left_corner = np.array([landmarks[eye_points[0]].x, landmarks[eye_points[0]].y])
        right_corner = np.array([landmarks[eye_points[3]].x, landmarks[eye_points[3]].y])
        iris_center = np.array([landmarks[eye_points[4]].x, landmarks[eye_points[4]].y])

        h, w, _ = frame.shape
        cv2.circle(frame, (int(left_corner[0] * w), int(left_corner[1] * h)), 2, (0, 255, 255), -1)
        cv2.circle(frame, (int(right_corner[0] * w), int(right_corner[1] * h)), 2, (0, 255, 255), -1)
        cv2.circle(frame, (int(iris_center[0] * w), int(iris_center[1] * h)), 3, (0, 0, 255), -1)

        eye_width = np.linalg.norm(right_corner - left_corner)
        if eye_width == 0: return 0.5
        dist_to_left = np.linalg.norm(iris_center - left_corner)
        return dist_to_left / eye_width

    def head_pose_estimation(self, img, landmarks):
        img_h, img_w, _ = img.shape
        face_3d = []
        face_2d = []
        key_points = [1, 199, 33, 263, 61, 291]

        for idx, lm in enumerate(landmarks):
            if idx in key_points:
                x, y = int(lm.x * img_w), int(lm.y * img_h)
                face_2d.append([x, y])
                face_3d.append([x, y, lm.z])

        face_2d = np.array(face_2d, dtype=np.float64)
        face_3d = np.array(face_3d, dtype=np.float64)
        focal_length = 1 * img_w
        cam_matrix = np.array([[focal_length, 0, img_h / 2], [0, focal_length, img_w / 2], [0, 0, 1]])
        dist_matrix = np.zeros((4, 1), dtype=np.float64)

        success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
        rmat, jac = cv2.Rodrigues(rot_vec)
        angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)

        return angles[0] * 360, angles[1] * 360

    def process_stream(self):
        cap = cv2.VideoCapture(0)
        print("Sınav Takip Sistemi Başlatıldı... (Kapatmak için 'q' basın)")

        while cap.isOpened():
            success, image = cap.read()
            if not success: continue

            image = cv2.flip(image, 1)
            self.frame_height, self.frame_width, _ = image.shape
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image_rgb)
            image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

            status_text = "GUVENLI"
            status_color = (0, 255, 0)
            violation_reason = ""
            is_violation = False

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    landmarks = face_landmarks.landmark

                    pitch, yaw = self.head_pose_estimation(image, landmarks)

                    left_indices = [33, 159, 145, 133, 468]
                    right_indices = [362, 386, 374, 263, 473]
                    l_ratio = self.get_gaze_ratio(left_indices, landmarks, image)
                    r_ratio = self.get_gaze_ratio(right_indices, landmarks, image)
                    avg_ratio = (l_ratio + r_ratio) / 2

                    # --- KURAL SETİ ---
                    if yaw < -self.HEAD_YAW_LIMIT:
                        is_violation = True;
                        violation_reason = "KAFA SOL"
                    elif yaw > self.HEAD_YAW_LIMIT:
                        is_violation = True;
                        violation_reason = "KAFA SAG"
                    elif pitch < self.HEAD_PITCH_LIMIT:
                        is_violation = True;
                        violation_reason = "KAFA ASAGI"

                    if not is_violation:
                        if avg_ratio < self.EYE_RATIO_LEFT_SAFE:
                            is_violation = True;
                            violation_reason = "GOZLER SAG"
                        elif avg_ratio > self.EYE_RATIO_RIGHT_SAFE:
                            is_violation = True;
                            violation_reason = "GOZLER SOL"

                    cv2.putText(image, f"Pitch: {int(pitch)} | Yaw: {int(yaw)}", (10, 30), cv2.FONT_HERSHEY_PLAIN, 1,
                                (200, 200, 0), 1)
                    cv2.putText(image, f"Eye Ratio: {avg_ratio:.3f}", (10, 50), cv2.FONT_HERSHEY_PLAIN, 1,
                                (200, 200, 0), 1)

                    if is_violation:
                        if self.violation_start_time is None:
                            self.violation_start_time = time.time()

                        msg, progress = self.log_violation(violation_reason)

                        if msg:
                            self.violation_start_time = time.time()

                        status_color = (0, 0, 255)
                        status_text = f"IHLAL: {violation_reason}"

                        h, w, _ = image.shape
                        cv2.rectangle(image, (0, 0), (w, h), (0, 0, 255), 10)
                        if msg:
                            cv2.putText(image, msg, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

                    else:
                        status_text = "ODAKLANDI"
                        self.violation_start_time = None
                        h, w, _ = image.shape
                        cv2.rectangle(image, (0, 0), (w, h), (0, 255, 0), 2)

            else:
                status_text = "YUZ YOK"
                status_color = (0, 0, 255)

            cv2.putText(image, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            cv2.imshow('AI Proctor V5 (Console Log)', image)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        # --- KAPANIŞTA RAPORU KONSOLA YAZ ---
        self.print_final_report()


if __name__ == "__main__":
    proctor = AIProctor()
    proctor.process_stream()