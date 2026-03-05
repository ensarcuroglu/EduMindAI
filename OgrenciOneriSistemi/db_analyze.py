import pandas as pd
import numpy as np
import os
import sys

# --- AYARLAR ---
# PyCharm proje yapına göre: 'data' klasörü projenin ana dizininde varsayılmıştır.
DATA_DIR = 'data'
OLD_DATASET_NAME = 'student_habits_performance.csv'
NEW_DATASET_NAME = 'final_training_dataset.csv'


def path_builder(filename):
    return os.path.join(DATA_DIR, filename)


def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def analyze_and_compare():
    old_path = path_builder(OLD_DATASET_NAME)
    new_path = path_builder(NEW_DATASET_NAME)

    print(f"🔍 ANALİZ BAŞLIYOR...")
    print(f"📂 Klasör: {os.path.abspath(DATA_DIR)}")

    # 1. DOSYA YÜKLEME KONTROLÜ
    try:
        df_old = pd.read_csv(old_path)
        df_new = pd.read_csv(new_path)
        print("✅ Dosyalar başarıyla okundu.")
    except FileNotFoundError as e:
        print(f"❌ HATA: Dosya bulunamadı! Lütfen 'data' klasörünü kontrol et.\nDetay: {e}")
        return
    except Exception as e:
        print(f"❌ HATA: Beklenmedik bir sorun oluştu.\nDetay: {e}")
        return

    # 2. GENEL BAKIŞ
    print_header("1. BOYUT VE YAPI KARŞILAŞTIRMASI")
    print(f"{'Metrik':<25} | {'Orijinal Veri':<15} | {'Yeni Veri':<15} | {'Fark'}")
    print("-" * 75)
    print(
        f"{'Satır Sayısı':<25} | {df_old.shape[0]:<15} | {df_new.shape[0]:<15} | {df_new.shape[0] - df_old.shape[0]:+}")
    print(
        f"{'Sütun Sayısı':<25} | {df_old.shape[1]:<15} | {df_new.shape[1]:<15} | {df_new.shape[1] - df_old.shape[1]:+}")

    # 3. SÜTUN VE UYUMLULUK KONTROLÜ
    print_header("2. SÜTUN UYUMLULUĞU (EKSİKLİK ANALİZİ)")
    old_cols = set(df_old.columns)
    new_cols = set(df_new.columns)

    missing = old_cols - new_cols
    added = new_cols - old_cols

    if missing:
        print(f"🚨 KRİTİK UYARI: Orijinalde olup Yeni sette OLMAYAN sütunlar ({len(missing)} adet):")
        for col in missing:
            print(f"   - {col}")
        print("   -> Bu sütunlar modeliniz için gerekliyse KOD HATASI alırsınız!")
    else:
        print("✅ MÜKEMMEL: Orijinal veri setindeki TÜM sütunlar yeni veri setinde mevcut.")

    if added:
        print(f"\nℹ️ BİLGİ: Yeni eklenen sütunlar ({len(added)} adet):")
        print(f"   {', '.join(list(added)[:5])} ... ve diğerleri.")

    # 4. İSTATİSTİKSEL SAPMA (DRIFT CHECK)
    print_header("3. SAYISAL DEĞİŞKENLERDE SAPMA (DRIFT CHECK)")
    print(f"{'Sütun Adı':<30} | {'Eski Ort.':<10} | {'Yeni Ort.':<10} | {'Değişim (%)'}")
    print("-" * 75)

    common_numeric = list(
        set(df_old.select_dtypes(include=np.number).columns) & set(df_new.select_dtypes(include=np.number).columns))
    common_numeric.sort()

    drift_detected = False
    for col in common_numeric:
        m1 = df_old[col].mean()
        m2 = df_new[col].mean()
        diff_pct = ((m2 - m1) / m1) * 100 if m1 != 0 else 0

        # Eğer değişim %20'den fazlaysa uyarı işareti koy
        marker = "⚠️" if abs(diff_pct) > 20 else ""

        print(f"{col:<30} | {m1:<10.2f} | {m2:<10.2f} | {diff_pct:>6.1f}% {marker}")
        if abs(diff_pct) > 20: drift_detected = True

    if drift_detected:
        print("\n⚠️ Not: %20'den fazla sapma olan sütunlar, modelin davranışını değiştirebilir.")

    # 5. ÖZEL SENARYO KONTROLLERİ (ZOMBI & VAMPIR & NOT ENFLASYONU)
    print_header("4. ALGORİTMA UYUMLULUK TESTLERİ (LOGIC CHECK)")

    # Check A: Zombi Bariyeri (Uyku < 6 saat olanların oranı)
    if 'sleep_hours' in df_new.columns:
        zombie_ratio_old = (df_old[df_old['sleep_hours'] < 6].shape[0] / df_old.shape[0]) * 100
        zombie_ratio_new = (df_new[df_new['sleep_hours'] < 6].shape[0] / df_new.shape[0]) * 100
        print(f"🧟 ZOMBİ BARİYERİ TESTİ (Uyku < 6 saat):")
        print(f"   - Eski Veri Oranı: %{zombie_ratio_old:.1f}")
        print(f"   - Yeni Veri Oranı: %{zombie_ratio_new:.1f}")
        if zombie_ratio_new < 5:
            print(
                "   ⚠️ UYARI: Yeni veri setinde uykusuz öğrenci neredeyse YOK. Zombi algoritması hiç tetiklenmeyebilir.")
        else:
            print("   ✅ DURUM: Yeterli miktarda riskli öğrenci var.")

    # Check B: Not Enflasyonu (Not > 85 olanların oranı)
    if 'exam_score' in df_new.columns:
        high_achievers_old = (df_old[df_old['exam_score'] > 85].shape[0] / df_old.shape[0]) * 100
        high_achievers_new = (df_new[df_new['exam_score'] > 85].shape[0] / df_new.shape[0]) * 100
        print(f"\n📈 NOT ENFLASYONU TESTİ (Puan > 85):")
        print(f"   - Eski Veri Oranı: %{high_achievers_old:.1f}")
        print(f"   - Yeni Veri Oranı: %{high_achievers_new:.1f}")
        if high_achievers_new > 50:
            print("   🚨 KRİTİK: Öğrencilerin yarısından fazlası 'Çok Başarılı'. Model 'Başarısızlığı' öğrenemez!")

    # Check C: Sosyal Medya (Vampir Modu)
    if 'social_media_hours' in df_new.columns:
        addict_old = (df_old[df_old['social_media_hours'] > 4].shape[0] / df_old.shape[0]) * 100
        addict_new = (df_new[df_new['social_media_hours'] > 4].shape[0] / df_new.shape[0]) * 100
        print(f"\n🧛 VAMPİR MODU TESTİ (Sosyal Medya > 4 saat):")
        print(f"   - Eski Veri Oranı: %{addict_old:.1f}")
        print(f"   - Yeni Veri Oranı: %{addict_new:.1f}")


if __name__ == "__main__":
    analyze_and_compare()