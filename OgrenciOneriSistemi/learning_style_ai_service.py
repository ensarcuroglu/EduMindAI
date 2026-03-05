import pandas as pd
import joblib
import os
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

MODEL_PATH = 'artifacts/models/sota_ensemble_learning_style_model.joblib'
FEATURES_PATH = 'artifacts/models/model_features.joblib'


# --- 1. AYNI ÖZELLİK MÜHENDİSLİĞİ ---
def engineer_features(df):
    df_eng = df.copy()
    df_eng = df_eng.fillna(0)
    df_eng['Tech_Score'] = df_eng['OnlineCourses'] * (1 + df_eng['EduTech'])
    df_eng['Social_Score'] = df_eng['Discussions'] * df_eng['Attendance']
    df_eng['Traditional_Score'] = df_eng['Resources'] * df_eng['AssignmentCompletion']
    df_eng['Active_Score'] = df_eng['Extracurricular'] * (1 + df_eng['Motivation'])
    return df_eng


# --- 2. GELİŞTİRİLMİŞ TAVSİYE MOTORU ---
def get_gemini_advice(student_profile, predictions):
    if not API_KEY: return "⚠️ HATA: API Key yok."
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        return f"⚠️ Client Hatası: {e}"

    # --- A. VERİ DOĞRULAMA (SANITY CHECK) ---
    # Eğer çalışma saati 24'ten büyükse veya çok gerçekçi değilse düzeltme notu ekle
    study_hours = student_profile['StudyHours']
    warning_note = ""
    if study_hours > 100:
        warning_note = f"(NOT: Verilen çalışma saati ({study_hours}) gerçekçi görünmüyor, muhtemelen bir veri girişi hatası var. Bunu nazikçe, esprili bir dille belirt.)"

    # --- B. HİBRİT STİL ANALİZİ ---
    # En yüksek iki değeri bul
    sorted_preds = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
    first_style, first_score = sorted_preds[0]
    second_style, second_score = sorted_preds[1]

    # Eğer ilk iki stil arasındaki fark %5'ten azsa "Hibrit" kabul et
    is_hybrid = (first_score - second_score) < 5.0

    style_context = f"BASKIN STİL: {first_style}"
    if is_hybrid:
        style_context = f"BASKIN STİL: {first_style} ve {second_style} (HİBRİT ÖĞRENME). Bu öğrenci iki stili harmanlamalı."

    # --- C. GELİŞMİŞ PROMPT ---
    prompt = f"""
    Sen üniversite öğrencileri için 'Atomik Alışkanlıklar' tarzında konuşan, zeki ve samimi bir Eğitim Koçusun.

    [ÖĞRENCİ PROFİLİ]
    - Yaş: {student_profile['Age']}
    - Çalışma Süresi: {study_hours} saat/hafta {warning_note}
    - Stres: {student_profile['StressLevel']} (0:Düşük, 1:Orta, 2:Yüksek)

    [ANALİZ SONUÇLARI]
    {predictions}

    {style_context}

    [GÖREV]
    Bu öğrenciye maksimum verim için 3 tane 'Hemen Uygulanabilir' taktik ver.

    [KURALLAR]
    1. **Asla 'Kitap Gibi' Konuşma:** Uzun, devrik, akademik cümleler kurma. Youtube shorts videosu metni gibi akıcı ve net ol.
    2. **Hibrit Yaklaşım:** Eğer hibrit durumu varsa, iki stili birleştiren (örn: Hem yazıp hem çizmek) taktikler öner.
    3. **Emoji Kullan:** Maddelerin başına ilgili emojileri koy.
    4. **Veri Hatası:** Eğer çalışma saati mantıksızsa (örn: 150 saat), "Sanırım veri girişinde parmağın kaydı ama çok çalıştığını anladım" gibi esprili bir giriş yap.

    [ÇIKTI FORMATI]
    🧠 **Genel Bakış:** (Tek cümle)

    🚀 **Taktik 1:** (Başlık) - (Kısa açıklama)
    🎨 **Taktik 2:** (Başlık) - (Kısa açıklama)
    🔥 **Taktik 3:** (Başlık) - (Kısa açıklama)

    💪 **Motivasyon:** (Tek cümlelik kapanış)
    """

    # --- D. MODEL SEÇİMİ ---
    models_to_try = ['gemini-1.5-flash', 'gemini-flash-latest']

    config = types.GenerateContentConfig(
        temperature=0.8,  # Biraz daha yaratıcı olsun
        max_output_tokens=2000,
    )

    print(f"\n🤖 Mentör düşünüyor... ({style_context})")

    for model_name in models_to_try:
        try:
            final_name = model_name if model_name.startswith("models/") else model_name
            response = client.models.generate_content(model=final_name, contents=prompt, config=config)
            if response and response.text:
                return response.text.strip()
        except Exception:
            continue

    return "⚠️ AI yanıt veremedi."


# --- 3. TEST VERİSİ ---
def main():
    print("📂 Model yükleniyor...")
    try:
        loaded_model = joblib.load(MODEL_PATH)
        feature_cols = joblib.load(FEATURES_PATH)
    except:
        return

    # TEST VERİSİ (Hala 25 saat bırakıyoruz ki AI'ın tepkisini görelim)
    new_student_data = [25, 90, 2, 1, 2, 1, 0, 21, 3, 1, 95, 1, 1]

    # ... (Veri işleme kısımları aynı) ...
    raw_columns = ['StudyHours', 'Attendance', 'Resources', 'Extracurricular', 'Motivation', 'Internet', 'Gender',
                   'Age', 'OnlineCourses', 'Discussions', 'AssignmentCompletion', 'EduTech', 'StressLevel']
    df = pd.DataFrame([new_student_data], columns=raw_columns)
    df_eng = engineer_features(df)

    probs = loaded_model.predict_proba(df_eng[feature_cols])[0]
    style_names = ['Görsel (Visual)', 'İşitsel (Auditory)', 'Okuma/Yazma (Read/Write)', 'Kinestetik (Kinesthetic)']
    pred_dict = {style: prob * 100 for style, prob in zip(style_names, probs)}

    print("\n📊 Sonuçlar:")
    for k, v in pred_dict.items(): print(f"{k}: %{v:.1f}")

    advice = get_gemini_advice({
        'Age': 21,
        'StudyHours': 25,  # Hatalı veri bilerek gönderiliyor
        'StressLevel': 1
    }, pred_dict)

    print("\n" + "=" * 50)
    print(advice)
    print("=" * 50)


if __name__ == "__main__":
    main()