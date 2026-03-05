import pandas as pd
import sys
import os
import joblib

# Mevcut dizini yola ekle
sys.path.append(os.getcwd())

# --- KRİTİK DÜZELTME BAŞLANGICI ---
# Model yüklenirken "FeatureEngineer" ve "OutlierCapper" sınıflarını
# __main__ modülünde bulmak istiyor. Onları oneri_motoru_V2'den çekip
# buraya (main scope'a) manuel olarak tanıtıyoruz.

try:
    from oneri_motoru_V2 import SmartAdvisor, FeatureEngineer, OutlierCapper
    from optimizer import AcademicOptimizer

    # Joblib'i kandırmak için sınıfları main namespace'e atıyoruz
    import __main__

    __main__.FeatureEngineer = FeatureEngineer
    __main__.OutlierCapper = OutlierCapper

except ImportError as e:
    print(f"❌ HATA: Modüller yüklenemedi: {e}")
    print("Lütfen 'oneri_motoru_V2.py' ve 'optimizer.py' dosyalarının aynı klasörde olduğundan emin olun.")
    sys.exit()


# --- KRİTİK DÜZELTME BİTİŞİ ---

def generate_real_negotiation_table():
    print("🚀 Pazarlık Modu (Counterfactual) Gerçek Veri Testi Başlatılıyor...\n")

    # --- 1. SİSTEMİ BAŞLAT ---
    try:
        advisor = SmartAdvisor()

        # Modelin gerçekten yüklenip yüklenmediğini kontrol et
        if advisor.model is None:
            print("❌ Hata: 'SmartAdvisor' modeli yükleyemedi. 'artifacts' klasörünü kontrol et.")
            return

        optimizer = AcademicOptimizer(advisor)
        print("✅ Yapay Zeka Motoru ve Genetik Algoritma başarıyla yüklendi.")
    except Exception as e:
        print(f"❌ Başlatma Hatası: {e}")
        return

    # --- 2. SANAL ÖĞRENCİ PROFİLİ (Baseline) ---
    # Bu profili projenize uygun şekilde değiştirebilirsiniz
    student_data = {
        'student_id': 101,
        'age': 21,
        'gender': 'Male',
        'study_hours_per_day': 3.0,
        'social_media_hours': 4.0,
        'netflix_hours': 2.5,
        'sleep_hours': 6.5,
        'attendance_percentage': 70.0,
        'diet_quality': 'Fair',
        'mental_health_rating': 5,
        'internet_quality': 'Average',
        'parental_education_level': 'High School',
        'exercise_frequency': 1,
        'part_time_job': 'No',
        'extracurricular_participation': 'No'
    }

    # Mevcut Puanı Hesapla
    try:
        enriched = advisor._calculate_derived(student_data)
        current_score = advisor.predict(enriched)
        print(f"\n👤 Öğrenci Profili (Başlangıç): {current_score:.2f} Puan")
        print("-" * 60)
    except Exception as e:
        print(f"❌ Tahmin Hatası: {e}")
        return

    # --- 3. SENARYOLARI TANIMLA ---
    scenarios = [
        {
            "name": "Serbest Mod (Kısıt Yok)",
            "target": 75,
            "frozen": []
        },
        {
            "name": "\"Netflix'i Elleme\" Modu",
            "target": 75,
            "frozen": ['netflix_hours']
        },
        {
            "name": "\"Uykumu Elleme\" Modu",
            "target": 75,
            "frozen": ['sleep_hours']
        },
        {
            "name": "İmkansız Hedef (Full Kısıt)",
            "target": 98,  # Çok yüksek hedef + Çok kısıt
            "frozen": ['netflix_hours', 'social_media_hours', 'sleep_hours', 'attendance_percentage']
        }
    ]

    results_table = []

    # --- 4. TESTLERİ KOŞTUR ---
    for sc in scenarios:
        print(f"🧪 Test Ediliyor: {sc['name']} -> Hedef: {sc['target']}")

        # Genetik Algoritmayı Tetikle
        try:
            plan = optimizer.find_optimal_path(
                student_data=student_data,
                target_score=sc['target'],
                frozen_features=sc['frozen']
            )

            status = plan.get('status')

            if status == "Success":
                final_score = plan.get('achieved_score', 0)

                # Değişiklikleri okunabilir metne çevir
                actions = []
                for item in plan.get('changes', []):
                    feat = item['feature']
                    diff = item['diff']

                    # Sütun isimlerini Türkçeleştir/Kısalt
                    labels = {
                        'study_hours_per_day': 'Ders',
                        'social_media_hours': 'Sosyal M.',
                        'netflix_hours': 'Netflix',
                        'sleep_hours': 'Uyku',
                        'attendance_percentage': 'Devam',
                        'diet_quality': 'Diyet',
                        'mental_health_rating': 'Mental',
                        'exercise_frequency': 'Egzersiz'
                    }
                    label = labels.get(feat, feat)

                    # Format: Ders +1.5s veya Netflix -1.0s
                    if feat == 'diet_quality':
                        actions.append(f"Diyet->{item['new']}")
                    else:
                        actions.append(f"{label} {diff:+.1f}s")

                action_summary = ", ".join(actions)
                violation = "Hayır"

                # Frozen özellik değişmiş mi kontrolü (Safety Check)
                for f in sc['frozen']:
                    for item in plan.get('changes', []):
                        if item['feature'] == f and abs(item['diff']) > 0.01:
                            violation = "EVET (HATA!)"

            else:
                # Başarısız Senaryo
                final_score = "-"
                action_summary = f"⚠️ {plan.get('msg')}"
                violation = "N/A (Sistem Reddetti)"

        except Exception as e:
            print(f"⚠️ Senaryo Hatası: {e}")
            final_score = "HATA"
            action_summary = str(e)
            violation = "-"

        # Sonucu kaydet
        results_table.append({
            "Senaryo / Kısıt": sc['name'],
            "Hedef": sc['target'],
            "Sistem Önerisi (Aksiyon)": action_summary,
            "Sonuç Puanı": f"{final_score:.2f}" if isinstance(final_score, float) else final_score,
            "Kısıt İhlali?": violation
        })

    # --- 5. ÇIKTIYI GÖSTER VE KAYDET ---
    df = pd.DataFrame(results_table)

    print("\n" + "=" * 85)
    print("📊 TABLO 4.2: PAZARLIK MODU (COUNTERFACTUAL) GERÇEK SONUÇLARI")
    print("=" * 85)

    # Konsola güzel yazdır
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 1000)
    print(df.to_string(index=False))

    # CSV Olarak Kaydet
    try:
        df.to_csv("tablo_4_2_pazarlik_sonuclari.csv", index=False, encoding="utf-8-sig")
        print("\n✅ Sonuçlar 'tablo_4_2_pazarlik_sonuclari.csv' dosyasına kaydedildi.")
    except Exception as e:
        print(f"\n⚠️ Kaydetme hatası (Dosya açık olabilir): {e}")


if __name__ == "__main__":
    generate_real_negotiation_table()