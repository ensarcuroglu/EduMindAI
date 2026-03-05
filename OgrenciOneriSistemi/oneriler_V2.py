# -*- coding: utf-8 -*-
"""
oneriler_V2.py — Gelişmiş Öneri Kataloğu (Gold Edition)
Bu modül, oneri_motoru_V2.py'nin simülasyon (Counterfactual Analysis) yapabilmesi için
gerekli matematiksel talimatları ve İKNA EDİCİ PSİKOLOJİK tavsiye metinlerini içerir.
"""

from typing import Any, Dict, List, Optional
import json
import os
import csv

# ==========================================
# KATALOG YAPISI AÇIKLAMASI
# id: Benzersiz kimlik
# category: Raporlama için kategori (Academic, Wellness, Discipline, Social)
# difficulty: Uygulama zorluğu (Easy, Medium, Hard)
# condition: Python expression olarak tetiklenme koşulu
# simulation: Motorun uygulayacağı matematiksel işlem
#    - feature: Değişecek sütun
#    - operation: 'add' (ekle/çıkar), 'multiply' (çarp), 'set' (sabitle)
#    - value: Değer
# ==========================================

RECOMMENDATION_CATALOG: List[Dict[str, Any]] = [

    # ====================================================
    # 1. AKADEMİK PERFORMANS & ÇALIŞMA SÜRESİ
    # ====================================================

    # --- Seviye 1: Küçük Başlangıçlar ---
    {
        "id": "study_micro_boost",
        "category": "Academic",
        "difficulty": "Easy",
        "text": "🚀 **Ateşleyici Güç:** Günde sadece 30 dakika eklemek sana küçük gelebilir ama bu, "
                "haftada fazladan 3.5 saatlik dev bir avantaj yaratır. Sadece bir kahve molası kadar "
                "kısa bir süreyle rakiplerinin önüne geçebilirsin.",
        "condition": "study_hours_per_day < 2.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.5}
    },

    # --- Seviye 2: Orta Seviye Artış ---
    {
        "id": "study_standard_boost",
        "category": "Academic",
        "difficulty": "Medium",
        "text": "📈 **Vites Artırma Zamanı:** Mevcut tempon iyi ama senin potansiyelin bunun çok üzerinde. Günlük çalışmana +1 saat eklemek, sınav anında 'Keşke' demek yerine 'İyi ki' demeni sağlayacak o kritik farkı yaratır.",
        "condition": "study_hours_per_day < 4.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
    },

    # --- Seviye 3: Sınav Modu (Hardcore) ---
    {
        "id": "study_exam_mode",
        "category": "Academic",
        "difficulty": "Hard",
        "text": "🔥 **Şampiyonlar Ligi:** Hedefin zirve ise normal çalışmak yetmez. Günde ekstra 2 saatlik 'Derin Çalışma' (Deep Work) ile konuları yetiştirmekle kalmaz, onlara hükmedersin. Bu tempoya vücudun 3 günde alışacak, güven bana.",
        "condition": "study_hours_per_day >= 3.0 and study_hours_per_day < 6.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 2.0}
    },

    # --- Devamsızlık Sorunu ---
    {
        "id": "fix_attendance_critical",
        "category": "Academic",
        "difficulty": "Medium",
        "text": "🏫 **İçeriden Bilgi:** En iyi notlar kitapta değil, hocanın dudaklarının arasındadır."
                " Devamsızlığın kritik seviyede. Sadece derslere giderek (çalışmadan bile!)"
                " sınav sorularının %30'unu yakalayabilirsin. Bu fırsatı tepme.",
        "condition": "attendance_percentage < 85.0",
        "simulation": {"feature": "attendance_percentage", "operation": "set", "value": 90.0}
    },

    # ====================================================
    # 2. DİJİTAL DİSİPLİN (SOSYAL MEDYA & NETFLIX)
    # ====================================================

    # --- Sosyal Medya Diyeti (%50 Azaltma) ---
    {
        "id": "social_media_diet",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "📱 **Zaman Hırsızını Yakala:** Telefon ekranına bakarak geçirdiğin o saatler geri gelmeyecek."
                " Sosyal medya süreni yarıya indirirsen, günün sana ait olan 'altın saatlerini' geri kazanırsın. Denemeye değer.",
        "condition": "social_media_hours > 3.0",
        "simulation": {"feature": "social_media_hours", "operation": "multiply", "value": 0.5}
    },

    # --- Sosyal Medya Detoksu (Sıfırlama) ---
    {
        "id": "social_media_detox",
        "category": "Discipline",
        "difficulty": "Hard",
        "text": "📵 **Dijital Özgürlük:** Dikkat dağınıklığın alarm veriyor. Bildirimlerin kölesi olma. Sosyal medyayı günde 30 dakikaya sabitlemek, zihinsel berraklığını (IQ'nu artırmış gibi) hissettirecek.",
        "condition": "social_media_hours > 5.0",
        "simulation": {"feature": "social_media_hours", "operation": "set", "value": 0.5}
    },

    # --- Netflix/Dizi Kısıtlaması ---
    {
        "id": "limit_netflix",
        "category": "Discipline",
        "difficulty": "Easy",
        "text": "🎬 **Bölüm Sonu Canavarı:** Diziler harika ama akademik geleceğini 'Sonraki Bölüm' butonuna kurban etme. İzleme süreni günde 1 saatin altına çekersen, hem eğlenirsin hem de kazanırsın. Denge senin elinde.",
        "condition": "netflix_hours > 1.5",
        "simulation": {"feature": "netflix_hours", "operation": "set", "value": 0.8}
    },

    # ====================================================
    # 3. FİZİKSEL SAĞLIK & YAŞAM TARZI (UYKU - SPOR - BESLENME)
    # ====================================================

    # --- Uyku Düzeltme (Az Uyuyanlar) ---
    {
        "id": "fix_sleep_deprivation",
        "category": "Wellness",
        "difficulty": "Hard",
        "text": "😴 **Hafıza Kayıt Cihazı:** 6 saatin altında uyuduğunda beynin 'Kaydet' butonuna basamıyor. Öğrendiğin her şeyi çöpe atmamak için uykunu 7.5 saate tamamlamalısın. Uyku, tembellik değil biyolojik bir zorunluluktur.",
        "condition": "sleep_hours < 6.0",
        "simulation": {"feature": "sleep_hours", "operation": "set", "value": 7.5}
    },

    # --- Uyku Optimize Etme (Çok Uyuyanlar) ---
    {
        "id": "reduce_oversleeping",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "⏰ **Uyan ve Kazan:** 9 saatin üzerinde uyumak seni dinlendirmez, aksine sersemletir. İdeal 8 saatlik döngüye geçip güne erken başlamak, sana her gün fazladan 1 saat hediye eder.",
        "condition": "sleep_hours > 9.0",
        "simulation": {"feature": "sleep_hours", "operation": "set", "value": 8.0}
    },

    # --- Spora Başlama ---
    {
        "id": "start_movement",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "🏃‍♂️ **Beynine Oksijen Gönder:** Hiç spor yapmamak, beynini havasız bir odada çalıştırmak gibidir. Haftada sadece 2 gün, 20 dakikalık tempolu yürüyüş bile nöronlarını ateşlemeye yeter.",
        "condition": "exercise_frequency == 0",
        "simulation": {"feature": "exercise_frequency", "operation": "set", "value": 2}
    },

    # --- Beslenme Kalitesi ---
    {
        "id": "boost_nutrition",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🥑 **Ferrari'ye Tüp Takma:** Beynin yüksek performanslı bir motor gibidir; ona kötü yakıt (şeker, fast-food) verirsen tekler. Beslenmeni 'İyi' seviyeye çekmek, odaklanma sorununu kökten çözer.",
        "condition": "diet_quality == 'Poor'",
        "simulation": {"feature": "diet_quality", "operation": "set", "value": "Good"}
    },

    # ====================================================
    # 4. SOSYAL & MENTAL DESTEK
    # ====================================================

    # --- Kulüp/Aktivite Katılımı ---
    {
        "id": "join_social_activity",
        "category": "Social",
        "difficulty": "Easy",
        "text": "🤝 **Yalnız Kurt Olma:** Sadece ders çalışmak seni tükenmişliğe sürükler. Bir kulübe katılmak veya hobi edinmek 'zaman kaybı' değil, beynini şarj eden bir moladır. Sosyal destek başarıyı artırır.",
        "condition": "extracurricular_participation == 'No' and study_hours_per_day > 4.0",
        "simulation": {"feature": "extracurricular_participation", "operation": "set", "value": "Yes"}
    },

    # --- Mental Yorgunluk Yönetimi (Ders Azaltma Stratejisi) ---
    {
        "id": "mental_break_balance",
        "category": "Wellness",
        "difficulty": "Hard",
        "text": "🧘 **Stratejik Mola:** Şu an zihnin dolu bir bardak gibi; ne kadar su koyarsan o kadar taşıyor. Çalışma süreni biraz azaltıp kendine nefes alma alanı yaratırsan, verimin (ve notların) yükselecek.",
        "condition": "mental_health_rating < 4 and study_hours_per_day > 5.0",
        "simulation": {"feature": "mental_health_rating", "operation": "set", "value": 8}
    },

    # ====================================================
    # 5. ALTYAPI & ÇEVRE
    # ====================================================

    # --- İnternet Kalitesi ---
    {
        "id": "fix_internet",
        "category": "Infrastructure",
        "difficulty": "Medium",
        "text": "🌐 **Hızını Kesme:** İnternetinin yavaş olması, bilgiye erişimini sabote ediyor. Bağlantını iyileştirmek veya kütüphaneye gitmek, sana çalışma sırasında kaybettiğin o değerli dakikaları geri verecek.",
        "condition": "internet_quality == 'Poor'",
        "simulation": {"feature": "internet_quality", "operation": "set", "value": "Good"}
    },

    # ====================================================
    # 6. YENİ EKLENEN: İLERİ SEVİYE & SPESİFİK SENARYOLAR
    # ====================================================

    # --- 1. "Çalışan Öğrenci" Dengesini Kurma ---
    {
        "id": "part_time_efficiency",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "💼 **Zamanı Bükmek:** Hem çalışıp hem okumak zor, ama imkansız değil. İşe gidip gelirken veya molalarda yaratacağın 45 dakikalık 'Mikro-Odaklanma' blokları, günde 3 saat çalışan birine bedeldir.",
        "condition": "part_time_job == 'Yes' and study_hours_per_day < 2.5",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.8}
    },

    # --- 2. "Tükenmişlik Sendromu" (Burnout) Önleyici ---
    {
        "id": "prevent_burnout",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🧠 **Acil Durum Freni:** Çok çalışıyorsun ama verim alamıyorsun çünkü zihinsel pilin bitmek üzere! Kitabı kapat, yürüyüşe çık veya müzik dinle. Dinlenmiş bir zihin, yorgun bir zihinden 10 kat hızlı öğrenir.",
        "condition": "study_hours_per_day > 4.5 and mental_health_rating < 5",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 3}
    },

    # --- 3. "İntikamcı Uyku Erteleme" (Revenge Bedtime Procrastination) ---
    {
        "id": "swap_scroll_sleep",
        "category": "Wellness",
        "difficulty": "Hard",
        "text": "🌙 **Gece Tuzağından Çık:** Gün içinde kendine vakit ayıramadığın için gece uyumayıp telefona bakıyorsun, biliyorum. Ama bu seni ertesi gün zombiye çeviriyor. Telefonu odadan çıkar, uykuyu seç.",
        "condition": "sleep_hours < 6.0 and social_media_hours > 4.0",
        "simulation": {"feature": "sleep_hours", "operation": "set", "value": 7.5}
    },

    # --- 4. "Orta Şeker" Beslenmeyi İyileştirme ---
    {
        "id": "diet_optimization_fair",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "🍎 **Biyolojik İnce Ayar:** Beslenmen fena değil ama 'İyi' olmakla 'Mükemmel' olmak arasındaki fark burada gizli. Şekeri azaltıp suyu artırmak, öğleden sonra gelen o meşhur uyku bastırmasını yok eder.",
        "condition": "diet_quality == 'Fair'",
        "simulation": {"feature": "diet_quality", "operation": "set", "value": "Good"}
    },

    # --- 5. Devamsızlıkta "Mükemmeliyetçilik" ---
    {
        "id": "attendance_mastery",
        "category": "Academic",
        "difficulty": "Easy",
        "text": "💎 **Sıfır Kayıp:** Devamlılığın iyi ama %100'e yaklaştırmak, hocanın sınavda soracağı o sürpriz 'dipnot' sorusunu yakalamanı garanti eder. Risk alma, derse gir.",
        "condition": "attendance_percentage >= 85.0 and attendance_percentage < 95.0",
        "simulation": {"feature": "attendance_percentage", "operation": "set", "value": 100.0}
    },

    # --- 6. İnternet Hızı Optimizasyonu (Ortalama -> İyi) ---
    {
        "id": "internet_upgrade_pro",
        "category": "Infrastructure",
        "difficulty": "Medium",
        "text": "🚀 **Teknik Avantaj:** Yoğun çalışıyorsun ama 'Ortalama' internet hızı seni yavaşlatıyor olabilir. Daha kaliteli kaynaklara takılmadan erişmek için bağlantını güçlendirmen sana zaman kazandırır.",
        "condition": "internet_quality == 'Average' and study_hours_per_day > 3.0",
        "simulation": {"feature": "internet_quality", "operation": "set", "value": "Good"}
    },

    # ====================================================
    # 7. GÜNCELLENEN BÖLÜM: VERİMLİLİK & ODAK YÖNETİMİ (REFACTOR)
    # Strateji: Girdiyi artırma (Ders Ekleme), Sürtünmeyi azalt (Dikkat Dağıtıcıları Kes).
    # ====================================================

    # 1. Odak Oranı (Focus Ratio) Düzeltme
    # Mantık: Sosyal medyayı %40 azaltmak, Focus Ratio'yu matematiksel olarak %60 iyileştirir.
    {
        "id": "optimize_focus_ratio",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "🎯 **Lazer Odaklanma:** Masada geçirdiğin süre iyi ama 'Odak Oranın' düşük. Telefon yanındayken çalışmak, delik kovayla su taşımaya benzer. Sosyal medyayı %40 azaltırsan, mevcut çalışman 2 kat verimli hale gelir.",
        "condition": "focus_ratio < 0.6 and study_hours_per_day > 2.0",
        "simulation": {"feature": "social_media_hours", "operation": "multiply", "value": 0.6}
    },

    # 2. "Derin Çalışma" (Deep Work - Monk Mode)
    # Mantık: Toplam dikkat dağıtıcıları %80 azaltmak. Bu, modelde 'focus_ratio'yu tavan yaptırır.
    {
        "id": "monk_mode_activation",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "🧘 **Keşiş Modu:** Çalışma saatin az değil, sadece 'sığ'. Bildirimler, mesajlar... Zihnin bölünüyor. Telefonu kapatıp 'Uçak Modu'nda çalışırsan, 2 saatlik çalışma sana 5 saatlik verim sağlar. Zaman kazanmanın yolu budur.",
        "condition": "total_distraction_hours > 2.0 and study_hours_per_day > 3.0",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.2}
    },

    # 3. "Azalan Verim Yasası" (Diminishing Returns)
    # Mantık: Aşırı çalışmayı törpülemek. Azalan zaman V6.0 motorunda otomatik olarak 'Mental Health' veya 'Sleep'e gider.
    {
        "id": "diminishing_returns_fix",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "📉 **Çok Değil, Öz Çalış:** İstatistikler uyarıyor: Günde 7 saatin üzerindeki her dakika 'Çöp Zaman'. Beynin doldu. Çalışma süreni 6 saate İNDİRİP o 1 saati dinlenmeye ayırırsan, öğrendiklerin hafızanda kalıcı olur.",
        "condition": "study_hours_per_day > 7.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "set", "value": 6.0}
    },

    # 4. "Sabah Kuşu Avantajı" (Chronotype Shift)
    # Mantık: Gece uykusunu değil, sabah verimini hedefliyoruz. Mental sağlığı artırır.
    {
        "id": "morning_glory_routine",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "🌅 **Altın Saatler:** Gece 01:00'de çalışmakla Sabah 07:00'de çalışmak aynı değildir. Gece zihnin yorgun. Uykunu öne çekip sabahın sessizliğinde çalışırsan, konuyu anlama hızın iki katına çıkar.",
        "condition": "sleep_hours > 7.0 and mental_health_rating < 6",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 2}
    },

    # 5. "Multitasking Katili" (Single Tasking)
    # Mantık: Hem Netflix hem Sosyal Medya açıksa beyin yanar. İkisini de %50 kesiyoruz.
    {
        "id": "kill_multitasking",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "🤹 **Beynini Yakma:** Bir gözün dizide, bir gözün telefonda, aklın derste... Bu multitasking değil, beyin sisidir. İki ekranı da kapatıp tek bir işe odaklanırsan, 3 saatte bitecek iş 1 saatte biter.",
        "condition": "netflix_hours > 1.0 and social_media_hours > 1.0",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.5}
    },

    # 6. "Enerji Yönetimi" (Energy over Time)
    # Mantık: Çok uyuyor ama enerjisi düşükse (Mental Health düşük), Egzersiz ile enerji pompalıyoruz.
    # (Vitality Score formülünü destekler: sleep * exercise)
    {
        "id": "energy_activation",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "🔋 **Enerji Santrali:** Çok uyumana rağmen yorgun musun? Sorun uykusuzluk değil, hareketsizlik. Kan dolaşımın yavaşlamış. Günde 20 dakika tempolu yürüyüş, 2 kupa kahveden daha fazla odaklanma sağlar.",
        "condition": "sleep_hours > 8.0 and mental_health_rating < 5",
        "simulation": {"feature": "exercise_frequency", "operation": "add", "value": 2}
    },

    # 7. "Akıllı Kaynak Kullanımı" (Leverage Resources)
    # Mantık: İnternet iyiyse, çalışma verimi artar. Çalışma süresini çok az (%10) artırır ama etkisi yüksek olur.
    {
        "id": "smart_resource_leverage",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "💎 **Kaliteli Kaynak:** İyi bir internetin ve altyapın var ama notların potansiyelinin altında. Kitaba gömülmek yerine, o konunun en iyi YouTube videosunu izle. Görsel öğrenme hafızanı güçlendirir.",
        "condition": "internet_quality == 'Good' and study_hours_per_day < 3.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "multiply", "value": 1.1}
    },

    # 8. "Analog Mod" (Digital Detox Lite)
    # Mantık: Toplam dikkat dağınıklığını %60 azaltır.
    {
        "id": "analog_mode_switch",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "📝 **Analog Mod:** Dijital dünyada kaybolmuşsun. Bilgisayarı kapat. Sadece kağıt, kalem ve kitap. Bu 'Eski Usul' çalışma saati, bildirimlerin tacizinden kurtulmuş saf bir öğrenme deneyimi sunacak.",
        "condition": "total_distraction_hours > 4.0",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.4}
    },

    # ====================================================
    # 8. YENİ EKLENEN: KİŞİSELLEŞTİRİLMİŞ DERİN ANALİZ
    # ====================================================

    # --- 1. "Kendi Kendinin Mentoru" (Aile Eğitimi Desteği) ---
    {
        "id": "self_mentor_infrastructure",
        "category": "Infrastructure",
        "difficulty": "Medium",
        "text": "🎓 **Kendi Yolunu Çiz:** Aileden akademik destek sınırlı olabilir, bu senin suçun değil. Ama senin süper gücün 'İnternet'. Bağlantını güçlendirirsen, dünyanın en iyi hocaları odana gelir.",
        "condition": "parental_education_level in ['High School', 'None'] and internet_quality != 'Good'",
        "simulation": {"feature": "internet_quality", "operation": "set", "value": "Good"}
    },

    # --- 2. "Hayalet Öğrenci" (Yüksek Çalışma / Düşük Katılım) ---
    {
        "id": "ghost_student_paradox",
        "category": "Academic",
        "difficulty": "Easy",
        "text": "👻 **Hayalet Olma:** Evde çok çalışıyorsun ama okula gitmiyorsun. Unutma, sınavı hazırlayan kişi evdeki kitabın değil, sınıftaki hocan. Sadece derslere giderek çalışma yükünü azaltabilirsin.",
        "condition": "study_hours_per_day > 3.0 and attendance_percentage < 60.0",
        "simulation": {"feature": "attendance_percentage", "operation": "set", "value": 85.0}
    },

    # --- 3. "Azalan Verim Yasası" (Aşırı Çalışma Törpüsü) ---
    {
        "id": "diminishing_returns_fix",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "📉 **Çok Değil, Öz Çalış:** Günde 6 saatin üzerinde çalışmak beyni 'Çöp Bilgi' moduna sokar. Çalışma süreni 5 saate İNDİRİP dinlenirsen, beynin bilgileri daha iyi işleyecektir. Bazen az, çoktur.",
        "condition": "study_hours_per_day > 6.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "set", "value": 5.0}
    },

    # --- 4. "Çifte Tehlike" (Netflix + Sosyal Medya Birlikte) ---
    {
        "id": "entertainment_consolidation",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "⚔️ **Birini Feda Et:** Hem Netflix hem Sosyal Medya aynı anda yüksekse başarman imkansızlaşır. Stratejik bir karar ver: Ya dizileri bırak ya da Instagram'ı. İkisini birden taşıyamazsın.",
        "condition": "netflix_hours > 1.5 and social_media_hours > 1.5",
        "simulation": {"feature": "netflix_hours", "operation": "set", "value": 0.0}
    },

    # --- 5. "Genç Profesyonel" (Yaş Faktörü) ---
    {
        "id": "senior_student_focus",
        "category": "Academic",
        "difficulty": "Medium",
        "text": "🕴️ **Profesyonel Bakış:** Yaşın ve tecrüben gereği artık işi şansa bırakamazsın. Uyku ve çalışma düzenine getireceğin 15 dakikalık disiplin bile, senin olgunluğunla birleşince büyük fark yaratır.",
        "condition": "age >= 22 and sleep_hours < 7.0",
        "simulation": {"feature": "sleep_hours", "operation": "add", "value": 1.0}
    },

    # ====================================================
    # 9. YENİ EKLENEN: DAVRANIŞSAL PSİKOLOJİ & MİKRO ALIŞKANLIKLAR
    # ====================================================

    # --- 1. "2 Dakika Kuralı" (Sıfır Çekenler İçin) ---
    {
        "id": "two_minute_rule",
        "category": "Discipline",
        "difficulty": "Easy",
        "text": "🚀 **Sadece 2 Dakika:** Gözünde büyütme. Kendine 'Sadece 2 dakika çalışıp bırakacağım' de. Masaya oturmak en zor kısımdır. Bir kez başladığında, beynin devamını getirecek.",
        "condition": "study_hours_per_day < 0.5",
        "simulation": {"feature": "study_hours_per_day", "operation": "set", "value": 0.5}
    },

    # --- 2. "Sosyal Simyacı" (Social Alchemist) ---
    {
        "id": "social_study_group",
        "category": "Social",
        "difficulty": "Easy",
        "text": "🧪 **Sosyal Zekanı Kullan:** Arkadaş canlısı birisin, bu harika! Ama geyik muhabbeti yerine 'Kütüphane Buluşması' organize et. Sosyalleşme ihtiyacını ders çalışarak gidermek senin için oyun değiştirici olur.",
        "condition": "extracurricular_participation == 'Yes' and study_hours_per_day < 2.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
    },

    # --- 3. "Dopamin Detoksu" (Eğlence > Çalışma) ---
    {
        "id": "dopamine_reversal",
        "category": "Discipline",
        "difficulty": "Hard",
        "text": "🧠 **Beynini Kandır:** Şu an beynin ucuz eğlenceye (Netflix) alışmış durumda. Dizi süresini ders süresinin ALTINA indirdiğin an, beynin sıkılacak ve ders çalışmayı 'daha çekici' bulmaya başlayacak.",
        "condition": "netflix_hours > study_hours_per_day and study_hours_per_day > 0",
        "simulation": {"feature": "netflix_hours", "operation": "multiply", "value": 0.4}
    },

    # ====================================================
    # 10. YENİ EKLENEN: KRİZ VE ZİRVE YÖNETİMİ
    # ====================================================

    # --- 1. "Acil Durum Çekici" (Emergency Protocol) ---
    {
        "id": "emergency_protocol_attendance",
        "category": "Academic",
        "difficulty": "Hard",
        "text": "🚨 **KIRMIZI ALARM:** Durum ciddi. Plan, program, diyet... Hepsini unut. Tek bir görevin var: Sadece derse git. Devamsızlığını düzeltmezsen diğer hiçbir şey seni kurtarmaz.",
        "condition": "attendance_percentage < 60.0 and study_hours_per_day < 1.5",
        "simulation": {"feature": "attendance_percentage", "operation": "set", "value": 85.0}
    },

    # --- 2. "Zirve Koruma" (Maintenance Mode) ---
    {
        "id": "peak_maintenance_mindset",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🏆 **Şampiyon Kalmak:** Zirvedesin, harika! Ama orada kalmak, oraya çıkmaktan zordur. Şimdi amacın daha çok çalışmak değil, 'kafanı rahatlatmak' olmalı. Mental sağlığını koru ki düşüş yaşama.",
        "condition": "study_hours_per_day > 6.0 and attendance_percentage > 90.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 2}
    },

    # --- 3. "Gizli Cevher" (Düşük Profil, Yüksek Zeka) ---
    {
        "id": "smart_work_leverage",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "💎 **Akıllı Oyna:** Az çalışıyorsun ama kaynakların sağlam. 'Çok' değil 'Akıllı' çalışarak rakiplerini geçebilirsin. Kaliteli kaynaklarla günde +45 dk odaklı çalışma sana yeter de artar.",
        "condition": "study_hours_per_day < 2.5 and internet_quality == 'Good' and mental_health_rating > 6",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.75}
    },

    # ====================================================
    # 11. YENİ EKLENEN: BIOHACKING & NÖRO-OPTİMİZASYON
    # ====================================================

    # --- 1. "Bağırsak-Beyin Aksı" (Gut-Brain Connection) ---
    {
        "id": "gut_brain_axis_hack",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🧬 **Biyohack:** Mutluluk hormonu serotoninin %90'ı bağırsakta üretilir. Kötü beslenmek seni mutsuz ve odaklanamaz yapıyor. 'Fast Food'u kesip sağlıklı beslenmek, en güçlü ilaçtan daha etkilidir.",
        "condition": "diet_quality == 'Poor' and mental_health_rating < 6",
        "simulation": {"feature": "diet_quality", "operation": "set", "value": "Good"}
    },

    # --- 2. "Uyku Döngüsü Mühendisliği" (Sleep Architecture) ---
    {
        "id": "rem_cycle_optimization",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "🌙 **REM Mühendisliği:** Uykun fena değil ama 'Tam Döngü'yü kaçırıyorsun. Bir uyku döngüsü 90 dakikadır. Uykunu 7.5 saate (5 tam döngü) ayarlarsan, sabah 'zombi' gibi değil, fişek gibi uyanırsın.",
        "condition": "sleep_hours >= 6.0 and sleep_hours < 7.0",
        "simulation": {"feature": "sleep_hours", "operation": "set", "value": 7.5}
    },

    # --- 3. "Kortizol Yönetimi" (Stres Altında Performans) ---
    {
        "id": "cortisol_flush_exercise",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🔥 **Stres Temizliği:** Stres seviyen beynini kilitliyor. En iyi stres ilacı koşmaktır. Haftada 3 gün ter atarak kanındaki stres hormonu kortizolu temizle ve zihnini aç.",
        "condition": "mental_health_rating < 4 and exercise_frequency < 3",
        "simulation": {"feature": "exercise_frequency", "operation": "set", "value": 3}
    },

    # ====================================================
    # 12. YENİ EKLENEN: ÖZEL ÖĞRENCİ ARKETİPLERİ (PERSONA)
    # ====================================================

    # --- 1. "Keşiş Disiplini" (The Monk) ---
    {
        "id": "monk_mode_activation",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "🧘 **Keşiş Modu:** İnanılmaz bir iraden var! Dikkat dağıtıcıların sıfır. Ama bu boş zamanı derse çevirmiyorsun. Önünde hiçbir engel yok; sadece masaya otur ve potansiyelini serbest bırak.",
        "condition": "(social_media_hours + netflix_hours) < 1.0 and study_hours_per_day < 3.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 2.0}
    },

    # --- 2. "Yetenek Tuzağı" (The Talent Trap) ---
    {
        "id": "talent_trap_warning",
        "category": "Discipline",
        "difficulty": "Hard",
        "text": "🐇 **Tavşan ve Kaplumbağa:** Zekana ve altyapına güveniyorsun ama unutma: 'Çalışmayan yetenek, çalışan azme yenilir.' Güvendiğin zekanı disiplinle taçlandırmazsan geride kalırsın.",
        "condition": "study_hours_per_day < 2.0 and parental_education_level in ['Master', 'PhD']",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.5}
    },

    # --- 3. "Fedakar Emekçi" (The Grinder) ---
    {
        "id": "grinder_optimization",
        "category": "Lifestyle",
        "difficulty": "Medium",
        "text": "⚙️ **Demir Adam:** Hem iş, hem spor, hem okul... İnanılmaz bir tempon var. Senin için zaman nakittir. Uykudan çalamayız, ama kalitesini artırabiliriz. Odanı karanlık ve serin tutarak uykundan %100 verim al.",
        "condition": "part_time_job == 'Yes' and exercise_frequency > 2 and attendance_percentage > 80",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 2}
    },

