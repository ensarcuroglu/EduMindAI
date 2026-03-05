document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("learningStyleForm");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const btnText = analyzeBtn.querySelector(".btn-text");
    const spinner = analyzeBtn.querySelector(".spinner-border");

    const resultPlaceholder = document.getElementById("resultPlaceholder");
    const resultPanel = document.getElementById("resultPanel");
    const geminiOutput = document.getElementById("geminiOutput");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        setLoading(true);
        resultPanel.classList.add("d-none");
        resultPanel.classList.remove("fade-in-active");
        resultPlaceholder.classList.remove("d-none");

        // 1. HAFTALIK SAATİ DİREKT AL (DÜZELTME)
        // Kullanıcı artık arayüzde direkt haftalık giriyor (Örn: 20 saat).
        // Çarpma işlemi kaldırıldı.
        const weeklyStudyHours = parseFloat(document.getElementById("StudyHours").value);

        // 2. FORM VERİSİNİ TOPLA
        const requestData = {
            Age: parseInt(document.getElementById("Age").value),
            Gender: parseInt(document.getElementById("Gender").value),

            StudyHours: weeklyStudyHours,

            Attendance: parseFloat(document.getElementById("Attendance").value),
            AssignmentCompletion: parseFloat(document.getElementById("AssignmentCompletion").value),

            OnlineCourses: parseInt(document.getElementById("OnlineCourses").value),
            Resources: parseInt(document.getElementById("Resources").value),
            Motivation: parseInt(document.getElementById("Motivation").value),
            StressLevel: parseInt(document.getElementById("StressLevel").value),

            Extracurricular: document.getElementById("Extracurricular").checked ? 1 : 0,
            Internet: document.getElementById("Internet").checked ? 1 : 0,
            Discussions: document.getElementById("Discussions").checked ? 1 : 0,
            EduTech: document.getElementById("EduTech").checked ? 1 : 0
        };

        try {
            const response = await fetch('/Home/AnalyzeLearningStyle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) throw new Error("API Hatası");

            const result = await response.json();
            displayResults(result);

        } catch (error) {
            console.error("Hata:", error);
            alert("Analiz sırasında bir hata oluştu. Lütfen Python API'nin çalıştığından emin olun.");
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        analyzeBtn.disabled = isLoading;
        if (isLoading) {
            btnText.textContent = "Analiz Yapılıyor...";
            spinner.classList.remove("d-none");
        } else {
            btnText.innerHTML = 'ANALİZ ET <i class="fa-solid fa-rocket ms-2"></i>';
            spinner.classList.add("d-none");
        }
    }

    function displayResults(data) {
        resultPlaceholder.classList.add("d-none");
        resultPanel.classList.remove("d-none");

        setTimeout(() => {
            resultPanel.classList.add("fade-in-active");
        }, 10);

        const predictions = data.predictions;

        updateProgressBar("visualBar", "visualVal", predictions['Görsel (Visual)']);
        updateProgressBar("auditoryBar", "auditoryVal", predictions['İşitsel (Auditory)']);
        updateProgressBar("readWriteBar", "readWriteVal", predictions['Okuma/Yazma (Read/Write)']);
        updateProgressBar("kinestheticBar", "kinestheticVal", predictions['Kinestetik (Kinesthetic)']);

        document.getElementById("dominantStyleText").textContent = data.dominant_style;
        geminiOutput.innerHTML = marked.parse(data.advice);
    }

    function updateProgressBar(barId, textId, value) {
        const bar = document.getElementById(barId);
        const textSpan = document.getElementById(textId);

        if (bar && value) {
            const width = Math.max(5, value);
            bar.style.width = `${width}%`;
            if (textSpan) textSpan.textContent = `%${value.toFixed(1)}`;
        }
    }
});