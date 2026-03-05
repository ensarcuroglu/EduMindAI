document.addEventListener('DOMContentLoaded', function () {

    // --- ELEMENTS ---
    const tabs = document.querySelectorAll('.tab-btn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const formTitle = document.getElementById('formTitle');
    const formSubtitle = document.getElementById('formSubtitle');

    // --- 1. TAB SWITCHING ---
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from buttons
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const target = tab.dataset.target;

            if (target === 'login') {
                loginForm.classList.add('active');
                registerForm.classList.remove('active');
                formTitle.innerText = "Tekrar Hoşgeldin! 👋";
                formSubtitle.innerText = "Hesabına giriş yap ve çalışmaya başla.";
            } else {
                loginForm.classList.remove('active');
                registerForm.classList.add('active');
                formTitle.innerText = "Aramıza Katıl 🚀";
                formSubtitle.innerText = "Başarı yolculuğuna bugün başla.";
            }
        });
    });

    // --- 2. PASSWORD TOGGLE ---
    window.togglePassword = function (inputId, btn) {
        const input = document.getElementById(inputId);
        const icon = btn.querySelector('i');

        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    }

    // --- 3. LOGIN SIMULATION ---
    window.handleLogin = function (btn) {
        const email = document.getElementById('loginEmail').value;
        const pass = document.getElementById('loginPass').value;

        if (!email || !pass) {
            alert("Lütfen tüm alanları doldur.");
            return;
        }

        animateButton(btn, "Giriş Yapılıyor...", () => {
            // Başarılı giriş sonrası yönlendirme
            window.location.href = '/Home/Index'; // Ana sayfaya yönlendir
        });
    }

    // --- 4. REGISTER SIMULATION ---
    window.handleRegister = function (btn) {
        const name = document.getElementById('regName').value;
        const email = document.getElementById('regEmail').value;

        if (!name || !email) {
            alert("Lütfen gerekli alanları doldur.");
            return;
        }

        animateButton(btn, "Hesap Oluşturuluyor...", () => {
            alert("Hesabın oluşturuldu! Şimdi giriş yapabilirsin.");
            // Otomatik olarak giriş tabına geç
            tabs[0].click();
        });
    }

    // Button Animation Helper
    function animateButton(btn, loadingText, callback) {
        const originalContent = btn.innerHTML;
        const originalWidth = btn.offsetWidth;

        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> ${loadingText}`;

        // Simüle edilmiş bekleme süresi (1.5 sn)
        setTimeout(() => {
            btn.innerHTML = `<i class="fa-solid fa-check"></i> Başarılı!`;
            btn.style.background = "#10b981"; // Success green

            setTimeout(() => {
                btn.innerHTML = originalContent;
                btn.style.background = ""; // Revert CSS
                btn.disabled = false;
                if (callback) callback();
            }, 1000);
        }, 1500);
    }

});