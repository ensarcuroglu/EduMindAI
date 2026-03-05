# -*- coding: utf-8 -*-
"""
oneriler.py — Gelişmiş Öneri Kataloğu (Gold Edition)
Bu modül, oneri_motoru.py'nin simülasyon (Counterfactual Analysis) yapabilmesi için
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
    # 7. YENİ EKLENEN: STRATEJİK OPTİMİZASYON & ODAK YÖNETİMİ
    # ====================================================

    # --- 1. Odak Oranı (Focus Ratio) Düzeltme ---
    {
        "id": "optimize_focus_ratio",
        "category": "Efficiency",
        "difficulty": "Hard",
        "text": "🎯 **Lazer Odaklanma:** Masada çok kalıyorsun ama dikkatin sürekli bölünüyor. Sadece sosyal medyayı %30 azaltmak bile 'Odak Oranını' ikiye katlar. Az zamanda çok iş yapmak istiyorsan formül bu.",
        "condition": "focus_ratio < 0.5 and study_hours_per_day > 2.0",
        "simulation": {"feature": "social_media_hours", "operation": "multiply", "value": 0.6}
    },

    # --- 2. Yaşam Tarzı Dengesi (Lifestyle Balance) ---
    {
        "id": "lifestyle_rebalance_swap",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "⚖️ **Enerji Takası:** Uykuyu biraz fazla seviyor olabilir misin? Uykundan sadece 1 saat kısıp bunu doğrudan derse aktarırsan, başarı grafiğinin nasıl dikleşeceğini göreceksin. Adil bir takas.",
        "condition": "lifestyle_balance > 2.5 and sleep_hours > 8.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
    },

    # --- 3. "Gizli Potansiyel" (High Mental Health Leverage) ---
    {
        "id": "leverage_mental_resilience",
        "category": "Academic",
        "difficulty": "Easy",
        "text": "🧠 **Psikolojik Üstünlük:** Mental dayanıklılığın harika seviyede (8+). Bu, stres olmadan daha fazla yükü kaldırabileceğin anlamına geliyor. Korkmadan vites artırabilirsin, motorun bu hızı kaldırır.",
        "condition": "mental_health_rating >= 8 and study_hours_per_day < 3.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.5}
    },

    # --- 4. Hafta Sonu Kampı Simülasyonu ---
    {
        "id": "weekend_bootcamp",
        "category": "Academic",
        "difficulty": "Medium",
        "text": "📅 **Hafta Sonu Kampı:** Hafta içi zaman bulamıyorsan strateji değiştir. Cumartesi ve Pazar yapacağın toplam 6 saatlik yoğunlaştırılmış çalışma, tüm haftanın açığını kapatmaya yeter.",
        "condition": "study_hours_per_day < 2.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.8}
    },

    # --- 5. "Son %1" Mükemmeliyetçilik (Akademik Disiplin) ---
    {
        "id": "perfect_attendance_bonus",
        "category": "Academic",
        "difficulty": "Hard",
        "text": "🥇 **Altın Rozet:** İyisin, ama en iyisi olabilirsin. 'Sıfır Kayıp' politikasıyla derslere %100 katılım sağlarsan, akademik bağlılık puanın tavan yapar ve hocaların gözdesi olursun.",
        "condition": "attendance_percentage > 90.0 and attendance_percentage < 98.0",
        "simulation": {"feature": "attendance_percentage", "operation": "set", "value": 100.0}
    },

    # --- 6. Dijital Minimalizm (Extreme) ---
    {
        "id": "digital_minimalism_radical",
        "category": "Discipline",
        "difficulty": "Hard",
        "text": "🛑 **Dijital OHAL İlanı:** Eğlenceye ayırdığın vakit, ders sürenin 3 katı! Bu sürdürülebilir değil. Radikal bir kararla ekran süreni günde 1 saate indirmezsen potansiyelin heba olacak.",
        "condition": "total_distraction_hours > (study_hours_per_day * 3) and study_hours_per_day > 0.5",
        "simulation": {"feature": "social_media_hours", "operation": "set", "value": 0.5}
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
    # 15. YENİ EKLENEN: DERİNLEMESİNE VERİMLİLİK VE SINIR YÖNETİMİ
    # ====================================================

    # --- 1. "Pomodoro Başlangıç Kiti" (Dikkat Dağınıklığı Çözümü) ---
    # Durum: Az çalışıyor (<2s) VE Odak Oranı Düşük (<0.4).
    # Psikoloji: Uzun süre masada kalamayanlara "parçala ve yönet" taktiği.
    {
        "id": "pomodoro_kickstart",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "🍅 **Domates Tekniği:** Masada uzun süre kalamıyorsun, sorun değil. 25 dakika ders, 5 dakika mola. Bu döngüyü günde sadece 4 kez yaparsan, verimin saatlerce boş boş oturan birinden fazla olur.",
        "condition": "study_hours_per_day < 2.0 and focus_ratio < 0.4",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.8}
    },

    # --- 2. "Uyku Borcu Tahsilatı" (Hafta Sonu Uykusu) ---
    # Durum: Hafta içi az uyuyor (<6s) VE Mental Sağlık Düşük.
    # Strateji: Hafta sonu stratejik uyku ile toparlanma.
    {
        "id": "sleep_debt_recovery",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "💤 **Uyku Borcunu Öde:** Hafta içi uykusuzluktan tükenmişsin. Beynin 'Hata Veriyor'. Bu hafta sonu için tek hedefin günde 9 saat uyuyarak zihinsel reset atmak olsun. Pazartesiye fişek gibi başla.",
        "condition": "sleep_hours < 6.0 and mental_health_rating < 5",
        "simulation": {"feature": "sleep_hours", "operation": "add", "value": 2.0} # Ortalamayı yükseltir
    },

    # --- 3. "Sosyal Medya Vampiri" (Gece Kullanımı) ---
    # Durum: Uyku az (<6s) VE Sosyal Medya çok (>4s).
    # Psikoloji: Mavi ışık uykuyu kaçırıyor, uyku kaçınca telefona bakılıyor. Kısır döngü.
    {
        "id": "blue_light_blocker",
        "category": "Wellness",
        "difficulty": "Hard",
        "text": "🧛 **Mavi Işık Vampiri:** Gece telefona bakmak beynine 'Güneş doğdu, uyanık kal' sinyali gönderiyor. Uyumadan 1 saat önce telefonu başka odaya bırakırsan, uyku kaliten %40 artacak.",
        "condition": "sleep_hours < 6.5 and social_media_hours > 4.0",
        "simulation": {"feature": "social_media_hours", "operation": "set", "value": 1.0}
    },

    # --- 4. "Sınav Öncesi Depar" (Crunch Time) ---
    # Durum: Çalışma iyi (4s+) AMA yetmiyor, potansiyel var.
    # Strateji: Kısa süreliğine limiti zorlamak.
    {
        "id": "final_sprint_push",
        "category": "Academic",
        "difficulty": "Hard",
        "text": "🏁 **Son Düzlük:** Tempon harika ama bitiş çizgisi göründü. Şu an konfor alanından çıkıp günde +1.5 saat daha ekleyerek rakiplerine toz yutturma zamanı. Sadece 2 hafta dayan, sonra dinlenirsin.",
        "condition": "study_hours_per_day >= 4.0 and study_hours_per_day < 6.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.5}
    },

    # --- 5. "Beslenme ile Zihin Açma" (Su Tüketimi) ---
    # Durum: Beslenme 'Poor' VE Mental Sağlık 'Düşük'.
    # Bilgi: Dehidrasyon (susuzluk) dikkati %20 düşürür.
    {
        "id": "hydration_brain_boost",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "💧 **Beyin Suyu Sever:** Odaklanamamanın sebebi sadece susuzluk olabilir mi? Beyninin %75'i sudur. Günde 2.5 litre su içmeye başladığın an, o zihinsel sisin dağıldığını göreceksin.",
        "condition": "diet_quality == 'Poor' and mental_health_rating < 5",
        "simulation": {"feature": "diet_quality", "operation": "set", "value": "Fair"}
    },

    # --- 6. "Kulüp Ağı" (Networking) ---
    # Durum: Sosyal yönü zayıf (No activity) VE Notlar İyi (>4s çalışma).
    # Strateji: Akademik başarıyı sosyal ağla taçlandırmak.
    {
        "id": "networking_leverage",
        "category": "Social",
        "difficulty": "Medium",
        "text": "🕸️ **Ağını Ör:** Notların süper ama iş hayatında 'Kim olduğun' kadar 'Kimi tanıdığın' da önemli. Kütüphaneden çık ve bir öğrenci kulübüne gir. Gelecekteki iş ortağın orada olabilir.",
        "condition": "study_hours_per_day > 4.0 and extracurricular_participation == 'No'",
        "simulation": {"feature": "extracurricular_participation", "operation": "set", "value": "Yes"}
    },

    # --- 7. "Netflix'i Ödüle Dönüştürme" ---
    # Durum: Netflix orta seviye (1-2s).
    # Psikoloji: Yasaklamak yerine ödül mekanizması kurmak.
    {
        "id": "netflix_reward_system",
        "category": "Discipline",
        "difficulty": "Medium",
        "text": "🎁 **Ödül Maması:** Diziyi yasaklamayalım, onu bir 'havuç' olarak kullanalım. 'Bugünkü konu bitmeden o bölüm açılmayacak' kuralını koy. Böylece izlediğin diziden suçluluk değil, keyif duyarsın.",
        "condition": "netflix_hours > 1.0 and netflix_hours < 2.5",
        "simulation": {"feature": "netflix_hours", "operation": "multiply", "value": 0.5}
    },

    # --- 8. "Sabah Kuşu Avantajı" (Early Bird) ---
    # Durum: Çok uyuyor (>9s) VE Çalışma Saati Düşük.
    # Strateji: Sabahın sessizliğini kullanmak.
    {
        "id": "morning_glory_routine",
        "category": "Efficiency",
        "difficulty": "Medium",
        "text": "🌅 **Altın Saatler:** Gece herkes ayaktayken değil, sabah herkes uyurken çalış. Sabah 06:00-09:00 arası zihnin en açık olduğu zamandır. Uykudan kısıp sabah saatlerine eklemek sana süper güç kazandırır.",
        "condition": "sleep_hours > 9.0 and study_hours_per_day < 3.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.5}
    },

    # --- 9. "Hareketsizlik Kırıcı" (Desk Job Syndrome) ---
    # Durum: Çok ders çalışıyor (>5s) AMA Hiç Egzersiz Yok (0).
    # Risk: Fiziksel ağrılar dikkati dağıtır.
    {
        "id": "posture_performance_fix",
        "category": "Wellness",
        "difficulty": "Easy",
        "text": "chair **Sandalye Tuzağı:** Çok çalışıyorsun ama bel/boyun ağrıların yakında seni durduracak. Sandalyeden kalk! Günde sadece 15 dakika esneme hareketi yapmak, çalışma ömrünü yıllarca uzatır.",
        "condition": "study_hours_per_day > 5.0 and exercise_frequency == 0",
        "simulation": {"feature": "exercise_frequency", "operation": "set", "value": 1}
    },

    # --- 10. "Mükemmeliyetçilik Felci" (Analysis Paralysis) ---
    # Durum: Mental sağlık düşük, çalışma saati düşük, ama hedef yüksek.
    # Psikoloji: "En iyisini yapamayacaksam hiç yapmayayım" korkusu.
    {
        "id": "beat_perfectionism",
        "category": "Mental",
        "difficulty": "Easy",
        "text": "🔨 **Kervan Yolda Düzülür:** Mükemmel zamanı veya mükemmel planı bekleme; onlar gelmeyecek. 'Kötü de olsa başla'. 15 dakika kötü çalışmak, hiç çalışmamaktan sonsuz kat iyidir.",
        "condition": "mental_health_rating < 4 and study_hours_per_day < 1.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 0.5}
    },

    # --- 11. "Part-Time Kahramanı" (İş + Okul Dengesi) ---
    # Durum: Çalışıyor, Uyku az, Ders az.
    # Strateji: Gerçekçi hedef koyma.
    {
        "id": "working_student_reality",
        "category": "Academic",
        "difficulty": "Medium",
        "text": "⚖️ **Denge Sanatı:** Hem iş hem okul... Süpermen değilsin. Uykundan daha fazla çalamazsın. Tek çaren hafta sonunu (iş yoksa) tamamen derse ayırmak. Hafta içi rölanti, hafta sonu tam gaz.",
        "condition": "part_time_job == 'Yes' and sleep_hours < 6.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
    },

    # --- 12. "Dijital Göçebe" (İnternet Bağımlısı ama İnterneti Kötü) ---
    # Durum: İnternet Kötü AMA Sosyal Medya Yüksek.
    # İroni: Kötü internetle bile vakit öldürebiliyor.
    {
        "id": "bad_net_social_addict",
        "category": "Discipline",
        "difficulty": "Hard",
        "text": "🐌 **Yavaş Zehir:** İnternetin yavaş, videolar donuyor ama sen yine de telefondasın. Bu, bağımlılığın kanıtıdır. Madem internet kötü, telefonu bırak ve o süreyi internetsiz yapılabilen tek şeye, kitaplara ayır.",
        "condition": "internet_quality == 'Poor' and social_media_hours > 3.0",
        "simulation": {"feature": "social_media_hours", "operation": "set", "value": 0.5}
    },

    # --- 13. "Beslenme ile Uyku Kalitesi" ---
    # Durum: Diyet Kötü, Uyku Kötü.
    # Bilgi: Ağır yemekler uyku kalitesini bozar.
    {
        "id": "diet_sleep_synergy",
        "category": "Wellness",
        "difficulty": "Medium",
        "text": "🍔 **Gece Atıştırması:** Gece yediğin o ağır yemekler vücudunu sabaha kadar çalıştırıyor, dinlenemiyorsun. Akşam yemeğini hafifletip uyku kaliteni artırırsan, sabah ders çalışacak enerjiyi bulursun.",
        "condition": "diet_quality == 'Poor' and sleep_hours < 6.5",
        "simulation": {"feature": "diet_quality", "operation": "set", "value": "Average"}
    },

    # --- 14. "Eski Usul Disiplin" (Kağıt Kalem) ---
    # Durum: Teknoloji (PC/Tel) kullanımı çok yüksek, verim düşük.
    {
        "id": "analog_mode_switch",
        "category": "Efficiency",
        "difficulty": "Easy",
        "text": "📝 **Analog Mod:** Dijital dünyada kaybolmuşsun. Bilgisayarı kapat. Sadece kağıt, kalem ve kitap. Bu 'Eski Usul' çalışma saati, bildirimlerin tacizinden kurtulmuş saf bir öğrenme deneyimi sunacak.",
        "condition": "total_distraction_hours > 4.0",
        "simulation": {"feature": "total_distraction_hours", "operation": "multiply", "value": 0.5}
    },

    # --- 15. "Son Şans Uyarısı" (Her şey kötü) ---
    # Durum: Not düşük, Çalışma yok, Devam yok.
    # Psikoloji: Şok etkisi yaratma.
    {
        "id": "rock_bottom_bounce",
        "category": "Discipline",
        "difficulty": "Hard",
        "text": "💥 **Dip Noktası:** İstatistikler yalan söylemez; bu gidişatın sonu okulun uzaması. Şu an 'Dip'tesin. Güzel haber şu: Buradan gidebileceğin tek yön 'Yukarı'. Bugün miladın olsun, 1 saat çalışarak geri dönüşü başlat.",
        "condition": "study_hours_per_day < 1.0 and attendance_percentage < 50.0",
        "simulation": {"feature": "study_hours_per_day", "operation": "add", "value": 1.0}
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
    CRITICAL_FEATURES = [
        "mental_health_rating",
        "sleep_hours",
        "social_media_hours",
        "attendance_percentage",
        "diet_quality",
    ]

    # Modelde kullanılan ve koşullarda geçmesini beklediğimiz değişkenler
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

