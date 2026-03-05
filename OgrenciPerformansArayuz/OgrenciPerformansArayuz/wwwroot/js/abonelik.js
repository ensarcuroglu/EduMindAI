document.addEventListener('DOMContentLoaded', function () {

    // --- DEĞİŞKENLER ---
    const billingToggle = document.getElementById('billingToggle');
    const proPriceEl = document.getElementById('proPrice');
    const stickyPriceEl = document.getElementById('stickyPrice');
    const billNoteEl = document.getElementById('billNote');
    const saveBadge = document.querySelector('.badge-save');

    const PRICE_MONTHLY = 49;
    const PRICE_YEARLY = 39; // İndirimli

    // --- 1. RAKAM ANİMASYONU (Rolling Numbers) ---
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // --- 2. TOGGLE MANTIĞI ---
    if (billingToggle) {
        billingToggle.addEventListener('change', function () {
            // Görsel Feedback (Tasarruf Hesaplayıcı)
            if (this.checked) {
                // Yıllık Mod
                animateValue(proPriceEl, PRICE_MONTHLY, PRICE_YEARLY, 500);
                if (stickyPriceEl) animateValue(stickyPriceEl, PRICE_MONTHLY, PRICE_YEARLY, 500);

                billNoteEl.style.opacity = 0;
                setTimeout(() => {
                    billNoteEl.innerText = "Yıllık 468₺ peşin faturalandırılır";
                    billNoteEl.style.opacity = 1;
                }, 200);

                // Tasarruf Badge Efekti
                saveBadge.style.backgroundColor = "#22c55e"; // Koyu Yeşil
                saveBadge.style.color = "#fff";
                saveBadge.innerHTML = "🔥 120₺ Cebinde!";
                saveBadge.style.transform = "scale(1.1)";
            } else {
                // Aylık Mod
                animateValue(proPriceEl, PRICE_YEARLY, PRICE_MONTHLY, 500);
                if (stickyPriceEl) animateValue(stickyPriceEl, PRICE_YEARLY, PRICE_MONTHLY, 500);

                billNoteEl.style.opacity = 0;
                setTimeout(() => {
                    billNoteEl.innerText = "Her ay faturalandırılır";
                    billNoteEl.style.opacity = 1;
                }, 200);

                // Reset Badge
                saveBadge.style.backgroundColor = "#dcfce7";
                saveBadge.style.color = "#166534";
                saveBadge.innerHTML = "%20 İndirim";
                saveBadge.style.transform = "scale(1)";
            }
        });
    }

    // --- 3. KONFETİ VE SATIN ALMA EFEKTİ ---
    window.startTrial = function (btnElement) {
        // Konfeti Patlat
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#6366f1', '#ec4899', '#22d3ee']
        });

        // Buton Durumu
        const originalText = btnElement.innerText;
        btnElement.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Yönlendiriliyor...';
        btnElement.disabled = true;

        // Yönlendirme Simülasyonu
        setTimeout(() => {
            // Gerçek senaryoda: window.location.href = '/Checkout';
            alert("Ödeme sayfasına yönlendiriliyorsunuz! (Demo)");
            btnElement.innerText = originalText;
            btnElement.disabled = false;
        }, 2000);
    }

    // --- 4. FAQ ACCORDION ---
    document.querySelectorAll('.faq-question').forEach(button => {
        button.addEventListener('click', () => {
            const faqItem = button.parentElement;
            const isActive = faqItem.classList.contains('active');

            // Hepsini kapat
            document.querySelectorAll('.faq-item').forEach(item => item.classList.remove('active'));

            // Tıklananı aç (eğer zaten açık değilse)
            if (!isActive) {
                faqItem.classList.add('active');
            }
        });
    });

    // --- 5. VANILLA TILT INIT (Otomatik çalışır ama manuel tetikleme gerekirse) ---
    // VanillaTilt kütüphanesi 'data-tilt' attribute'unu otomatik algılar.
});