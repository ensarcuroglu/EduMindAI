document.addEventListener('DOMContentLoaded', function () {
    // --- Element Seçicileri ---
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('deskImageInput');
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadContent = document.querySelector('.upload-content');
    const removeBtn = document.getElementById('removeBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analysisForm = document.getElementById('analysisForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const loadingProgress = document.getElementById('loadingProgress');

    // --- State Yönetimi ---
    const togglePreview = (hasImage) => {
        if (hasImage) {
            uploadContent.classList.add('d-none');
            previewContainer.style.display = 'block';
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = `<span>ANALİZİ BAŞLAT</span> <i class="fa-solid fa-rocket"></i>`;
        } else {
            uploadContent.classList.remove('d-none');
            previewContainer.style.display = 'none';
            analyzeBtn.disabled = true;
            fileInput.value = '';
            analyzeBtn.innerHTML = `<span>ANALİZİ BAŞLAT</span> <i class="fa-solid fa-arrow-right-long"></i>`;
        }
    };

    // --- Sürükle & Bırak ---
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
    });

    dropZone.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files));
    fileInput.addEventListener('change', function () { handleFiles(this.files); });

    function handleFiles(files) {
        if (files.length === 0) return;
        const file = files[0];

        if (!file.type.startsWith('image/')) {
            showToast('Lütfen geçerli bir resim dosyası (JPG, PNG) yükleyin.', 'error');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            showToast('Dosya boyutu çok büyük. Maksimum 5MB yükleyebilirsiniz.', 'warning');
            return;
        }

        if (fileInput.files.length === 0 || fileInput.files[0] !== file) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            togglePreview(true);
            showToast('Fotoğraf başarıyla yüklendi.', 'success');
        };
        reader.readAsDataURL(file);
    }

    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        togglePreview(false);
    });

    // --- ANALİZ SİMÜLASYONU VE GÖNDERİM ---
    analysisForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Otomatik gönderimi durdur

        if (fileInput.files.length === 0) {
            showToast('Lütfen analiz için bir fotoğraf seçin.', 'warning');
            return;
        }

        // Loading Ekranını Aç
        loadingOverlay.classList.remove('d-none');
        analyzeBtn.disabled = true;

        // Öğrenci Dostu, Eğlenceli Adımlar
        const steps = [
            { pct: 5, text: 'Fotoğrafına göz atıyorum... 👀' },
            { pct: 25, text: 'Işık yeterli mi diye bakıyorum... 💡' },
            { pct: 45, text: 'Masandaki dağınıklık taranıyor (Umarım topludur)... 🧹' },
            { pct: 65, text: 'Odaklanma seviyen hesaplanıyor... 🧠' },
            { pct: 85, text: 'Süper verimli çalışma tüyoları hazırlanıyor... 🚀' },
            { pct: 100, text: 'Her şey hazır! İşte sonuçlar... 🎉' }
        ];

        let currentStep = 0;
        const totalTime = 5000; // 5 saniye
        const intervalTime = totalTime / (steps.length - 1);

        // Başlangıç durumu
        loadingText.innerText = steps[0].text;
        loadingProgress.style.width = steps[0].pct + '%';

        const updateText = (text) => {
            loadingText.style.opacity = 0;
            setTimeout(() => {
                loadingText.innerText = text;
                loadingText.style.opacity = 1;
            }, 150);
        };

        const interval = setInterval(() => {
            currentStep++;
            if (currentStep < steps.length) {
                updateText(steps[currentStep].text);
                loadingProgress.style.width = steps[currentStep].pct + '%';
            } else {
                clearInterval(interval);
                setTimeout(() => {
                    analysisForm.submit();
                }, 500);
            }
        }, intervalTime);
    });

    // --- Toast Bildirim ---
    function showToast(message, type = 'info') {
        const existing = document.querySelector('.modern-toast');
        if (existing) existing.remove();

        const config = {
            success: { color: '#10b981', icon: 'fa-check-circle' },
            error: { color: '#ef4444', icon: 'fa-circle-xmark' },
            warning: { color: '#f59e0b', icon: 'fa-triangle-exclamation' },
            info: { color: '#3b82f6', icon: 'fa-circle-info' }
        };

        const currentConfig = config[type] || config.info;
        const toast = document.createElement('div');
        toast.className = 'modern-toast';
        toast.style.borderLeftColor = currentConfig.color;
        toast.innerHTML = `
            <i class="fa-solid ${currentConfig.icon}" style="color: ${currentConfig.color}; font-size: 1.2rem;"></i>
            <span style="font-weight: 500; color: #334155;">${message}</span>
        `;

        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.transition = 'all 0.5s ease';
            toast.style.transform = 'translateX(100%)';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 500);
        }, 3500);
    }
});