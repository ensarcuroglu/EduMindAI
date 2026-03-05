#gesture_control.py:
import os
import sys

# --- KRİTİK DÜZELTME (PROTOBUF FIX) ---
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import cv2
import time
import math
import numpy as np

# MediaPipe Import (Güvenli Blok)
try:
    import mediapipe as mp
except ImportError:
    mp = None

# --- JEST KÜTÜPHANESİ ---
GESTURE_LIBRARY = {
    "OPEN_HAND": [1, 1, 1, 1, 1],
    "FIST": [0, 0, 0, 0, 0],
    "VICTORY": [0, 1, 1, 0, 0],
    "SHAKA": [1, 0, 0, 0, 1],
    "ROCK": [0, 1, 0, 0, 1],
    "GUN": [1, 1, 0, 0, 0]
}


class PomodoroGestureController:
    """
    Pomodoro Sayacı için Jest ve Biyometrik Postür Kontrolcüsü (V5.3 - Stability Fix).
    """

    def __init__(self):
        if mp is None:
            self._raise_import_error("MediaPipe kütüphanesi yüklü değil. 'pip install mediapipe' çalıştırın.")

        self.mp_hands = None
        self.mp_pose = None
        self.mp_draw = None

        # --- GÜVENLİ MODÜL BAŞLATMA ---
        try:
            # Doğrudan erişim
            self.mp_hands = mp.solutions.hands
            self.mp_pose = mp.solutions.pose
            self.mp_draw = mp.solutions.drawing_utils
        except AttributeError:
            self._raise_import_error("MediaPipe modülleri yüklenemedi. Kurulum bozuk olabilir.")
        except Exception as e:
            self._raise_import_error(f"MediaPipe modülleri yüklenirken hata: {e}")

        # 1. EL MODELİ
        try:
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
        except Exception as e:
            self._raise_import_error(f"El modeli başlatılamadı: {e}")

        # 2. POSTÜR MODELİ
        try:
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        except Exception as e:
            self._raise_import_error(f"Postür modeli başlatılamadı: {e}")

        # Durum Değişkenleri
        self.last_gesture = None
        self.gesture_start_time = 0
        self.CONFIRMATION_TIME = 1.0
        self.posture_bad_start_time = 0
        self.POSTURE_WARNING_THRESHOLD = 3.0

        # Renkler
        self.primary_color = (0, 255, 255)  # Sarı
        self.success_color = (0, 255, 0)  # Yeşil
        self.alert_color = (0, 0, 255)  # Kırmızı

        # Varsayılan Ayarlar
        self.action_map = {
            "PAUSE": "SHAKA",
            "START": "GUN",
            "SHORT_BREAK": "ROCK"
        }

    def _raise_import_error(self, specific_error=""):
        print(f"❌ KRİTİK HATA: {specific_error}")
        sys.exit(1)

    def set_gesture_config(self, new_config):
        for action, gesture_name in new_config.items():
            if gesture_name in GESTURE_LIBRARY:
                self.action_map[action] = gesture_name

    # --- YARDIMCI FONKSİYONLAR ---
    def _calculate_angle(self, p1, p2):
        """
        İki nokta arasındaki vektörün DİKEY eksenle yaptığı açıyı hesaplar.
        p1: Alt Nokta (Omuz), p2: Üst Nokta (Burun)
        """
        dx = p2[0] - p1[0]
        dy = p1[1] - p2[1]
        angle_rad = math.atan2(abs(dx), abs(dy))
        angle_deg = math.degrees(angle_rad)
        return angle_deg

    # --- EL ANALİZİ METOTLARI ---
    def _get_finger_states(self, lm_list, handedness_label="Right"):
        if not lm_list: return []
        fingers = []
        tip_ids = [4, 8, 12, 16, 20]
        thumb_tip_x = lm_list[tip_ids[0]][1]
        thumb_ip_x = lm_list[tip_ids[0] - 1][1]

        if handedness_label == "Right":
            fingers.append(1 if thumb_tip_x < thumb_ip_x else 0)
        else:
            fingers.append(1 if thumb_tip_x > thumb_ip_x else 0)

        for id in range(1, 5):
            fingers.append(1 if lm_list[tip_ids[id]][2] < lm_list[tip_ids[id] - 2][2] else 0)
        return fingers

    def _classify_gesture(self, fingers):
        if not fingers: return None
        for action, gesture_name in self.action_map.items():
            target_pattern = GESTURE_LIBRARY.get(gesture_name)
            if target_pattern and fingers == target_pattern:
                return action
        return None

    # --- GELİŞMİŞ POSTÜR ANALİZİ ---
    def _analyze_posture(self, frame, rgb_frame):
        h, w, c = frame.shape
        results = self.pose.process(rgb_frame)

        warning_msg = None
        is_bad_posture = False
        posture_score = 100
        metrics = {}

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            nose = lm[self.mp_pose.PoseLandmark.NOSE.value]
            l_shoulder = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            r_shoulder = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            if l_shoulder.visibility > 0.5 and r_shoulder.visibility > 0.5:
                nose_pt = (int(nose.x * w), int(nose.y * h))
                l_sh_pt = (int(l_shoulder.x * w), int(l_shoulder.y * h))
                r_sh_pt = (int(r_shoulder.x * w), int(r_shoulder.y * h))

                shoulder_mid_x = int((l_sh_pt[0] + r_sh_pt[0]) / 2)
                shoulder_mid_y = int((l_sh_pt[1] + r_sh_pt[1]) / 2)
                shoulder_mid_pt = (shoulder_mid_x, shoulder_mid_y)

                # Metrik 1: Açı
                flexion_angle = self._calculate_angle(shoulder_mid_pt, nose_pt)
                metrics['angle'] = flexion_angle

                if flexion_angle > 15:
                    penalty = (flexion_angle - 15) * 2.5
                    posture_score -= penalty

                # Metrik 2: Sıkışma
                shoulder_width = math.dist(l_sh_pt, r_sh_pt)
                neck_dist = math.dist(shoulder_mid_pt, nose_pt)

                if shoulder_width > 0:
                    compression_ratio = neck_dist / shoulder_width
                    metrics['ratio'] = compression_ratio
                    if compression_ratio < 0.35:
                        penalty = (0.35 - compression_ratio) * 200
                        posture_score -= penalty

                # Metrik 3: Simetri
                shoulder_slope = abs(l_sh_pt[1] - r_sh_pt[1]) / (shoulder_width + 0.1)
                if shoulder_slope > 0.15:
                    posture_score -= 15

                posture_score = max(0, min(100, int(posture_score)))

                if posture_score < 50:
                    is_bad_posture = True
                    color = self.alert_color

                    if self.posture_bad_start_time == 0:
                        self.posture_bad_start_time = time.time()
                    elif (time.time() - self.posture_bad_start_time) > self.POSTURE_WARNING_THRESHOLD:
                        if flexion_angle > 40:
                            warning_msg = "BASINI KALDIR!"
                        elif compression_ratio < 0.30:
                            warning_msg = "DIK DUR!"
                        else:
                            warning_msg = "POSTUR BOZUK!"
                else:
                    self.posture_bad_start_time = 0
                    color = self.success_color

                cv2.line(frame, l_sh_pt, r_sh_pt, (255, 255, 255), 2)
                cv2.line(frame, shoulder_mid_pt, nose_pt, color, 3)

        return frame, warning_msg, is_bad_posture, posture_score

    def _draw_hud(self, frame, gesture_name, progress, posture_warning, posture_score):
        h, w, c = frame.shape
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 100), (30, 30, 30), -1)
        alpha = 0.8
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        if posture_warning:
            if int(time.time() * 5) % 2 == 0:
                cv2.rectangle(frame, (0, 0), (w, h), self.alert_color, 10)
            cv2.putText(frame, posture_warning, (int(w / 2) - 150, int(h / 2)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, self.alert_color, 4)
            status_text = f"POSTUR: %{posture_score} (RISKLI)"
            status_color = self.alert_color
        else:
            status_text = f"KOMUT: {gesture_name if gesture_name else 'BEKLENIYOR...'}"
            status_color = self.success_color if progress >= 1.0 else self.primary_color

        cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2, cv2.LINE_AA)

        if not posture_warning:
            cv2.putText(frame, f"OMURGA: %{posture_score}", (w - 220, 50), cv2.FONT_HERSHEY_PLAIN, 1.2, (200, 200, 200),
                        1)
            bar_color = self.success_color if posture_score > 70 else (0, 165, 255)
            cv2.rectangle(frame, (w - 220, 60), (w - 20 + int((posture_score - 100) * 2), 70), bar_color, -1)

        if gesture_name and progress > 0 and not posture_warning:
            bar_width = int(w * progress)
            bar_color = self.success_color if progress >= 1.0 else self.primary_color
            cv2.rectangle(frame, (0, 95), (bar_width, 100), bar_color, -1)

        return frame

    def detect_action(self, frame):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        command = "NO_ACTION"
        current_gesture = None
        progress = 0.0

        frame, posture_warning, is_bad_posture, score = self._analyze_posture(frame, img_rgb)
        results_hand = self.hands.process(img_rgb)

        if results_hand.multi_hand_landmarks and results_hand.multi_handedness:
            hand_landmarks = results_hand.multi_hand_landmarks[0]
            handedness = results_hand.multi_handedness[0].classification[0].label
            self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

            lm_list = []
            h, w, c = frame.shape
            for id, lm in enumerate(hand_landmarks.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append([id, cx, cy])

            fingers = self._get_finger_states(lm_list, handedness)
            current_gesture = self._classify_gesture(fingers)

            if current_gesture:
                if current_gesture == self.last_gesture:
                    elapsed = time.time() - self.gesture_start_time
                    progress = min(elapsed / self.CONFIRMATION_TIME, 1.0)
                    if progress >= 1.0:
                        command = current_gesture
                        cv2.putText(frame, "ONAYLANDI", (20, 150),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    self.last_gesture = current_gesture
                    self.gesture_start_time = time.time()
                    progress = 0.0
            else:
                self.last_gesture = None
                progress = 0.0

        frame = self._draw_hud(frame, self.last_gesture, progress, posture_warning, score)
        return frame, command, posture_warning  # 3 DEĞER DÖNÜYOR


if __name__ == "__main__":
    try:
        cap = cv2.VideoCapture(0)
        controller = PomodoroGestureController()

        print("\n=== POMODORO GESTURE & POSTURE CONTROL V5.3 ===")
        print("🎥 Kamera Başlatılıyor...")

        while True:
            success, frame = cap.read()
            if not success: break

            frame = cv2.flip(frame, 1)

            try:
                # --- GÜNCEL KOD BURASI ---
                # Fonksiyon 3 değer döndürüyor, biz de 3 değer ile karşılıyoruz.
                frame, cmd, warn = controller.detect_action(frame)

                if cmd != "NO_ACTION":
                    print(f"🔥 KOMUT: {cmd}")

                if warn:
                    print(f"⚠️ UYARI: {warn}")
            except ValueError as ve:
                print(f"❌ Değer Hatası: {ve}")
                print("Lütfen detect_action fonksiyonunun 3 değer (frame, cmd, warn) döndürdüğünden emin olun.")
                break

            cv2.imshow("Pomodoro AI Eye", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"❌ Program hatası: {e}")