import pandas as pd
import numpy as np
import os

# --- AYARLAR ---
DATA_DIR = 'data'
INPUT_FILE = 'enhanced_student_habits_performance_dataset.csv'
OUTPUT_FILE = 'final_training_dataset.csv'  # Temizlenmiş dosya bu isimle çıkacak


def path_builder(filename):
    return os.path.join(DATA_DIR, filename)


def clean_data():
    input_path = path_builder(INPUT_FILE)
    output_path = path_builder(OUTPUT_FILE)

    print("🧹 TEMİZLİK OPERASYONU BAŞLIYOR...")

    try:
        df = pd.read_csv(input_path)
        print(f"📥 Giriş Verisi: {df.shape[0]} satır")
    except Exception as e:
        print(f"❌ Hata: Dosya okunamadı. {e}")
        return

    # --- 1. MANTIK TEMİZLİĞİ (Anomaly Removal) ---
    # Senaryo: Derse katılımı düşük (< %50) ama notu çok yüksek (> 85) olanlar.
    # Bu veriler muhtemelen hatalı veya "outlier".
    anomaly_mask = (df['attendance_percentage'] < 50) & (df['exam_score'] > 85)
    anomaly_count = anomaly_mask.sum()

    df_clean = df[~anomaly_mask]  # Tilde (~) işareti "DEĞİL" demektir, yani bunları çıkar.
    print(f"👻 Mantık Hatası Temizliği: {anomaly_count} adet 'Hayalet Öğrenci' (Düşük Katılım/Yüksek Not) silindi.")

    # --- 2. NOT ENFLASYONU DÜZELTME (Downsampling High Achievers) ---
    # Hedef: 85 üzeri not alanların oranını %67'den %25-30 bandına çekmek.

    # Yüksek not alanları ayır
    high_achievers = df_clean[df_clean['exam_score'] > 85]
    normal_achievers = df_clean[df_clean['exam_score'] <= 85]

    # Yüksek not alanların %70'ini rastgele sil (Keep ratio = 0.3)
    # random_state=42 sayesinde her çalıştırmada aynı satırları siler (tekrarlanabilirlik).
    high_achievers_sampled = high_achievers.sample(frac=0.30, random_state=42)

    print(
        f"📉 Enflasyon Müdahalesi: {len(high_achievers)} başarılı öğrenciden {len(high_achievers) - len(high_achievers_sampled)} tanesi elendi.")

    # Verileri tekrar birleştir
    df_final = pd.concat([normal_achievers, high_achievers_sampled])

    # Karıştırma (Shuffle) - Sıralı kalmasınlar
    df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

    # --- SONUÇ RAPORU ---
    print("\n" + "=" * 40)
    print("✅ OPERASYON TAMAMLANDI")
    print("=" * 40)
    print(f"Eski Satır Sayısı : {df.shape[0]}")
    print(f"Yeni Satır Sayısı : {df_final.shape[0]}")
    print(f"Silinen Veri      : {df.shape[0] - df_final.shape[0]}")

    # Yeni Oran Kontrolü
    new_high_ratio = (df_final[df_final['exam_score'] > 85].shape[0] / df_final.shape[0]) * 100
    print(f"\n📊 Yeni 'Yüksek Başarı' Oranı: %{new_high_ratio:.1f} (Hedef: %20-%30 arası)")

    # Kaydetme
    df_final.to_csv(output_path, index=False)
    print(f"\n💾 Dosya Kaydedildi: {output_path}")
    print("🚀 Artık modelinizi bu dosya ('final_training_dataset.csv') ile eğitebilirsiniz!")


if __name__ == "__main__":
    clean_data()