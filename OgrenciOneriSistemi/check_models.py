from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

print("Kullanılabilir Modeller Listeleniyor...")
try:
    # Yeni SDK ile model listeleme
    for m in client.models.list():
        # Sadece generateContent destekleyenleri filtrele
        if "generateContent" in m.supported_actions:
            print(f"- {m.name}")

except Exception as e:
    print(f"Hata: {e}")