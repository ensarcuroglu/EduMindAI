import pandas as pd


def analyze_dataset():
    # Dosya yolunu belirle (Aynı dizinde varsayıyoruz)
    file_path = 'data/student_performance.csv'

    print(f"📂 '{file_path}' dosyası yükleniyor...\n")

    try:
        # CSV dosyasını oku
        df = pd.read_csv(file_path)

        # 1. İlk 5 Satırı Göster
        print("-" * 50)
        print("👀 İLK 5 SATIR")
        print("-" * 50)
        print(df.head().to_string())  # to_string() tüm sütunların görünmesini sağlar

        # 2. Genel Bilgiler (Sütun tipleri, boş değerler)
        print("\n" + "-" * 50)
        print("ℹ️ GENEL BİLGİLER")
        print("-" * 50)
        print(df.info())

        # 3. İstatistiksel Özet (Ortalama, Min, Max vb.)
        print("\n" + "-" * 50)
        print("📊 İSTATİSTİKSEL ÖZET")
        print("-" * 50)
        print(df.describe().to_string())

        # 4. Sütun Listesi
        print("\n" + "-" * 50)
        print("📝 SÜTUN İSİMLERİ")
        print("-" * 50)
        print(df.columns.tolist())

    except FileNotFoundError:
        print(f"❌ HATA: '{file_path}' bulunamadı. Lütfen dosyanın script ile aynı dizinde olduğundan emin ol.")
    except Exception as e:
        print(f"❌ BEKLENMEYEN HATA: {e}")


if __name__ == "__main__":
    analyze_dataset()