# ====================================================
    # 13. YENİ EKLENEN: YAŞ VE ADAPTASYON PSİKOLOJİSİ
    # (Üniversite Evrelerine Göre Özel Uyarılar)
    # ====================================================

    # --- 1. "Freshman Şoku" (Üniversiteye Başlangıç) ---
    # Durum: Yaşı 19 veya altı VE Çalışma Saati Düşük.
    # Psikoloji: Lise mantığıyla üniversiteyi geçebileceğini sanıyor.
    # Strateji: Erken uyarı sistemi.
    {
        "id": "freshman_reality_check",
        "category": "Academic",
        "difficulty": "Easy",
        "text": "👶 **Lise Bitti, Uyan:** Üniversiteye hoş geldin. Buradaki oyunun kuralları liseden farklı; zeka yetmez, sistem gerekir. İlk senende ipin ucunu kaçırırsan toparlaman 3 yıl sürer. Günde +45 dakika ile temelini sağlam at.",
        "condition": "age <= 19 and study_hours_per_day < 2.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.75}
    },

    # --- 2. "Mezuniyet Sendromu" (Kariyer Kaygısı) ---
    # Durum: Yaşı 23 ve üzeri VE Mental Sağlık Düşük.
    # Psikoloji: Gelecek kaygısı (iş bulma stresi) performansı düşürüyor.
    # Strateji: Kaygıyı eyleme dönüştürmek.
    {
        "id": "senior_anxiety_conversion",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🎓 **Gelecek Kaygısı:** Mezuniyet yaklaştıkça stresin artıyor, bunu görebiliyorum. Ama kaygı, sallanan sandalye gibidir; sallanırsın ama yol alamazsın. Stresini atmak için spora başla, zihnin berraklaşsın.",
        "condition": "age >= 23 and mental_health_rating < 5",
        "simulation": {"feature": "exercise_frequency", "operation": "set", "value": 3}
    },

    # --- 3. "Orta Sınıf Rehaveti" (Sophomore Slump) ---
    # Durum: Yaş 20-21, Her şey "Average" veya "Fair".
    # Psikoloji: "Ne başındayım ne sonundayım" rahatlığı.
    # Strateji: Silkinip kendine gelmek.
    {
        "id": "sophomore_slump_break",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "⚓ **Konfor Alanı Tuzağı:** Yolun ortasındasın ve rehavet çökmesi çok doğal. Ama vasatlık (ortalama olmak) yapışkan bir hastalıktır. Bir yerden zinciri kır: Beslenmeni 'İyi' seviyeye çek ve farkı hisset.",
        "condition": "age in [20, 21] and study_hours_per_day < 3.0 and diet_quality == 'Fair'",
        "simulation": {"feature": "diet_quality", "operation": "set", "value": "Good"}
    },

    # ====================================================
    # 14. YENİ EKLENEN: KAYNAK YÖNETİMİ & PARADOKSLAR
    # (Var Olup Da Kullanılmayan Potansiyeller)
    # ====================================================

    # --- 1. "Dijital Mirasyedi" (Resource Waster) ---
    # Durum: İnternet 'Good', Aile Eğitimi Yüksek AMA Çalışma Düşük.
    # Psikoloji: Elindeki imkanların kıymetini bilmemek.
    # Strateji: Kaynakları verime dönüştürmek.
    {
        "id": "resource_waster_alert",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "👑 **Altın Tepsi:** Harika bir internetin ve eğitimli bir ailen var. Çoğu öğrenci bu imkanlara sahip değil. Elindeki 'Ferrari'yi garajda çürütme. Bu imkanlarla günde 1 saat çalışmak bile seni uçurur.",
        "condition": "internet_quality == 'Good' and parental_education_level in ['Bachelor', 'Master'] and study_hours_per_day < 1.5",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.5}
    },

    # --- 2. "Yalancı Çalışma" (Pseudo-Work / The Fake Busy) ---
    # Durum: Masada çok kalıyor (>5 saat) AMA Telefon da elinden düşmüyor (>3 saat).
    # Psikoloji: Kendini kandırmak. "Bugün çok çalıştım" diyip aslında Instagram'da gezmek.
    # Strateji: Sert bir gerçeklik kontrolü.
    {
        "id": "pseudo_work_reality",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "🎭 **Kendini Kandırma:** Günde 5 saat masada oturup 3 saat telefona bakıyorsan, sen ders çalışmıyorsun; masada 'takılıyorsun'. Bu verimsizliği durdur. Sosyal medyayı kes, o 2 saati gerçek dinlenmeye ayır.",
        "condition": "study_hours_per_day > 5.0 and social_media_hours > 3.0",
        # Simülasyon: Sosyal medyayı azalttığımızda, aslında 'Verimli Çalışma' artmış gibi model tepki verir.
        "simulation": {"feature": "social_media_hours", "operation": "multiply", "value": 0.3}
    },

    # --- 3. "Finansal Stres Yönetimi" (The Struggling Worker) ---
    # Durum: Part-time çalışıyor VE Beslenme Kötü.
    # Psikoloji: Para/Zaman kısıtı yüzünden kötü besleniyor, bu da beyni yavaşlatıyor.
    # Strateji: Uygun maliyetli ama beyin dostu beslenme (Su, Yumurta vs.)
    {
        "id": "financial_fuel_fix",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🔋 **Ekonomik Yakıt:** Hem çalışıp hem okuyorsun, bütçe ve zaman kısıtlı, biliyorum. Ama kötü beslenmek (şeker/hamur) beynini sisli yapar. En azından suyu artırıp şekeri keserek beslenme kaliteni 'Orta' seviyeye taşı.",
        "condition": "part_time_job == 'Yes' and diet_quality == 'Poor'",
        "simulation": {"feature": "diet_quality", "operation": "set", "value": "Fair"}
    },

    # ====================================================
    # 15. GÜNCELLENEN BÖLÜM: DERİNLEMESİNE VERİMLİLİK VE SINIR YÖNETİMİ
    # Strateji: Mikro alışkanlıklar, Biyolojik Ritim ve Psikolojik Sınırlar.
    # ====================================================

    # 1. "Pomodoro Başlangıç Kiti"
    # Mantık: Çalışma saati eklemez, Netflix süresinden çalarak denge kurar.
    {
        "id": "pomodoro_kickstart",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "🍅 **Domates Tekniği:** Uzun süre odaklanamıyorsan kendini zorlama. 25 dakika ders, 5 dakika 'Netflix Molası' değil, 'Nefes Molası'. Bu teknikle dikkatin dağılmadan çalışabilirsin.",
        "condition": "study_hours_per_day < 2.0 and netflix_hours > 2.0",
        "simulation": {"feature": "netflix_hours", "operation": "multiply", "value": 0.5}
    },

    # 2. "Parkinson Yasası" (Süre Kısıtlaması)
    # Mantık: "Bir iş, bitirilmesi için ayrılan süre kadar uzar." Çalışma süresini kısarak yoğunluğu artırıyoruz.
    {
        "id": "parkinsons_law_limit",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "⏳ **Süre Kısıtlaması:** 'Bütün gün çalışacağım' dersen, o çalışma bütün güne yayılır ve verimsizleşir. Kendine 'Bu konu 2 saatte bitecek' de ve süreyi kısıtla. Baskı altında beynin elmas üretir.",
        "condition": "study_hours_per_day > 5.0 and mental_health_rating < 6",
        "simulation": {"feature": "study_hours_per_day", "operation": "multiply", "value": 0.8}
    },

    # 3. "Mavi Işık Vampiri" (Biyolojik Ritim)
    # Mantık: Gece sosyal medyayı kesmek, uyku kalitesini artırır (Vitality Score artışı).
    {
        "id": "blue_light_blocker",
        "category": "Wellness",
        "difficulty": "Hard",
        "text": "🧛 **Mavi Işık Vampiri:** Gece telefona bakmak beynine 'Güneş doğdu, uyanık kal' sinyali gönderiyor. Uyumadan 1 saat önce telefonu başka odaya bırakırsan, uyku kaliten %40 artacak.",
        "condition": "sleep_hours < 6.5 and social_media_hours > 4.0",
        "simulation": {"feature": "social_media_hours", "operation": "set", "value": 1.0}
    },

    # 4. "Pareto Prensibi" (80/20 Kuralı)
    # Mantık: Az çalışıp yüksek not alan (ama potansiyeli daha yüksek olan) öğrenciye ince ayar.
    {
        "id": "pareto_principle_optimization",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "📊 **80/20 Kuralı:** Sonuçlarının %80'i, çalışmalarının %20'sinden geliyor. Hangi konuların sınavda daha çok çıktığını analiz et ve sadece onlara odaklan. Gereksiz detaylarda boğulma.",
        "condition": "study_hours_per_day < 3.0 and attendance_percentage > 90.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 1.5}
    },

    # 5. "Aktif Hatırlama" (Active Recall)
    # Mantık: Pasif okumayı (düşük verim) aktif çalışmaya çevirmek. Mental yükü hafifletir.
    {
        "id": "active_recall_switch",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "🧠 **Okuma, Kendine Sor:** Kitabı defalarca okumak öğrenmek değildir, sadece tanışıklıktır. Kitabı kapat ve 'Ne hatırlıyorum?' diye kendine sor. Bu zorlanma, nöronlarını birbirine bağlar.",
        "condition": "study_hours_per_day > 4.0 and mental_health_rating < 5",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 2.0}
    },

    # 6. "Mikro Alışkanlıklar" (Tiny Habits)
    # Mantık: Hiç çalışmayan öğrenciye (0 saat), sadece "başlangıç" yaptırmak.
    {
        "id": "tiny_habits_start",
        "category": "Discipline",
        "difficulty": "Easy",
        "text": "🌱 **Tohum Ek:** Günde 10 dakika bile olsa masaya otur. Amaç ders çalışmak değil, 'masaya oturma alışkanlığını' kazanmak. Zinciri kırma, gerisi kendiliğinden gelir.",
        "condition": "study_hours_per_day < 0.5",
        "simulation": {"feature": "study_hours_per_day", "operation": "set", "value": 0.5}
    },

    # 7. "Hayır Deme Sanatı" (Sınır Yönetimi)
    # Mantık: Sosyal aktivite çok fazlaysa (>Yes), bunu dengelemek gerekir.
    # Not: 'No' yapmak yerine etkisini azaltıyoruz (Ders saatini koruyarak).
    {
        "id": "say_no_muscle",
        "category": "Social",
        "difficulty": "Medium",
        "text": "🛑 **Sınır Çiz:** Arkadaşlarınla vakit geçirmek güzel ama hedeflerinden çalıyorsa 'Hayır' demeyi öğrenmelisin. Bu hafta sonu yapılan 3 plandan sadece 1'ine git, diğer 2'sini kendine ayır.",
        "condition": "extracurricular_participation == 'Yes' and study_hours_per_day < 2.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
    },

    # 8. "Akış Durumu Tetikleyicisi" (Flow State Ritual)
    # Mantık: Dikkat dağınıklığı yüksekse, ritüel ile odaklanma.
    {
        "id": "flow_state_ritual",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "🌊 **Akışa Gir:** Derse başlamadan önce kendine bir ritüel belirle (Bir kahve, lo-fi müzik, telefon sessize). Beynini 'Şimdi odaklanma zamanı' moduna şartla. Akışa girdiğinde zamanın nasıl geçtiğini anlamayacaksın.",
        "condition": "focus_ratio < 0.5 and total_distraction_hours > 3.0",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.7}
    },
