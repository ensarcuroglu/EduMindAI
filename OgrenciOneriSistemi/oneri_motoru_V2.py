#oneri_motoru_V2.py:

import pandas as pd
import numpy as np
import joblib
import os
import sys
import time
from typing import List, Dict, Any
from sklearn.base import BaseEstimator, TransformerMixin
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import set_config
from sklearn.pipeline import Pipeline
from optimizer import AcademicOptimizer
import mentor
import json

# --- KRİTİK AYAR: Scikit-learn'ü Pandas Çıktısına Zorla ---
set_config(transform_output="pandas")

# --- GÜVENLİK AYARI: Matplotlib Backend (API'de GUI hatası vermemesi için) ---
import matplotlib

matplotlib.use('Agg')

# --- SHAP Kütüphanesi Kontrolü ---
try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️ UYARI: 'shap' kütüphanesi bulunamadı.")


# =============================================================================
# 1. OUTLIER CAPPER (Hata Korumalı)
# =============================================================================
class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if not isinstance(X, pd.DataFrame):
            return X
        X_ = X.copy()
        if hasattr(self, 'lower_bounds_') and self.lower_bounds_:
            for col, lower in self.lower_bounds_.items():
                if col in X_.columns:
                    upper = self.upper_bounds_.get(col, np.inf)
                    X_[col] = np.clip(X_[col], lower, upper)
        return X_


# =============================================================================
# 2. FeatureEngineer SINIFI (Hata Korumalı)
# =============================================================================
class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_ = X.copy()

        # --- Temel Türetimler (V1) ---
        # Not: .get() yerine doğrudan erişim kullanıyoruz çünkü DataFrame garantimiz var
        # Eğer sütun yoksa hata vermemesi için get kullanılabilir ama eğitim mantığı sütunların varlığını varsayar.

        # Güvenli toplama için fillna(0) mantığı eklenebilir ama eğitim kodu direkt topluyor:
        X_['total_distraction_hours'] = X_['social_media_hours'] + X_['netflix_hours']

        # 0'a bölme hatasını önlemek için +1 ekliyoruz
        X_['focus_ratio'] = X_['study_hours_per_day'] / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = X_['sleep_hours'] / (X_['study_hours_per_day'] + 1)
        X_['study_efficiency'] = X_['study_hours_per_day'] * X_['mental_health_rating']
        X_['academic_engagement'] = X_['attendance_percentage'] * X_['study_hours_per_day']
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        # --- İleri Seviye Türetimler (V2) ---

        # 1. Zindelik Skoru (Vitality): Uyku ^ 1.2 (DÜZELTİLMİŞ HALİ)
        X_['vitality_score'] = (X_['sleep_hours'] ** 1.2) * (X_['exercise_frequency'] + 1)

        # 2. Tükenmişlik Riski (Burnout Risk): np.where kullanımı
        # Part-time çalışıp çok ders çalışan öğrenci yorgun düşebilir.
        part_time_val = np.where(X_['part_time_job'] == 'Yes', 1.5, 1.0)
        X_['burnout_risk'] = X_['study_hours_per_day'] * part_time_val

        # 3. Adanmışlık (Dedication): np.where kullanımı
        # Okul dışı aktiviteye katılıp devamsızlığı az olan öğrenci "sosyal inektir".
        extra_curr_val = np.where(X_['extracurricular_participation'] == 'Yes', 1.2, 1.0)
        X_['dedication_level'] = X_['attendance_percentage'] * extra_curr_val

        return X_


# =============================================================================
# KATALOG YÜKLEME
# =============================================================================
try:
    from oneriler_V2 import RECOMMENDATION_CATALOG
except ImportError:
    RECOMMENDATION_CATALOG = []
    print("UYARI: oneriler_V2.py bulunamadı!")


