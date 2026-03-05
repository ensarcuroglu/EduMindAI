// Mock Data (Başlangıç Verileri)
let goals = [
    {
        id: 1,
        title: "İngilizce B1 Seviyesine Ulaş",
        category: "Personal",
        current: 65,
        target: 100,
        unit: "Ders",
        dueDate: "2025-12-30"
    },
    {
        id: 2,
        title: "Algoritma Analizi Kitabını Bitir",
        category: "Academic",
        current: 120,
        target: 350,
        unit: "Sayfa",
        dueDate: "2025-11-20"
    },
    {
        id: 3,
        title: "Haftada 3 Gün Koşu",
        category: "Health",
        current: 1,
        target: 3,
        unit: "Gün",
        dueDate: "2025-11-15"
    }
];

document.addEventListener('DOMContentLoaded', function () {
    renderGoals(goals);

    // Form Submit
    document.getElementById('newGoalForm').addEventListener('submit', function (e) {
        e.preventDefault();

        // Yeni Hedef Objesi
        const newGoal = {
            id: Date.now(),
            title: document.getElementById('goalTitle').value,
            category: document.getElementById('goalCategory').value,
            current: 0,
            target: parseInt(document.getElementById('goalTarget').value),
            unit: "Birim",
            dueDate: document.getElementById('goalDate').value
        };

        goals.unshift(newGoal); // Başa ekle
        renderGoals(goals);
        closeModal();

        // Formu temizle
        e.target.reset();
    });
});

// Hedefleri Ekrana Bas
function renderGoals(data) {
    const container = document.getElementById('goalsContainer');
    container.innerHTML = '';

    data.forEach(goal => {
        const percent = Math.min(100, Math.round((goal.current / goal.target) * 100));

        // Kalan Gün Hesapla
        const today = new Date();
        const due = new Date(goal.dueDate);
        const diffTime = due - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        let daysText = diffDays > 0 ? `${diffDays} gün kaldı` : "Süre doldu";
        if (percent >= 100) daysText = "Tamamlandı";

        // Kategori Renkleri
        let badgeClass = "bg-acad";
        if (goal.category === 'Personal') badgeClass = "bg-pers";
        if (goal.category === 'Health') badgeClass = "bg-heal";

        const html = `
            <div class="goal-card" id="goal-${goal.id}">
                <div class="card-top">
                    <span class="cat-badge ${badgeClass}">${goal.category}</span>
                    <span class="days-left">${daysText}</span>
                </div>
                
                <h3 class="goal-title">${goal.title}</h3>

                <div class="goal-progress">
                    <div class="prog-head">
                        <span>${goal.current} / ${goal.target} ${goal.unit}</span>
                        <span>%${percent}</span>
                    </div>
                    <div class="prog-track">
                        <div class="prog-fill" style="width: ${percent}%; background-color: ${percent >= 100 ? '#10B981' : ''}"></div>
                    </div>
                </div>

                <div class="goal-actions">
                    <button class="btn-update" onclick="updateProgress(${goal.id}, -1)">
                        <i class="fa-solid fa-minus"></i>
                    </button>
                    
                    ${percent >= 100
                ? '<span style="color:#10B981; font-weight:700;"><i class="fa-solid fa-check"></i> Harika!</span>'
                : `<button class="btn-complete" onclick="updateProgress(${goal.id}, 10)">+ İlerleme</button>`
            }
                    
                    <button class="btn-update" onclick="updateProgress(${goal.id}, 1)">
                        <i class="fa-solid fa-plus"></i>
                    </button>
                </div>
            </div>
        `;
        container.innerHTML += html;
    });
}

// Filtreleme
function filterGoals(type) {
    // Buton aktiflik durumu
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');

    if (type === 'all') {
        renderGoals(goals);
    } else {
        const filtered = goals.filter(g => g.category.toLowerCase() === type.toLowerCase());
        renderGoals(filtered);
    }
}

// İlerleme Güncelleme
function updateProgress(id, amount) {
    const goal = goals.find(g => g.id === id);
    if (goal) {
        // İlerleme ekle ama 0'ın altına inme
        let newVal = goal.current + amount;
        if (newVal < 0) newVal = 0;

        // Hedefi geçip geçmediğini kontrol et (Konfeti için)
        const wasNotComplete = goal.current < goal.target;

        goal.current = newVal;
        renderGoals(goals);

        // Eğer yeni tamamlandıysa Konfeti Patlat!
        if (wasNotComplete && goal.current >= goal.target) {
            triggerConfetti();
        }
    }
}

// AI Goal Generator (Simülasyon)
function generateAiGoal() {
    const aiGoal = {
        id: Date.now(),
        title: "🤖 AI: Günde 30dk İngilizce Kelime Ezberi",
        category: "Personal",
        current: 0,
        target: 30,
        unit: "Dakika",
        dueDate: "2025-11-25"
    };
    goals.unshift(aiGoal);
    renderGoals(goals);
    alert("Yapay Zeka analizi sonucunda yeni bir hedef eklendi!");
}

// Konfeti Efekti Fonksiyonu
function triggerConfetti() {
    if (typeof confetti === 'function') {
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#4F46E5', '#10B981', '#F59E0B']
        });
    }
}

// Modal İşlemleri
function openModal() {
    const modal = document.getElementById('goalModal');
    modal.classList.remove('hidden');
}

function closeModal() {
    const modal = document.getElementById('goalModal');
    modal.classList.add('hidden');
}

// Dışarı tıklandığında modal kapat
window.onclick = function (event) {
    const modal = document.getElementById('goalModal');
    if (event.target == modal) {
        closeModal();
    }
}