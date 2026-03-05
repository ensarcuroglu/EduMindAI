// Global Değişkenler
let chatHistory = []; // Konuşma geçmişini tutar
const chatContainer = document.getElementById('chatContainer');
const messagesWrapper = document.getElementById('messagesWrapper');
const emptyState = document.getElementById('emptyState');
const typingIndicator = document.getElementById('typingIndicator');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const scrollAnchor = document.getElementById('scrollAnchor');

// Sayfa Yüklendiğinde
document.addEventListener('DOMContentLoaded', () => {
    // Markdown ayarları (Enter tuşunu <br> yapması için)
    marked.setOptions({
        breaks: true,
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });

    // Enter tuşu kontrolü
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Textarea otomatik boyutlandırma
    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = 'auto';
    });
});

// Mesaj Gönderme İşlemi
async function handleSend() {
    const message = chatInput.value.trim();
    if (!message) return;

    // 1. UI'ı Güncelle
    chatInput.value = '';
    chatInput.style.height = 'auto';
    emptyState.style.display = 'none'; // Boş ekranı gizle

    // Kullanıcı mesajını ekrana bas
    appendMessage('user', message);
    scrollToBottom();

    // Butonu pasife al
    setLoading(true);

    try {
        // 2. Backend'e İstek At
        // NOT: Geçmişi (chatHistory) gönderiyoruz ki yapay zeka konuyu unutmasın.
        const payload = {
            userMessage: message,
            history: chatHistory
        };

        const response = await fetch('/Home/ChatWithMentor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            // 3. Başarılı Cevap
            const aiResponse = data.response || "Cevap alınamadı.";

            // Cevabı ekrana bas (Markdown renderlanacak)
            appendMessage('model', aiResponse);

            // Geçmişi Güncelle (Hafıza)
            chatHistory.push({ role: "user", message: message });
            chatHistory.push({ role: "model", message: aiResponse });

        } else {
            // Hata Durumu
            appendMessage('error', data.message || "Bir hata oluştu.");
        }

    } catch (error) {
        console.error('Fetch Hatası:', error);
        appendMessage('error', "Sunucuya bağlanılamadı. Lütfen internet bağlantını kontrol et.");
    } finally {
        setLoading(false);
        scrollToBottom();
    }
}

// Öneri Kartlarına Tıklayınca
function sendSuggestion(text) {
    chatInput.value = text;
    handleSend();
}

// Yeni Konuşma (Temizle)
function resetChat() {
    chatHistory = [];
    messagesWrapper.innerHTML = '';
    emptyState.style.display = 'flex';
    chatInput.value = '';
}

// Ekrana Mesaj Ekleme Fonksiyonu
function appendMessage(role, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(role === 'user' ? 'message-user' : (role === 'error' ? 'message-error' : 'message-ai'));

    let contentHtml = '';

    if (role === 'user') {
        // Kullanıcı mesajı (Düz metin)
        contentHtml = `<div class="content">${escapeHtml(text)}</div>`;
    } else if (role === 'error') {
        // Hata mesajı
        contentHtml = `<div class="content"><i class="fa-solid fa-triangle-exclamation"></i> ${text}</div>`;
    } else {
        // AI Mesajı (Markdown Render + Avatar)
        // Markdown'ı HTML'e çevir
        const parsedHtml = marked.parse(text);

        contentHtml = `
            <div class="ai-avatar">
                <img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" alt="AI">
            </div>
            <div class="content ai-content markdown-body">
                ${parsedHtml}
            </div>
        `;
    }

    messageDiv.innerHTML = contentHtml;
    messagesWrapper.appendChild(messageDiv);

    // Eğer kod bloğu varsa highlight et (Highlight.js)
    if (role === 'model') {
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
}

// Yükleniyor Durumu (Üç nokta animasyonu)
function setLoading(isLoading) {
    if (isLoading) {
        typingIndicator.classList.remove('hidden');
        sendBtn.disabled = true;
        chatInput.disabled = true;
    } else {
        typingIndicator.classList.add('hidden');
        sendBtn.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

// En alta kaydır
function scrollToBottom() {
    scrollAnchor.scrollIntoView({ behavior: "smooth" });
}

// HTML Injection Koruması (Basit)
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}