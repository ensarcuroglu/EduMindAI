document.addEventListener('DOMContentLoaded', function () {

    // ==========================================
    // 1. DOM ELEMENTLERİ SEÇİMİ
    // ==========================================

    // Ana Ekran & Timer
    const timeDisplay = document.getElementById('timeDisplay');
    const modeLabel = document.getElementById('modeLabel');
    const toggleBtn = document.getElementById('toggleBtn');
    const toggleIcon = document.getElementById('toggleIcon');
    const toggleText = document.getElementById('toggleText');
    const resetBtn = document.getElementById('resetBtn');
    const ring = document.querySelector('.ring-fill');
    const modeChips = document.querySelectorAll('.mode-chip');
    const soundBtns = document.querySelectorAll('.sound-btn');
    const sessionCountEl = document.getElementById('sessionCount');
    const body = document.body;

    // AI Vision (Kamera, Jest, Postür)
    const cameraToggle = document.getElementById('cameraToggle');
    const videoEl = document.getElementById('webcamVideo');
    const canvasEl = document.getElementById('captureCanvas');
    const processedImg = document.getElementById('processedFeed');
    const aiStatusEl = document.getElementById('aiConnectionStatus');
    const aiStatusText = document.getElementById('statusText'); // Yeni tasarımda span içinde
    const gestureHintEl = document.getElementById('gestureHint');

    // Postür Bildirimi
    const postureAlertEl = document.getElementById('postureAlert');
    const postureTextEl = document.getElementById('postureAlertText');
    let ctx = null;

    // Görev Yönetimi
    const activeTaskDisplay = document.getElementById('activeTaskDisplay');
    const taskModal = document.getElementById('taskModal');
    const newTaskInput = document.getElementById('newTaskInput');
    const todoListUl = document.getElementById('todoList');
    const emptyState = document.getElementById('emptyState');

    // Mindfulness
    const mindfulnessOverlay = document.getElementById('mindfulnessOverlay');
    const mindfulnessQuote = document.getElementById('mindfulnessQuote');
    const breathingCircle = document.getElementById('breathingCircle');
    const breathText = document.getElementById('breathText');
    const breathTimer = document.getElementById('breathTimer');
    const breathSubtext = document.getElementById('breathSubtext');
    const breathModePills = document.querySelectorAll('.mode-pill');

    // Spotify & Youtube
    const spotifyModal = document.getElementById('spotifyModal');
    const spotifyInput = document.getElementById('spotifyUrlInput');
    const spotifyFrame = document.getElementById('spotifyFrame');
    const youtubeModal = document.getElementById('youtubeModal');
    const youtubeInput = document.getElementById('youtubeUrlInput');
    const youtubeFrame = document.getElementById('youtubeFrame');

    // Sesler
    const sounds = {
        rain: document.getElementById('audio-rain'),
        cafe: document.getElementById('audio-cafe'),
        fire: document.getElementById('audio-fire'),
        none: null
    };
    const endSound = new Audio('/audio/bell.mp3');

    // ==========================================
    // 2. DEĞİŞKENLER VE AYARLAR
    // ==========================================

    let timer = null;
    let isRunning = false;
    let currentMode = 'focus';
    let totalTime = 25 * 60;
    let timeLeft = totalTime;
    let completedSessions = 0;
    let currentSound = null;

    // AI Değişkenleri
    let gestureSocket = null;
    let videoStream = null;
    let videoInterval = null;
    let postureTimeout = null; // Uyarı mesajı zamanlayıcısı

    // Görev & Mindfulness Değişkenleri
    let todoList = [];
    let activeTaskId = null;
    let breathingInterval = null;
    let breathCountInterval = null;
    let currentBreathMode = 'box';

    // Kullanıcı Ayarları
    let settings = {
        focusTime: 25, shortTime: 5, longTime: 15,
        autoStartBreaks: false, masterVolume: 80, desktopNotif: true,
        gestureMode: 'secure' // 'secure' veya 'easy'
    };

    // SVG Halka Ayarı
    const radius = 170;
    const circumference = 2 * Math.PI * radius;
    ring.style.strokeDasharray = `${circumference} ${circumference}`;
    ring.style.strokeDashoffset = 0;

    const studentAffirmations = [
        "Bir sınav kağıdı senin zekanı değil, o anki performansını ölçer.",
        "Mükemmel olmak zorunda değilsin, sadece dünden biraz daha iyi ol yeter.",
        "Dinlenmek, çalışmanın bir parçasıdır.",
        "Karmaşık problemler küçük parçalara bölündüğünde çözülür.",
        "Şu ana odaklan. Gelecek zaten şu an yaptıklarınla şekilleniyor.",
        "Yorgun hissetmen normal, bu pes etmen gerektiği anlamına gelmez.",
        "Başarı bir varış noktası değil, bir alışkanlıktır."
    ];

    const breathConfigs = {
        box: { inhale: 4, hold: 4, exhale: 4, hold2: 4, text: "Kutu Tekniği: Dengelenmek için ritmi takip et.", totalCycle: 16000 },
        relax: { inhale: 4, hold: 7, exhale: 8, hold2: 0, text: "4-7-8 Tekniği: Anksiyeteyi düşürmek ve gevşemek için.", totalCycle: 19000 }
    };

    // ==========================================
    // 3. POMODORO FONKSİYONLARI
    // ==========================================

    function playSoundSafe(audioElement) {
        if (!audioElement) return;
        audioElement.volume = settings.masterVolume / 100;
        const playPromise = audioElement.play();
        if (playPromise !== undefined) {
            playPromise.then(_ => { }).catch(error => console.warn("Ses çalınamadı:", error));
        }
    }

    function setProgress(percent) {
        const offset = circumference - (percent / 100) * circumference;
        ring.style.strokeDashoffset = offset;
    }

    function updateDisplay() {
        const mins = Math.floor(timeLeft / 60);
        const secs = timeLeft % 60;
        const timeStr = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        timeDisplay.innerText = timeStr;
        document.title = isRunning ? `(${timeStr}) Odaklan...` : "Focus Zone";
    }

    function toggleTimer() { isRunning ? pauseTimer() : startTimer(); }

    function startTimer() {
        if (isRunning) return;
        isRunning = true;
        body.classList.add('timer-running');
        toggleIcon.className = 'fa-solid fa-pause';
        toggleText.innerText = 'DURAKLAT';

        if (currentSound && sounds[currentSound]) {
            playSoundSafe(sounds[currentSound]);
        }

        timer = setInterval(() => {
            if (timeLeft > 0) {
                timeLeft--;
                updateDisplay();
                setProgress((timeLeft / totalTime) * 100);
            } else {
                completeTimer();
            }
        }, 1000);
    }

    function pauseTimer() {
        isRunning = false;
        body.classList.remove('timer-running');
        clearInterval(timer);
        toggleIcon.className = 'fa-solid fa-play';
        toggleText.innerText = 'DEVAM ET';
        if (currentSound && sounds[currentSound]) sounds[currentSound].pause();
    }

    function resetTimer(updateTimeFromSettings = false) {
        pauseTimer();
        toggleText.innerText = 'BAŞLAT';

        if (updateTimeFromSettings) {
            let mins = 25;
            if (currentMode === 'focus') mins = settings.focusTime;
            else if (currentMode === 'short') mins = settings.shortTime;
            else mins = settings.longTime;
            totalTime = mins * 60;
        }

        timeLeft = totalTime;
        updateDisplay();
        setProgress(100);
    }

    function completeTimer() {
        pauseTimer();
        playSoundSafe(endSound);

        if (settings.desktopNotif && Notification.permission === "granted") {
            new Notification(currentMode === 'focus' ? "Seans Bitti!" : "Mola Bitti!");
        }

        if (currentMode === 'focus') {
            completedSessions++;
            sessionCountEl.innerText = completedSessions;
            switchMode('short');
            if (settings.autoStartBreaks) startTimer();
        } else {
            switchMode('focus');
        }
    }

    function switchMode(mode) {
        currentMode = mode;
        modeChips.forEach(c => {
            c.classList.remove('active');
            if (c.dataset.mode === mode) c.classList.add('active');
        });

        if (mode === 'focus') modeLabel.innerText = "ODAKLAN";
        else if (mode === 'short') modeLabel.innerText = "KISA MOLA";
        else modeLabel.innerText = "UZUN MOLA";

        resetTimer(true);
    }

    // ==========================================
    // 4. AI JEST & POSTÜR KONTROLÜ
    // ==========================================

    if (canvasEl) ctx = canvasEl.getContext('2d');

    // Global toggle fonksiyonu
    window.toggleCamera = async () => {
        const isChecked = cameraToggle.checked;

        if (isChecked) {
            try {
                updateAIStatus("Başlatılıyor...", "online");

                videoStream = await navigator.mediaDevices.getUserMedia({ video: { width: 480, height: 360 } });
                videoEl.srcObject = videoStream;

                connectWebSocket();
                processedImg.style.opacity = "1";

            } catch (err) {
                alert("Kamera hatası: " + err);
                cameraToggle.checked = false;
                updateAIStatus("Hata", "error");
            }
        } else {
            stopCamera();
        }
    };

    function stopCamera() {
        if (videoStream) videoStream.getTracks().forEach(track => track.stop());
        if (gestureSocket) gestureSocket.close();
        if (videoInterval) clearInterval(videoInterval);

        processedImg.src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="; // Boş gif
        processedImg.style.opacity = "0";
        updateAIStatus("Pasif", "offline");
    }

    function updateAIStatus(text, type) {
        if (aiStatusText) aiStatusText.innerText = text;
        if (aiStatusEl) {
            aiStatusEl.className = `status-badge ${type}`;
        }
    }

    function connectWebSocket() {
        // Python API Endpoint
        gestureSocket = new WebSocket("ws://127.0.0.1:8000/ws/gesture-control");

        gestureSocket.onopen = function () {
            updateAIStatus("AI Aktif", "online");

            // Kare gönderme döngüsü (100ms = 10 FPS)
            videoInterval = setInterval(sendFrame, 100);

            // Başlangıç ayarını gönder
            sendGestureConfig(settings.gestureMode);
        };

        gestureSocket.onmessage = function (event) {
            const data = JSON.parse(event.data);

            // 1. Görüntüyü Güncelle
            if (data.image) {
                processedImg.src = "data:image/jpeg;base64," + data.image;
            }

            // 2. Jest Komutlarını İşle
            if (data.command) {
                handleGestureCommand(data.command);
            }

            // 3. Postür Uyarısını İşle (YENİ)
            if (data.warning) {
                handlePostureWarning(data.warning);
            }
        };

        gestureSocket.onclose = function () {
            if (cameraToggle.checked) {
                updateAIStatus("Koptu", "error");
            }
        };
    }

    function sendFrame() {
        if (gestureSocket.readyState === WebSocket.OPEN && videoEl.readyState === videoEl.HAVE_ENOUGH_DATA) {
            canvasEl.width = videoEl.videoWidth;
            canvasEl.height = videoEl.videoHeight;
            ctx.drawImage(videoEl, 0, 0);

            canvasEl.toBlob(blob => {
                gestureSocket.send(blob);
            }, 'image/jpeg', 0.6);
        }
    }

    function handleGestureCommand(cmd) {
        if (cmd === "START" && !isRunning) {
            console.log("AI: Başlatılıyor...");
            startTimer();
        } else if (cmd === "PAUSE" && isRunning) {
            console.log("AI: Duraklatılıyor...");
            pauseTimer();
        }
    }

    function handlePostureWarning(warningMsg) {
        if (warningMsg && postureAlertEl) {
            postureTextEl.innerText = warningMsg;
            postureAlertEl.classList.remove('hidden');

            if (postureTimeout) clearTimeout(postureTimeout);

            postureTimeout = setTimeout(() => {
                postureAlertEl.classList.add('hidden');
            }, 3000); // 3 saniye sonra gizle
        }
    }

    // Jest Ayarları
    window.selectGestureMode = (mode) => {
        settings.gestureMode = mode;
        updateGestureUI();
        sendGestureConfig(mode);
        localStorage.setItem('pomodoroSettings', JSON.stringify(settings));
    };

    function updateGestureUI() {
        const btnSecure = document.getElementById('btnGestureSecure');
        const btnEasy = document.getElementById('btnGestureEasy');

        if (btnSecure && btnEasy) {
            btnSecure.classList.remove('active');
            btnEasy.classList.remove('active');

            if (settings.gestureMode === 'secure') {
                btnSecure.classList.add('active');
                if (gestureHintEl) gestureHintEl.innerText = "Durdur: Shaka 🤙 | Başlat: Silah 👉";
            } else {
                btnEasy.classList.add('active');
                if (gestureHintEl) gestureHintEl.innerText = "Durdur: El Açık ✋ | Başlat: Yumruk ✊";
            }
        }
    }

    async function sendGestureConfig(mode) {
        const config = mode === 'secure'
            ? { "PAUSE": "SHAKA", "START": "GUN", "SHORT_BREAK": "ROCK" }
            : { "PAUSE": "OPEN_HAND", "START": "FIST", "SHORT_BREAK": "VICTORY" };

        try {
            await fetch('/Home/UpdateGestureConfig', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config: config })
            });
        } catch (err) {
            console.error("Jest ayarı güncellenemedi:", err);
        }
    }

    // ==========================================
    // 5. GÖREV YÖNETİMİ
    // ==========================================

    window.openTaskManager = () => {
        renderTasks();
        taskModal.classList.remove('hidden');
        setTimeout(() => newTaskInput.focus(), 100);
    };

    window.closeTaskManager = () => taskModal.classList.add('hidden');

    window.addNewTask = () => {
        const text = newTaskInput.value.trim();
        if (!text) return;
        const newTask = { id: Date.now(), text: text, completed: false };
        todoList.push(newTask);
        newTaskInput.value = '';
        if (!activeTaskId) setActiveTask(newTask.id);
        saveTasks();
        renderTasks();
    };

    window.handleTaskInput = (e) => { if (e.key === 'Enter') addNewTask(); };

    function renderTasks() {
        todoListUl.innerHTML = '';
        if (todoList.length === 0) emptyState.classList.remove('hidden');
        else {
            emptyState.classList.add('hidden');
            todoList.forEach(task => {
                const li = document.createElement('li');
                li.className = `task-item ${task.completed ? 'completed' : ''} ${task.id === activeTaskId ? 'active-selected' : ''}`;
                li.onclick = (e) => {
                    if (!e.target.closest('.btn-delete-task') && !e.target.closest('.task-checkbox')) setActiveTask(task.id);
                };
                li.innerHTML = `
                    <div class="task-checkbox" onclick="toggleTaskComplete(${task.id})">
                        ${task.completed ? '<i class="fa-solid fa-check"></i>' : ''}
                    </div>
                    <span class="task-text">${task.text}</span>
                    <button class="btn-delete-task" onclick="deleteTask(${task.id})"><i class="fa-solid fa-trash"></i></button>
                `;
                todoListUl.appendChild(li);
            });
        }
    }

    window.toggleTaskComplete = (id) => {
        const task = todoList.find(t => t.id === id);
        if (task) {
            task.completed = !task.completed;
            saveTasks();
            renderTasks();
        }
    };

    window.deleteTask = (id) => {
        todoList = todoList.filter(t => t.id !== id);
        if (activeTaskId === id) { activeTaskId = null; updateActiveTaskDisplay(); }
        saveTasks();
        renderTasks();
    };

    window.setActiveTask = (id) => {
        activeTaskId = id;
        updateActiveTaskDisplay();
        saveTasks();
        renderTasks();
    };

    function updateActiveTaskDisplay() {
        const task = todoList.find(t => t.id === activeTaskId);
        activeTaskDisplay.innerText = task ? task.text : "Bir görev seç...";
    }

    function saveTasks() {
        localStorage.setItem('pomodoroTasks', JSON.stringify(todoList));
        localStorage.setItem('activeTaskId', activeTaskId);
    }

    function loadTasks() {
        const storedTasks = localStorage.getItem('pomodoroTasks');
        const storedActiveId = localStorage.getItem('activeTaskId');
        if (storedTasks) todoList = JSON.parse(storedTasks);
        if (storedActiveId) activeTaskId = parseInt(storedActiveId);
        updateActiveTaskDisplay();
    }

    // ==========================================
    // 6. MINDFULNESS
    // ==========================================

    window.openMindfulness = () => {
        if (isRunning) pauseTimer();
        mindfulnessOverlay.classList.remove('hidden');
        const randomQuote = studentAffirmations[Math.floor(Math.random() * studentAffirmations.length)];
        mindfulnessQuote.innerText = `"${randomQuote}"`;
        updateBreathUI();
        startBreathingExercise();
    };

    window.closeMindfulness = () => {
        mindfulnessOverlay.classList.add('hidden');
        stopBreathingExercise();
    };

    window.changeBreathMode = (mode) => {
        if (currentBreathMode === mode) return;
        currentBreathMode = mode;
        stopBreathingExercise();
        updateBreathUI();
        startBreathingExercise();
    };

    function updateBreathUI() {
        breathModePills.forEach(pill => {
            pill.classList.remove('active');
            if (pill.dataset.mode === currentBreathMode) pill.classList.add('active');
        });
        if (breathSubtext) breathSubtext.innerText = breathConfigs[currentBreathMode].text;
    }

    function startBreathingExercise() {
        runBreathCycle();
        const config = breathConfigs[currentBreathMode];
        breathingInterval = setInterval(runBreathCycle, config.totalCycle);
    }

    function runBreathCycle() {
        const config = breathConfigs[currentBreathMode];
        setBreathState("Nefes Al...", "circle-inhale", config.inhale, () => {
            setBreathState("Tut...", "circle-hold", config.hold, () => {
                setBreathState("Yavaşça Ver...", "circle-exhale", config.exhale, () => {
                    if (config.hold2 > 0) setBreathState("Tut...", "circle-hold", config.hold2, () => { });
                });
            });
        });
    }

    function stopBreathingExercise() {
        if (breathingInterval) clearInterval(breathingInterval);
        if (breathCountInterval) clearInterval(breathCountInterval);
        breathingCircle.className = 'guide-circle-inner';
        breathText.innerText = 'Hazır mısın?';
        breathTimer.innerText = '';
    }

    function setBreathState(text, cssClass, durationSec, callback) {
        if (mindfulnessOverlay.classList.contains('hidden')) return;
        breathText.innerText = text;
        breathingCircle.className = 'guide-circle-inner';
        void breathingCircle.offsetWidth;
        breathingCircle.classList.add(cssClass);
        let timeLeft = durationSec;
        breathTimer.innerText = timeLeft;
        if (breathCountInterval) clearInterval(breathCountInterval);
        breathCountInterval = setInterval(() => {
            timeLeft--;
            if (timeLeft > 0) breathTimer.innerText = timeLeft;
            else {
                clearInterval(breathCountInterval);
                if (callback) callback();
            }
        }, 1000);
    }

    // ==========================================
    // 7. AYARLAR
    // ==========================================

    window.openSettings = () => {
        document.getElementById('customFocus').value = settings.focusTime;
        document.getElementById('customShort').value = settings.shortTime;
        document.getElementById('customLong').value = settings.longTime;
        document.getElementById('autoStartBreaks').checked = settings.autoStartBreaks;
        document.getElementById('masterVolume').value = settings.masterVolume;

        updateGestureUI();

        document.getElementById('settingsModal').classList.remove('hidden');
    };

    window.closeSettings = () => document.getElementById('settingsModal').classList.add('hidden');

    window.stepInput = (id, step) => {
        const input = document.getElementById(id);
        let val = parseInt(input.value) + step;
        if (val < 1) val = 1;
        input.value = val;
    };

    window.saveSettings = () => {
        settings.focusTime = parseInt(document.getElementById('customFocus').value);
        settings.shortTime = parseInt(document.getElementById('customShort').value);
        settings.longTime = parseInt(document.getElementById('customLong').value);
        settings.autoStartBreaks = document.getElementById('autoStartBreaks').checked;
        settings.masterVolume = parseInt(document.getElementById('masterVolume').value);

        localStorage.setItem('pomodoroSettings', JSON.stringify(settings));
        if (currentSound && sounds[currentSound]) sounds[currentSound].volume = settings.masterVolume / 100;
        closeSettings();
        if (!isRunning) resetTimer(true);
    };

    // ==========================================
    // 8. EVENT LISTENERS
    // ==========================================

    toggleBtn.addEventListener('click', toggleTimer);
    resetBtn.addEventListener('click', () => resetTimer(true));

    modeChips.forEach(chip => {
        chip.addEventListener('click', function () {
            if (isRunning && !confirm("Süre işliyor. Modu değiştirmek istiyor musun?")) return;
            switchMode(this.dataset.mode);
        });
    });

    soundBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            if (currentSound && sounds[currentSound]) {
                sounds[currentSound].pause();
                sounds[currentSound].currentTime = 0;
            }
            soundBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const sound = this.dataset.sound;
            currentSound = sound === 'none' ? null : sound;
            if (isRunning && currentSound && sounds[currentSound]) {
                playSoundSafe(sounds[currentSound]);
            }
        });
    });

    // ==========================================
    // 9. SPOTIFY & YOUTUBE WIDGET
    // ==========================================

    window.openSpotifyModal = () => spotifyModal.classList.remove('hidden');
    window.closeSpotifyModal = () => spotifyModal.classList.add('hidden');

    window.loadQuickPick = (type) => {
        let url = "";
        switch (type) {
            case 'lofi': url = "https://open.spotify.com/embed/playlist/0vvXsWCC9xrXsKd4FyS8kM?utm_source=generator"; break;
            case 'piano': url = "https://open.spotify.com/embed/playlist/37i9dQZF1DX4sWSpwq3LiO?utm_source=generator"; break;
            case 'white': url = "https://open.spotify.com/embed/playlist/37i9dQZF1DWV7EzJMK2FUI?utm_source=generator"; break;
        }
        if (url) {
            spotifyFrame.src = url;
            localStorage.setItem('userSpotifyUrl', url);
        }
    };

    window.updateSpotifyEmbed = () => {
        const rawUrl = spotifyInput.value.trim();
        if (!rawUrl) return;
        let embedUrl = rawUrl;
        if (!rawUrl.includes('/embed/')) embedUrl = rawUrl.replace('open.spotify.com/', 'open.spotify.com/embed/');
        spotifyFrame.src = embedUrl;
        localStorage.setItem('userSpotifyUrl', embedUrl);
        spotifyInput.value = '';
    };

    function loadSpotifySettings() {
        const savedUrl = localStorage.getItem('userSpotifyUrl');
        if (savedUrl) spotifyFrame.src = savedUrl;
    }

    if (spotifyModal) spotifyModal.addEventListener('click', (e) => { if (e.target === spotifyModal) closeSpotifyModal(); });

    // YouTube
    window.openYoutubeModal = () => youtubeModal.classList.remove('hidden');
    window.closeYoutubeModal = () => youtubeModal.classList.add('hidden');

    window.loadYoutubeQuickPick = (type) => {
        let videoId = "";
        switch (type) {
            case 'lofi': videoId = "jfKfPfyJRdk"; break;
            case 'jazz': videoId = "G5OQdI7J3kI"; break;
            case 'nature': videoId = "eKFTSSKCzWA"; break;
        }
        updateYoutubeFrame(videoId);
    };

    window.updateYoutubeEmbed = () => {
        const url = youtubeInput.value.trim();
        if (!url) return;
        const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
        const match = url.match(regExp);
        if (match && match[2].length === 11) {
            updateYoutubeFrame(match[2]);
            youtubeInput.value = '';
        } else {
            alert("Geçersiz YouTube linki!");
        }
    };

    function updateYoutubeFrame(videoId) {
        const embedUrl = `https://www.youtube.com/embed/${videoId}`;
        youtubeFrame.src = embedUrl;
        localStorage.setItem('userYoutubeUrl', embedUrl);
    }

    function loadYoutubeSettings() {
        const savedUrl = localStorage.getItem('userYoutubeUrl');
        if (savedUrl) youtubeFrame.src = savedUrl;
    }

    if (youtubeModal) youtubeModal.addEventListener('click', (e) => { if (e.target === youtubeModal) closeYoutubeModal(); });

    // ==========================================
    // 10. BAŞLANGIÇ (INIT)
    // ==========================================

    const savedSettings = JSON.parse(localStorage.getItem('pomodoroSettings'));
    if (savedSettings) settings = { ...settings, ...savedSettings };

    if (Notification.permission !== "granted") Notification.requestPermission();

    loadTasks();
    loadSpotifySettings();
    loadYoutubeSettings();
    updateDisplay();
    updateGestureUI(); // Başlangıçta Jest ayarını UI'a yansıt
});