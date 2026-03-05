document.addEventListener('DOMContentLoaded', function () {

    // --- 1. MOCK VERİLER ---
    // Gerçekte burası API'den gelecek
    const historyData = [
        { date: "14 Kasım 2025", score: 92, potential: 96, status: "Mükemmel", focus: "Koruma", id: 105 },
        { date: "01 Kasım 2025", score: 85, potential: 90, status: "İyi", focus: "Uyku", id: 104 },
        { date: "20 Ekim 2025", score: 78, potential: 88, status: "Gelişmeli", focus: "Çalışma Saati", id: 103 },
        { date: "05 Ekim 2025", score: 72, potential: 85, status: "Gelişmeli", focus: "Sosyal Medya", id: 102 },
        { date: "15 Eylül 2025", score: 65, potential: 80, status: "Riskli", focus: "Devamlılık", id: 101 },
    ];

    // --- 2. CHART.JS AYARLARI ---
    const ctx = document.getElementById('performanceChart').getContext('2d');

    // Gradient Oluşturma (Mor Geçiş)
    let gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(79, 70, 229, 0.2)'); // Primary color
    gradient.addColorStop(1, 'rgba(79, 70, 229, 0)');

    // Veriyi grafiğe uygun formata çevir
    // Tarihleri ters çeviriyoruz (eskiden yeniye)
    const labels = historyData.map(d => d.date).reverse();
    const scores = historyData.map(d => d.score).reverse();
    const potentials = historyData.map(d => d.potential).reverse();

    const performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Gerçekleşen Skor',
                    data: scores,
                    borderColor: '#4F46E5', // Primary
                    backgroundColor: gradient,
                    borderWidth: 3,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: '#4F46E5',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    fill: true,
                    tension: 0.4 // Eğrisel çizgi (smooth)
                },
                {
                    label: 'Potansiyel Hedef',
                    data: potentials,
                    borderColor: '#CBD5E1', // Gri
                    borderWidth: 2,
                    borderDash: [5, 5], // Kesikli çizgi
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }, // Legend'ı biz HTML'de yaptık
                tooltip: {
                    backgroundColor: '#1E293B',
                    titleFont: { size: 13, family: 'Inter' },
                    bodyFont: { size: 13, family: 'Inter' },
                    padding: 10,
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.y;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 40,
                    max: 100,
                    grid: { color: '#F1F5F9' },
                    ticks: { color: '#64748B', font: { family: 'Inter' } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748B', font: { family: 'Inter' } }
                }
            }
        }
    });


    // --- 3. TABLO RENDER ---
    const tableBody = document.getElementById('historyTableBody');

    historyData.forEach(item => {
        // Durum rengini belirle
        let badgeClass = "bg-yellow";
        if (item.score >= 85) badgeClass = "bg-green";
        if (item.score < 70) badgeClass = "bg-red";

        const row = `
            <tr>
                <td>${item.date}</td>
                <td style="font-weight: 700;">${item.score}</td>
                <td><span class="status-badge ${badgeClass}">${item.status}</span></td>
                <td>${item.focus}</td>
                <td>
                    <button class="btn-sm-ghost">
                        Detay <i class="fa-solid fa-chevron-right" style="font-size: 0.7em;"></i>
                    </button>
                </td>
            </tr>
        `;
        tableBody.innerHTML += row;
    });

    // --- 4. EXPORT BUTTON (Simülasyon) ---
    document.querySelector('.btn-export').addEventListener('click', function () {
        const btn = this;
        const originalContent = btn.innerHTML;

        btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Hazırlanıyor...`;
        btn.style.opacity = "0.7";

        setTimeout(() => {
            alert("Rapor PDF formatında indirildi (Simülasyon).");
            btn.innerHTML = originalContent;
            btn.style.opacity = "1";
        }, 1500);
    });
});