/**
 * EduMind AI - Product Page Master Script
 * Contains logic for:
 * 1. Animations (AOS)
 * 2. Hero Section 3D Parallax & Orbit
 * 3. Storytelling DOM Slider (Chaos vs Clarity)
 * 4. Advanced Counters
 * 5. Card 3D Tilt Effects
 */

document.addEventListener('DOMContentLoaded', () => {

    // ======================================================
    // 1. INITIALIZATION
    // ======================================================

    // Initialize AOS (Animate On Scroll)
    if (typeof AOS !== 'undefined') {
        AOS.init({
            once: true,
            mirror: false,
            offset: 80,
            duration: 1000,
            easing: 'ease-out-cubic'
        });
    }

    // Initialize VanillaTilt for Module Cards
    if (typeof VanillaTilt !== 'undefined') {
        VanillaTilt.init(document.querySelectorAll(".module-card, .value-card"), {
            max: 5,
            speed: 400,
            glare: true,
            "max-glare": 0.1,
            scale: 1.02
        });
    }

    // ======================================================
    // 2. HERO SECTION INTERACTIONS
    // ======================================================

    // Ambient Light Mouse Tracking (Arka plan ışığını mouse ile hareket ettirme)
    const ambientLight = document.querySelector('.mesh-background');
    if (ambientLight) {
        document.addEventListener('mousemove', (e) => {
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;

            // Işık kaynaklarını hafifçe kaydır
            ambientLight.style.transform = `translate(${x * -20}px, ${y * -20}px)`;
        });
    }

    // 3D Orbit System Perspective (Hero sağ taraftaki yörünge sistemi)
    const orbitSystem = document.querySelector('.orbit-system-wrapper');
    const heroSection = document.querySelector('.ultra-hero');

    if (heroSection && orbitSystem && window.innerWidth > 992) {
        heroSection.addEventListener('mousemove', (e) => {
            const xAxis = (window.innerWidth / 2 - e.pageX) / 40;
            const yAxis = (window.innerHeight / 2 - e.pageY) / 40;

            // Mevcut 3D dönüşüne (rotateX 60deg) mouse etkisini ekle
            orbitSystem.style.transform = `rotateX(${60 + yAxis}deg) rotateZ(${-20 + xAxis}deg) scale(0.9)`;
        });

        // Mouse çıkınca resetle
        heroSection.addEventListener('mouseleave', () => {
            orbitSystem.style.transition = 'transform 0.8s ease-out';
            orbitSystem.style.transform = `rotateX(60deg) rotateZ(-20deg) scale(0.9)`;
            setTimeout(() => { orbitSystem.style.transition = ''; }, 800);
        });
    }

    // ======================================================
    // 3. STORYTELLING SLIDER (CHAOS vs CLARITY)
    // ======================================================

    const sliderWrapper = document.querySelector('.comparison-wrapper');
    const chaosWorld = document.querySelector('.chaos-world');
    const handle = document.querySelector('.scroller-handle');
    let isSliderDown = false;

    if (sliderWrapper && chaosWorld && handle) {

        // Mouse & Touch Events
        const startSliding = () => isSliderDown = true;
        const stopSliding = () => isSliderDown = false;

        handle.addEventListener('mousedown', startSliding);
        handle.addEventListener('touchstart', startSliding);

        window.addEventListener('mouseup', stopSliding);
        window.addEventListener('touchend', stopSliding);

        // Movement Logic
        const moveSlider = (x) => {
            const rect = sliderWrapper.getBoundingClientRect();
            let position = x - rect.left;

            // Sınırları Belirle
            if (position < 0) position = 0;
            if (position > rect.width) position = rect.width;

            // Width ve Handle pozisyonunu güncelle
            chaosWorld.style.width = `${position}px`;
            handle.style.left = `${position}px`;
        };

        // Event Listeners for Move
        sliderWrapper.addEventListener('mousemove', (e) => {
            if (!isSliderDown) return;
            e.preventDefault();
            moveSlider(e.clientX);
        });

        sliderWrapper.addEventListener('touchmove', (e) => {
            if (!isSliderDown) return;
            moveSlider(e.touches[0].clientX);
        });

        // Tıklama ile zıplama (Opsiyonel UX)
        sliderWrapper.addEventListener('click', (e) => {
            moveSlider(e.clientX);
        });
    }

    // ======================================================
    // 4. ADVANCED COUNTERS (İstatistikler için)
    // ======================================================

    const counters = document.querySelectorAll('.counter, .avatar-count');

    const animateCounter = (counter) => {
        // Hedef değeri al (örn: data-target="94" veya text içinden "+1.5k")
        let targetText = counter.getAttribute('data-target') || counter.innerText;
        let target = parseFloat(targetText.replace(/[^0-9.]/g, ''));

        // Eğer sayı bulunamazsa animasyonu geç
        if (isNaN(target)) return;

        const duration = 2000; // ms
        const startTime = performance.now();
        const startValue = 0;

        // Easing function: Ease Out Expo
        const easeOutExpo = (t) => {
            return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
        };

        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const ease = easeOutExpo(progress);

            const current = Math.floor(startValue + (target - startValue) * ease);

            // Formatı koruyarak yazdır
            if (targetText.includes('%')) counter.innerText = `%${current}`;
            else if (targetText.includes('+')) counter.innerText = `+${current}${targetText.includes('k') ? 'k' : ''}`;
            else if (targetText.includes('ms')) counter.innerText = `${current}ms`;
            else counter.innerText = current;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                // Bitiş değerini tam oturt
                counter.innerText = targetText;
            }
        };

        requestAnimationFrame(update);
    };

    // Intersection Observer ile sayaçları görünce başlat
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => counterObserver.observe(c));

    // ======================================================
    // 5. SMOOTH SCROLL (Navigation Buttons)
    // ======================================================

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});