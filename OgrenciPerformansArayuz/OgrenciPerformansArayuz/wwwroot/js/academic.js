// Global Değişkenler
let examsBuffer = [];
let trendChartInst = null;
let radarChartInst = null;
let riskChartInst = null;
let lessonTrendChartInst = null;

const DEFAULT_LESSONS = ["Türkçe", "Matematik", "Sosyal", "Fen"];

// Sayfa Yüklendiğinde
document.addEventListener('DOMContentLoaded', function () {
    // Varsayılan 4 dersi ekle
    DEFAULT_LESSONS.forEach(lesson => addLessonRow(lesson));

    // Tarih alanına bugünü ata
    document.getElementById('examDate').valueAsDate = new Date();
});

// Ders Satırı Ekleme Fonksiyonu
function addLessonRow(defaultName = "") {
    const container = document.getElementById('lessonsContainer');
    const rowId = `lesson-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    const html = `
        <div class="row g-2 mb-2 align-items-center animate-fade-in-left" id="${rowId}">
            <div class="col-4">
                <input type="text" class="form-control form-control-sm glass-input lesson-name" 
                       value="${defaultName}" placeholder="Ders Adı">
            </div>
            <div class="col-2">
                <input type="number" class="form-control form-control-sm glass-input dogru" placeholder="D" min="0">
            </div>
            <div class="col-2">
                <input type="number" class="form-control form-control-sm glass-input yanlis" placeholder="Y" min="0">
            </div>
            <div class="col-2">
                <input type="number" class="form-control form-control-sm glass-input bos" placeholder="B" min="0">
            </div>
            <div class="col-2 text-end">
                <button type="button" class="btn btn-sm text-danger" onclick="removeLessonRow('${rowId}')">
                    <i class="bi bi-trash3-fill"></i>
                </button>
            </div>
        </div>`;

    container.insertAdjacentHTML('beforeend', html);
}

function removeLessonRow(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Deneme Listesine Ekleme
function addExamToList() {
    const name = document.getElementById('examName').value;
    const dateRaw = document.getElementById('examDate').value;

    if (!name || !dateRaw) {
        Swal.fire({
            icon: 'warning',
            title: 'Eksik Bilgi',
            text: 'Lütfen deneme adı ve tarihini giriniz.',
            confirmButtonColor: '#764ba2'
        });
        return;
    }

    // Tarih formatı (dd.MM.yyyy)
    const d = new Date(dateRaw);
    const formattedDate = `${d.getDate().toString().padStart(2, '0')}.${(d.getMonth() + 1).toString().padStart(2, '0')}.${d.getFullYear()}`;

    let lessons = [];
    let totalNet = 0;
    let isValid = true;

    const rows = document.querySelectorAll('#lessonsContainer > div');
    rows.forEach(row => {
        const dersAdi = row.querySelector('.lesson-name').value;
        const dogru = parseInt(row.querySelector('.dogru').value) || 0;
        const yanlis = parseInt(row.querySelector('.yanlis').value) || 0;
        const bos = parseInt(row.querySelector('.bos').value) || 0;

        if (!dersAdi) isValid = false;

        const net = dogru - (yanlis * 0.25);
        totalNet += net;

        lessons.push({ ders_adi: dersAdi, dogru: dogru, yanlis: yanlis, bos: bos });
    });

    if (!isValid || lessons.length === 0) {
        Swal.fire({ icon: 'error', title: 'Hata', text: 'Lütfen ders adlarını kontrol ediniz.' });
        return;
    }

    const examObj = { ad: name, tarih: formattedDate, dersler: lessons };
    examsBuffer.push(examObj);

    updateExamListUI();

    // Formu temizle ama ders isimlerini koru
    document.getElementById('examName').value = '';
    document.querySelectorAll('.dogru, .yanlis, .bos').forEach(i => i.value = '');

    // Toast bildirimi
    const Toast = Swal.mixin({
        toast: true, position: 'top-end', showConfirmButton: false, timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    });
    Toast.fire({ icon: 'success', title: 'Deneme listeye eklendi' });
}

function updateExamListUI() {
    const list = document.getElementById('examList');
    const emptyState = document.getElementById('emptyState');
    const badge = document.getElementById('examCountBadge');

    list.innerHTML = '';

    if (examsBuffer.length === 0) {
        emptyState.style.display = 'block';
    } else {
        emptyState.style.display = 'none';
        examsBuffer.forEach((exam, index) => {
            // Basit toplam net hesabı (görsel amaçlı)
            let net = exam.dersler.reduce((acc, curr) => acc + (curr.dogru - curr.yanlis * 0.25), 0);

            const li = document.createElement('li');
            li.className = 'list-group-item exam-list-item d-flex justify-content-between align-items-center';
            li.innerHTML = `
                <div>
                    <div class="fw-bold text-dark">${exam.ad}</div>
                    <div class="small text-muted"><i class="bi bi-calendar-event me-1"></i>${exam.tarih} | <span class="text-primary fw-bold">${net.toFixed(2)} Net</span></div>
                </div>
                <button class="btn btn-sm btn-light text-danger rounded-circle shadow-sm" onclick="removeExam(${index})">
                    <i class="bi bi-x-lg"></i>
                </button>
            `;
            list.appendChild(li);
        });
    }
    badge.innerText = examsBuffer.length;
}

function removeExam(index) {
    examsBuffer.splice(index, 1);
    updateExamListUI();
}

// Analiz Gönderme
async function sendToAnalysis() {
    if (examsBuffer.length < 2) {
        Swal.fire({
            icon: 'info',
            title: 'Veri Yetersiz',
            text: 'Trend analizi ve gelecek tahmini için en az 2 deneme girmelisiniz.',
            confirmButtonColor: '#764ba2'
        });
        return;
    }

    // Loading State
    Swal.fire({
        title: 'Analiz Ediliyor...',
        html: 'Yapay zeka verilerinizi işliyor.<br>Lütfen bekleyiniz.',
        timerProgressBar: true,
        didOpen: () => { Swal.showLoading() }
    });

    try {
        const response = await fetch('/Academic/Analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ denemeler: examsBuffer })
        });

        const res = await response.json();

        if (res.success) {
            Swal.close();
            renderResults(res.data);
        } else {
            Swal.fire({ icon: 'error', title: 'Analiz Hatası', text: res.message });
        }
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Bağlantı Hatası', text: err.message });
    }
}

function renderResults(data) {
    document.getElementById('resultArea').style.display = 'block';

    // API'den gelen veri yapısı: { data: AnalysisData, ... }
    // Controller'da Json(new { success=true, data=result }) dediğimiz için 
    // burada "data" parametresi result nesnesidir. 
    // result nesnesinin içinde de "data" property'si var.
    const analysisResult = data.data;

    // 1. Kartları Doldur (Özet)
    renderStatCards(analysisResult);

    // 2. AI Özet Metni
    document.getElementById('aiSummaryContent').innerHTML = formatSummaryText(data.summary_text);

    // 3. GRAFİKLERİ ÇİZ

    // A) Genel Trend ve Tahmin
    drawTrendChart(analysisResult);

    // B) Radar (Akademik Denge)
    drawRadarChart(analysisResult);

    // C) Risk Matrisi (Scatter) - Veriyi frontend'den hesaplayacağız
    drawRiskScatterChart();

    // D) Ders Bazlı Trendler (Line)
    drawLessonTrendChart(analysisResult);

    // E) Isı Haritası (Table)
    renderHeatmap(analysisResult);

    // Panele Kaydır
    document.getElementById('resultPanel').scrollIntoView({ behavior: 'smooth' });
}

function renderStatCards(data) {
    const ozet = data.genel_performans.son_durum;
    const gelecek = data.gelecek_projeksiyonu;

    const statsHTML = `
        <div class="col-md-4">
            <div class="stat-card bg-stat-1 shadow">
                <div class="h6 opacity-75">Son Net</div>
                <div class="display-6 fw-bold">${ozet.son_net.toFixed(2)}</div>
                <div class="small"><i class="bi bi-bar-chart-fill"></i> Momentum Serisi: ${ozet.momentum_serisi}</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card bg-stat-2 shadow">
                <div class="h6 opacity-75 text-dark">Gelecek Tahmini</div>
                <div class="display-6 fw-bold text-dark">${gelecek.beklenen_gelecek_net ? gelecek.beklenen_gelecek_net.toFixed(2) : '-'}</div>
                <div class="small text-dark"><i class="bi bi-magic"></i> R² Güven: %${(gelecek.r2_skoru * 100).toFixed(0)}</div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card bg-stat-3 shadow">
                <div class="h6 opacity-75 text-dark">Model Tipi</div>
                <div class="fs-4 fw-bold text-dark mt-2">${gelecek.tahmin_modeli || 'Lineer'}</div>
                <div class="small text-dark mt-1">Yapay Zeka Destekli</div>
            </div>
        </div>
    `;
    document.getElementById('statsRow').innerHTML = statsHTML;
}

// --- GRAFİK 1: GENEL TREND ---
function drawTrendChart(data) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    if (trendChartInst) trendChartInst.destroy();

    const gp = data.genel_performans;
    const proj = data.gelecek_projeksiyonu;

    let labels = [...gp.deneme_isimleri];
    let values = [...gp.net_gecmisi];
    let pointColors = Array(values.length).fill('#667eea');

    // Tahmin Ekleme
    if (proj.beklenen_gelecek_net) {
        labels.push("Gelecek");
        values.push(proj.beklenen_gelecek_net);
        pointColors.push('#ff6b6b');
    }

    trendChartInst = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Toplam Net',
                data: values,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                pointBackgroundColor: pointColors,
                pointRadius: 6,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                annotation: {
                    annotations: proj.guven_araligi ? {
                        box1: {
                            type: 'box',
                            xMin: labels.length - 1.3,
                            xMax: labels.length - 0.7,
                            yMin: proj.guven_araligi.alt,
                            yMax: proj.guven_araligi.ust,
                            backgroundColor: 'rgba(255, 99, 132, 0.15)',
                            borderWidth: 0
                        }
                    } : {}
                }
            },
            scales: {
                y: { grid: { color: '#f0f0f0' } },
                x: { grid: { display: false } }
            }
        }
    });
}

// --- GRAFİK 2: RADAR ---
function drawRadarChart(data) {
    const ctx = document.getElementById('radarChart').getContext('2d');
    if (radarChartInst) radarChartInst.destroy();

    const dersler = data.ders_analizleri;
    const labels = Object.keys(dersler);
    const scores = Object.values(dersler).map(d => d.ortalama_basari_orani);

    radarChartInst = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Başarı (%)',
                data: scores,
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                borderColor: 'rgba(255, 206, 86, 1)',
                pointBackgroundColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: '#f0f0f0' },
                    grid: { color: '#f0f0f0' },
                    min: 0, max: 100,
                    ticks: { display: false, stepSize: 20 }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// --- GRAFİK 3: RİSK SCATTER (VERİLER FRONTEND'DEN) ---
function drawRiskScatterChart() {
    const ctx = document.getElementById('riskScatterChart').getContext('2d');
    if (riskChartInst) riskChartInst.destroy();

    // examsBuffer'dan ders bazlı ortalama Yanlış ve Boş hesapla
    let dersStats = {};

    examsBuffer.forEach(exam => {
        exam.dersler.forEach(d => {
            if (!dersStats[d.ders_adi]) dersStats[d.ders_adi] = { yanlis: 0, bos: 0, count: 0 };
            dersStats[d.ders_adi].yanlis += d.yanlis;
            dersStats[d.ders_adi].bos += d.bos;
            dersStats[d.ders_adi].count++;
        });
    });

    const scatterData = Object.keys(dersStats).map(ders => ({
        x: dersStats[ders].bos / dersStats[ders].count, // Ortalama Boş
        y: dersStats[ders].yanlis / dersStats[ders].count, // Ortalama Yanlış
        label: ders
    }));

    riskChartInst = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Dersler',
                data: scatterData,
                backgroundColor: scatterData.map(d =>
                    (d.y > d.x * 1.5) ? '#ff6b6b' : // Riskli (Kırmızı)
                        (d.x > d.y * 1.5) ? '#4ecdc4' : // Temkinli (Yeşil/Mavi)
                            '#ffce56' // Dengeli (Sarı)
                ),
                pointRadius: 8,
                pointHoverRadius: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            let p = ctx.raw;
                            return `${p.label}: ${p.y.toFixed(1)} Yanlış, ${p.x.toFixed(1)} Boş`;
                        }
                    }
                },
                annotation: {
                    annotations: {
                        line1: {
                            type: 'line',
                            scaleID: 'x',
                            value: (ctx) => ctx.chart.scales.x.max,
                            borderColor: 'rgba(0,0,0,0.1)',
                            borderWidth: 1,
                        }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Ortalama Boş Sayısı' }, min: 0 },
                y: { title: { display: true, text: 'Ortalama Yanlış Sayısı' }, min: 0 }
            }
        }
    });
}

// --- GRAFİK 4: DERS BAZLI TRENDLER ---
function drawLessonTrendChart(data) {
    const ctx = document.getElementById('lessonTrendChart').getContext('2d');
    if (lessonTrendChartInst) lessonTrendChartInst.destroy();

    const dersler = data.ders_analizleri;
    const labels = data.genel_performans.deneme_isimleri;

    // Datasetleri hazırla
    const datasets = Object.keys(dersler).map((ders, index) => {
        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
        return {
            label: ders,
            data: dersler[ders].net_gecmisi,
            borderColor: colors[index % colors.length],
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.3
        };
    });

    lessonTrendChartInst = new Chart(ctx, {
        type: 'line',
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } }
        }
    });
}

// --- GRAFİK 5: ISI HARİTASI (TABLO) ---
function renderHeatmap(data) {
    const table = document.getElementById('heatmapTable');
    const dersler = data.ders_analizleri;
    const denemeler = data.genel_performans.deneme_isimleri;

    let html = `<thead><tr><th>Ders</th>`;
    denemeler.forEach(d => html += `<th>${d}</th>`);
    html += `</tr></thead><tbody>`;

    Object.keys(dersler).forEach(ders => {
        const netler = dersler[ders].net_gecmisi;
        const maxNet = Math.max(...netler);
        const minNet = Math.min(...netler);

        html += `<tr><td class="fw-bold">${ders}</td>`;

        netler.forEach(net => {
            // Renk hesaplama (Kırmızı -> Sarı -> Yeşil)
            let colorClass = "";
            let percent = (net - minNet) / (maxNet - minNet || 1); // 0 ile 1 arası

            let bgStyle = "";
            if (net <= 0) bgStyle = "background-color: #ffebee;"; // Çok kötü
            else {
                // Yeşil tonlama (Basitçe)
                const alpha = 0.2 + (percent * 0.6); // 0.2 ile 0.8 arası opaklık
                bgStyle = `background-color: rgba(75, 192, 192, ${alpha});`;
            }

            html += `<td style="${bgStyle}">${net.toFixed(1)}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody>`;
    table.innerHTML = html;
}

function formatSummaryText(text) {
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<span class="text-primary fw-bold">$1</span>')
        .replace(/🚀/g, '<i class="bi bi-rocket-takeoff-fill text-danger"></i>')
        .replace(/🚨/g, '<i class="bi bi-exclamation-triangle-fill text-warning"></i>')
        .replace(/📉/g, '<i class="bi bi-graph-down-arrow text-danger"></i>');
}