# ====================================================
    # 16. YENİ EKLENEN: ZİHİNSEL DETOKS & HOBİ TERAPİSİ (WELLNESS 2.0)
    # Strateji: Mental Sağlık Puanını artırarak 'Study Efficiency' çarpanını yükseltmek.
    # ====================================================

    # 1. "Mikro-Meditasyon" (Zihin Sıfırlama)
    # Mantık: Mental sağlık düşükse, çalışma verimi de düşüktür. 10 dk meditasyon verimi artırır.
    {
        "id": "mindfulness_reset",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "🧘‍♂️ **Zihin Duşu:** Zihnin o kadar dolu ki yeni bilgiye yer kalmamış. Günde sadece 10 dakika (Headspace veya Calm ile) meditasyon yapmak, beynindeki 'açık sekmeleri' kapatır ve işlemci hızını artırır.",
        "condition": "mental_health_rating < 5 and study_hours_per_day > 3.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 1.5}
    },

    # 2. "Dijital Gün Batımı" (Doğa Terapisi)
    # Mantık: Ekran süresini azaltıp, bu süreyi mental dinlenmeye (Doğa) aktarmak.
    {
        "id": "digital_sunset_nature",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🌲 **Yeşil Reçete:** Ekran ışığı ruhunu emiyor. Telefonu evde bırak ve 30 dakika dışarı çık. Ağaçlara ve gökyüzüne bakmak, dikkat dağınıklığını %20 azaltan bilimsel bir yöntemdir.",
        "condition": "total_distraction_hours > 3.0 and mental_health_rating < 6",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.7}
    },

    # 3. "Yaratıcı Deşarj" (Hobi Edinme)
    # Mantık: Okul dışı aktivitesi olmayan ama stresli öğrenciye "Sanatsal/Yaratıcı" bir çıkış yolu.
    # (Extracurricular 'Yes' yapmak dedication puanını artırır).
    {
        "id": "creative_outlet_art",
        "category": "Social", # Veya Wellness, ama modelde extracurricular Social ile tetikleniyor
        "difficulty": "Easy",
        "text": "🎨 **Ruhunu Boya:** Sürekli mantıklı düşünmek beyni yorar. Bir enstrüman çalmak, resim yapmak veya yazı yazmak beyninin sağ lobunu çalıştırır. Bu 'Yaratıcı Mola', ders çalışırken analitik zekanı keskinleştirir.",
        "condition": "extracurricular_participation == 'No' and mental_health_rating < 5",
        "simulation": {"feature": "extracurricular_participation", "operation": "set", "value": "Yes"}
    },

    # 4. "Şükran Günlüğü" (Pozitif Psikoloji)
    # Mantık: Depresif moda giren öğrencinin motivasyonunu artırmak.
    {
        "id": "gratitude_journaling",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "📔 **Şükran Günlüğü:** Her sabah 'Minnettar olduğun 3 şeyi' yazmak klişe gelebilir ama dopamin seviyeni artırır. Daha mutlu bir beyin, daha hızlı öğrenir. Güne negatif değil, pozitif başla.",
        "condition": "mental_health_rating <= 4",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 2.0}
    },

    # 5. "4-7-8 Nefes Tekniği" (Anlık Stres Yönetimi)
    # Mantık: Sınav kaygısı veya yoğun çalışma stresi olanlar için.
    {
        "id": "breathing_technique_478",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "🌬️ **Panik Butonu:** Stresten kalbin çarpıyor, odaklanamıyorsun. Hemen dur. 4 saniye nefes al, 7 saniye tut, 8 saniye ver. Bunu 4 kez yap. Beynin 'Savaş ya da Kaç' modundan çıkıp 'Öğren' moduna geçecek.",
        "condition": "study_hours_per_day > 5.0 and mental_health_rating < 6",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 1.0}
    },

    # 6. "Uyku Öncesi Beyin Boşaltımı" (Brain Dump)
    # Mantık: Gece kafası dolu olduğu için uyuyamayanlara çözüm. Uyku kalitesini artırır.
    {
        "id": "bedtime_brain_dump",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "📝 **Zihin Çöpçüsü:** Gece yatağa girince aklına bin tane düşünce mi geliyor? Uyumadan önce hepsini bir kağıda yaz ve 'Yarına kadar bekle' de. Zihnin boşalınca uykuya dalış süren 10 dakikaya inecek.",
        "condition": "sleep_hours < 6.5 and study_hours_per_day > 4.0",
        "simulation": {"feature": "sleep_hours", "operation": "add", "value": 1.0}
        # Kalite arttığı için süre artmış gibi simüle ediyoruz.
    },

    # 7. "Haftalık Ödül Ritüeli" (Dopamin Yönetimi)
    # Mantık: Çok çalışan öğrenciye suçluluk duymadan eğlenme izni vermek.
    {
        "id": "guilt_free_reward",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "🏆 **Hakedilmiş Ödül:** Bütün hafta harika çalıştın. Şimdi bilgisayarı kapat ve en sevdiğin şeyi yap. Bu bir zaman kaybı değil, gelecek haftanın yakıt ikmalidir. Suçluluk duyma, tadını çıkar.",
        "condition": "study_hours_per_day > 5.0 and attendance_percentage > 90.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 2.5}
    },

    # 8. "Sosyal Detoks" (JOMO - Joy of Missing Out)
    # Mantık: Sosyal medya çok yüksekse ve mutsuzsa (FOMO), bunu kesmek mutluluk getirir.
    {
        "id": "jomo_embrace",
        "category": "Wellness",
        "difficulty": "Hard",
        "text": "📵 **Kaçırma Keyfi (JOMO):** Başkalarının hayatını izlemek seni mutsuz ediyor. Sosyal medyayı silip kendi hayatına odaklanmak, özgüvenini ve notlarını aynı anda yükseltecek tek hamledir.",
        "condition": "social_media_hours > 4.0 and mental_health_rating < 5",
        "simulation": {"feature": "social_media_hours", "operation": "multiply", "value": 0.2}
    },
