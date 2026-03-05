$(document).ready(function () {

    // --- 1. Counter Animation ---
    $('.counter').each(function () {
        var $this = $(this);
        var countTo = $this.attr('data-target');

        $({ countNum: $this.text() }).animate({
            countNum: countTo
        },
            {
                duration: 2000,
                easing: 'swing',
                step: function () {
                    $this.text(Math.floor(this.countNum));
                },
                complete: function () {
                    $this.text(this.countNum);
                }
            });
    });

    // --- 2. Chart.js Configs ---

    // Genel Ayarlar
    Chart.defaults.color = '#8b9bb4';
    Chart.defaults.font.family = "'Rajdhani', sans-serif";

    // Büyük Line Grafik (Performans Trendi)
    const ctxPerformance = document.getElementById('performanceChart').getContext('2d');

    // Gradient Oluşturma
    let gradientPurple = ctxPerformance.createLinearGradient(0, 0, 0, 400);
    gradientPurple.addColorStop(0, 'rgba(188, 19, 254, 0.5)');
    gradientPurple.addColorStop(1, 'rgba(188, 19, 254, 0)');

    let gradientBlue = ctxPerformance.createLinearGradient(0, 0, 0, 400);
    gradientBlue.addColorStop(0, 'rgba(0, 243, 255, 0.5)');
    gradientBlue.addColorStop(1, 'rgba(0, 243, 255, 0)');

    new Chart(ctxPerformance, {
        type: 'line',
        data: {
            labels: ['Pts', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'],
            datasets: [
                {
                    label: 'Odaklanma',
                    data: [65, 78, 70, 85, 92, 88, 95],
                    borderColor: '#00f3ff',
                    backgroundColor: gradientBlue,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#050507',
                    pointBorderColor: '#00f3ff',
                    pointHoverRadius: 8
                },
                {
                    label: 'Verimlilik',
                    data: [45, 60, 55, 70, 65, 75, 80],
                    borderColor: '#bc13fe',
                    backgroundColor: gradientPurple,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#050507',
                    pointBorderColor: '#bc13fe',
                    pointHoverRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    labels: { font: { family: "'Orbitron', sans-serif" } }
                },
                tooltip: {
                    backgroundColor: 'rgba(5, 5, 7, 0.9)',
                    titleColor: '#00f3ff',
                    bodyColor: '#fff',
                    borderColor: '#bc13fe',
                    borderWidth: 1,
                    displayColors: false,
                    padding: 10
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    beginAtZero: true
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });

    // Radar Grafik (Yetenek Matrisi)
    const ctxRadar = document.getElementById('skillsRadar').getContext('2d');
    new Chart(ctxRadar, {
        type: 'radar',
        data: {
            labels: ['Matematik', 'Fizik', 'Kodlama', 'Dil', 'Tarih', 'Mantık'],
            datasets: [{
                label: 'Mevcut Seviye',
                data: [90, 75, 85, 60, 70, 95],
                fill: true,
                backgroundColor: 'rgba(0, 243, 255, 0.2)',
                borderColor: '#00f3ff',
                pointBackgroundColor: '#fff',
                pointBorderColor: '#00f3ff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#00f3ff'
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: {
                        color: '#e0e6ed',
                        font: { family: "'Share Tech Mono', monospace", size: 12 }
                    },
                    ticks: { display: false, backdropColor: 'transparent' }
                }
            },
            plugins: { legend: { display: false } }
        }
    });

    // --- 3. Heatmap Generator ---
    const heatmapGrid = document.getElementById('heatmapGrid');
    for (let i = 0; i < 120; i++) { // 120 küçük kare
        const div = document.createElement('div');
        div.classList.add('heat-cell');

        // Rastgele aktivite seviyesi ata
        const rand = Math.random();
        if (rand > 0.9) div.classList.add('h-l4');
        else if (rand > 0.7) div.classList.add('h-l3');
        else if (rand > 0.5) div.classList.add('h-l2');
        else if (rand > 0.2) div.classList.add('h-l1');

        heatmapGrid.appendChild(div);
    }

    // --- 4. AI Terminal Typing Effect ---
    const terminalOutput = document.getElementById('terminalOutput');
    const logs = [
        "[SİSTEM] Kullanıcı girişi doğrulandı...",
        "[SİSTEM] Nöral veriler senkronize ediliyor...",
        "> Analiz başlatıldı: Hedef 'Matematik'...",
        "[UYARI] Dikkat dağınıklığı tespit edildi (21:00 - 22:00)",
        "> Öneri: Pomodoro süresini 45 dakikaya çıkar.",
        "> Tebrikler! 'Kodlama' yeteneğinde %5 artış.",
        "[AI] Bir sonraki çalışma seansı için 'Diferansiyel Denklemler' öneriliyor..."
    ];

    let logIndex = 0;

    function typeLog() {
        if (logIndex < logs.length) {
            const p = document.createElement('div');
            p.style.marginBottom = "5px";
            p.style.opacity = "0";

            // Log türüne göre renk
            if (logs[logIndex].includes("[UYARI]")) p.style.color = "#ff0055";
            else if (logs[logIndex].includes(">")) p.style.color = "#00f3ff";

            p.textContent = logs[logIndex];
            terminalOutput.appendChild(p);

            // Fade in efekti
            $(p).animate({ opacity: 1 }, 300);

            // Auto scroll
            terminalOutput.scrollTop = terminalOutput.scrollHeight;

            logIndex++;
            setTimeout(typeLog, 1500); // Her satır arası bekleme
        }
    }
    setTimeout(typeLog, 1000); // Başlama gecikmesi

    // --- 5. Particle Background ---
    const canvas = document.getElementById("particleCanvas");
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    let particlesArray;

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.1; // Çok küçük partiküller
            this.speedX = (Math.random() * 1.5 - 0.75) * 0.5;
            this.speedY = (Math.random() * 1.5 - 0.75) * 0.5;
            this.color = Math.random() > 0.5 ? "rgba(0, 243, 255, " : "rgba(188, 19, 254, ";
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x > canvas.width || this.x < 0) this.speedX = -this.speedX;
            if (this.y > canvas.height || this.y < 0) this.speedY = -this.speedY;
        }
        draw() {
            ctx.fillStyle = this.color + Math.random() + ")"; // Yanıp sönme efekti için opacity random
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function initParticles() {
        particlesArray = [];
        for (let i = 0; i < 100; i++) {
            particlesArray.push(new Particle());
        }
    }

    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < particlesArray.length; i++) {
            particlesArray[i].update();
            particlesArray[i].draw();
        }
        requestAnimationFrame(animateParticles);
    }

    initParticles();
    animateParticles();

    window.addEventListener('resize', function () {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        initParticles();
    });

    // --- 6. Hex Time (Clock) ---
    function updateHexTime() {
        const date = new Date();
        const h = date.getHours().toString().padStart(2, '0');
        const m = date.getMinutes().toString().padStart(2, '0');
        const s = date.getSeconds().toString().padStart(2, '0');
        document.getElementById('hexTime').innerText = `0X:${h}:${m}:${s}`;
    }
    setInterval(updateHexTime, 1000);
});