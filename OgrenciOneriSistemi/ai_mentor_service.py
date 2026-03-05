#ai_mentor_service.py:
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


class AIMentorService:
    def __init__(self):
        """
        Servisi başlatır, API anahtarını kontrol eder ve istemciyi kurar.
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("⚠️ API Anahtarı Bulunamadı. .env dosyasını kontrol et.")

        # Client Başlatma
        self.client = genai.Client(api_key=self.api_key)

        # Senin belirlediğin öncelikli model listesi
        self.models_to_try = [
            'gemini-2.0-flash',  # Kararlı ve hızlı (Genellikle 'models/' öneki olmadan çalışır ama duruma göre bakarız)
            'gemini-1.5-flash',  # Standart yedek
            'gemini-1.5-pro',  # Daha akıllı alternatif
            'gemini-flash-latest'  # Son çare
        ]

        # Sistem Talimatı (Persona)
        self.system_instruction = """
        Sen üniversite öğrencileri için "AI Akademik Mentör"sün.

        [KİMLİK]
        - Adın: AI Koç.
        - Tarzın: Arkadaş canlısı, motive edici ama disiplinli (Abi/Abla tavsiyesi gibi).
        - Emoji Kullanımı: Mesajlarında uygun yerlerde 📚, 🚀, 💪, 💡 gibi emojiler kullan.

        [GÖREVLER]
        1. Öğrencinin sorularını yanıtlarken her zaman akademik başarıyı ve kişisel gelişimi hedefle.
        2. Eğer öğrenci stresliyse onu sakinleştir ve küçük adımlarla plan yapmasını sağla.
        3. Kod veya ders sorusu sorarsa, cevabı doğrudan vermek yerine mantığını anlat ve ipuçları ver.
        4. Cevapların çok uzun olmasın (maksimum 1-2 paragraf), öğrenciyi okurken sıkma.

        [DİL]
        Türkçe konuş. Samimi ol ama labali olma.
        """

    def _format_history_for_gemini(self, raw_history):
        """
        ASP.NET'ten gelen geçmişi (list of dict) Gemini API formatına (types.Content) çevirir.
        Gelen Format: [{'role': 'user', 'message': '...'}, {'role': 'model', 'message': '...'}]
        """
        formatted_contents = []

        # Önce sistem talimatını ekleyebiliriz (Opsiyonel, ama config'de system_instruction var zaten)

        if not raw_history:
            return formatted_contents

        for chat in raw_history:
            # Rol eşleştirmesi: ASP.NET 'user'/'model' -> Gemini 'user'/'model'
            role = "user" if chat.get("role") == "user" else "model"
            text_content = chat.get("message", "")

            # types.Content objesi oluşturma
            content = types.Content(
                role=role,
                parts=[types.Part(text=text_content)]
            )
            formatted_contents.append(content)

        return formatted_contents

    def get_chat_response(self, user_message, history=None):
        """
        Kullanıcı mesajını ve geçmişi alır, uygun modeli deneyerek cevap döner.
        """
        # 1. Geçmişi Formatla
        chat_contents = self._format_history_for_gemini(history or [])

        # 2. Yeni mesajı geçmişin sonuna ekle (API çağrısı için)
        chat_contents.append(types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        ))

        # 3. Konfigürasyon
        config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=1000,
            system_instruction=self.system_instruction
        )

        # 4. Model Deneme Döngüsü (Retry Logic)
        last_error = None

        for model_name in self.models_to_try:
            # Her model için 2 deneme hakkı
            for attempt in range(2):
                try:
                    # API Çağrısı (Stateless - Her seferinde tüm geçmişi gönderiyoruz)
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=chat_contents,
                        config=config
                    )

                    if response and response.text:
                        return response.text.strip()

                except Exception as e:
                    error_str = str(e)
                    last_error = error_str

                    # 429: Kota Doldu -> Bekle
                    if "429" in error_str or "exhausted" in error_str:
                        wait_time = 1.5 * (attempt + 1)
                        print(f"⚠️ Kota ({model_name}) - {wait_time}s bekleniyor...")
                        time.sleep(wait_time)

                    # 404: Model Bulunamadı -> Döngüden çık, sonraki modele geç
                    elif "404" in error_str or "not found" in error_str.lower():
                        print(f"❌ Model bulunamadı: {model_name}, diğerine geçiliyor.")
                        break  # İçteki for döngüsünü kırar, dıştaki (model) döngüsü devam eder

                    else:
                        # Diğer hatalar
                        print(f"⚠️ Hata ({model_name}): {error_str}")
                        time.sleep(1)

        # Hiçbir model çalışmazsa
        return f"Üzgünüm, şu an bağlantımda geçici bir sorun var. Lütfen biraz sonra tekrar dene. (Hata: {str(last_error)[:50]}...)"


# --- TEST BLOĞU ---
if __name__ == "__main__":
    print("🧪 AI Mentor Servisi Test Ediliyor...")

    service = AIMentorService()

    # Simüle edilmiş geçmiş (ASP.NET'ten gelmiş gibi)
    dummy_history = [
        {"role": "user", "message": "Merhaba, sınav haftam yaklaşıyor."},
        {"role": "model",
         "message": "Selam! Sınav haftası biraz stresli olabilir ama hallederiz. Hangi dersler seni zorluyor? 📚"}
    ]

    user_input = "Matematik çok zor, çalışasım gelmiyor."

    print(f"\nKullanıcı: {user_input}")
    print("Mentör Düşünüyor...")

    yanit = service.get_chat_response(user_input, dummy_history)

    print(f"\nMentör: {yanit}")