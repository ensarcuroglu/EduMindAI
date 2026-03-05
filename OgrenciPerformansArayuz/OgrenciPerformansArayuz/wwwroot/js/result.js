$(document).ready(function () {
    console.log("🚀 Result Page Initialized");

    // --- 1. Circle Progress & Counter Animations ---
    const circumference = 377; // 2 * pi * 60

    function setProgress(percent, elementSelector) {
        const offset = circumference - (percent / 100) * circumference;
        const circle = document.querySelector(elementSelector);
        if (circle) {
            circle.style.strokeDasharray = `${circumference} ${circumference}`;
            circle.style.strokeDashoffset = circumference;
            setTimeout(() => { circle.style.strokeDashoffset = offset; }, 500);
        }
    }

    // Skor Animasyonlarını Başlat
    if (typeof CURRENT_SCORE !== 'undefined') setProgress(CURRENT_SCORE, '.current-wrapper .val');
    if (typeof POTENTIAL_SCORE !== 'undefined') setProgress(POTENTIAL_SCORE, '.potential-wrapper .val');

    // Sayıları Saydır (Counter Up)
    $('.counter-anim').each(function () {
        const $this = $(this);
        const targetText = $this.attr('data-target') ? $this.attr('data-target').replace(',', '.') : "0";
        const target = parseFloat(targetText);
        const decimals = $this.attr('data-decimals') ? parseInt($this.attr('data-decimals')) : 0;

        $({ countNum: 0 }).animate({
            countNum: target
        },
            {
                duration: 2500,
                easing: 'swing',
                step: function () {
                    $this.text(this.countNum.toFixed(decimals));
                },
                complete: function () {
                    $this.text(this.countNum.toFixed(decimals));
                }
            });
    });

    // --- 2. Slider Interaction ---
    $('#targetScoreSlider').on('input', function () {
        $('#targetScoreDisplay').text($(this).val());
    });

    // --- 3. Negotiation Logic (TAM HALİ) ---
    $('#btnNegotiate').click(function (e) {
        e.preventDefault();

        const $btn = $(this);
        // Diğer değişkenleri burada tanımlasak bile, handleSuccess içinde tekrar tanımlamak en güvenlisidir.

        if (typeof STUDENT_DATA === 'undefined') return;

        // --- YENİ LOADING STATE BAŞLATMA ---
        $btn.addClass('loading').prop('disabled', true);
        $btn.find('.btn-text').text('AI Analiz Ediyor...');

        // Prepare Payload
        const targetScore = parseFloat($('#targetScoreSlider').val());
        const frozenFeatures = [];
        $('.feature-lock:checked').each(function () {
            frozenFeatures.push($(this).val());
        });

        const payload = {
            StudentData: STUDENT_DATA,
            TargetScore: targetScore,
            FrozenFeatures: frozenFeatures
        };

        // AJAX Request
        $.ajax({
            url: '/Home/Negotiate',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            success: function (response) {
                setTimeout(() => handleSuccess(response), 1200);
            },
            error: function (xhr) {
                console.warn("Backend hatası veya ağ sorunu.");
                setTimeout(() => {
                    resetButtonState();
                    alert("Bir hata oluştu. Lütfen tekrar deneyin.");
                }, 1000);
            }
        });

        function resetButtonState() {
            $btn.removeClass('loading').prop('disabled', false);
            $btn.find('.btn-text').text("Yeni Rota Hesapla");
        }

        function handleSuccess(response) {
            // ---------------------------------------------------------
            // 1. HAZIRLIK VE TEMİZLİK
            // ---------------------------------------------------------
            resetButtonState(); // Buton loading durumunu kapat

            const $mentorMessage = $('#mentorMessage');
            const $changesList = $('#changesList');
            const $resultBox = $('#negotiationResult');
            const $resultHeader = $resultBox.find('.result-header');

            console.log("📥 Backend'den Gelen Cevap:", response);

            // ---------------------------------------------------------
            // 2. GÜVENLİ JSON PARSING
            // ---------------------------------------------------------
            let data = response;
            if (typeof response === 'string') {
                try {
                    data = JSON.parse(response);
                } catch (e) {
                    console.error("JSON Parse Hatası:", e);
                    alert("Sunucudan gelen veri işlenemedi.");
                    return;
                }
            }

            // Backend'den gelen verileri al (Farklı isimlendirmelere karşı önlem)
            const changesData = data.required_changes || data.changes || [];
            const messageData = data.mentor_message || data.msg || "Sonuç hazır.";

            // Status değerini normalize et (küçük harfe çevir)
            const status = (data.status || "").toString().toLowerCase();

            // UI'ı Temizle (Önceki başarılı/başarısız durum sınıflarını sil)
            $resultBox.removeClass('hidden visible success-mode error-mode');
            $changesList.empty();

            // ---------------------------------------------------------
            // 3. DURUM: IMPOSSIBLE / FAIL (HATA VE UYARI DURUMU)
            // ---------------------------------------------------------
            if (status === "impossible" || status === "fail") {
                // Kutuya CSS'teki hata stilini ekle
                $resultBox.addClass('visible error-mode');

                // Başlığı Hata Formatına Çevir
                $resultHeader.html(`
            <div class="error-icon-anim">
                <i class="fa-solid fa-triangle-exclamation"></i>
            </div>
            <span class="error-title">Hedefine Ulaşılamadı!</span>
        `);

                // Mentor Mesajını Yaz
                $mentorMessage.html(messageData);

                // Kullanıcıya Ne Yapması Gerektiğini Gösteren Kart
                $changesList.html(`
            <div class="change-item fade-in-up">
                <div class="error-suggestion">
                    <i class="fa-solid fa-arrow-trend-down"></i>
                    <span>Hedef puanı biraz düşürmeyi veya kilitlediğin özellikleri (Netflix, Uyku vb.) serbest bırakmayı dene.</span>
                </div>
            </div>
        `);

                // Sonuç kutusuna kaydır
                $('html, body').animate({ scrollTop: $resultBox.offset().top - 150 }, 600);

                // Hata durumunda konfeti patlatmıyoruz ve fonksiyondan çıkıyoruz
                return;
            }

            // ---------------------------------------------------------
            // 4. DURUM: SUCCESS (BAŞARI VE ANLAŞMA DURUMU)
            // ---------------------------------------------------------
            if (status === "success") {
                // Kutuya CSS'teki başarı stilini ekle
                $resultBox.addClass('visible success-mode');

                // Başlığı Başarı Formatına Çevir
                $resultHeader.html(`
            <div class="success-icon-anim"><i class="fa-solid fa-check"></i></div>
            <span>Anlaşma Sağlandı!</span>
        `);

                // Mentor Mesajını Yaz
                $mentorMessage.text(messageData);

                // --- SÖZLÜK VE HARİTALAMA ---
                const termDictionary = {
                    "study_hours_per_day": { label: "Günlük Çalışma", icon: "fa-solid fa-book-open", color: "text-primary", unit: "Saat" },
                    "social_media_hours": { label: "Sosyal Medya", icon: "fa-brands fa-instagram", color: "text-danger", unit: "Saat" },
                    "netflix_hours": { label: "Netflix / Dizi", icon: "fa-solid fa-tv", color: "text-danger", unit: "Saat" },
                    "sleep_hours": { label: "Uyku Süresi", icon: "fa-solid fa-moon", color: "text-secondary", unit: "Saat" },
                    "attendance_percentage": { label: "Derse Katılım", icon: "fa-solid fa-school", color: "text-info", unit: "%" },
                    "diet_quality": { label: "Beslenme Düzeni", icon: "fa-solid fa-apple-whole", color: "text-success", unit: "" }
                };

                const dietMap = { 'Poor': 'Kötü', 'Fair': 'Orta', 'Good': 'İyi' };

                // --- LİSTELEME DÖNGÜSÜ ---
                if (changesData.length > 0) {
                    changesData.forEach((change, index) => {
                        let featureKey = change.feature;
                        let oldVal = change.old;
                        let newVal = change.new;

                        // Eğer özellik adı yoksa ama text varsa (Fallback)
                        if (!featureKey && change.text) {
                            $changesList.append(`<div class="change-item"><div class="simple-text">${change.text}</div></div>`);
                            return;
                        }

                        // Metadata al
                        const meta = termDictionary[featureKey] || { label: featureKey, icon: "fa-solid fa-circle", color: "text-muted", unit: "" };

                        // Değerleri Formatla
                        let oldValDisplay = typeof oldVal === 'number' ? parseFloat(oldVal).toFixed(1) : oldVal;
                        let newValDisplay = typeof newVal === 'number' ? parseFloat(newVal).toFixed(1) : newVal;

                        // Diyet Kalitesi Çevirisi
                        if (featureKey === 'diet_quality') {
                            oldValDisplay = dietMap[oldVal] || oldVal;
                            newValDisplay = dietMap[newVal] || newVal;
                        }

                        // Animasyon Gecikmesi
                        const delayStyle = `animation-delay: ${index * 0.1}s`;

                        // HTML Kart Oluştur
                        const html = `
                    <div class="change-item fade-in-up" style="${delayStyle}">
                        <div class="change-info">
                            <div class="change-icon-box ${meta.color}">
                                <i class="${meta.icon}"></i>
                            </div>
                            <div class="change-label">
                                <span>${meta.label}</span>
                                <small>Gerekli Değişim</small>
                            </div>
                        </div>
                        
                        <div class="change-values">
                            <div class="val-box old">
                                <span class="num">${oldValDisplay}</span>
                                <span class="unit">${meta.unit}</span>
                            </div>
                            <div class="change-arrow">
                                <i class="fa-solid fa-arrow-right-long"></i>
                            </div>
                            <div class="val-box new">
                                <span class="num">${newValDisplay}</span>
                                <span class="unit">${meta.unit}</span>
                            </div>
                        </div>
                    </div>
                `;
                        $changesList.append(html);
                    });
                } else {
                    // Liste boşsa (Her şey yolundaysa)
                    $changesList.append('<div class="change-item text-success"><i class="fa-solid fa-check"></i> Hedefin mevcut düzeninle zaten uyumlu!</div>');
                }

                // Sonuç kutusuna kaydır
                $('html, body').animate({ scrollTop: $resultBox.offset().top - 150 }, 600);

                // Başarı durumunda konfeti patlat
                triggerConfetti();
            }
        }
    });

    // --- Confetti ---
    function triggerConfetti() {
        if (typeof confetti === 'function') {
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#6366f1', '#ec4899', '#14b8a6']
            });
        }
    }
});