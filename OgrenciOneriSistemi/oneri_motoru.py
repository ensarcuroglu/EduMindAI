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

# --- SHAP Kütüphanesi Kontrolü ---
try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️ UYARI: 'shap' kütüphanesi bulunamadı. Kök neden analizi devre dışı.")
    print("   Yüklemek için: pip install shap")


# =============================================================================
# 1. FeatureEngineer SINIFI (Model Entegrasyonu İçin Zorunlu)
# =============================================================================
class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self): pass

    def fit(self, X, y=None): return self

    def transform(self, X, y=None):
        X_ = X.copy()
        # Model eğitimiyle birebir aynı türetilmiş özellikler
        X_['total_distraction_hours'] = X_['social_media_hours'] + X_['netflix_hours']
        X_['focus_ratio'] = X_['study_hours_per_day'] / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = X_['sleep_hours'] / (X_['study_hours_per_day'] + 1)
        X_['study_efficiency'] = X_['study_hours_per_day'] * X_['mental_health_rating']
        X_['academic_engagement'] = X_['attendance_percentage'] * X_['study_hours_per_day']
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])
        return X_


# =============================================================================
# 2. KATALOG YÜKLEME
# =============================================================================
try:
    from oneriler import RECOMMENDATION_CATALOG
except ImportError:
    RECOMMENDATION_CATALOG = []
    print("UYARI: oneriler.py bulunamadı! Simülasyon yapılamayabilir.")


