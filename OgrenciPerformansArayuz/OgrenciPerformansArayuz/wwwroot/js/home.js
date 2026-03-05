document.addEventListener('DOMContentLoaded', function () {
    let currentStep = 1;
    const totalSteps = 3;

    // --- DOM ELEMENTLERİ ---
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressFill = document.getElementById('progressLine');
    const steps = document.querySelectorAll('.step-item');
    const form = document.getElementById('predictionForm');

    // AI Loading Overlay Elementleri
    const overlay = document.getElementById('ai-loading-overlay');
    const loadingText = document.getElementById('aiLoadingText');
    const aiProgressBar = document.getElementById('aiProgressBar');

    // Zaman Kotası Elementleri
    const timeInputs = document.querySelectorAll('.time-input');
    const alertBox = document.getElementById('timeBudgetAlert');
    const totalHoursSpan = document.getElementById('totalHoursCalc');

    // --- YENİ EKLENEN: Mental Durum Slider Elementleri ---
    const moodSlider = document.querySelector('.modern-range');

    // --- 1. ZAMAN KONTROLÜ (Canlı) ---
    function checkTimeBudget() {
        let total = 0;
        timeInputs.forEach(input => {
            const val = parseFloat(input.value);
            if (!isNaN(val)) total += val;
        });

        if (totalHoursSpan) totalHoursSpan.innerText = total;

        if (total > 24) {
            alertBox.classList.remove('hidden');
            // Hata durumunda ileri gitmeyi ve göndermeyi engelle
            disableButtons(true);
        } else {
            alertBox.classList.add('hidden');
            disableButtons(false);
        }
    }

    function disableButtons(isDisabled) {
        if (isDisabled) {
            submitBtn.disabled = true;
            submitBtn.style.opacity = "0.5";
            submitBtn.style.cursor = "not-allowed";
            nextBtn.disabled = true;
            nextBtn.style.opacity = "0.5";
            nextBtn.style.cursor = "not-allowed";
        } else {
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
            submitBtn.style.cursor = "pointer";
            nextBtn.disabled = false;
            nextBtn.style.opacity = "1";
            nextBtn.style.cursor = "pointer";
        }
    }

    // Inputları dinle
    timeInputs.forEach(input => input.addEventListener('input', checkTimeBudget));

    // --- 2. MENTAL DURUM SLIDER FONKSİYONU (YENİ) ---
    if (moodSlider) {
        // Sayfa açıldığında mevcut değeri çalıştır
        updateMood(moodSlider.value);

        // Slider değiştikçe güncelle
        moodSlider.addEventListener('input', function () {
            updateMood(this.value);
        });
    }

    function updateMood(value) {
        const textEl = document.getElementById('moodText');
        const emojiEl = document.getElementById('moodEmoji');
        const wrapper = document.querySelector('.mood-status');
        const emojiBox = document.querySelector('.emoji-box');

        // Öğrenci hali sözlüğü
        const moods = {
            1: { text: "Kritik: Tükenmişlik Sendromu", emoji: "📉" },
            2: { text: "Ağır Mental Yorgunluk", emoji: "😫" },
            3: { text: "Yüksek Stres ve Kaygı", emoji: "😟" },
            4: { text: "Düşük Odaklanma", emoji: "🤔" },
            5: { text: "Stabil / Nötr Durum", emoji: "😐" },
            6: { text: "Yönetilebilir Stres", emoji: "🙂" },
            7: { text: "Gelişime Açık Motivasyon", emoji: "💪" },
            8: { text: "Yüksek Bilişsel Performans", emoji: "🧠" },
            9: { text: "Tam Akademik Hazırbulunuşluk", emoji: "📚" },
            10: { text: "Optimal İyilik Hali (Flow)", emoji: "✨" }
        };

        // Değerleri güncelle
        if (moods[value]) {
            if (textEl) textEl.innerText = moods[value].text;
            if (emojiEl) emojiEl.innerText = moods[value].emoji;

            // Animasyon tetikle (emoji değişince zıplasın)
            if (emojiBox) {
                emojiBox.style.animation = 'none';
                emojiBox.offsetHeight; /* trigger reflow */
                emojiBox.style.animation = 'bounce 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            }

            // Renk tonunu değere göre ayarla
            if (wrapper) {
                if (value < 4) wrapper.style.color = "#e53e3e"; // Kırmızı
                else if (value < 8) wrapper.style.color = "#d69e2e"; // Sarı
                else wrapper.style.color = "#38b2ac"; // Yeşil
            }
        }
    }

    // --- 3. WIZARD NAVIGASYON FONKSİYONU ---
    function updateWizard() {
        // Tüm adımları gizle
        document.querySelectorAll('.wizard-step').forEach(el => el.classList.add('hidden-step'));

        // Aktif adımı göster
        const activeStep = document.getElementById(`step${currentStep}`);
        if (activeStep) activeStep.classList.remove('hidden-step');

        // Wizard Progress Bar Güncelle
        const percents = [15, 50, 100];
        progressFill.style.width = `${percents[currentStep - 1]}%`;

        // Step İkonlarını Güncelle
        steps.forEach(s => {
            const stepNum = parseInt(s.dataset.step);
            if (stepNum <= currentStep) s.classList.add('active');
            else s.classList.remove('active');
        });

        // Butonları Yönet
        if (currentStep === 1) prevBtn.classList.add('hidden');
        else prevBtn.classList.remove('hidden');

        if (currentStep === totalSteps) {
            nextBtn.classList.add('hidden');
            submitBtn.classList.remove('hidden');
        } else {
            nextBtn.classList.remove('hidden');
            submitBtn.classList.add('hidden');
        }
    }

    // --- 4. BUTON OLAYLARI ---

    // İleri Butonu
    nextBtn.addEventListener('click', () => {
        if (validateStep(currentStep)) {
            currentStep++;
            updateWizard();
        }
    });

    // Geri Butonu
    prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
    });

    // Validasyon Fonksiyonu
    function validateStep(step) {
        const activeDiv = document.getElementById(`step${step}`);
        const inputs = activeDiv.querySelectorAll('input, select');
        let isValid = true;

        inputs.forEach(input => {
            // Range slider her zaman geçerlidir, kontrol etmeye gerek yok
            if (input.type === 'range') return;

            if (!input.checkValidity()) {
                isValid = false;
                input.reportValidity(); // Tarayıcı baloncuğunu göster

                // Hata görsel efekti
                input.style.borderColor = "#ef4444"; // Tailwind red-500
                input.classList.add('shake-anim'); // CSS'de varsa titreme efekti

                setTimeout(() => {
                    input.style.borderColor = "rgba(255, 255, 255, 0.1)";
                    input.classList.remove('shake-anim');
                }, 2000);
            }
        });
        return isValid;
    }

    // --- 5. FORM SUBMIT (AI ANALİZ ANİMASYONU) ---
    form.addEventListener('submit', function (e) {
        // 1. Form geçerli mi kontrol et (HTML5 validasyonu)
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
            // İlk geçersiz elemanı bul ve göster
            const invalidInput = form.querySelector(':invalid');
            if (invalidInput) invalidInput.reportValidity();
            return;
        }

        // 2. Normal gönderimi DURDUR (Animasyon oynayacak)
        e.preventDefault();

        // 3. Butonu kilitle (Çift tıklamayı önle)
        submitBtn.disabled = true;

        // 4. Overlay'i Göster (Fade-in efekti ile)
        if (overlay) {
            overlay.classList.remove('hidden');
            // CSS transition tetiklenmesi için minik gecikme
            setTimeout(() => overlay.classList.add('active'), 10);
        }

        // 5. Animasyon Senaryosu (Zaman Çizelgesi)
        let progress = 0;

        // Başlangıç
        updateAiLoader(10, "Veriler doğrulanıyor...");

        // 800ms sonra
        setTimeout(() => {
            updateAiLoader(40, "Yapay zeka motoru başlatılıyor...");
        }, 800);

        // 1.6 saniye sonra
        setTimeout(() => {
            updateAiLoader(70, "Akademik ve biyolojik veriler işleniyor...");
        }, 1600);

        // 2.4 saniye sonra
        setTimeout(() => {
            updateAiLoader(90, "Size özel başarı rotası çiziliyor...");
        }, 2400);

        // 3.0 saniye sonra - BİTİŞ
        setTimeout(() => {
            updateAiLoader(100, "Analiz tamamlandı! Yönlendiriliyorsunuz...");

            // Kullanıcı %100'ü görsün diye yarım saniye bekle ve FORMU GÖNDER
            setTimeout(() => {
                form.submit();
            }, 1500);

        }, 3000);
    });

    // Yardımcı Fonksiyon: AI Loader Metin ve Bar Güncelleme
    function updateAiLoader(percent, text) {
        if (aiProgressBar) aiProgressBar.style.width = percent + '%';

        if (loadingText) {
            loadingText.style.opacity = 0; // Metni söndür
            setTimeout(() => {
                loadingText.innerText = text;
                loadingText.style.opacity = 1; // Yeni metni yak
            }, 200);
        }
    }
});