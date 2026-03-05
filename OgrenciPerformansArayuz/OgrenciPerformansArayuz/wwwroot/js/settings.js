document.addEventListener('DOMContentLoaded', function () {

    // --- TAB SWITCHING ---
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanels = document.querySelectorAll('.tab-panel');

    navItems.forEach(item => {
        item.addEventListener('click', function () {
            // 1. Update Sidebar
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');

            // 2. Switch Content with Animation
            const targetId = this.getAttribute('data-target');

            tabPanels.forEach(panel => {
                if (panel.classList.contains('active')) {
                    // Fade out old one (optional advanced logic, keeping it simple for now)
                    panel.classList.remove('active');
                }
            });

            const targetPanel = document.getElementById(targetId);
            targetPanel.classList.add('active');

            // Scroll to top on mobile
            if (window.innerWidth < 992) {
                targetPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // --- AVATAR PREVIEW ---
    const avatarInput = document.getElementById('avatarUpload');
    const avatarPreview = document.getElementById('avatarPreview');
    const sidebarAvatar = document.getElementById('sidebarAvatar');

    if (avatarInput) {
        avatarInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    avatarPreview.src = e.target.result;
                    if (sidebarAvatar) sidebarAvatar.src = e.target.result; // Update sidebar too
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // --- PASSWORD STRENGTH METER ---
    const newPassInput = document.getElementById('newPassword');
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');

    if (newPassInput) {
        newPassInput.addEventListener('input', function () {
            const val = this.value;
            let strength = 0;
            let color = '#e2e8f0';
            let text = 'Şifre girilmedi';

            if (val.length > 0) {
                if (val.length < 6) { strength = 20; color = '#ef4444'; text = 'Çok Zayıf'; }
                else {
                    strength = 40; color = '#f59e0b'; text = 'Zayıf';
                    if (/[A-Z]/.test(val)) strength += 20;
                    if (/[0-9]/.test(val)) strength += 20;
                    if (/[^A-Za-z0-9]/.test(val)) strength += 20;

                    if (strength >= 80) { color = '#10b981'; text = 'Güçlü'; }
                    else if (strength >= 60) { color = '#3b82f6'; text = 'Orta'; }
                }
            }

            strengthFill.style.width = strength + '%';
            strengthFill.style.backgroundColor = color;
            strengthText.innerText = text;
            strengthText.style.color = color;
        });
    }

    // --- SAVE BUTTON ANIMATION (Advanced) ---
    window.saveChanges = function (btn) {
        const originalContent = btn.innerHTML;
        const originalWidth = btn.offsetWidth;

        // Lock button size to prevent layout shift
        btn.style.width = originalWidth + 'px';
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
        btn.disabled = true;
        btn.style.opacity = '0.8';

        setTimeout(() => {
            btn.innerHTML = '<i class="fa-solid fa-check"></i>';
            btn.style.backgroundColor = '#10b981'; // Success Green
            btn.style.borderColor = '#10b981';
            btn.style.boxShadow = '0 0 15px rgba(16, 185, 129, 0.4)';
            btn.style.color = 'white';

            // Show Toast Notification (Optional implementation)
            // showToast("Ayarlar başarıyla kaydedildi.");

            setTimeout(() => {
                btn.innerHTML = originalContent;
                btn.style.width = '';
                btn.style.backgroundColor = '';
                btn.style.borderColor = '';
                btn.style.boxShadow = '';
                btn.style.color = '';
                btn.disabled = false;
                btn.style.opacity = '1';
            }, 2000);
        }, 1200);
    };

});