# =============================================================================
# 3. AKILLI DANIŞMAN (SmartAdvisor Ultimate)
# =============================================================================
class SmartAdvisor:
    def __init__(self, model_path: str = "artifacts/student_score_xgb_pipeline.joblib"):
        self.catalog = RECOMMENDATION_CATALOG
        self.model = None
        self.explainer = None

        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                print(f"✅ [SmartAdvisor] YZ Modeli Hazır: {model_path}")

                # SHAP Explainer Hazırlığı
                if SHAP_AVAILABLE:
                    try:
                        # Model Pipeline ise son aşamayı (XGBoost) al
                        self.regressor = self.model[-1]
                        # Ön işlem adımlarını al
                        self.preprocessor = self.model[:-1]
                        # TreeExplainer başlat
                        self.explainer = shap.TreeExplainer(self.regressor)
                    except Exception as e:
                        print(f"⚠️ SHAP Başlatılamadı: {e}")
            except Exception as e:
                print(f"❌ Model Hatası: {e}")
        else:
            print(f"⚠️ Model Dosyası Yok: {model_path}")

    def _calculate_derived(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Türetilmiş özellikleri anlık hesaplar."""
        d = row.copy()
        d['total_distraction_hours'] = d.get('social_media_hours', 0) + d.get('netflix_hours', 0)
        d['focus_ratio'] = d.get('study_hours_per_day', 0) / (d['total_distraction_hours'] + 1)
        d['lifestyle_balance'] = d.get('sleep_hours', 0) / (d.get('study_hours_per_day', 0) + 1)
        return d

    def predict(self, data: Dict[str, Any]) -> float:
        """Tekil tahmin yapar."""
        if not self.model: return 0.0
        try:
            return float(self.model.predict(pd.DataFrame([data]))[0])
        except:
            return 0.0

    def analyze_root_cause(self, student_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """SHAP kullanarak puanı düşüren ana faktörleri bulur."""
        if not self.explainer: return []
        try:
            # 1. Veriyi modele uygun hale getir
            df = pd.DataFrame([student_data])
            X_transformed = self.preprocessor.transform(df)

            # 2. SHAP hesapla
            shap_values = self.explainer.shap_values(X_transformed)

            # 3. Özellik isimlerini DOĞRU yerden al (GÜNCELLENEN KISIM)
            feature_names = []
            try:
                # Pipeline içindeki 'preprocessor' adlı adıma ulaşmaya çalış
                # self.model bir Pipeline ise steps veya named_steps özelliğine sahiptir
                if hasattr(self.model, 'named_steps'):
                    preprocessor_step = self.model.named_steps['preprocessor']
                    feature_names = preprocessor_step.get_feature_names_out()
                else:
                    # Model bir liste ise (manuel pipeline)
                    # Genellikle [FeatureEngineer, ColumnTransformer, XGBoost] sırasındadır
                    # Ortadaki (index 1) genellikle preprocessor'dır.
                    preprocessor_step = self.model[1]
                    feature_names = preprocessor_step.get_feature_names_out()
            except Exception as e:
                # İsimler alınamazsa SHAP'in kendi feature feature isimlerine güvenmeyip manuel fallback yapıyoruz
                # Ancak burada feature sayısı tutmayabilir, o yüzden Feature X dönüyordu.
                print(f"İsimlendirme Hatası: {e}")
                feature_names = [f"Feature {i}" for i in range(X_transformed.shape[1])]

            contributions = []
            # SHAP değerleri bazen (1, N) bazen (N,) döner, onu düzeltelim
            values = shap_values[0] if len(shap_values.shape) > 1 else shap_values

            for name, value in zip(feature_names, values):
                # Sklearn çıktısı genelde "num__study_hours" şeklindedir, temizleyelim
                clean_name = name.split("__")[-1]
                contributions.append({"feature": clean_name, "impact": float(value)})

            # En negatif etki yapanları sırala
            contributions.sort(key=lambda x: x['impact'])
            return contributions
        except Exception as e:
            print(f"SHAP Analiz Hatası: {e}")
            return []

    def apply_simulation(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Tekil simülasyon."""
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

            # Sınırlar
            if "hours" in feat: sim[feat] = max(0.0, min(24.0, sim[feat]))
            if "percentage" in feat: sim[feat] = min(100.0, max(0.0, sim[feat]))
            if "rating" in feat: sim[feat] = min(10, max(1, sim[feat]))

        elif isinstance(val, str) and op == "set":
            sim[feat] = val

        return sim

    def find_sweet_spot(self, student_data: Dict[str, Any], feature: str, min_change=0.5, max_change=2.5, step=0.5) -> \
    Dict[str, Any]:
        """En verimli artış miktarını (Sweet Spot) bulur."""
        best_uplift = 0
        best_val = 0
        original_score = self.predict(student_data)

        for change in np.arange(min_change, max_change + step, step):
            sim_config = {"feature": feature, "operation": "add", "value": float(change)}
            sim_data = self.apply_simulation(student_data, sim_config)

            if feature == "study_hours_per_day" and sim_data[feature] > 14: continue

            new_score = self.predict(sim_data)
            uplift = new_score - original_score

            if uplift > best_uplift:
                best_uplift = uplift
                best_val = float(change)

        return {"best_change": best_val, "max_uplift": best_uplift}

    def format_advice_text(self, text: str, student_data: Dict[str, Any], sim_config: Dict[str, Any]) -> str:
        feature = sim_config.get('feature')
        current_val = student_data.get(feature, 0)
        if isinstance(current_val, (int, float)):
            return f"{text} (Şu an: {current_val:.1f})"
        return text

    def calculate_cumulative_impact(self, student_data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> float:
        """Kümülatif etkiyi hesaplar ve gerçekçilik (dampening) uygular."""
        sim_data = student_data.copy()
        for rec in recommendations:
            sim_config = rec.get('simulation', {})
            if sim_config:
                sim_data = self.apply_simulation(sim_data, sim_config)

        raw_final = self.predict(sim_data)
        current = self.predict(student_data)
        uplift = raw_final - current

        # --- PUAN TÖRPÜLEME (DAMPENING) ---
        # 15 puandan fazla artışları gerçekçi kılmak için baskıla
        if uplift > 15:
            uplift = 15 + (uplift - 15) * 0.6

        final_score = min(99.9, current + uplift)
        return final_score

    def generate_advice(self, student_data: Dict[str, Any], max_recs: int = 4) -> Dict[str, Any]:
        enriched = self._calculate_derived(student_data)
        current_score = self.predict(student_data)
        root_causes = self.analyze_root_cause(student_data)

        candidates = []
        for item in self.catalog:
            try:
                if item.get("condition") and not eval(item.get("condition"), {}, enriched): continue
            except:
                continue

            sim_config = item.get("simulation", {}).copy()
            impact = 0.5
            original_text = item.get("text", "")

            # --- OPTİMİZASYON (SWEET SPOT) ---
            if self.model and sim_config.get('operation') == 'add' and 'hours' in sim_config.get('feature', ''):
                opt = self.find_sweet_spot(student_data, sim_config['feature'])
                if opt['max_uplift'] > 0:
                    sim_config['value'] = opt['best_change']
                    impact = opt['max_uplift']
                    original_text = f"🎯 **Optimize Edildi:** Standart yerine +{opt['best_change']} saatlik artış en verimlisi. \n   🗣️  {original_text}"

            # --- STANDART SİMÜLASYON ---
            elif self.model and sim_config:
                sim_data = self.apply_simulation(student_data, sim_config)
                impact = self.predict(sim_data) - current_score

            if impact > 0.05:
                cand = item.copy()
                cand['calculated_impact'] = impact
                cand['simulation'] = sim_config
                cand['text'] = self.format_advice_text(original_text, student_data, sim_config)

                # Zaman Maliyeti Hesapla (Time Cost)
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

                cand['time_cost'] = time_cost
                candidates.append(cand)

        candidates.sort(key=lambda x: x['calculated_impact'], reverse=True)

        # --- AKILLI SEÇİM (DIVERSITY & TIME BUDGET) ---
        final_recs = []
        seen_cats = set()
        total_time_spent = 0.0
        MAX_EXTRA_HOURS = 3.5  # Günde en fazla 3.5 saat yeni yük

        for c in candidates:
            cat = c.get('category', 'General')

            # 1. Çeşitlilik: Aynı kategoriden çok fazla öneri alma
            if cat in seen_cats and len(final_recs) < max_recs - 1: continue

            # 2. Zaman Bütçesi: Gün 24 saattir, aşma
            if total_time_spent + c['time_cost'] > MAX_EXTRA_HOURS: continue

            final_recs.append(c)
            seen_cats.add(cat)
            total_time_spent += c['time_cost']

            if len(final_recs) >= max_recs: break

        # Tekrar puana göre sırala
        final_recs.sort(key=lambda x: x['calculated_impact'], reverse=True)

        potential_score = self.calculate_cumulative_impact(student_data, final_recs)

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
# 4. YARDIMCI GÖRSELLEŞTİRME
# =============================================================================
def draw_progress_bar(val, max_val=100, length=30, label=""):
    val = max(0, min(max_val, val))  # Sınırla
    normalized = val / max_val
    filled = int(length * normalized)
    bar = "█" * filled + "░" * (length - filled)
    print(f"{label.ljust(15)}: [{bar}] {val:.1f}/100")


# =============================================================================
# 6. SUNUM VE RAPORLAMA MODÜLÜ (PRESENTATION LAYER)
# =============================================================================
def generate_presentation_artifacts(advisor_obj, student_row, result_dict):
    """
    Sunum için görsel grafikler ve detaylı analiz raporu üretir.
    """
    print("\n" + "█" * 60)
    print("📢 SUNUM MODU: AKADEMİK ÇIKTILAR OLUŞTURULUYOR...")
    print("█" * 60)

    # Klasör kontrolü
    output_dir = "sunum_cikti"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    sns.set_theme(style="whitegrid")

    # -------------------------------------------------------------------------
    # GRAFİK 1: ÇOKLU DEĞİŞKEN ANALİZİ (STRATEJİ HARİTASI / HEATMAP)
    # AMACI: Hocaya modelin "Sadece çalış demiyor, uyku-çalışma dengesini kuruyor" dedirtmek.
    # -------------------------------------------------------------------------
    try:
        plt.figure(figsize=(10, 8))

        # Grid Hazırlığı (Ders Çalışma vs Uyku Süresi)
        study_range = np.linspace(0, 8, 30)  # 0-8 saat ders
        sleep_range = np.linspace(4, 10, 30)  # 4-10 saat uyku
        Z = np.zeros((len(sleep_range), len(study_range)))

        base_copy = student_row.copy()

        # Her piksel için tahmin yap
        for i, slp in enumerate(sleep_range):
            for j, std in enumerate(study_range):
                temp = advisor_obj._calculate_derived(base_copy)
                temp['study_hours_per_day'] = std
                temp['sleep_hours'] = slp
                # Türetilmişleri güncelle (Önemli!)
                temp['lifestyle_balance'] = slp / (std + 1)
                temp['academic_engagement'] = temp['attendance_percentage'] * std
                Z[i, j] = advisor_obj.predict(temp)

        # Kontur Grafiği (Contourf)
        cp = plt.contourf(study_range, sleep_range, Z, levels=20, cmap='viridis')
        cbar = plt.colorbar(cp)
        cbar.set_label('Tahmini Sınav Puanı', rotation=270, labelpad=15)

        # Öğrencinin şu anki konumu
        curr_study = base_copy.get('study_hours_per_day', 0)
        curr_sleep = base_copy.get('sleep_hours', 0)
        plt.scatter([curr_study], [curr_sleep], color='red', s=150, edgecolors='white', linewidth=2,
                    label='Öğrenci Mevcut Konum', zorder=10)

        plt.title(f"Model Karar Uzayı: Uyku ve Çalışma Dengesi\n(Non-Lineer Etkileşim Analizi)", fontsize=14,
                  fontweight='bold')
        plt.xlabel("Günlük Çalışma Saati")
        plt.ylabel("Günlük Uyku Saati")
        plt.legend(loc='lower right')
        plt.grid(False)  # Heatmap üzerinde grid karmaşık görünür

        plt.savefig(f"{output_dir}/1_strateji_haritasi_heatmap.png")
        print(f"✅ [1/4] Strateji Haritası (Heatmap) kaydedildi. (Modelin karmaşık mantığını gösterir)")
    except Exception as e:
        print(f"❌ Grafik 1 Hatası: {e}")

    # -------------------------------------------------------------------------
    # GRAFİK 2: OPTİMİZASYON EĞRİSİ (SWEET SPOT)
    # AMACI: "Azalan Verim Yasası"nı (Diminishing Returns) modellediğimizi göstermek.
    # -------------------------------------------------------------------------
    try:
        plt.figure(figsize=(10, 6))
        x_range = np.linspace(0, 12, 50)
        y_preds = []

        base_data = student_row.copy()

        for hours in x_range:
            temp = advisor_obj._calculate_derived(base_data)
            temp['study_hours_per_day'] = hours
            # Türetilmiş özellik güncellemeleri
            temp['focus_ratio'] = hours / (temp['total_distraction_hours'] + 1)
            temp['lifestyle_balance'] = temp['sleep_hours'] / (hours + 1)
            y_preds.append(advisor_obj.predict(temp))

        # Eğriyi çiz
        plt.plot(x_range, y_preds, color='#2980b9', linewidth=3, label='Performans Eğrisi')

        # Zirve Noktayı Bul (Max Puan)
        max_y = max(y_preds)
        max_x = x_range[y_preds.index(max_y)]

        plt.axvline(max_x, color='green', linestyle='--', alpha=0.6, label=f'Optimal Nokta ({max_x:.1f}s)')

        # Mevcut Durum
        curr_val = advisor_obj.predict(base_data)
        curr_x = base_data.get('study_hours_per_day', 0)
        plt.scatter([curr_x], [curr_val], color='red', s=100, zorder=5, label='Şu An')

        plt.title(f"Tek Değişken Duyarlılık Analizi: Çalışma Saati\n(Verim Kaybı Noktası Tespiti)", fontsize=14)
        plt.xlabel("Çalışma Saati")
        plt.ylabel("Tahmini Puan")
        plt.legend()
        plt.savefig(f"{output_dir}/2_diminishing_returns.png")
        print(f"✅ [2/4] Optimizasyon Eğrisi kaydedildi.")
    except Exception as e:
        print(f"❌ Grafik 2 Hatası: {e}")

    # -------------------------------------------------------------------------
    # GRAFİK 3: KÖK NEDEN ANALİZİ (SHAP WATERFALL BENZERİ)
    # AMACI: Modelin "Explainable AI (XAI)" yeteneğini kanıtlamak.
    # -------------------------------------------------------------------------
    if result_dict.get('root_causes'):
        try:
            plt.figure(figsize=(10, 6))
            causes = result_dict['root_causes']

            # Veri hazırlığı
            feats = [x['feature'] for x in causes]
            impacts = [x['impact'] for x in causes]

            # Renklendirme (Negatifler Kırmızı, Pozitifler Yeşil)
            colors = ['#e74c3c' if x < 0 else '#2ecc71' for x in impacts]

            sns.barplot(x=impacts, y=feats, palette=colors)

            plt.title("X-RAY Analizi: SHAP Değerleri ile Kök Nedenler", fontsize=14)
            plt.xlabel("Puan Üzerindeki Etki (+/-)")
            plt.axvline(0, color='black', linewidth=0.8)

            # Barların ucuna değer yaz
            for i, v in enumerate(impacts):
                offset = 1 if v >= 0 else -1
                plt.text(v, i, f"{v:.2f}", va='center', fontsize=10, fontweight='bold')

            plt.tight_layout()
            plt.savefig(f"{output_dir}/3_xai_explainability.png")
            print(f"✅ [3/4] XAI (SHAP) Analizi kaydedildi.")
        except Exception as e:
            print(f"❌ Grafik 3 Hatası: {e}")

    # -------------------------------------------------------------------------
    # 4. METİNSEL RAPOR (TXT ÇIKTISI)
    # AMACI: Bir danışman gibi çıktı üretebildiğimizi göstermek.
    # -------------------------------------------------------------------------
    try:
        report_path = f"{output_dir}/ogrenci_raporu_{student_row.get('student_id')}.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"OTOMATİK OLUŞTURULAN PERFORMANS RAPORU\n")
            f.write(f"Tarih: {time.strftime('%d.%m.%Y %H:%M')}\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"1. MEVCUT DURUM\n")
            f.write(f"- Mevcut Tahmin: {result_dict['current_score']:.2f}\n")
            f.write(f"- Potansiyel: {result_dict['potential_score']:.2f}\n")
            f.write(f"- Kazanım Fırsatı: +{result_dict['potential_score'] - result_dict['current_score']:.2f}\n\n")

            f.write(f"2. TESPİT EDİLEN KÖK NEDENLER (XAI)\n")
            for rc in result_dict.get('root_causes', []):
                f.write(f"* {rc['feature']}: {rc['impact']:.2f} puan etkisi var.\n")

            f.write(f"\n3. YAPAY ZEKA ÖNERİLERİ\n")
            for rec in result_dict['recommendations']:
                f.write(f"* [{rec.get('category')}] {rec['text']} (Beklenen Artış: +{rec['calculated_impact']:.2f})\n")

        print(f"✅ [4/4] Detaylı metin raporu kaydedildi: {report_path}")
    except Exception as e:
        print(f"❌ Rapor Yazma Hatası: {e}")

    print("\n📂 TÜM DOSYALAR 'sunum_cikti' KLASÖRÜNDE HAZIR.")
    print("   Hocaya özellikle '1_strateji_haritasi_heatmap.png' dosyasını gösteriniz.")




def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')


# =============================================================================
# 5. ANA UYGULAMA BLOĞU (MAIN)
# =============================================================================
if __name__ == "__main__":
    clear_screen()
    advisor = SmartAdvisor()

    csv_paths = ['student_habits_performance.csv', 'data/student_habits_performance.csv']
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

        # --- RAPOR EKRANI ---
        print("\n" + "═" * 60)
        print(f"📋 ANALİZ RAPORU: {s_data.get('student_id')}")
        print("═" * 60)
        print(f"👤 {int(s_data.get('age', 0))} Yaş | {s_data.get('gender')} | {s_data.get('parental_education_level')}")
        print(
            f"⏳ {s_data.get('study_hours_per_day')}s Ders | {s_data.get('sleep_hours')}s Uyku | %{s_data.get('attendance_percentage')} Devamsızlık")
        print("-" * 60)

        # KÖK NEDENLER (SHAP)
        if result.get('root_causes'):
            print("📉 PERFORMANSI DÜŞÜREN GİZLİ FAKTÖRLER (X-RAY)")
            for rc in result['root_causes']:
                if rc['impact'] < 0:
                    print(f"   ⚠️  {rc['feature'].ljust(20)} : {rc['impact']:.2f} Puan Kaybı")
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
            icon = {"Academic": "📚", "Wellness": "🧘", "Discipline": "⏳", "Social": "🤝", "Efficiency": "⚡"}.get(cat, "💡")
            print(f"\n{i}. {icon} {cat.upper()} (+{imp:.2f})")
            print(f"   \"{rec['text']}\"")
            sim = rec['simulation']
            print(f"   👉 Hedef: {sim['feature']} -> {sim['value']}")

        # --- SUNUM İSTEĞİ (DÖNGÜ DIŞINA ALINDI) ---
        sunum_istek = input("\n📊 Sunum için grafikleri oluşturayım mı? (e/h): ").lower()
        if sunum_istek == 'e':
            generate_presentation_artifacts(advisor, s_data, result)


        print("\n" + "-" * 60)
        while True:
            choice = input("\n🧪 Sandbox: Değer değiştirip denemek ister misin? (e/h): ").lower()
            if choice != 'e': break
            feats = ['study_hours_per_day', 'sleep_hours', 'social_media_hours', 'attendance_percentage',
                     'mental_health_rating']
            for idx, f in enumerate(feats, 1): print(f"{idx}. {f} ({s_data.get(f)})")
            try:
                f_idx = int(input("Seçim: ")) - 1
                val = float(input("Yeni Değer: "))
                temp = analysis_data.copy()
                temp[feats[f_idx]] = val
                new_p = advisor.predict(temp)
                print(f"\n🔄 Sonuç: {curr_score:.2f} -> {new_p:.2f} (Fark: {new_p - curr_score:+.2f})")
            except:
                print("❌ Geçersiz.")

        print("\nDevam etmek için ENTER...")
        input()
        clear_screen()


