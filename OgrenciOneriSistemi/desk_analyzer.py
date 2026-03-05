#desk_analyzer.py:
import cv2
import numpy as np
from ultralytics import YOLO
import math
import base64
from PIL import Image, ImageDraw, ImageFont
import os


class DeskTaxonomy:
    """
    V8.1: The Omniscient Architect Taksonomisi - Balanced Edition.
    V8 üzerine adil puanlama, tekrar eden uyarı filtresi ve hata düzeltmeleri.
    """

    def __init__(self):
        self.categories = {
            'study': {'weight': 1.0, 'color': (50, 205, 50)},  # Lime Green
            'distractor': {'weight': -2.0, 'color': (255, 69, 0)},  # Red-Orange
            'wellness': {'weight': 0.5, 'color': (255, 191, 0)},  # Amber
            'irrelevant': {'weight': 0.0, 'color': (192, 192, 192)}  # Silver
        }

        self.class_map = {
            # STUDY TOOLS
            63: ('Laptop', 'study'), 64: ('Mouse', 'study'), 66: ('Klavye', 'study'),
            62: ('Monitör', 'study'), 73: ('Kitap', 'study'), 77: ('Makas', 'study'),
            # DISTRACTORS
            67: ('Telefon', 'distractor'), 65: ('Kumanda', 'distractor'),
            76: ('Oyuncak', 'distractor'),
            # WELLNESS
            39: ('Şişe', 'wellness'), 41: ('Bardak/Kupa', 'wellness'),
            46: ('Atıştırmalık', 'wellness'), 47: ('Atıştırmalık', 'wellness'),
            58: ('Bitki', 'wellness'), 75: ('Vazo', 'wellness'),
            # IRRELEVANT
            56: ('Sandalye', 'irrelevant'), 57: ('Koltuk', 'irrelevant'),
            24: ('Çanta', 'irrelevant'), 26: ('El Çantası', 'irrelevant'),
            74: ('Saat', 'irrelevant'), 28: ('Bavul', 'irrelevant')
        }

    def get_info(self, cls_id):
        return self.class_map.get(cls_id, ('Bilinmeyen', 'irrelevant'))


