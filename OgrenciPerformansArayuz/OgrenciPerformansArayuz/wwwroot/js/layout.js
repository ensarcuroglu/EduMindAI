document.addEventListener('DOMContentLoaded', function () {

    // --- 1. DİNAMİK SELAMLAMA (Greeting) ---
    const greetingEl = document.getElementById('greetingText');
    if (greetingEl) {
        const hour = new Date().getHours();
        let text = "Merhaba,";
        let icon = "👋";

        if (hour >= 6 && hour < 12) { text = "Günaydın"; icon = "☀️"; }
        else if (hour >= 12 && hour < 17) { text = "Tünaydın"; icon = "👋"; }
        else if (hour >= 17 && hour < 22) { text = "İyi Akşamlar"; icon = "🌙"; }
        else { text = "İyi Geceler"; icon = "🦉"; }

        // Yumuşak geçiş efekti
        greetingEl.style.opacity = 0;
        setTimeout(() => {
            greetingEl.innerHTML = `${text} ${icon}`;
            greetingEl.style.transition = "opacity 0.6s ease";
            greetingEl.style.opacity = 1;
        }, 100);
    }

    // --- 2. SMART NAVBAR SCROLL (Morphing Effect) ---
    const navbar = document.querySelector('.glass-navbar');

    // Scroll olayını dinle
    const handleScroll = () => {
        const currentScrollY = window.scrollY;

        // 20px'den fazla aşağı inilirse 'scrolled' sınıfını ekle
        // Bu sınıf CSS'de yüksekliği düşürür, arkaplanı beyazlaştırır ve gölgeyi artırır.
        if (currentScrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    };

    window.addEventListener('scroll', handleScroll);
    // Sayfa ilk yüklendiğinde de kontrol et (refresh durumu için)
    handleScroll();

    // --- 3. MOBİL MENÜ ANIMASYONU ---
    const toggleBtn = document.getElementById('mobileToggle');
    const mobileMenu = document.getElementById('mobileMenu');

    if (toggleBtn && mobileMenu) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            mobileMenu.classList.toggle('show');

            // Hamburger ikonunu X'e dönüştürme animasyonu
            const spans = toggleBtn.querySelectorAll('.hamburger span');
            if (mobileMenu.classList.contains('show')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -8px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });

        // Menü açıkken dışarı tıklanırsa kapat
        document.addEventListener('click', (e) => {
            if (mobileMenu.classList.contains('show') && !mobileMenu.contains(e.target) && !toggleBtn.contains(e.target)) {
                mobileMenu.classList.remove('show');
                // İkonu sıfırla
                const spans = toggleBtn.querySelectorAll('.hamburger span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }

    // --- 4. FOOTER: GÜNÜN SÖZÜ (Fade-In Animasyonu) ---
    const quoteEl = document.getElementById('footerQuote');
    if (quoteEl) {
        const quotes = [
            "Başarı, her gün tekrarlanan küçük çabaların toplamıdır.",
            "Geleceği tahmin etmenin en iyi yolu, onu yaratmaktır.",
            "Yapabileceğine inan, yolun yarısını geçtin demektir.",
            "Bugün yaptıkların, yarınlarını inşa eder.",
            "Zorluklar, başarının değerini artıran süslerdir.",
            "En iyi yatırım, kendine yaptığın yatırımdır."
        ];

        // Rastgele seç ve animasyonla göster
        const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];

        // Başlangıç stili (görünmez ve biraz aşağıda)
        quoteEl.style.opacity = 0;
        quoteEl.style.transform = "translateY(10px)";
        quoteEl.style.transition = "all 0.8s cubic-bezier(0.22, 1, 0.36, 1)";

        setTimeout(() => {
            quoteEl.innerText = `"${randomQuote}"`;
            quoteEl.style.opacity = 1;
            quoteEl.style.transform = "translateY(0)";
        }, 400);
    }

    // --- 5. FOOTER: 3D TILT CARD EFFECT ---
    const tiltCard = document.getElementById('tiltCard');
    if (tiltCard) {
        tiltCard.addEventListener('mousemove', (e) => {
            const rect = tiltCard.getBoundingClientRect();
            // Mouse'un kart içindeki konumu
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Merkezden uzaklık yüzdesi (-1 ile 1 arası)
            const xPct = (x / rect.width - 0.5) * 2;
            const yPct = (y / rect.height - 0.5) * 2;

            // Dönüş açıları (Maksimum 15 derece eğim)
            const rotateX = yPct * -15;
            const rotateY = xPct * 15;

            // 3D Transform Uygula
            tiltCard.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.05)`;

            // Parlama Efektini Hareket Ettir
            const shine = tiltCard.querySelector('.card-shine');
            if (shine) {
                // Parlamayı mouse'un tersine hareket ettir
                shine.style.transform = `skewX(-20deg) translateX(${xPct * 100}px)`;
                shine.style.opacity = 0.8;
            }
        });

        tiltCard.addEventListener('mouseleave', () => {
            // Mouse çıkınca kartı sıfırla
            tiltCard.style.transform = `perspective(1000px) rotateX(0) rotateY(0) scale(1)`;

            // Parlamayı gizle
            const shine = tiltCard.querySelector('.card-shine');
            if (shine) {
                shine.style.opacity = 0;
            }
        });
    }

    // --- 6. NEWSLETTER BUTON ANİMASYONU ---
    const newsletterBtn = document.getElementById('newsletterBtn');
    const newsletterInput = document.getElementById('newsletterEmail');

    if (newsletterBtn && newsletterInput) {
        newsletterBtn.addEventListener('click', () => {
            const email = newsletterInput.value.trim();
            // Basit e-posta kontrolü
            if (email && email.includes('@')) {
                // Uçak uçurma animasyonunu tetikle (CSS class)
                newsletterBtn.classList.add('sent');

                setTimeout(() => {
                    // Butonu başarı durumuna getir
                    newsletterBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
                    newsletterBtn.classList.remove('sent');
                    newsletterBtn.style.backgroundColor = "#10b981"; // Yeşil renk

                    // Inputu güncelle
                    newsletterInput.value = "Abone oldunuz!";
                    newsletterInput.disabled = true;
                    newsletterInput.style.borderColor = "#10b981";
                }, 600); // Animasyon süresiyle senkronize
            } else {
                // Hata durumu: Inputu salla
                newsletterInput.style.borderColor = "#ef4444";

                // Shake animasyonu için geçici transform
                newsletterInput.animate([
                    { transform: 'translateX(0)' },
                    { transform: 'translateX(-5px)' },
                    { transform: 'translateX(5px)' },
                    { transform: 'translateX(0)' }
                ], {
                    duration: 300,
                    iterations: 1
                });
            }
        });

        // Inputa odaklanınca hata rengini kaldır
        newsletterInput.addEventListener('focus', () => {
            newsletterInput.style.borderColor = "";
        });
    }

    // --- 7. DROPDOWN MENÜ YÖNETİMİ (Merkezi) ---
    const dropdowns = {
        profile: {
            trigger: document.getElementById('profileTrigger'),
            menu: document.getElementById('profileDropdown')
        },
        tools: {
            // Wrapper içindeki trigger butonunu buluyoruz
            trigger: document.querySelector('#smartToolsDropdown .nav-dropdown-trigger'),
            menu: document.querySelector('#smartToolsDropdown .nav-drop-menu'),
            wrapper: document.getElementById('smartToolsDropdown')
        }
    };

    // Tüm dropdownları kapatma fonksiyonu
    const closeAllDropdowns = () => {
        if (dropdowns.profile.menu) dropdowns.profile.menu.classList.remove('active');
        if (dropdowns.tools.wrapper) dropdowns.tools.wrapper.classList.remove('active');

        // Araçlar menüsündeki okun yönünü düzelt
        if (dropdowns.tools.wrapper) {
            const arrow = dropdowns.tools.wrapper.querySelector('.arrow-icon');
            if (arrow) arrow.style.transform = 'rotate(0deg)';
        }
    };

    // Profil Dropdown Eventleri
    if (dropdowns.profile.trigger && dropdowns.profile.menu) {
        dropdowns.profile.trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = dropdowns.profile.menu.classList.contains('active');
            closeAllDropdowns(); // Önce diğerlerini kapat
            if (!isActive) dropdowns.profile.menu.classList.add('active');
        });
    }

    // Akıllı Araçlar Dropdown Eventleri
    if (dropdowns.tools.trigger && dropdowns.tools.wrapper) {
        dropdowns.tools.trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = dropdowns.tools.wrapper.classList.contains('active');
            closeAllDropdowns();

            if (!isActive) {
                dropdowns.tools.wrapper.classList.add('active');
                // Oku döndür
                const arrow = dropdowns.tools.trigger.querySelector('.arrow-icon');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        });
    }

    // Sayfada boş bir yere tıklayınca hepsini kapat
    document.addEventListener('click', (e) => {
        const isClickInsideProfile = dropdowns.profile.trigger?.contains(e.target) || dropdowns.profile.menu?.contains(e.target);
        const isClickInsideTools = dropdowns.tools.wrapper?.contains(e.target);

        if (!isClickInsideProfile && !isClickInsideTools) {
            closeAllDropdowns();
        }
    });

    // ESC tuşu ile kapatma
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllDropdowns();
            if (mobileMenu) {
                mobileMenu.classList.remove('show');
                // Hamburger ikonunu sıfırla
                if (toggleBtn) {
                    const spans = toggleBtn.querySelectorAll('.hamburger span');
                    spans[0].style.transform = 'none';
                    spans[1].style.opacity = '1';
                    spans[2].style.transform = 'none';
                }
            }
        }
    });

    // --- 8. BİLDİRİM ZİLİ (Basit Etkileşim) ---
    const notifBtn = document.querySelector('.notification-trigger');
    if (notifBtn) {
        notifBtn.addEventListener('click', function () {
            // Zili salla
            const icon = this.querySelector('i');
            icon.style.transition = "transform 0.2s ease";
            icon.style.transform = "rotate(15deg) scale(1.1)";

            setTimeout(() => {
                icon.style.transform = "rotate(-15deg) scale(1.1)";
                setTimeout(() => {
                    icon.style.transform = "rotate(0deg) scale(1)";
                }, 150);
            }, 150);

            // Okundu işaretle (noktayı gizle)
            const indicator = this.querySelector('.indicator');
            if (indicator) {
                indicator.style.transition = "transform 0.3s, opacity 0.3s";
                indicator.style.transform = "scale(0)";
                indicator.style.opacity = "0";
            }
        });
    }

});