# ====================================================
    # 17. YENİ EKLENEN: USTA PLANLAMACI & ZAMAN MİMARİSİ (ADVANCED EFFICIENCY)
    # Strateji: Zaman Yönetimi Teknikleri ile 'Study Efficiency' artırmak.
    # ====================================================

    # 1. "Zaman Bloklama" (Time Blocking)
    # Mantık: Dağınık çalışmayı önler. Dikkat dağınıklığını azaltır.
    {
        "id": "time_blocking_method",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "📅 **Zamanı Blokla:** Günün 'kevgir' gibi delik deşik. 'Ne zaman çalışacağım?' diye düşünmek enerji harcar. Gününü 'Ders Bloğu', 'Dinlenme Bloğu', 'Sosyal Blok' diye ayır. Karar yorgunluğunu bitir.",
        "condition": "total_distraction_hours > 3.0 and study_hours_per_day > 2.0",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.6}
    },

    # 2. "Eisenhower Matrisi" (Önemli vs Acil)
    # Mantık: Çok çalışıp az verim alan (meşgul ama verimsiz) öğrenci için.
    # Gereksiz işleri (busy work) atarak çalışma saatini azaltır ama verimi (Mental Health) artırır.
    {
        "id": "eisenhower_matrix_priority",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "⚖️ **Meşguliyet Tuzağı:** Çok çalışıyorsun ama yerinde sayıyorsun. Çünkü 'Önemli' işler yerine 'Acil' (ama gereksiz) işlerle uğraşıyorsun. Yapılacaklar listeni Eisenhower Matrisi ile sadeleştir. Az ama öz yap.",
        "condition": "study_hours_per_day > 6.0 and mental_health_rating < 5",
        "simulation": {"feature": "study_hours_per_day", "operation": "multiply", "value": 0.85}
        # Gereksiz çalışmayı atar, verim artar.
    },

    # 3. "Kurbağayı Ye" (Eat That Frog)
    # Mantık: Erteleme (Procrastination) hastalığı olanlar için.
    # En zor dersi sabah ilk iş halletmek.
    {
        "id": "eat_that_frog_first",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "🐸 **Kurbağayı Ye:** En zor, en korktuğun ders hangisi? Onu günün 'ilk işi' olarak yap. En zoru aradan çıkarmanın verdiği özgüven dopaminiyle günün geri kalanı çocuk oyuncağına döner.",
        "condition": "study_hours_per_day < 2.0 and mental_health_rating < 6",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
    },

    # 4. "Feynman Tekniği" (Öğreterek Öğrenme)
    # Mantık: Konuyu anladığını sanıp sınavda yapamayanlar için.
    # Mental Health (Özgüven) artırır.
    {
        "id": "feynman_technique_teach",
        "category": "Academic",
        "difficulty": "Medium",
        "text": "👨‍🏫 **Hoca Ol:** Bir konuyu basitçe anlatamıyorsan, anlamamışsın demektir. Odanın duvarına veya hayali bir öğrenciye konuyu sesli anlat. Takıldığın yer, eksik olduğun yerdir. (Feynman Tekniği).",
        "condition": "study_hours_per_day > 3.0 and attendance_percentage > 80.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 1.5}
    },

    # 5. "Zeigarnik Etkisi" (Yarıda Bırakma Sanatı)
    # Mantık: Derse başlamakta zorlananlar için psikolojik hile.
    {
        "id": "zeigarnik_effect_start",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "🧩 **Yarıda Bırak:** Derse başlamaya üşeniyor musun? Sadece kitabın kapağını aç ve ilk cümleyi oku, sonra bırak. Beynin 'tamamlanmamış işleri' sevmez ve seni o masaya geri çeker (Zeigarnik Etkisi).",
        "condition": "study_hours_per_day < 1.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.5}
    },

    # 6. "Uzaylı Tekrarı" (Spaced Repetition)
    # Mantık: Hafızayı güçlendirmek için çalışma sıklığını (frequency) değil kalitesini artırır.
    {
        "id": "spaced_repetition_system",
        "category": "Academic",
        "difficulty": "Hard",
        "text": "🧠 **Unutma Eğrisi:** Bugün çalıştığını 3 gün sonra unutacaksın. Bunu engellemek için 'Aralıklı Tekrar' (Spaced Repetition) yap. 1 saatlik blok çalışma yerine, konuyu 3 güne yayarak 20'şer dakika çalış.",
        "condition": "study_hours_per_day > 4.0 and study_hours_per_day < 6.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 1.0}
    },

    # 7. "5 Saniye Kuralı" (Mel Robbins)
    # Mantık: Yataktan kalkamayan veya telefona dalanlar için anlık aksiyon.
    {
        "id": "five_second_rule_action",
        "category": "Discipline",
        "difficulty": "Easy",
        "text": "🚀 **5-4-3-2-1 Başla:** Aklına 'Ders çalışmam lazım' fikri geldiği an 5 saniyen var. Eğer 5 saniye içinde harekete geçmezsen beynin bahaneler üretir. İçinden 5'ten geriye say ve roket gibi fırla.",
        "condition": "total_distraction_hours > 5.0",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.8}
    },
