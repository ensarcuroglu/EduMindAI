// --- Veri Modeli (Mock Data) ---
// Gerçek projede bu veriler API'den gelecek.
const currentUser = {
    name: "Ensar Sami Curoğlu",
    avatar: "https://ui-avatars.com/api/?name=Ensar+Curoglu&background=6366f1&color=fff",
    level: 14,
    archetype: "Power Grinder"
};

const postsData = [
    {
        id: 101,
        type: "system_event", // Özel tip: Sistem Otomatik Paylaşımı
        user: "System AI",
        avatar: "https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
        time: "5 dk önce",
        content: "🎉 <strong>Ensar Sami</strong> 'Pazarlık Modu' kullanarak hedefini başarıyla tutturdu! Sosyal medya kullanımı %40 azaldı.",
        image: null,
        likes: 24,
        comments: 2,
        tag: "#Başarı",
        isLiked: false,
        analysisData: null
    },
    {
        id: 102,
        type: "user_post",
        user: "Merve Yılmaz",
        avatar: "https://ui-avatars.com/api/?name=Merve+Y&background=10b981&color=fff",
        time: "35 dk önce",
        content: "Masa düzenimi YOLOv8 ile analiz ettirdim. 'Dikkat Dağıtıcı' sayısı 0'a indi! 🚀 Ortam skoru %95.",
        image: "https://images.unsplash.com/photo-1497215728101-856f4ea42174?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
        likes: 56,
        comments: 14,
        tag: "#MasaAnalizi",
        isLiked: true,
        analysisData: { score: 95, items: ["Laptop", "Su Şişesi"] } // YOLO verisi simülasyonu
    },
    {
        id: 103,
        type: "user_post",
        user: "Can Berk",
        avatar: "https://ui-avatars.com/api/?name=Can+B&background=f59e0b&color=fff",
        time: "1 saat önce",
        content: "XGBoost modeline göre, uyku düzenimi 1 saat artırırsam başarım %4.2 artacakmış. Bu akşam erken yatıyorum. 😴 #ZombiBariyeri",
        image: null,
        likes: 12,
        comments: 4,
        tag: "#Sağlık",
        isLiked: false,
        analysisData: null
    }
];

// AI Tavsiyeleri
const aiAdvicePool = [
    "Dün gece 'Zombi Bariyeri'ne takıldın. Bugün algoritma programını hafifletti. Öneri: 14:00'te 20 dk 'Power Nap' yap.",
    "Odaklanma oranın %85 seviyesinde. Harika gidiyorsun! Mola vermeyi unutma.",
    "Bu hafta sosyal medya kullanımın %10 arttı. Dijital detoks moduna geçmek ister misin?",
    "Yarınki sınavın için 'Aralıklı Tekrar' zamanı geldi. Konu: Veri Yapıları.",
    "Masa analizin güncel değil. Yeni bir fotoğraf yükleyerek ortam skorunu güncelle."
];

// --- Başlatıcı ---
document.addEventListener("DOMContentLoaded", function () {
    // Spinner simülasyonu
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) spinner.classList.remove("d-none");

    // AI Tavsiyesi Yükle
    refreshAdvice();

    setTimeout(() => {
        if (spinner) spinner.classList.add("d-none");
        renderPosts(postsData);
    }, 800); // 0.8sn yapay gecikme
});

// --- Fonksiyonlar ---