class DeskAgentSovereignAPI:
    def __init__(self, model_path='yolov8x.pt'):
        print(f"🚀 SOVEREIGN API V8.1 (Balanced Architect) BAŞLATILIYOR...")
        print(f"🧠 Model: {model_path} | Modüller: ScreenState, CableHunter, LightGrid")
        self.model = YOLO(model_path)
        self.taxonomy = DeskTaxonomy()

    def _gaussian(self, x, mu, sigma):
        return math.exp(-0.5 * ((x - mu) / sigma) ** 2)

    def _verify_liquid_container(self, frame, bbox):
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0: return True, 0.0
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        return edge_density < 0.15, edge_density

    def analyze_screen_activity(self, frame, screen_bbox):
        x1, y1, x2, y2 = screen_bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0: return False

        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        std_dev = np.std(gray_roi)
        mean_val = np.mean(gray_roi)

        is_active = std_dev > 10 and mean_val > 20
        return is_active

    def analyze_lighting_uniformity(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        grid_h, grid_w = h // 3, w // 3

        brightness_map = []
        for r in range(3):
            for c in range(3):
                cell = gray[r * grid_h:(r + 1) * grid_h, c * grid_w:(c + 1) * grid_w]
                brightness_map.append(np.mean(cell))

        b_mean = np.mean(brightness_map)
        b_std = np.std(brightness_map)
        uniformity_score = 100 - min(100, (b_std / (b_mean + 1)) * 100 * 2)

        warnings = []
        if uniformity_score < 60:
            warnings.append("💡 Işık dağılımı dengesiz (Gölgeli bölgeler var). Masa lambanı yeniden konumlandır.")

        return int(uniformity_score), warnings

    def analyze_advanced_lighting(self, frame):
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l_mean, b_mean, l_std = np.mean(l), np.mean(b), np.std(l)
        glare_ratio = (np.sum(l > 240) / l.size) * 100

        feedback = []
        score_l = 100 * self._gaussian(l_mean, mu=145, sigma=45)

        temp_mood = "Nötr"
        if b_mean < 120:
            temp_mood = "Soğuk (Odak)"
        elif b_mean > 138:
            temp_mood = "Sıcak (Yaratıcılık)"

        dist_from_neutral = abs(b_mean - 128)
        score_temp = 100 * self._gaussian(dist_from_neutral, mu=0, sigma=30)

        uniformity_score, uni_warnings = self.analyze_lighting_uniformity(frame)
        feedback.extend(uni_warnings)

        final_score = (0.4 * score_l) + (0.2 * score_temp) + (0.2 * uniformity_score) + (
                    0.2 * (100 - min(glare_ratio * 5, 100)))

        if score_l < 50: feedback.append(f"💡 Ortam loş ({int(l_mean)}). Göz yorgunluğu yaratabilir.")
        if glare_ratio > 2.0: feedback.append("✨ Ekranda parlama var. Işık açısını değiştir.")

        confidence = min(100, (100 * self._gaussian(l_std, 50, 20)))
        return int(final_score), feedback, int(confidence), temp_mood

    def analyze_cable_clutter(self, frame, detections):
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        mask = np.ones((h, w), dtype=np.uint8) * 255
        valid_items = [d for d in detections if d['category'] in ['study', 'wellness', 'distractor']]
        for d in valid_items:
            cv2.rectangle(mask, (d['bbox'][0], d['bbox'][1]), (d['bbox'][2], d['bbox'][3]), 0, -1)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)

        _, binary = cv2.threshold(tophat, 20, 255, cv2.THRESH_BINARY)
        masked_clutter = cv2.bitwise_and(binary, binary, mask=mask)

        desk_area = masked_clutter[int(h * 0.40):, :]
        pixel_density = (cv2.countNonZero(desk_area) / desk_area.size) * 100

        # V8.1: Daha toleranslı formül (Eşik 1.5 -> 2.0, Çarpan 20 -> 12)
        clutter_score = max(0, 100 - (max(0, pixel_density - 2.0) * 12))

        msg = None
        if pixel_density > 3.5:
            msg = "🔌 Görünen kablolar veya dağınık kağıtlar var. Kablo düzenleyici kullanabilirsin."

        return int(clutter_score), msg

    def analyze_spatial_topology(self, frame, detections, clutter_score):
        h, w = frame.shape[:2]
        score_topology = 100
        # V8.1: Tekrar eden mesajları önlemek için set kullanıyoruz
        msgs = set()
        risk_msgs = set()

        study_objs = [d for d in detections if d['category'] == 'study']
        distractors = [d for d in detections if d['category'] == 'distractor']
        wellness_objs = [d for d in detections if d['category'] == 'wellness']

        keyboard = next((d for d in study_objs if 'Klavye' in d['name']), None)
        laptop = next((d for d in study_objs if 'Laptop' in d['name']), None)
        monitor = next((d for d in study_objs if 'Monitör' in d['name']), None)

        # EKRAN AKTİVİTESİ
        active_screens = 0
        if laptop:
            if self.analyze_screen_activity(frame, laptop['bbox']): active_screens += 1
        if monitor:
            if self.analyze_screen_activity(frame, monitor['bbox']): active_screens += 1

        if (laptop or monitor) and active_screens == 0:
            msgs.add("💤 Ekranlar kapalı veya uyku modunda görünüyor.")

        # ERGONOMİ
        is_internal_keyboard = False
        if keyboard and laptop:
            lx1, ly1, lx2, ly2 = laptop['bbox']
            kx, ky = keyboard['center']
            if lx1 < kx < lx2 and ly1 < ky < ly2: is_internal_keyboard = True

        if keyboard and (monitor or laptop) and not is_internal_keyboard:
            main_screen = monitor if monitor else laptop
            sx, _ = main_screen['center']
            kx, _ = keyboard['center']
            if abs(sx - kx) / w > 0.15:
                score_topology -= 20
                msgs.add("📐 Klavye ve Ekran tam hizalı değil.")

        elif laptop and not monitor:
            lx, _ = laptop['center']
            if abs(lx - (w / 2)) / w > 0.25:
                score_topology -= 10
                msgs.add("📐 Laptop masanın kenarına çok yakın.")

        # İSTİLACILAR (Ceza Limiti)
        fz_x1, fz_x2 = w * 0.25, w * 0.75
        distractor_penalty = 0
        max_distractor_penalty = 60  # V8.1: Maksimum ceza limiti

        detected_distractors = set()  # Aynı türden birden fazla nesne için kontrol

        for d in distractors:
            dx, dy = d['center']
            d_name = d['name']

            # Aynı isimli nesne (örn. Telefon) daha önce cezalandırıldıysa daha az ceza ver veya uyarıyı tekrar etme
            penalty_multiplier = 0.5 if d_name in detected_distractors else 1.0

            if fz_x1 < dx < fz_x2:
                penalty = 35 * penalty_multiplier
                msgs.add(f"🚫 {d_name} tam odak alanında!")
            else:
                penalty = 15 * penalty_multiplier
                msgs.add(f"⚠️ {d_name} masada dikkat dağıtabilir.")

            distractor_penalty += penalty
            detected_distractors.add(d_name)

        distractor_penalty = min(distractor_penalty, max_distractor_penalty)
        score_topology -= distractor_penalty

        # SIVI RİSKİ
        electronics = [x for x in [laptop, keyboard, monitor] if x]
        liquids = [d for d in wellness_objs if d['name'] in ['Bardak/Kupa', 'Şişe']]

        for liq in liquids:
            l_cx, l_cy = liq['center']
            for elec in electronics:
                e_cx, e_cy = elec['center']
                dist = math.sqrt((l_cx - e_cx) ** 2 + (l_cy - e_cy) ** 2)
                if dist < w * 0.15:
                    risk_msgs.add(f"⚠️ DİKKAT: {liq['name']} elektroniğe çok yakın!")
                    score_topology -= 15
                    break

        final_topo_score = (score_topology * 0.6) + (clutter_score * 0.4)

        # Liste olarak döndür
        return int(max(0, final_topo_score)), list(msgs) + list(risk_msgs), bool(distractor_penalty > 0), active_screens

    def analyze_wellness_holistic(self, unique_items, topo_score, light_score):
        base_score = 0
        msgs = []
        pos_msgs = []

        has_water = any(item in unique_items for item in ['Şişe', 'Bardak/Kupa', 'Termos'])
        has_snack = any(item in unique_items for item in ['Atıştırmalık', 'Meyve'])

        if has_water:
            base_score += 35
            pos_msgs.append("✅ Su kaynağın erişilebilir.")
        else:
            msgs.append("💧 Masanda su yok.")

        if has_snack:
            base_score += 5
            pos_msgs.append("🍎 Atıştırmalıklar mevcut.")

        has_nature = any(item in unique_items for item in ['Bitki', 'Vazo'])
        if has_nature:
            base_score += 30
            pos_msgs.append("✅ Bitki varlığı stresi azaltıyor.")
        else:
            msgs.append("🌿 İpucu: Bitki eklemek stresi azaltabilir.")

        env_quality = (topo_score + light_score) / 200
        base_score += 30 * env_quality

        return int(min(100, base_score)), msgs, pos_msgs

    def get_context_aware_tip(self, scores, meta):
        if meta['active_screens'] == 0:
            return "🚀 Pro Tip: Masa çalışmaya hazır ama ekranlar kapalı. Dijital detoks mu yapıyorsun?"
        if scores['clutter_free'] < 70:
            return "🚀 Pro Tip: Kablo düzenleyiciler masadaki görsel gürültüyü %40 azaltır."
        if meta['work_mode'] == 'Deep Work':
            return "🚀 Pro Tip: Deep Work modundasın. Telefonu başka odaya koyarak verimi 2 katına çıkar."
        return "🚀 Pro Tip: Pomodoro tekniği (25dk çalışma / 5dk mola) ile başla."

    def determine_work_mode(self, detections, has_distractors, active_screens):
        study_objs = [d for d in detections if d['category'] == 'study']

        if not study_objs: return "Boş / Hazırlık"
        if has_distractors: return "Riskli (Distracted)"

        has_book = any(d['name'] == 'Kitap' for d in study_objs)
        if active_screens == 0 and has_book: return "Analog Study"

        if len(study_objs) >= 2: return "Deep Work"
        return "Casual Work"

    def draw_overlay_pil(self, frame, detections, focus_zone_coords):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(pil_image)
        try:
            font = ImageFont.truetype("arial.ttf", 18)
            font_bold = ImageFont.truetype("arialbd.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            font_bold = font

        fz_x1, fz_x2, fz_y1, fz_y2 = focus_zone_coords
        corner_len = 40
        color_fz = (255, 191, 0)
        width_fz = 3

        lines = [
            [(fz_x1, fz_y1), (fz_x1 + corner_len, fz_y1)], [(fz_x1, fz_y1), (fz_x1, fz_y1 + corner_len)],
            [(fz_x2, fz_y1), (fz_x2 - corner_len, fz_y1)], [(fz_x2, fz_y1), (fz_x2, fz_y1 + corner_len)],
            [(fz_x1, fz_y2), (fz_x1 + corner_len, fz_y2)], [(fz_x1, fz_y2), (fz_x1, fz_y2 - corner_len)],
            [(fz_x2, fz_y2), (fz_x2 - corner_len, fz_y2)], [(fz_x2, fz_y2), (fz_x2, fz_y2 - corner_len)]
        ]
        for line in lines: draw.line(line, fill=color_fz, width=width_fz)
        draw.text((fz_x1 + 10, fz_y1 + 10), "FOCUS ZONE", font=font, fill=color_fz)

        for d in detections:
            x1, y1, x2, y2 = d['bbox']
            color = d['meta']['color']
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            label_text = f"{d['name']}"
            text_bbox = draw.textbbox((x1, y1), label_text, font=font_bold)
            text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            label_y = y1 - 25 if y1 > 25 else y1 + 5
            draw.rectangle([x1, label_y, x1 + text_w + 10, label_y + text_h + 10], fill=color)
            draw.text((x1 + 5, label_y + 2), label_text, font=font_bold, fill=(255, 255, 255))

        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    def process_image(self, image_bytes):
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None: raise ValueError("Görüntü okunamadı.")
        except Exception as e:
            return {"error": str(e)}

        h, w, _ = frame.shape
        results = self.model(frame, verbose=False)
        detections = []
        detected_names = set()

        potential_objects = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                name, category = self.taxonomy.get_info(cls_id)
                potential_objects.append({"name": name, "category": category, "conf": conf, "box": box})

        study_boxes = []
        for obj in potential_objects:
            if obj['category'] == 'study' and obj['conf'] > 0.40:
                x1, y1, x2, y2 = map(int, obj['box'].xyxy[0])
                study_boxes.append({'name': obj['name'], 'rect': (x1, y1, x2, y2)})

        for obj in potential_objects:
            name, category, conf = obj['name'], obj['category'], obj['conf']
            if category == 'irrelevant': continue

            threshold = 0.60 if category == 'wellness' else 0.40
            if conf < threshold: continue

            x1, y1, x2, y2 = map(int, obj['box'].xyxy[0])
            w_obj, h_obj = x2 - x1, y2 - y1
            if (w_obj * h_obj) < (w * h * 0.005): continue

            is_ghost = False
            if category == 'wellness':
                obj_cx, obj_cy = (x1 + x2) / 2, (y1 + y2) / 2
                for s_box in study_boxes:
                    sx1, sy1, sx2, sy2 = s_box['rect']
                    if sx1 < obj_cx < sx2 and sy1 < obj_cy < sy2:
                        is_ghost = True
                        break
            if is_ghost: continue

            if name == 'Şişe' and (w_obj / h_obj > 1.2): continue

            if name in ['Bardak/Kupa', 'Şişe']:
                is_liquid, _ = self._verify_liquid_container(frame, (x1, y1, x2, y2))
                if not is_liquid:
                    name = "Kalemlik"
                    category = "study"

            detections.append({
                "name": name, "category": category,
                "bbox": (x1, y1, x2, y2), "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                "conf": conf, "meta": self.taxonomy.categories[category]
            })
            detected_names.add(name)

        clutter_score, clutter_msg = self.analyze_cable_clutter(frame, detections)
        light_score, light_msgs, light_conf, light_mood = self.analyze_advanced_lighting(frame)
        topo_score, topo_msgs, has_distractors, active_screens = self.analyze_spatial_topology(frame, detections,
                                                                                               clutter_score)

        if clutter_msg: topo_msgs.append(clutter_msg)
        well_score, well_crit, well_pos = self.analyze_wellness_holistic(list(detected_names), topo_score, light_score)

        overall_score = (topo_score * 0.30) + (light_score * 0.25) + (well_score * 0.25) + (clutter_score * 0.20)
        work_mode = self.determine_work_mode(detections, has_distractors, active_screens)

        scores_dict = {
            "overall_focus": int(overall_score), "lighting": int(light_score),
            "ergonomics": int(topo_score), "wellness": int(well_score),
            "clutter_free": int(clutter_score)
        }
        meta_dict = {
            "confidence": int(light_conf), "work_mode": work_mode,
            "light_mood": light_mood, "detected_items": list(detected_names),
            "active_screens": active_screens
        }

        fz_coords = (int(w * 0.25), int(w * 0.75), int(h * 0.30), int(h * 0.95))
        overlay_img = self.draw_overlay_pil(frame, detections, fz_coords)
        _, buffer = cv2.imencode('.jpg', overlay_img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        final_recs = light_msgs + topo_msgs + well_crit
        if overall_score > 75:
            final_recs.extend(well_pos)
            final_recs.append(self.get_context_aware_tip(scores_dict, meta_dict))
        if not final_recs: final_recs.append("🏆 Ortam gayet iyi görünüyor!")

        return {
            "scores": scores_dict, "meta": meta_dict,
            "recommendations": final_recs, "processed_image_base64": img_base64
        }


if __name__ == "__main__":
    test_image_path = 'masa_3.jpg'
    if os.path.exists(test_image_path):
        agent = DeskAgentSovereignAPI()
        with open(test_image_path, "rb") as f:
            result = agent.process_image(f.read())

        if "error" in result:
            print(f"Hata: {result['error']}")
        else:
            s = result['scores']
            print("\n📊 ANALİZ SONUCU (V8.1 Balanced):")
            print(f"Genel Odak: {s['overall_focus']}/100")
            print(f"Işık: {s['lighting']} | Ergonomi: {s['ergonomics']} | Düzen: {s['clutter_free']}")
            print(f"Mod: {result['meta']['work_mode']}")
            print("Öneriler:", result['recommendations'])
            with open("output_v8_1.jpg", "wb") as f:
                f.write(base64.b64decode(result['processed_image_base64']))
            print("✅ 'output_v8_1.jpg' kaydedildi.")