# ====================================================
    # 18. YENİ EKLENEN: SINAV HACKER & STRATEJİK SALDIRI (EXAM TACTICS)
    # Strateji: Çalışma süresini artırmadan, sınav anındaki puanı maksimize etme.
    # ====================================================

    # 1. "Çıkmış Sorular Arkeolojisi" (Past Papers)
    # Mantık: Hoca'nın soru sorma stilini çözmek. Çalışma verimini (Mental Health/Güven) artırır.
    {
        "id": "past_papers_archeology",
        "category": "Academic",
        "difficulty": "Easy",
        "text": "🔍 **Sınav Arkeolojisi:** Konuyu bilmek yetmez, hocayı bilmek gerekir. Son 5 yılın çıkmış sorularını bul ve çöz. Göreceksin ki soruların %40'ı aslında kendini tekrar ediyor. Amerika'yı yeniden keşfetme.",
        "condition": "study_hours_per_day > 2.0 and attendance_percentage > 70.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 2.0}
    },

    # 2. "Hata Defteri" (Error Log)
    # Mantık: Bildiğini değil, yapamadığını çalışmak.
    {
        "id": "error_log_optimization",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "📓 **Kara Kutu Analizi:** Deneme sınavlarında yanlış yaptıklarını geçiştirme. Onlar senin hazinendir. Bir 'Hata Defteri' tut ve sadece yanlışlarına odaklan. Bir hatayı bir kez yaparsan ders olur, iki kez yaparsan tercih olur.",
        "condition": "study_hours_per_day > 4.0 and mental_health_rating < 6",
        "simulation": {"feature": "study_hours_per_day", "operation": "multiply", "value": 1.2}
        # Verimi artırır, sanki %20 daha fazla çalışmış gibi etki eder.
    },

    # 3. "Sınav Simülasyonu" (Mock Exam)
    # Mantık: Sınav kaygısını (Düşük Mental Health) yenmek için evde sınav provası yapmak.
    {
        "id": "exam_simulation_mode",
        "category": "Wellness",
        "difficulty": "Hard",
        "text": "🎭 **Prova Sahnesi:** Sınavda heyecanlanıyorsan, evde sınav ortamı kur. Telefonu kapat, süreyi başlat ve masadan kalkma. Beynini o stresli ortama alıştırırsan, gerçek sınavda nabzın bile yükselmez.",
        "condition": "mental_health_rating < 4 and study_hours_per_day > 3.0",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 3.0}
    },

    # 4. "Hile Kağıdı Metodu" (Cheat Sheet - Hazırlamak için, kullanmak için değil!)
    # Mantık: Tüm konuyu 1 A4 kağıdına özetlemek, sentez yeteneğini geliştirir.
    {
        "id": "cheat_sheet_synthesis",
        "category": "Academic",
        "difficulty": "Medium",
        "text": "📄 **Yasal Kopya:** Sınava sanki '1 sayfa kopya kağıdı sokmak serbestmiş' gibi hazırlan. Tüm dönemi tek bir A4 kağıdına özetlemeye çalış. Bu özetleme süreci, bilgiyi beynine lazerle kazır.",
        "condition": "study_hours_per_day > 2.5 and focus_ratio < 0.5",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.5}
    },

    # 5. "Tersine Mühendislik" (Reverse Engineering)
    # Mantık: Ders kitabını baştan sona okumak yerine, sorudan konuya gitmek.
    {
        "id": "reverse_engineering_study",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "⚙️ **Tersine Mühendislik:** Kitabı baştan sona okuyacak vaktin yok. Önce bölüm sonu sorularını oku, sonra o soruların cevabını metinde ara. Beynin 'cevap arama modunda'yken 3 kat hızlı okur.",
        "condition": "study_hours_per_day < 1.5 and attendance_percentage < 60.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "multiply", "value": 1.5}
    },
