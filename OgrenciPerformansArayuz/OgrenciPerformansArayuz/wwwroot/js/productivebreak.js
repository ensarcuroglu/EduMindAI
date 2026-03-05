// --- GLOBAL MODAL CONTROLS ---
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('active');
        // Lazy Init Specific Games
        if (id === 'modalSchulte') resetSchulteUI();
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
        // Cleanups
        stopResetSequence();
        stopEyeYogaRoutine();
        stopBreathing();
        clearTimeout(reflexTimeout);
        stopSchulteGame();
    }
}

// --- AMBIENT SOUND PLAYER ---
const sounds = {
    rain: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-light-rain-loop-1253.mp3'),
    cafe: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-restaurant-crowd-talking-ambience-443.mp3'),
    forest: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-forest-birds-ambience-1210.mp3'),
    waves: new Audio('https://assets.mixkit.co/sfx/preview/mixkit-sea-waves-loop-1196.mp3')
};

let currentSound = null;

document.querySelectorAll('.amb-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        const type = this.dataset.sound;

        // Stop current
        if (currentSound) {
            currentSound.pause();
            currentSound.currentTime = 0;
            document.querySelectorAll('.amb-btn').forEach(b => b.classList.remove('active'));
        }

        // Play new if different or first time
        if (currentSound !== sounds[type] || !currentSound.paused) {
            currentSound = sounds[type];
            currentSound.loop = true;
            currentSound.volume = document.getElementById('masterVolume').value / 100;
            currentSound.play();
            this.classList.add('active');
        } else {
            // Clicked same button -> Stop
            currentSound = null;
        }
    });
});

document.getElementById('masterVolume').addEventListener('input', function () {
    if (currentSound) currentSound.volume = this.value / 100;
});

// --- 1. ZİHİNSEL RESET (90s Sequence) ---
let resetInterval;
const resetSteps = [
    { t: 0, msg: "Gözlerini kapat..." },
    { t: 5, msg: "Omuzlarını düşür..." },
    { t: 15, msg: "Derin nefes al..." },
    { t: 30, msg: "Çeneni gevşet..." },
    { t: 45, msg: "Sessizliği dinle..." },
    { t: 60, msg: "Hazır hisset..." },
    { t: 85, msg: "Gözlerini aç ✨" }
];

function startResetSequence() {
    let seconds = 0;
    const textEl = document.getElementById('resetText');
    const btn = document.querySelector('#modalReset .btn-primary-glass');

    if (btn) btn.style.display = 'none'; // Hide button

    textEl.innerText = resetSteps[0].msg;

    resetInterval = setInterval(() => {
        seconds++;
        const step = resetSteps.find(s => s.t === seconds);
        if (step) {
            textEl.style.opacity = 0;
            setTimeout(() => {
                textEl.innerText = step.msg;
                textEl.style.opacity = 1;
            }, 500);
        }
        if (seconds >= 90) stopResetSequence();
    }, 1000);
}

function stopResetSequence() {
    clearInterval(resetInterval);
    const btn = document.querySelector('#modalReset .btn-primary-glass');
    if (btn) btn.style.display = 'inline-block';
    document.getElementById('resetText').innerText = "Odaklanmaya Hazır mısın?";
}

// --- 2. SCHULTE GRID (GAME LOGIC) ---
let schulteNumbers = [];
let currentNumber = 1;
let schulteTimerInt;
let schulteStartTime;

function resetSchulteUI() {
    document.getElementById('schulteIntro').classList.remove('d-none');
    document.getElementById('schulteGrid').classList.add('d-none');
    document.getElementById('schulteResult').classList.add('d-none');
    document.getElementById('schulteTimer').innerText = "00:00";
}

function initSchulteGame() {
    document.getElementById('schulteIntro').classList.add('d-none');
    document.getElementById('schulteResult').classList.add('d-none');
    const grid = document.getElementById('schulteGrid');
    grid.classList.remove('d-none');
    grid.innerHTML = '';

    // Generate 1-25
    schulteNumbers = Array.from({ length: 25 }, (_, i) => i + 1).sort(() => Math.random() - 0.5);
    currentNumber = 1;

    // Render Grid
    schulteNumbers.forEach(num => {
        const cell = document.createElement('div');
        cell.className = 'schulte-cell';
        cell.innerText = num;
        cell.onclick = () => handleSchulteClick(cell, num);
        grid.appendChild(cell);
    });

    // Start Timer
    schulteStartTime = Date.now();
    schulteTimerInt = setInterval(() => {
        const diff = Math.floor((Date.now() - schulteStartTime) / 1000);
        const m = Math.floor(diff / 60).toString().padStart(2, '0');
        const s = (diff % 60).toString().padStart(2, '0');
        document.getElementById('schulteTimer').innerText = `${m}:${s}`;
    }, 1000);
}

function handleSchulteClick(cell, num) {
    if (num === currentNumber) {
        // Correct
        cell.classList.add('correct');
        currentNumber++;
        if (currentNumber > 25) finishSchulteGame();
    } else {
        // Wrong
        cell.classList.add('wrong');
        setTimeout(() => cell.classList.remove('wrong'), 300);
    }
}

