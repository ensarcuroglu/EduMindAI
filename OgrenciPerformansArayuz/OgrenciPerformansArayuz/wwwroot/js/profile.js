document.addEventListener('DOMContentLoaded', function () {

    // --- 1. HEATMAP GENERATOR (Sahte Veri) ---
    const heatmapGrid = document.getElementById('studyHeatmap');

    // Toplam kutu sayısı (Yaklaşık 3 ay ~ 90 gün)
    const totalDays = 126; // 18 hafta * 7 gün

    // Son 4 ayın verisini simüle et
    for (let i = 0; i < totalDays; i++) {
        const box = document.createElement('div');
        box.classList.add('heat-box');

        // Rastgele aktivite seviyesi (0-4 arası)
        // 0: Boş, 4: Çok yoğun
        // Öğrenciyi motive etmek için genellikle dolu gösterelim
        let activityLevel = 0;
        const rand = Math.random();

        if (rand > 0.8) activityLevel = 4;      // %20 ihtimalle çok yoğun
        else if (rand > 0.6) activityLevel = 3; // %20 ihtimalle yoğun
        else if (rand > 0.4) activityLevel = 2; // %20 ihtimalle orta
        else if (rand > 0.2) activityLevel = 1; // %20 ihtimalle az
        else activityLevel = 0;                 // %20 ihtimalle boş

        box.classList.add(`l-${activityLevel}`);

        // Tooltip (Tarih ve Saat)
        box.title = `${i + 1}. Gün: ${activityLevel * 1.5} saat çalışma`;

        heatmapGrid.appendChild(box);
    }

    // --- 2. STATS ANIMATION (Sayıların artarak gelmesi) ---
    // Basit bir counter animasyonu
    /*
    const stats = document.querySelectorAll('.stat-info h3');
    stats.forEach(stat => {
        // Metin içindeki sayıyı al (örn: "42.5 Saat" -> 42.5)
        // Bu demo için karmaşık regex'e girmedik, CSS animasyonu yeterli.
    });
    */

    // --- 3. BADGE TOOLTIPS ---
    // Tarayıcının varsayılan tooltip'i yerine custom bir şey yapılabilir
    // ancak şu an HTML 'title' attribute yeterli.

});