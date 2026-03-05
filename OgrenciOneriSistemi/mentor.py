import os
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ==========================================
# 🔑 GÜVENLİK VE AYARLAR
# ==========================================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


def generate_mentor_advice(student_name, predicted_score, sleep_hours, is_zombie, top_suggestion):
    """
    oneri_motoru_V2.py tarafından çağrılan AI Mentör Fonksiyonu.
    Parametreler:
    - student_name (str): Öğrenci ID veya İsmi
    - predicted_score (float): Hedeflenen/Tahmin edilen puan
    - sleep_hours (float): Uyku saati
    - is_zombie (bool): 6 saatin altında uyku var mı?
    - top_suggestion (str): Yapılması gereken değişikliklerin özeti (Metin)
    """

    # 1. API Anahtarı Kontrolü
    if not API_KEY:
        return "⚠️ (Mentör Devre Dışı: API Anahtarı Bulunamadı. .env dosyasını kontrol et.)"

    # --- CLIENT BAŞLATMA ---
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception:
        return "⚠️ (Mentör Bağlantı Hatası)"

    # --- SENİN HESABINA ÖZEL MODEL LİSTESİ ---
    # Testlerimizde senin hesabında çalışan modeller bunlardı.
    models_to_try = [
        'models/gemini-2.5-flash',  # En yeni ve hızlı
        'models/gemini-2.0-flash',  # Güçlü alternatif
        'models/gemini-1.5-flash',  # Standart yedek
        'models/gemini-flash-latest'  # Son çare
    ]

    # --- İSİM DÜZELTME ---
    display_name = str(student_name) if student_name else "Sevgili Öğrenci"

    # --- DURUM ANALİZİ VE TONLAMA ---
    tone = "yapıcı, koçvari ve veri odaklı"
    context = "Gelişim alanlarına odaklan."
    emoji = "📊"

    if is_zombie:
        context = "ACİL DURUM: Öğrenci zombi modunda (Az uyku). Akademik başarıdan önce uykusunu düzeltmesini sert ama şefkatli bir dille emret."
        emoji = "🚨"
    elif predicted_score >= 90:
        context = "ZİRVE PERFORMANS: Öğrenci harika gidiyor. Onu bir şampiyon gibi tebrik et ve zirvede kalması için gaz ver."
        emoji = "🏆"
    elif predicted_score >= 75:
        context = "ÇOK İYİ: Hedefe çok yakın. Son bir itici güç ver."
        emoji = "🚀"
    else:
        context = "GELİŞİME AÇIK: Düşük puan ama potansiyel var. Asla pes etmemesini söyle, umut ver."
        emoji = "💪"

    # --- PROMPT (İSTEM) ---
    prompt = f"""
    Sen üniversite öğrencileri için yapay zeka destekli bir 'Akademik Performans Mentörü'sün.

    [ÖĞRENCİ BİLGİLERİ]
    - İsim: {display_name}
    - Potansiyel Puan: {predicted_score:.1f}
    - Uyku Durumu: {sleep_hours} saat/gün
    - Yapılması Gerekenler: "{top_suggestion}"

    [GÖREV]
    Bu öğrenciye, yukarıdaki 'Yapılması Gerekenler' listesini hayata geçirmesi için motive edici kişisel bir not yaz.

    [KURALLAR]
    1. Tonun: {tone} olsun.
    2. Bağlam: {context}
    3. Robotik konuşma, samimi ol (Abi/Abla tavsiyesi gibi).
    4. Teknik terimleri (study_hours vb.) kullanma, doğal konuş ("Ders süreni artır" de).
    5. ÇOK KISA YAZ: En fazla 2-3 cümle.
    6. Mesajın sonuna {emoji} ekle.
    """

    # --- CONFIG ---
    config = types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=3000,  # Kısa ve öz cevap
    )

    # --- MODEL DENEME DÖNGÜSÜ (RETRY LOGIC) ---
    for model_name in models_to_try:
        # Her model için 2 şans ver (Hız için 3'ten 2'ye düşürdük)
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )

                if response and response.text:
                    return response.text.strip()

            except Exception as e:
                error_str = str(e)

                # 429 = Kota Doldu -> Bekle ve Tekrar Dene
                if "429" in error_str or "exhausted" in error_str:
                    wait_time = 2 * (attempt + 1) + random.uniform(0, 1)
                    # Ana programda kullanıcı beklemesin diye sadece print atıp bekliyoruz
                    # print(f"   (Mentör düşünüyor... {model_name})")
                    time.sleep(wait_time)

                # 404 = Model Yok -> Döngüyü kır, diğer modele geç
                elif "404" in error_str or "not found" in error_str.lower():
                    break

                else:
                    # Diğer hatalarda kısa bekle
                    time.sleep(1)

    # Hiçbir model çalışmazsa
    return f"Mentör şu an çok yoğun ama {predicted_score:.1f} puana ulaşman için gerekenleri listeledim! Başarılar! 🤖"


# --- MODÜL TESTİ (Doğrudan çalıştırılırsa) ---
if __name__ == "__main__":
    print("🧪 Mentör Modülü Test Ediliyor...")
    ornek_tavsiye = "Netflix'i azalt, uykuyu 7 saate çıkar."
    mesaj = generate_mentor_advice("TestOgrenci", 85.5, 6.5, False, ornek_tavsiye)
    print("\n--- MENTÖR MESAJI ---\n")
    print(mesaj)