# =============================================================================
# 3. AKILLI DANIŞMAN (SmartAdvisor Ultimate)
# =============================================================================
class SmartAdvisor:
    def __init__(self, model_path: str = "artifacts/student_score_xgb_pipeline_v2.joblib"):
        self.catalog = RECOMMENDATION_CATALOG
        self.model = None
        self.explainer = None
        self.prep_pipeline = None

        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                try:
                    if hasattr(self.model, 'set_output'):
                        self.model.set_output(transform="pandas")
                except Exception:
                    pass
                print(f"✅ [SmartAdvisor] YZ Modeli Hazır: {model_path}")

                if SHAP_AVAILABLE:
                    self._init_shap()
            except Exception as e:
                print(f"❌ Model Yükleme Hatası: {e}")
        else:
            print(f"⚠️ Model Dosyası Yok: {model_path}")

    def _init_shap(self):
        try:
            if hasattr(self.model, 'regressor_'):
                internal_pipeline = self.model.regressor_
            else:
                internal_pipeline = self.model

            self.regressor = internal_pipeline.named_steps['regressor']
            self.prep_pipeline = Pipeline(internal_pipeline.steps[:-1])
            try:
                if hasattr(self.prep_pipeline, 'set_output'):
                    self.prep_pipeline.set_output(transform="pandas")
            except:
                pass
            self.explainer = shap.TreeExplainer(self.regressor)
        except Exception as e:
            print(f"⚠️ SHAP Başlatılamadı: {e}")

    def _calculate_derived(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Türetilmiş özellikleri hesaplar."""
        d = row.copy()
        study = d.get('study_hours_per_day', 0)
        sleep = d.get('sleep_hours', 0)
        social = d.get('social_media_hours', 0)
        netflix = d.get('netflix_hours', 0)
        attend = d.get('attendance_percentage', 0)
        exercise = d.get('exercise_frequency', 0)

        d['total_distraction_hours'] = social + netflix
        d['focus_ratio'] = study / (d['total_distraction_hours'] + 1)
        d['lifestyle_balance'] = sleep / (study + 1)
        d['vitality_score'] = (sleep ** 1.2) * (exercise + 1)

        pt_val = 1.5 if d.get('part_time_job') == 'Yes' else 1.0
        d['burnout_risk'] = study * pt_val
        ec_val = 1.2 if d.get('extracurricular_participation') == 'Yes' else 1.0
        d['dedication_level'] = attend * ec_val
        return d

    def predict(self, data: Dict[str, Any]) -> float:
        if not self.model: return 0.0
        try:
            df = pd.DataFrame([data])
            prediction = self.model.predict(df)
            val = float(prediction[0])
            return max(0.0, min(100.0, val))
        except Exception as e:
            print(f"❌ TAHMİN HATASI: {e}")
            return 0.0

    def analyze_root_cause(self, student_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.explainer or not self.prep_pipeline: return []
        try:
            df = pd.DataFrame([student_data])
            X_transformed = self.prep_pipeline.transform(df)
            shap_values = self.explainer.shap_values(X_transformed)
            values = shap_values[0] if len(shap_values.shape) > 1 else shap_values

            feature_names = []
            try:
                feature_names = list(self.prep_pipeline.get_feature_names_out())
            except:
                if isinstance(X_transformed, pd.DataFrame):
                    feature_names = list(X_transformed.columns)
                else:
                    feature_names = [f"Feature {i}" for i in range(len(values))]

            contributions = []
            min_len = min(len(feature_names), len(values))
            for i in range(min_len):
                raw_name = str(feature_names[i])
                clean_name = raw_name.split("__")[-1].replace("_", " ").title()
                contributions.append({"feature": clean_name, "impact": float(values[i])})
            contributions.sort(key=lambda x: x['impact'])
            return contributions
        except Exception as e:
            print(f"SHAP Runtime Hatası: {e}")
            return []

    def apply_simulation(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        sim = data.copy()
        feat, op, val = config.get("feature"), config.get("operation"), config.get("value")
        if feat not in sim and feat not in ['total_distraction_hours']: return sim
        curr = sim.get(feat, 0)
        if isinstance(val, (int, float)) and isinstance(curr, (int, float)):
            if op == "add":
                sim[feat] = curr + val
            elif op == "multiply":
                sim[feat] = curr * val
            elif op == "set":
                sim[feat] = val
            if "hours" in feat: sim[feat] = max(0.0, min(24.0, sim[feat]))
            if "percentage" in feat: sim[feat] = min(100.0, max(0.0, sim[feat]))
            if "rating" in feat: sim[feat] = min(10, max(1, sim[feat]))
        elif isinstance(val, str) and op == "set":
            sim[feat] = val
        return sim

    # --- YENİ EKLENEN AKILLI SİMÜLASYON METODLARI ---
    def apply_smart_simulation(self, student_data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[
        str, Any]:
        """
        V6.0 PROFESYONEL SİMÜLASYON MOTORU (Holistik Yaklaşım)
        ------------------------------------------------------
        Bu versiyon, zamanı sadece matematiksel bir "kap" olarak değil,
        psikolojik ve biyolojik bir kaynak olarak yönetir.

        1. Zaman Borcu (Debt): Öncelik sırasına göre kesinti yapar.
        2. Zaman Fazlası (Surplus): 'İhtiyaçlar Hiyerarşisi'ne göre dağıtır.
           - Önce Biyolojik İhtiyaç (Uyku)
           - Sonra Zihinsel İhtiyaç (Dinlenme/Mental)
           - En Son Üretkenlik (Ders)
        """
        sim_data = student_data.copy()
        manually_changed_features = set()
        time_balance = 0.0

        # --- ADIM 1: Önerileri Uygula ve Bütçeyi Hesapla ---
        for rec in recommendations:
            sim_config = rec.get('simulation', {})
            feat = sim_config.get('feature')
            op, val = sim_config.get('operation'), sim_config.get('value')

            current_val = sim_data.get(feat, 0)

            if 'hours' in feat:
                change = 0.0
                if op == 'set':
                    change = val - current_val
                    sim_data[feat] = val
                elif op == 'add':
                    # Global Tavan Sınırı (Günde 24 saatin 16 saati aktivite olamaz)
                    if feat == 'study_hours_per_day' and (current_val + val) > 12:
                        val = 12 - current_val
                    sim_data[feat] = current_val + val
                    change = val
                elif op == 'multiply':
                    new_val = current_val * val
                    change = new_val - current_val
                    sim_data[feat] = new_val

                time_balance += change
                manually_changed_features.add(feat)
            else:
                if op == 'set':
                    sim_data[feat] = val
                elif op == 'add':
                    sim_data[feat] += val

        # --- ADIM 2: ZAMAN YÖNETİMİ ---

        # SENARYO A: ZAMAN BORCU VAR (Kesinti Yap)
        if time_balance > 0.05:
            # Kesinti Sırası: Önce Eğlence, Sonra Uyku (Mecbursa)
            sacrifice_order = ['netflix_hours', 'social_media_hours', 'sleep_hours']
            remaining_debt = time_balance

            for sacrifice_col in sacrifice_order:
                if remaining_debt <= 0: break
                if sacrifice_col in manually_changed_features: continue

                current_sac_val = sim_data.get(sacrifice_col, 0)
                if current_sac_val > 0:
                    deduction = min(current_sac_val, remaining_debt)

                    # Kritik Uyku Koruması (5 saatin altına inme)
                    if sacrifice_col == 'sleep_hours':
                        max_deduct = max(0, current_sac_val - 5.0)
                        deduction = min(deduction, max_deduct)

                    sim_data[sacrifice_col] -= deduction
                    remaining_debt -= deduction

        # SENARYO B: ZAMAN FAZLASI VAR (Yatırım Yap)
        elif time_balance < -0.05:
            surplus = abs(time_balance)

            # 1. Öncelik: UYKU (Biyolojik Temel)
            # Eğer uyku 7.5 saatin altındaysa, artan zamanın %60'ını veya ihtiyacı kadarını buraya ver.
            current_sleep = sim_data.get('sleep_hours', 0)
            if 'sleep_hours' not in manually_changed_features and current_sleep < 7.5:
                # İhtiyaç duyulan
                needed = 7.5 - current_sleep
                # Elimizdeki kaynağın bir kısmını ayır
                allocatable = min(surplus, needed)

                sim_data['sleep_hours'] += allocatable
                surplus -= allocatable  # Kalan zamanı güncelle

            # 2. Öncelik: MENTAL SAĞLIK / DİNLENME (Yorgunluk Yönetimi)
            # Eğer çok çalışıyorsa (6+ saat), artan zamanı derse değil, "Mental Health" puanına yatır.
            # (Bu modelde mental sağlık puanını artırmak, verimi artırır)
            current_study = sim_data.get('study_hours_per_day', 0)
            if current_study > 6.0 and surplus > 0:
                # Zamanı puana dönüştür: Her 1 saatlik dinlenme +1 Mental Health
                mental_boost = min(2, int(surplus))
                sim_data['mental_health_rating'] = min(10, sim_data.get('mental_health_rating', 5) + mental_boost)
                surplus -= (mental_boost * 0.5)  # Yarım saat maliyet sayalım

            # 3. Öncelik: AKADEMİK (Kalanı Derse Yatır)
            # Ancak "Diminishing Returns" (Azalan Verim) kuralı uygula.
            # Zaten 8 saat çalışıyorsa daha fazla ekleme.
            if surplus > 0 and 'study_hours_per_day' not in manually_changed_features:
                if current_study < 8.0:
                    sim_data['study_hours_per_day'] += surplus
                else:
                    # 8 saati geçtiyse, artan zamanı "Sosyalleşme" olarak kullan (Motivasyon artırır)
                    # Modelde extracurricular varsa onu 'Yes' yapabiliriz veya
                    # vitality skoruna etki etmesi için bu zamanı 'yok' sayabiliriz (Dinlenme)
                    pass

                    # 4. Türetilmiş özellikleri YENİDEN hesapla
        sim_data = self._calculate_derived(sim_data)
        return sim_data


    def predict_future_potential(self, student_data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[
        str, Any]:
        """
        Mevcut durum ile simüle edilmiş durum arasındaki farkı hesaplar.
        """
        current_enriched = self._calculate_derived(student_data)
        current_score = self.predict(current_enriched)

        future_data = self.apply_smart_simulation(student_data, recommendations)
        future_score = self.predict(future_data)

        # Mantık kontrolü: Eğer model düşüş öngörürse değişimi 0 kabul et
        if future_score < current_score:
            future_score = current_score

        return {
            "current_score": round(current_score, 2),
            "future_score": round(future_score, 2),
            "uplift": round(future_score - current_score, 2),
            "simulated_data": future_data
        }

    def find_sweet_spot(self, student_data: Dict[str, Any], feature: str, min_change=0.5, max_change=2.5, step=0.5) -> \
    Dict[str, Any]:
        best_uplift = 0
        best_val = 0
        original_score = self.predict(student_data)

        for change in np.arange(min_change, max_change + step, step):
            sim_config = {"feature": feature, "operation": "add", "value": float(change)}
            sim_data = self.apply_simulation(student_data, sim_config)
            if feature == "study_hours_per_day" and sim_data[feature] > 14: continue

            # Burada da basit predict yerine mantıklı bir şeyler yapılabilir ama
            # şimdilik tekil simülasyon olduğu için eski usul kalsın.
            new_score = self.predict(sim_data)
            uplift = new_score - original_score
            if uplift > best_uplift:
                best_uplift, best_val = uplift, float(change)

        return {"best_change": best_val, "max_uplift": best_uplift}

    def format_advice_text(self, text: str, student_data: Dict[str, Any], sim_config: Dict[str, Any]) -> str:
        feature = sim_config.get('feature')
        current_val = student_data.get(feature, 0)
        if isinstance(current_val, (int, float)):
            return f"{text} (Şu an: {current_val:.1f})"
        return text

    def calculate_cumulative_impact(self, student_data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> float:
        # Bu fonksiyon artık kullanılmıyor olabilir ama eski uyumluluk için tutuyoruz
        sim_data = student_data.copy()
        for rec in recommendations:
            sim_config = rec.get('simulation', {})
            if sim_config:
                sim_data = self.apply_simulation(sim_data, sim_config)
        raw_final = self.predict(sim_data)
        current = self.predict(student_data)
        uplift = raw_final - current
        if uplift > 15: uplift = 15 + (uplift - 15) * 0.6
        return min(99.9, current + uplift)

    def generate_advice(self, student_data: Dict[str, Any], max_recs: int = 4) -> Dict[str, Any]:
        """
        Öğrenci için en uygun tavsiyeleri oluşturur.
        Güncellemeler: Uyku Vetosu, Puan Sönümleme (Damping).
        """
        enriched = self._calculate_derived(student_data)
        current_score = self.predict(student_data)
        # Şimdilik SHAP analizini kapatıyoruz (Feature 8 sorunu çözülene kadar)
        # root_causes = []
        root_causes = self.analyze_root_cause(student_data)

        candidates = []

        # --- KRİTİK KONTROL 1: UYKU KRİZİ (Zombi Modu Engelleme) ---
        current_sleep = student_data.get('sleep_hours', 0)
        critical_sleep_mode = False

        if current_sleep < 6.0:
            critical_sleep_mode = True
            # Uyku önerisini en tepeye, zorunlu ve yüksek puanlı olarak ekle
            sleep_fix = {
                "id": "critical_sleep_fix",
                "category": "Wellness",
                "difficulty": "Easy",
                "text": f"🚨 **ACİL DURUM:** Günde {current_sleep} saat uyku ile beynin 'Tasarruf Modu'nda çalışıyor. Akademik yüklenmeden önce biyolojik ihtiyacını karşılamalısın. İlk hedefin uykunu 7 saate çıkarmak.",
                "simulation": {"feature": "sleep_hours", "operation": "set", "value": 7.0},
                "calculated_impact": 99.0,  # En üstte çıksın diye yapay yüksek puan
                "time_cost": 0  # Uyku temel ihtiyaçtır, maliyet değildir
            }
            candidates.append(sleep_fix)

        # --- KATALOG TARAMA ---
        for item in self.catalog:
            try:
                # Koşul kontrolü (Eval güvenliği için enriched data kullanılır)
                if item.get("condition") and not eval(item.get("condition"), {}, enriched): continue
            except:
                continue

            # --- KRİTİK KONTROL 2: VETO ---
            # Eğer uykusuzluk krizi varsa, 'Academic' (Ders artırma) önerilerini engelle.
            if critical_sleep_mode:
                allowed_categories = ['Wellness', 'Discipline']
                if item.get('category') not in allowed_categories:
                    continue

            sim_config = item.get("simulation", {}).copy()
            impact = 0.5
            original_text = item.get("text", "")

            # Tekil etki hesaplaması (Burada hala basit simülasyon kullanılır)
            if self.model and sim_config.get('operation') == 'add' and 'hours' in sim_config.get('feature', ''):
                opt = self.find_sweet_spot(student_data, sim_config['feature'])
                if opt['max_uplift'] > 0:
                    sim_config['value'] = opt['best_change']
                    impact = opt['max_uplift']
                    original_text = f"🎯 Optimize: +{opt['best_change']} saat öneriliyor. \n   🗣️ {original_text}"
            elif self.model and sim_config:
                # Basit etki hesabı (Diğer özelliklerden çalmadan saf etki)
                sim_data = self.apply_simulation(student_data, sim_config)
                impact = self.predict(sim_data) - current_score

            if impact > 0.05:
                cand = item.copy()
                cand['calculated_impact'] = impact
                cand['simulation'] = sim_config
                cand['text'] = self.format_advice_text(original_text, student_data, sim_config)

                # Zaman maliyeti hesabı
                time_cost = 0.0
                feat = sim_config.get('feature', '')
                if 'hours' in feat:
                    op, val = sim_config.get('operation'), sim_config.get('value')
                    curr = student_data.get(feat, 0)
                    if op == 'add':
                        time_cost = val
                    elif op == 'set':
                        time_cost = val - curr
                    elif op == 'multiply':
                        time_cost = (curr * val) - curr
                cand['time_cost'] = max(0.0, time_cost)
                candidates.append(cand)

        # Adayları etkiye göre sırala
        candidates.sort(key=lambda x: x['calculated_impact'], reverse=True)

        # Nihai önerileri seç
        final_recs = []
        seen_cats = set()
        seen_features = set()  # YENİ: Hangi özelliklere dokunduk?
        total_time_spent = 0.0
        MAX_EXTRA_HOURS = 3.5

        for c in candidates:
            cat = c.get('category', 'General')
            feat = c['simulation']['feature']  # YENİ

            # AYNI ÖZELLİĞİ (örn: extracurricular) İKİ KERE ÖNERME!
            if feat in seen_features: continue

            # Kategori limiti (Eskisi gibi)
            if cat in seen_cats and len(final_recs) < max_recs - 1: continue

            # Zaman bütçesi
            if total_time_spent + c['time_cost'] > MAX_EXTRA_HOURS: continue

            final_recs.append(c)
            seen_cats.add(cat)
            seen_features.add(feat)  # YENİ
            total_time_spent += c['time_cost']

            if len(final_recs) >= max_recs: break

        # Nihai sıralama
        final_recs.sort(key=lambda x: x['calculated_impact'], reverse=True)

        # --- KRİTİK KONTROL 3: PUAN SÖNÜMLEME (Damping) ---
        # Akıllı simülasyon ile gerçekçi puanı hesapla
        simulation_result = self.predict_future_potential(student_data, final_recs)
        raw_future_score = simulation_result['future_score']

        # Artış miktarını hesapla
        uplift = raw_future_score - current_score

        # Damping: Artışın sadece %70'ini yansıt (Gerçekçilik için)
        # Eğer çok büyük bir artış varsa (%20 üstü), daha da sönümle.
        damping_factor = 0.70
        if uplift > 15: damping_factor = 0.60

        real_uplift = uplift * damping_factor
        potential_score = current_score + real_uplift

        # Tavana takılmasın (Max 100)
        potential_score = min(100.0, potential_score)

        return {
            "student_id": student_data.get("student_id", "Unknown"),
            "current_score": round(current_score, 2),
            "potential_score": round(potential_score, 2),
            "recommendations": final_recs,
            "root_causes": root_causes[:3],
            "total_opportunities": len(candidates),
            "time_budget_used": total_time_spent
        }


# =============================================================================
# GÖRSELLEŞTİRME & SUNUM
# =============================================================================
def generate_presentation_artifacts(advisor_obj, student_row, result_dict):
    print("\n📢 SUNUM MODU: AKADEMİK ÇIKTILAR OLUŞTURULUYOR...")
    output_dir = "sunum_cikti"
    if not os.path.exists(output_dir): os.mkdir(output_dir)
    sns.set_theme(style="whitegrid")

    # --- GRAFİK 1: STRATEJİ HARİTASI (HEATMAP) ---
    try:
        plt.figure(figsize=(10, 8))

        # --- DİNAMİK EKSEN AYARLAMASI ---
        # Öğrencinin mevcut değerlerini al
        curr_study = student_row.get('study_hours_per_day', 0)
        curr_sleep = student_row.get('sleep_hours', 0)

        # Eksen sınırlarını öğrenciye göre esnet (Out of bounds hatasını önler)
        # Ders: En az 8 saat göster, ama öğrenci 9 saat çalışıyorsa 11'e kadar uzat.
        max_study_limit = max(8.0, curr_study + 2.0)

        # Uyku: En az 4-10 arasını göster, ama öğrenci dışındaysa genişlet.
        min_sleep_limit = max(0.0, min(4.0, curr_sleep - 1.0))
        max_sleep_limit = max(10.0, curr_sleep + 1.0)

        # Dinamik aralıkları oluştur
        study_range = np.linspace(0, max_study_limit, 30)
        sleep_range = np.linspace(min_sleep_limit, max_sleep_limit, 30)

        Z = np.zeros((len(sleep_range), len(study_range)))
        base_copy = student_row.copy()

        # Isı haritası hesaplama
        for i, slp in enumerate(sleep_range):
            for j, std in enumerate(study_range):
                temp_raw = base_copy.copy()
                temp_raw['study_hours_per_day'] = std
                temp_raw['sleep_hours'] = slp
                temp_enriched = advisor_obj._calculate_derived(temp_raw)
                Z[i, j] = advisor_obj.predict(temp_enriched)

        # Çizim
        cp = plt.contourf(study_range, sleep_range, Z, levels=20, cmap='viridis')
        plt.colorbar(cp).set_label('Tahmini Puan', rotation=270, labelpad=15)

        # Mevcut durumu işaretle
        plt.scatter([curr_study], [curr_sleep], color='red', s=150, edgecolors='white', linewidth=2,
                    label='Mevcut Konum', zorder=5)

        # Hedeflenen (Potansiyel) durumu işaretle (Opsiyonel ama şık olur)
        # Önerilerden sonraki tahmini yeni konum (Basit bir kestirim)
        if result_dict.get('total_time_cost', 0) > 0 or result_dict.get('recommendations'):
            # Bu tam doğru olmayabilir çünkü simülasyon karmaşık, ama görsel olarak hedef göstermek iyidir.
            pass

        plt.title(f"Başarı Isı Haritası: {student_row.get('student_id', 'Öğrenci')}", fontsize=14)
        plt.xlabel("Günlük Ders Çalışma (Saat)")
        plt.ylabel("Günlük Uyku (Saat)")
        plt.legend(loc='upper right')

        save_path = f"{output_dir}/1_strateji_haritasi_heatmap.png"
        plt.savefig(save_path)
        print(f"✅ [1/4] Strateji Haritası oluşturuldu: {save_path}")

    except Exception as e:
        print(f"❌ Grafik 1 Hatası: {e}")


def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')


def draw_progress_bar(val, max_val=100, length=30, label=""):
    val = max(0, min(max_val, val))
    filled = int(length * (val / max_val))
    bar = "█" * filled + "░" * (length - filled)
    print(f"{label.ljust(15)}: [{bar}] {val:.1f}/100")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    clear_screen()
    advisor = SmartAdvisor()

    csv_paths = ['student_habits_performance.csv', 'data/student_habits_performance.csv',
                 'D:\Ensar Dosya\OgrenciOneriSistemi\data\student_habits_performance.csv']
    csv_path = next((p for p in csv_paths if os.path.exists(p)), None)
    df_real = pd.read_csv(csv_path) if csv_path else None

    if df_real is not None:
        print(f"📂 Veri Seti Aktif: {len(df_real)} öğrenci.")
    else:
        print("⚠️ Demo Modu (CSV Yok).")

    while True:
        print("\n" + "═" * 60)
        print("🎓 NEXT-GEN AI ÖĞRENCİ KOÇU (Çıkış: q)")
        print("═" * 60)

        s_data = None
        if df_real is not None:
            inp = input("\n🔍 Öğrenci ID (Boş=Rastgele): ").strip()
            if inp.lower() == 'q': break
            if inp:
                # String veya Int dönüşümünü güvenli yap
                try:
                    if df_real['student_id'].dtype == 'int64':
                        s_id = int(inp)
                        rec = df_real[df_real['student_id'] == s_id]
                    else:
                        rec = df_real[df_real['student_id'] == inp]
                except:
                    rec = df_real[df_real['student_id'] == inp]

                s_data = rec.iloc[0].to_dict() if not rec.empty else None
                if not s_data: print("❌ Bulunamadı."); continue
            else:
                s_data = df_real.sample(1).iloc[0].to_dict()
        else:
            if input("Demo (q=Çıkış): ").lower() == 'q': break
            s_data = {'student_id': 'S_DEMO', 'age': 20, 'gender': 'Male', 'study_hours_per_day': 1.5,
                      'social_media_hours': 4.0, 'netflix_hours': 2.0, 'attendance_percentage': 70.0,
                      'sleep_hours': 5.5, 'diet_quality': 'Poor', 'mental_health_rating': 4,
                      'internet_quality': 'Average', 'parental_education_level': 'High School', 'exercise_frequency': 0,
                      'part_time_job': 'No', 'extracurricular_participation': 'No', 'exam_score': 45.0}

        real_score = s_data.get('exam_score')
        analysis_data = s_data.copy()
        if 'exam_score' in analysis_data: del analysis_data['exam_score']

        result = advisor.generate_advice(analysis_data)
        clear_screen()

        print("\n" + "═" * 60)
        print(f"📋 ANALİZ RAPORU: {s_data.get('student_id')}")
        print("═" * 60)
        print(f"👤 {int(s_data.get('age', 0))} Yaş | {s_data.get('gender')} | Aile: {s_data.get('parental_education_level')}")
        print(
            f"⏳ {s_data.get('study_hours_per_day')}s Ders | {s_data.get('sleep_hours')}s Uyku | %{s_data.get('attendance_percentage')} Katılım")
        print("-" * 60)

        if result.get('root_causes'):
            print("📉 PERFORMANSI DÜŞÜREN GİZLİ FAKTÖRLER (X-RAY)")
            for rc in result['root_causes']:
                if rc['impact'] < 0:
                    clean_feat = rc['feature'].replace('_', ' ').title()
                    print(f"   ⚠️  {clean_feat.ljust(25)} : {rc['impact']:.2f} Puan Kaybı")
            print("-" * 60)

        curr_score = result['current_score']
        pot_score = result['potential_score']
        uplift = pot_score - curr_score

        print("📊 PERFORMANS DURUMU")
        if real_score: draw_progress_bar(real_score, label="GERÇEK NOT")
        draw_progress_bar(curr_score, label="MEVCUT TAHMİN")
        draw_progress_bar(pot_score, label="POTANSİYEL")
        print(f"\n🚀 TOPLAM KAZANIM FIRSATI: +{uplift:.2f} PUAN")
        print(f"⏱️ Gerekli Ekstra Zaman : {result['time_budget_used']:.1f} Saat/Gün")
        print("=" * 60)

        print("\n💡 AKILLI REÇETE")
        for i, rec in enumerate(result['recommendations'], 1):
            cat = rec.get('category', 'GENEL')
            imp = rec['calculated_impact']

            # YENİ: Görsel Düzeltme
            impact_str = f"+{imp:.2f}"
            if imp > 50:
                impact_str = "KRİTİK/ZORUNLU"

            sim = rec['simulation']
            target_val = sim['value']
            current_val = s_data.get(sim['feature'], 0)

            if sim['operation'] == 'add':
                target_val = current_val + sim['value']
            elif sim['operation'] == 'multiply':
                target_val = current_val * sim['value']

            icon = {"Academic": "📚", "Wellness": "🧘", "Discipline": "⏳", "Social": "🤝", "Efficiency": "⚡"}.get(cat, "💡")
            print(f"\n{i}. {icon} {cat.upper()} ({impact_str})") # Değişti
            print(f"   \"{rec['text']}\"")

            feat_name = sim['feature'].replace('_', ' ').title()
            val_fmt = f"{target_val:.1f}" if isinstance(target_val, (int, float)) else str(target_val)
            print(f"   👉 Hedef: {feat_name} -> {val_fmt}")

        sunum_istek = input("\n📊 Sunum için grafikleri oluşturayım mı? (e/h): ").lower()
        if sunum_istek == 'e':
            generate_presentation_artifacts(advisor, s_data, result)

        print("\n" + "-" * 60)
        print("🎯 PAZARLIK MODU (COUNTERFACTUAL ANALYSIS)")
        print("-" * 60)
        pazarlik = input("💰 Hedeflediğin bir puan var mı? (e/h): ").lower()

        if pazarlik == 'e':
            # --- DÜZELTME 1: GİRDİ HATASINI AYRI YAKALA ---
            target_input = 0.0
            valid_input = False
            try:
                target_input_str = input(f"   Hedef Puanın (Mevcut: {curr_score:.1f}): ")
                target_input = float(target_input_str)
                valid_input = True
            except ValueError:
                print("   ❌ HATA: Lütfen geçerli bir sayı girin (Örn: 85 veya 85.5).")

            if valid_input:
                # Klasör kontrolü
                output_dir = "outputs"
                os.makedirs(output_dir, exist_ok=True)
                json_path = os.path.join(output_dir, "pazarlik_sonucu.json")

                if target_input <= curr_score:
                    print("   ⚠️ Zaten bu puanın üzerindesin! Daha yüksek hedefle.")
                elif target_input > 100:
                    print("   ⚠️ Hocam 100'den büyük not yok, 100 diyelim.")
                    target_input = 100.0
                else:
                    # --- YENİ EKLENEN: KISITLAMA SEÇİM MENÜSÜ ---
                    print("\n🔒 Kısıtlamalar (Vazgeçmek istemediğin şeyler):")
                    print("1. Netflix'i Elleme (Sabit Kalsın)")
                    print("2. Sosyal Medyayı Elleme (Sabit Kalsın)")
                    print("3. Uykumu Elleme (Sabit Kalsın)")
                    print("4. Yok, her şeyi değiştirebilirsin (Serbest Mod)")

                    kist_secim = input("Seçim (1-4): ").strip()
                    frozen = []
                    if kist_secim == '1':
                        frozen = ['netflix_hours']
                    elif kist_secim == '2':
                        frozen = ['social_media_hours']
                    elif kist_secim == '3':
                        frozen = ['sleep_hours']

                    print(f"\n🧬 Genetik Algoritma Hazırlanıyor... (Kilitli: {frozen})")

                    # --- DÜZELTME 2: ALGORİTMA HATASINI GÖRMEK İÇİN GENEL CATCH ---
                    try:
                        # Optimizer'ı başlat
                        opt = AcademicOptimizer(advisor)

                        # Optimizer çağrısı
                        plan = opt.find_optimal_path(s_data, target_input, frozen_features=frozen)

                        if plan.get("status") == "Success":
                            achieved = plan['achieved_score']
                            print(f"\n✅ ÇÖZÜM BULUNDU! ({achieved:.2f} Puan)")

                            # 1. Değişiklikleri Listele
                            changes_list = []
                            changes_text_for_mentor = "Öğrenciye şunları yapmasını şart koş: "

                            print("   Yapman gereken minimum değişiklikler:")
                            for item in plan['changes']:
                                print(f"   👉 {item['text']}")
                                changes_list.append(item['text'])
                                feat_clean = item['feature'].replace('_', ' ').title()
                                changes_text_for_mentor += f"{feat_clean} değerini {item['new']} yap. "

                            # 2. LLM Mentörden Mektup Al
                            print("\n🧠 Mentör Mektubu Yazılıyor...")

                            # Mentor modülü hatasız çağrılıyor mu?
                            try:
                                mentor_note = mentor.generate_mentor_advice(
                                    student_name=s_data.get('student_id', 'Öğrenci'),
                                    predicted_score=achieved,
                                    sleep_hours=plan['optimized_data'].get('sleep_hours', 0),
                                    is_zombie=plan['optimized_data'].get('sleep_hours', 0) < 6.0,
                                    top_suggestion=changes_text_for_mentor
                                )
                                print(f"📝 Mentör: {mentor_note}")
                            except Exception as m_err:
                                print(f"⚠️ Mentör servisinde hata: {m_err}")
                                mentor_note = "Mentör şu an meşgul."

                            # 3. ASP.NET İçin JSON Kaydet
                            output_data = {
                                "status": "success",
                                "target_score": target_input,
                                "achieved_score": achieved,
                                "original_score": curr_score,
                                "required_changes": changes_list,
                                "mentor_message": mentor_note,
                                "optimized_values": plan['optimized_data']
                            }

                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump(output_data, f, ensure_ascii=False, indent=4)

                            print(f"\n💾 Sonuçlar kaydedildi: {json_path}")

                        else:
                            print(f"\n❌ Algoritma Çözüm Bulamadı: {plan.get('msg')}")
                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump({"status": "fail", "message": plan.get("msg")}, f)

                    except Exception as e:
                        # BURASI GERÇEK HATAYI GÖSTERECEK
                        print(f"\n❌ KRİTİK ALGORİTMA HATASI: {e}")
                        print("🔍 Hata Detayı:")
                        import traceback

                        traceback.print_exc()



        print("\n" + "-" * 60)
        while True:
            choice = input("\n🧪 Sandbox: Değer değiştirip denemek ister misin? (e/h): ").lower()
            if choice != 'e': break

            feats = ['study_hours_per_day', 'sleep_hours', 'social_media_hours', 'attendance_percentage',
                     'mental_health_rating']
            for idx, f in enumerate(feats, 1):
                print(f"{idx}. {f} ({s_data.get(f)})")

            try:
                f_idx = int(input("Seçim: ")) - 1
                val = float(input("Yeni Değer: "))
                temp = analysis_data.copy()
                temp[feats[f_idx]] = val
                new_p = advisor.predict(temp)
                print(f"\n🔄 Sonuç: {curr_score:.2f} -> {new_p:.2f} (Fark: {new_p - curr_score:+.2f})")
            except:
                print("❌ Geçersiz seçim veya değer.")

        print("\nDevam etmek için ENTER...")
        input()
        clear_screen()