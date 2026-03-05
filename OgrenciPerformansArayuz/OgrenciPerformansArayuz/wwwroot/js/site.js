// Tema toggle (light/dark) + localStorage
(function () {
    const html = document.documentElement;
    const btn = document.getElementById("themeToggle");
    const stored = localStorage.getItem("ui-theme");
    if (stored) html.setAttribute("data-bs-theme", stored);

    if (btn) {
        btn.addEventListener("click", () => {
            const cur = html.getAttribute("data-bs-theme") || "light";
            const next = cur === "light" ? "dark" : "light";
            html.setAttribute("data-bs-theme", next);
            localStorage.setItem("ui-theme", next);
            btn.innerHTML = next === "dark" ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
        });
    }

    // Form demo davranışı (backend yoksa bile görsel akış)
    document.addEventListener("submit", function (e) {
        const form = e.target;
        if (form.matches("[data-demo-form]")) {
            e.preventDefault();
            // Basit yönlendirme: Result sayfasına querystring ile
            const params = new URLSearchParams(new FormData(form));
            window.location.href = "/Predict/Result?" + params.toString();
        }
    });

    // Range output göstergeleri
    document.querySelectorAll("[data-range]").forEach(range => {
        const out = document.getElementById(range.dataset.range);
        const sync = () => out && (out.textContent = range.value);
        range.addEventListener("input", sync);
        sync();
    });
})();