function renderPosts(posts) {
    const container = document.getElementById("feedContainer");
    if (!container) return;

    container.innerHTML = ""; // Temizle

    posts.forEach(post => {
        const isSystem = post.type === 'system_event';
        const badgeClass = getBadgeClass(post.tag);

        // AI Analiz Overlay (Varsa)
        let imageHTML = "";
        if (post.image) {
            let overlayHTML = "";
            if (post.analysisData) {
                overlayHTML = `
                    <div class="ai-analysis-overlay">
                        <i class="bi bi-cpu-fill me-1"></i> 
                        Ortam Skoru: <span class="fw-bold text-success">${post.analysisData.score}</span>
                    </div>`;
            }
            imageHTML = `
                <div class="post-image-container mb-3 mt-2">
                    <img src="${post.image}" class="post-image" alt="Post Content">
                    ${overlayHTML}
                </div>`;
        }

        const postHTML = `
            <div class="social-card p-4 mb-4 ${isSystem ? 'bg-soft-primary border-primary-subtle' : ''}" id="post-${post.id}">
                <div class="post-header d-flex justify-content-between align-items-center mb-3">
                    <div class="d-flex align-items-center gap-3">
                        <img src="${post.avatar}" class="avatar-sm rounded-circle border ${isSystem ? 'p-1 bg-white' : ''}">
                        <div>
                            <h6 class="mb-0 fw-bold text-dark d-flex align-items-center gap-2">
                                ${post.user}
                                ${isSystem ? '<i class="bi bi-patch-check-fill text-primary small" title="Sistem Onaylı"></i>' : ''}
                            </h6>
                            <small class="text-muted">${post.time}</small>
                        </div>
                    </div>
                    <span class="badge ${badgeClass} text-dark bg-opacity-10 border">${post.tag}</span>
                </div>
                
                <div class="post-body mb-2">
                    <p class="post-content-text mb-0">${post.content}</p>
                    ${imageHTML}
                </div>

                <div class="post-footer d-flex justify-content-between pt-3 border-top border-light mt-2">
                    <div class="d-flex gap-3">
                        <button class="action-btn ${post.isLiked ? 'liked' : ''}" onclick="toggleLike(${post.id}, this)">
                            <i class="bi ${post.isLiked ? 'bi-heart-fill' : 'bi-heart'}"></i> 
                            <span>${post.likes}</span>
                        </button>
                        <button class="action-btn">
                            <i class="bi bi-chat-dots"></i> 
                            <span>${post.comments}</span>
                        </button>
                    </div>
                    <button class="action-btn" title="Kaydet">
                        <i class="bi bi-bookmark"></i>
                    </button>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', postHTML);
    });
}

// Etiket Renklendirme Yardımcısı
function getBadgeClass(tag) {
    if (tag.includes("Başarı")) return "bg-success-subtle text-success";
    if (tag.includes("Zombi")) return "bg-danger-subtle text-danger";
    if (tag.includes("Masa")) return "bg-info-subtle text-info";
    return "bg-light text-muted";
}

// Filtreleme Mantığı
function filterPosts(event, category) {
    // UI Güncelleme (Active Chip)
    document.querySelectorAll('.filter-chip').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // Filtreleme
    if (category === 'all') {
        renderPosts(postsData);
    } else if (category === 'achievement') {
        const filtered = postsData.filter(p => p.tag.includes("Başarı") || p.tag.includes("Zombi"));
        renderPosts(filtered);
    } else if (category === 'desk') {
        const filtered = postsData.filter(p => p.tag.includes("Masa"));
        renderPosts(filtered);
    }
}

// Beğeni Aksiyonu (Optimize Edilmiş)
function toggleLike(id, btnElement) {
    const post = postsData.find(p => p.id === id);
    if (post) {
        post.isLiked = !post.isLiked;
        post.likes += post.isLiked ? 1 : -1;

        // DOM Manipülasyonu (Re-render yapmadan)
        const icon = btnElement.querySelector('i');
        const countSpan = btnElement.querySelector('span');

        btnElement.classList.toggle('liked');

        // Animasyonlu ikon değişimi
        icon.style.transform = "scale(0.5)";
        setTimeout(() => {
            icon.className = post.isLiked ? 'bi bi-heart-fill' : 'bi bi-heart';
            icon.style.transform = "scale(1.2)";
            setTimeout(() => icon.style.transform = "scale(1)", 100);
        }, 100);

        countSpan.innerText = post.likes;
    }
}

// Textarea'ya Tag Ekleme
function addTag(tagName) {
    const textarea = document.getElementById("postContent");
    if (!textarea) return;
    textarea.value += (textarea.value.length > 0 ? " " : "") + tagName + " ";
    textarea.focus();
}

// Yeni Post Paylaşma
function sharePost() {
    const textarea = document.getElementById("postContent");
    const content = textarea ? textarea.value : "";

    if (!content.trim()) return;

    // Yeni post objesi
    const newPost = {
        id: Date.now(),
        type: "user_post",
        user: currentUser.name,
        avatar: currentUser.avatar,
        time: "Şimdi",
        content: content,
        image: null,
        likes: 0,
        comments: 0,
        tag: "#Genel",
        isLiked: false,
        analysisData: null
    };

    // İçerik analizi (Basit tag algılama)
    if (content.includes("Masa") || content.includes("YOLO")) newPost.tag = "#MasaAnalizi";
    if (content.includes("Zombi")) newPost.tag = "#ZombiBariyeri";
    if (content.includes("Pazarlık")) newPost.tag = "#PazarlıkModu";

    // Başa ekle ve yeniden çiz
    postsData.unshift(newPost);

    // Animasyonlu ekleme için önce render
    renderPosts(postsData);

    // Input temizle
    textarea.value = "";

    // Yeni postu vurgula (Flash effect)
    const firstPost = document.getElementById(`post-${newPost.id}`);
    if (firstPost) {
        firstPost.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstPost.style.transition = "background-color 0.5s";
        firstPost.style.backgroundColor = "var(--primary-soft)";
        setTimeout(() => {
            firstPost.style.backgroundColor = "var(--surface-color)";
        }, 1000);
    }
}

// AI Tavsiyesini Yenile
function refreshAdvice() {
    const textEl = document.getElementById("aiAdviceText");
    const btnIcon = document.querySelector(".ai-widget-card button i");

    if (btnIcon) btnIcon.classList.add("spin-anim"); // CSS'de animasyon tanımlanabilir

    // Simüle edilmiş gecikme
    if (textEl) {
        textEl.style.opacity = 0;
        setTimeout(() => {
            const randomAdvice = aiAdvicePool[Math.floor(Math.random() * aiAdvicePool.length)];
            textEl.innerText = `"${randomAdvice}"`;
            textEl.style.opacity = 1;
            if (btnIcon) btnIcon.classList.remove("spin-anim");
        }, 400);
    }
}

// Odaya Katılma Simülasyonu
function joinRoom(btn) {
    const originalText = btn.innerText;
    btn.innerText = "Katıldı ✓";
    btn.classList.remove("btn-outline-primary");
    btn.classList.add("btn-primary");
    btn.disabled = true;

    // Toast veya bildirim gösterilebilir
    // alert("Odaya başarıyla katıldınız!");
}

// Daha Fazla Yükle Simülasyonu
function loadMorePosts() {
    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;

    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Yükleniyor...';
    btn.disabled = true;

    setTimeout(() => {
        // Mock veri ekle
        const morePosts = [
            {
                id: 999,
                type: "user_post",
                user: "Selin Demir",
                avatar: "https://ui-avatars.com/api/?name=Selin+D&background=random&color=fff",
                time: "2 saat önce",
                content: "Bugün 8 Pomodoro tamamladım! Hedef 12. 🍅🔥",
                image: null,
                likes: 8,
                comments: 1,
                tag: "#Pomodoro",
                isLiked: false,
                analysisData: null
            }
        ];
        postsData.push(...morePosts);
        renderPosts(postsData);

        btn.innerHTML = originalContent;
        btn.disabled = false;
    }, 1000);
}