function finishSchulteGame() {
    clearInterval(schulteTimerInt);
    document.getElementById('schulteGrid').classList.add('d-none');
    document.getElementById('schulteResult').classList.remove('d-none');
    document.getElementById('schulteFinalTime').innerText = document.getElementById('schulteTimer').innerText;

    confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
}

function stopSchulteGame() {
    clearInterval(schulteTimerInt);
}

// --- 3. EYE YOGA (GUIDED) ---
let eyeAnimation;

function startEyeYogaRoutine() {
    document.getElementById('btnStartEye').style.display = 'none';
    const point = document.getElementById('eyePoint');
    const text = document.getElementById('eyeInstruction');

    // Animation Keyframes
    const sequence = async () => {
        const move = (x, y, msg, duration) => {
            return new Promise(resolve => {
                text.innerText = msg;
                point.style.transform = `translate(${x}px, ${y}px)`;
                setTimeout(resolve, duration);
            });
        };

        while (document.getElementById('modalEye').classList.contains('active')) {
            await move(-100, 0, "Sola Bak", 2000); // Left
            await move(100, 0, "Sağa Bak", 2000);  // Right
            await move(0, 0, "Merkeze Dön", 1000);
            await move(0, -80, "Yukarı Bak", 2000); // Up
            await move(0, 80, "Aşağı Bak", 2000);  // Down
            await move(0, 0, "Dinlen", 1500);
        }
    };
    sequence();
}

function stopEyeYogaRoutine() {
    document.getElementById('btnStartEye').style.display = 'inline-block';
    const point = document.getElementById('eyePoint');
    point.style.transform = `translate(0px, 0px)`;
    document.getElementById('eyeInstruction').innerText = "Başlat'a Bas";
}

// --- 4. ENDİŞE KUTUSU (WORRY BOX) ---
function shredWorry() {
    const input = document.getElementById('worryInput');
    if (!input.value.trim()) return;

    // Visual Feedback
    const btn = document.querySelector('.btn-shred');
    btn.innerHTML = '<i class="fa-solid fa-check"></i> Parçalanıyor...';

    setTimeout(() => {
        input.value = "";
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Zihinden At';
        // Basic notification or confetti
        confetti({ particleCount: 30, spread: 40, colors: ['#94a3b8'] }); // Grey confetti like paper dust
        alert("Düşünce zihninden silindi ve çöpe atıldı. Şimdi odaklanabilirsin."); // Replace with custom toast later
    }, 1000);
}

// --- 5. REFLEX (SIMPLE) ---
let reflexState = 'idle'; // idle, wait, go
let reflexTimer;
let reflexStartMs;

function handleReflexClick() {
    const box = document.getElementById('reflexBox');
    const msg = document.getElementById('reflexMsg');

    if (reflexState === 'idle') {
        reflexState = 'wait';
        box.className = 'reflex-container wait';
        msg.innerText = "BEKLE...";

        const delay = 2000 + Math.random() * 3000;
        reflexTimer = setTimeout(() => {
            reflexState = 'go';
            box.className = 'reflex-container go';
            msg.innerText = "TIKLA!";
            reflexStartMs = Date.now();
        }, delay);

    } else if (reflexState === 'wait') {
        clearTimeout(reflexTimer);
        reflexState = 'idle';
        box.className = 'reflex-container';
        msg.innerText = "Çok Erken! Tekrar Dene";

    } else if (reflexState === 'go') {
        const score = Date.now() - reflexStartMs;
        reflexState = 'idle';
        box.className = 'reflex-container';
        msg.innerText = `${score} ms`;
    }
}

// --- 6. BREATHING ---
let breathInterval;
let isBreathing = false;

function toggleBreathing() {
    const btn = document.getElementById('btnBreathStart');
    if (isBreathing) {
        stopBreathing();
        btn.innerText = "Başlat";
        btn.classList.remove('btn-danger');
    } else {
        isBreathing = true;
        btn.innerText = "Durdur";
        runBreathCycle(); // Immediate start
        breathInterval = setInterval(runBreathCycle, 19000); // 4+7+8 = 19s
    }
}

function runBreathCycle() {
    const ring = document.getElementById('breathRing');
    const lbl = document.getElementById('breathLabel');

    // Inhale (4s)
    lbl.innerText = "AL (4s)";
    ring.style.transform = "scale(1.5)";
    ring.style.borderWidth = "10px";

    setTimeout(() => {
        // Hold (7s)
        lbl.innerText = "TUT (7s)";
        ring.style.borderColor = "#6366f1"; // Color change

        setTimeout(() => {
            // Exhale (8s)
            lbl.innerText = "VER (8s)";
            ring.style.transform = "scale(1)";
            ring.style.borderWidth = "4px";
            ring.style.borderColor = "#10b981";
        }, 7000);
    }, 4000);
}

function stopBreathing() {
    clearInterval(breathInterval);
    isBreathing = false;
    const ring = document.getElementById('breathRing');
    if (ring) {
        ring.style.transform = "scale(1)";
        document.getElementById('breathLabel').innerText = "Hazır";
    }
}