# ====================================================
    # 19. YENİ EKLENEN: SOSYAL ZEKA & AĞ KURMA (SOCIAL BOOST)
    # Strateji: Yalnızlığı gider, motivasyonu artır (Mental Health Boost).
    # ====================================================

    # 1. "Akran Mentörlüğü" (Peer Mentoring)
    # Durum: Notu yüksek ama yalnız çalışıyor.
    # Mantık: Başkasına anlatmak, öğrenmenin en üst düzeyidir (Feynman Tekniği).
    {
        "id": "peer_mentor_activation",
        "category": "Social",
        "difficulty": "Easy",
        "text": "🎓 **Hoca Olma Zamanı:** Notların harika ama bu bilgiyi kendine saklamak seni köreltir. Bir çalışma grubu kur ve arkadaşlarına konuları anlat. Öğretirken, çalıştığından 2 kat daha fazla öğrenirsin.",
        "condition": "exam_score > 80 and study_hours_per_day > 3.0 and extracurricular_participation == 'No'",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 1.5}
    },

    # 2. "Çalışma Partneri" (Accountability Partner)
    # Durum: Motivasyonu düşük (Mental Health < 5) ve az çalışıyor.
    # Mantık: Yalnızken kaytarmak kolaydır, partner varken zordur.
    {
        "id": "study_buddy_finder",
        "category": "Social",
        "difficulty": "Medium",
        "text": "u26d3 **Sorumluluk Ortağı:** Kendi kendine söz geçirmen zor olabilir. Bir 'Çalışma Partneri' bul. Birbirinize sadece 'Başladım' ve 'Bitti' mesajı atın. Bu küçük sosyal baskı, iradeni çelik gibi yapar.",
        "condition": "mental_health_rating < 5 and study_hours_per_day < 2.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
    },

    # 3. "Dijital İnziva - Sosyal Versiyon"
    # Durum: Çok sosyal medya kullanıyor ama gerçek sosyal aktivitesi yok.
    # Mantık: Sanal sosyalliği gerçeğe dönüştürmek.
    {
        "id": "virtual_to_real_social",
        "category": "Social",
        "difficulty": "Hard",
        "text": "☕ **Ekranı Kapat, Kahveye Çık:** Günde 3 saat başkalarının hayatını izliyorsun (Instagram). O sürenin yarısını gerçek bir arkadaşınla kahve içmeye ayır. Gerçek sosyalleşme stresini alır, sanal olan ise stres yükler.",
        "condition": "social_media_hours > 3.0 and extracurricular_participation == 'No'",
        "simulation": {"feature": "social_media_hours", "operation": "multiply", "value": 0.5}
    },

    # 4. "Kariyer Ağı" (LinkedIn Mode)
    # Durum: Son sınıf (Age > 22) ve sosyal aktivite yok.
    # Mantık: Mezuniyet yaklaşıyor, sadece ders yetmez.
    {
        "id": "career_networking_push",
        "category": "Social",
        "difficulty": "Medium",
        "text": "b1f0 **Gelecek Ağı:** Mezuniyete az kaldı. Sadece kütüphanede oturmak sana iş buldurmaz. Sektörel etkinliklere veya kariyer günlerine katıl. Bir kartvizit, bazen bir diplomadan daha kapı açıcıdır.",
        "condition": "age >= 22 and extracurricular_participation == 'No'",
        "simulation": {"feature": "mental_health_rating", "operation": "add", "value": 1.0} # Gelecek kaygısını azaltır
    },

    # 5. "Kütüphane Etkisi" (Environment Design)
    # Durum: Evde çalışamıyor (Düşük verim), sosyal ortamı seviyor.
    {
        "id": "library_social_effect",
        "category": "Social",
        "difficulty": "Easy",
        "text": "📚 **Sessiz Kalabalık:** Evde dikkatin dağılıyor. Kütüphaneye git. Etrafında çalışan insanları görmek, beynindeki 'Ayna Nöronları' tetikler ve sen de istemsizce odaklanırsın. En verimli sosyalleşme budur.",
        "condition": "study_hours_per_day < 2.0 and total_distraction_hours > 3.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.5}
    }
]

# =========================
# KAYDETME FONKSİYONLARI
# =========================

def save_catalog(
    json_path: str = "artifacts/recommendation_catalog.json",
    csv_path: Optional[str] = "artifacts/recommendation_catalog.csv",
    ensure_dir: bool = True
) -> None:
    """
    Kataloğu JSON ve CSV olarak kaydeder.
    """
    if ensure_dir:
        for p in [json_path, csv_path]:
            if p:
                os.makedirs(os.path.dirname(p), exist_ok=True)

    # JSON Kaydet
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(RECOMMENDATION_CATALOG, f, ensure_ascii=False, indent=2)

    # CSV Kaydet
    if csv_path:
        fieldnames = ["id", "category", "difficulty", "text", "condition", "simulation_feature", "simulation_op", "simulation_val"]
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rec in RECOMMENDATION_CATALOG:
                sim = rec.get("simulation", {})
                writer.writerow({
                    "id": rec["id"],
                    "category": rec.get("category", ""),
                    "difficulty": rec.get("difficulty", ""),
                    "text": rec.get("text", ""),
                    "condition": rec.get("condition", ""),
                    "simulation_feature": sim.get("feature", ""),
                    "simulation_op": sim.get("operation", ""),
                    "simulation_val": sim.get("value", "")
                })

if __name__ == "__main__":
    save_catalog()
    print(f"✅ Katalog Kaydedildi! Toplam {len(RECOMMENDATION_CATALOG)} adet psikolojik derinliği olan öneri hazır.")

    # =========================
    # EK RAPOR VE GELİŞMİŞ GRAFİK BÖLÜMÜ
    # =========================
    import matplotlib.pyplot as plt
    from collections import Counter

    # Raporlarda özellikle vurgulamak istediğimiz kritik davranış alanları
    # GÜNCELLEME: Yeni V2 metriklerini buraya ekledik
    CRITICAL_FEATURES = [
        "mental_health_rating",
        "sleep_hours",
        "social_media_hours",
        "attendance_percentage",
        "diet_quality",
        "vitality_score",  # YENİ
        "burnout_risk",  # YENİ
        "dedication_level"  # YENİ
    ]

    # Modelde kullanılan ve koşullarda geçmesini beklediğimiz değişkenler
    # GÜNCELLEME: Yeni V2 feature'larını buraya ekledik ki raporda eksik çıkmasın
    KNOWN_VARS = [
        "study_hours_per_day",
        "attendance_percentage",
        "social_media_hours",
        "netflix_hours",
        "sleep_hours",
        "exercise_frequency",
        "diet_quality",
        "extracurricular_participation",
        "internet_quality",
        "part_time_job",
        "mental_health_rating",
        "total_distraction_hours",
        "parental_education_level",
        "age",
        "focus_ratio",
        "lifestyle_balance",
        "vitality_score",  # YENİ
        "burnout_risk",  # YENİ
        "dedication_level"  # YENİ
    ]


    def generate_text_overview() -> None:
        """
        RECOMMENDATION_CATALOG için genel özet rapor:
        - Toplam öneri sayısı
        - Kategori dağılımı
        - Zorluk (difficulty) dağılımı
        - Simülasyon operasyon tipleri
        """
        total = len(RECOMMENDATION_CATALOG)
        categories = Counter(rec.get("category", "Unknown") for rec in RECOMMENDATION_CATALOG)
        difficulties = Counter(rec.get("difficulty", "Unknown") for rec in RECOMMENDATION_CATALOG)
        sim_ops = Counter(rec.get("simulation", {}).get("operation", "none") for rec in RECOMMENDATION_CATALOG)

        print("\n" + "=" * 70)
        print("📊 ÖNERİ KATALOĞU GENEL ÖZETİ")
        print("=" * 70)
        print(f"• Toplam öneri (kural) sayısı: {total}\n")

        print("• Kategori bazlı dağılım:")
        for cat, cnt in sorted(categories.items(), key=lambda x: x[0]):
            oran = (cnt / total) * 100 if total else 0
            print(f"   - {cat:<18}: {cnt:>3} adet (%{oran:4.1f})")

        print("\n• Zorluk (difficulty) bazlı dağılım:")
        for diff, cnt in sorted(difficulties.items(), key=lambda x: x[0]):
            oran = (cnt / total) * 100 if total else 0
            print(f"   - {diff:<8}: {cnt:>3} adet (%{oran:4.1f})")

        print("\n• Simülasyon işlem tipleri (operation):")
        for op, cnt in sorted(sim_ops.items(), key=lambda x: x[0]):
            oran = (cnt / total) * 100 if total else 0
            print(f"   - {op:<8}: {cnt:>3} adet (%{oran:4.1f})")

        print("=" * 70 + "\n")


    def generate_feature_stats() -> Counter:
        """
        Hangi değişkenlere (feature) en çok müdahale edildiğini analiz eder.
        Dönen Counter, grafik üretiminde de kullanılabilir.
        """
        features = Counter(
            rec.get("simulation", {}).get("feature", "none")
            for rec in RECOMMENDATION_CATALOG
        )

        print("\n📌 Simülasyonda hedeflenen değişkenler (feature) – İlk 5")
        print("-" * 70)
        for feature, cnt in features.most_common(5):
            print(f"   - {feature:<30}: {cnt} kural")

        return features


    def generate_feature_graph(features: Counter, output_dir: str = "artifacts") -> None:
        """
        En çok hedeflenen feature'lar için bar grafiği üretir.
        """
        os.makedirs(output_dir, exist_ok=True)

        top_items = features.most_common(7)
        if not top_items:
            return

        labels = [x[0] for x in top_items]
        values = [x[1] for x in top_items]

        plt.figure()
        plt.bar(labels, values)
        plt.title("En Çok Hedeflenen Değişkenler (Feature)")
        plt.xlabel("Feature")
        plt.ylabel("Kural Sayısı")
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        path = os.path.join(output_dir, "catalog_top_features.png")
        plt.savefig(path)
        plt.close()

        print(f"   ➜ Feature grafiği kaydedildi: {path}")


    def generate_category_difficulty_matrix() -> Counter:
        """
        Kategori × Zorluk (difficulty) matrisi üretir ve konsola özetler.
        Örnek: Academic | Hard -> 5 kural
        """
        matrix = Counter(
            (rec.get("category", "Unknown"), rec.get("difficulty", "Unknown"))
            for rec in RECOMMENDATION_CATALOG
        )

        print("\n📌 Kategori × Zorluk matrisi")
        print("-" * 70)
        for (cat, diff), cnt in sorted(matrix.items()):
            print(f"   - {cat:<18} | {diff:<8} -> {cnt:>2} kural")

        return matrix


    def generate_risk_area_stats() -> None:
        """
        Mental sağlık, uyku, sosyal medya gibi kritik alanlar için
        kaç kuralın doğrudan ilgili feature'ı hedeflediğini raporlar.
        """
        print("\n📌 Kritik davranış alanlarını hedefleyen kural sayıları")
        print("-" * 70)
        for feat in CRITICAL_FEATURES:
            cnt = sum(
                1 for rec in RECOMMENDATION_CATALOG
                if rec.get("simulation", {}).get("feature") == feat
            )
            print(f"   - {feat:<24}: {cnt} kural")


    def generate_condition_complexity_stats() -> None:
        """
        Koşulların (condition) karmaşıklığını analiz eder:
        - Basit (hiç and/or yok)
        - Orta (1 tane and/or)
        - Karmaşık (2+ and/or)
        """
        simple = 0
        medium = 0
        complex_ = 0

        for rec in RECOMMENDATION_CATALOG:
            cond = rec.get("condition", "") or ""
            and_count = cond.count(" and ")
            or_count = cond.count(" or ")
            total_ops = and_count + or_count

            if total_ops == 0:
                simple += 1
            elif total_ops == 1:
                medium += 1
            else:
                complex_ += 1

        print("\n📌 Koşul karmaşıklığı analizi")
        print("-" * 70)
        print(f"   - Basit   (tek şart)      : {simple}")
        print(f"   - Orta    (1 bağlaç)      : {medium}")
        print(f"   - Karmaşık (2+ bağlaç)    : {complex_}")


    def generate_variable_coverage_report() -> None:
        """
        Bilinen değişkenlerin (KNOWN_VARS) condition içinde kaç kuralda
        kullanıldığını raporlar.
        """
        print("\n📌 Değişken kapsam analizi (condition içinde geçenler)")
        print("-" * 70)
        for var in KNOWN_VARS:
            cnt = sum(
                1 for rec in RECOMMENDATION_CATALOG
                if var in (rec.get("condition", "") or "")
            )
            if cnt > 0:
                print(f"   - {var:<28}: {cnt} kuralda kullanılıyor")


    def generate_all_reports_and_graphs(output_dir: str = "artifacts") -> None:
        """
        Tek çağrıyla tüm metin raporlarını ve grafikleri üretir.
        Hocaya sunumda kullanmak için ideal özet.
        """
        # Metin bazlı raporlar
        generate_text_overview()
        feature_counter = generate_feature_stats()
        generate_category_difficulty_matrix()
        generate_risk_area_stats()
        generate_condition_complexity_stats()
        generate_variable_coverage_report()

        # Grafikler
        print("\n📈 Grafik üretimi başlatılıyor...")
        try:
            generate_feature_graph(feature_counter, output_dir=output_dir)
        except Exception as e:
            print(f"⚠️ Feature grafiği üretimi sırasında hata oluştu: {e}")
        print("📈 Grafik üretimi tamamlandı.\n")


    # Bu blok, dosya doğrudan çalıştırıldığında (python oneriler.py) ek raporu üretir.
    # Üstteki orijinal __main__ bloğu önce çalışır (kataloğu kaydeder),
    # ardından bu blok gelişmiş analiz ve grafikleri oluşturur.
    if __name__ == "__main__":
        print("\n=== GELİŞMİŞ RAPOR VE GRAFİK ÇIKTILARI ===")
        generate_all_reports_and_graphs()

