/**
 * FLUX AI PLANLAYICI - FRONTEND LOGIC (V5 - Final & Stable)
 * Tasarım: Modern Scrollable Layout & Sticky Sidebar
 */

// --- GLOBAL STATE ---
let taskList = [];
const API_TIMEOUT_MS = 120000;
let loadingInterval = null;

const dayTranslationMap = {
    'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
    'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar',
    'Mon': 'Pazartesi', 'Tue': 'Salı', 'Wed': 'Çarşamba', 'Thu': 'Perşembe', 'Fri': 'Cuma', 'Sat': 'Cumartesi', 'Sun': 'Pazar'
};

document.addEventListener('DOMContentLoaded', () => {
    initUI();
});

function initUI() {
    const moodSlider = document.getElementById('userMoodScore');
    const moodDisplay = document.getElementById('moodDisplay');

    if (moodSlider && moodDisplay) {
        moodSlider.addEventListener('input', (e) => {
            moodDisplay.textContent = `${e.target.value}/10`;
        });
    }

    const form = document.getElementById('addTaskForm');
    if (form) {
        form.addEventListener('submit', handleAddTask);
    }
}

function handleAddTask(e) {
    e.preventDefault();

    const elName = document.getElementById('taskName');
    const elDuration = document.getElementById('taskDuration');
    const elDifficulty = document.getElementById('taskDifficulty');
    const elCategory = document.getElementById('taskCategory');
    const elPriority = document.getElementById('taskPriority');
    const elDeadline = document.getElementById('taskDeadline');
    const elIsNewTopic = document.getElementById('isNewTopic');

    const rawName = elName.value.trim();
    if (!rawName) {
        showToast('warning', 'Bir görev adı girmelisin.');
        return;
    }

    let deadlineDayValue = null;
    if (elDeadline.value !== "") {
        deadlineDayValue = parseInt(elDeadline.value);
    }

    const newTask = {
        id: generateUUID(),
        name: rawName,
        duration_minutes: parseInt(elDuration.value) || 60,
        difficulty: parseInt(elDifficulty.value) || 5,
        category: elCategory.value,
        priority: elPriority.value,
        deadline_day: deadlineDayValue,
        is_new_topic: elIsNewTopic.checked,
        fixed_start_slot: null,
        prerequisites: [],
        repetition_count: 0,
        postpone_count: 0
    };

    taskList.push(newTask);
    renderMiniList();
    resetForm(elName);
    updateGenerateButtonState();
    showToast('success', 'Listeye eklendi');
}

async function submitScheduleRequest() {
    if (taskList.length === 0) return;

    setLoadingState(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    try {
        const requestPayload = {
            tasks: taskList,
            user_profile: document.getElementById('userProfile').value,
            busy_intervals: [],
            user_history: {
                last_week_completion_rate: 1.0,
                failed_task_ids: [],
                actual_work_hours: [],
                consecutive_lazy_days: 0,
                early_finish_accumulated_minutes: 0,
                cancelled_slots: []
            },
            is_exam_week: document.getElementById('isExamWeek').checked,
            lazy_mode: document.getElementById('lazyMode').checked,
            user_mood_score: parseInt(document.getElementById('userMoodScore').value) || 5,
            horizon_days: 7
        };

        const response = await fetch('/Home/GenerateSchedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestPayload),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            let msg = "Sunucu hatası.";
            try {
                const err = await response.json();
                msg = err.message || err.error || msg;
            } catch (e) { msg = await response.text(); }
            throw new Error(msg);
        }

        const data = await response.json();
        renderScheduleResult(data);
        showToast('success', 'Program başarıyla oluşturuldu!');

    } catch (error) {
        console.error("Schedule Error:", error);
        let text = error.message;
        if (error.name === 'AbortError') text = 'İşlem zaman aşımına uğradı. Görev sayısını azaltmayı dene.';

        Swal.fire({ icon: 'error', title: 'Hata', text: text, confirmButtonColor: '#6366f1' });
    } finally {
        setLoadingState(false);
    }
}

function renderScheduleResult(data) {
    const emptyState = document.getElementById('calendarEmptyState');
    if (emptyState) emptyState.classList.add('d-none');

    const calendarView = document.getElementById('calendarView');
    if (calendarView) {
        calendarView.classList.remove('d-none');
        calendarView.classList.add('d-flex');
    }

    setTextSafe('totalTasksScheduled', data.total_tasks_scheduled || 0);
    setTextSafe('profileUsedLabel', data.profile_used || 'Standart');
    if (data.coach_notes && data.coach_notes.length > 0) {
        setTextSafe('topCoachNote', data.coach_notes[0]);
    } else {
        setTextSafe('topCoachNote', "Programın hazır! Başarılar.");
    }

    const days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];
    days.forEach(day => {
        const col = document.getElementById(`col-${day}`);
        if (col) col.innerHTML = '';
    });

    if (data.schedule && Array.isArray(data.schedule)) {
        data.schedule.forEach(item => {
            const trDay = translateDay(item.day);
            const colId = `col-${trDay}`;
            const targetCol = document.getElementById(colId);
            if (targetCol) {
                targetCol.appendChild(createEventCardHTML(item));
            }
        });
    }

    fillAnalysisList('aiRationaleList', data.ai_rationale);
    fillAnalysisList('coachNotesList', data.coach_notes);

    setTimeout(() => {
        calendarView.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function createEventCardHTML(item) {
    const div = document.createElement('div');
    div.className = `event-card cat-${item.category}`;

    let energyBadge = '';
    if (item.energy_match) {
        if (item.energy_match.includes("Flow")) {
            energyBadge = `<span class="card-badge" style="background:#dcfce7; color:#15803d;">🔥 Flow</span>`;
        } else {
            energyBadge = `<span class="card-badge">${item.energy_match}</span>`;
        }
    }

    const categoryLabel = getCategoryLabel(item.category);

    div.innerHTML = `
        <div class="event-time">
            <span>${item.start_fmt} - ${item.end_fmt}</span>
            <span>${item.duration}dk</span>
        </div>
        <div class="event-title">${item.task}</div>
        <div class="event-footer">
            <span class="card-badge">${categoryLabel}</span>
            <span class="card-badge">Lv.${item.difficulty}</span>
            ${energyBadge}
        </div>
    `;

    div.style.animation = "fadeIn 0.5s ease forwards";
    return div;
}

function renderMiniList() {
    const container = document.getElementById('taskListContainer');
    const badge = document.getElementById('taskCountBadge');

    badge.textContent = taskList.length;
    container.innerHTML = '';

    if (taskList.length === 0) {
        container.innerHTML = `
            <div class="p-4 text-center text-muted small">
                <i class="fa-solid fa-clipboard-list fa-2x mb-2 text-light"></i><br>
                Henüz ders eklenmedi.
            </div>`;
        return;
    }

    for (let i = taskList.length - 1; i >= 0; i--) {
        const t = taskList[i];
        const itemDiv = document.createElement('div');
        itemDiv.className = `mini-item`;

        itemDiv.innerHTML = `
            <div class="mini-item-info">
                <span class="mini-item-title">${t.name}</span>
                <span class="mini-item-meta">
                    ${t.duration_minutes}dk • ${getCategoryLabel(t.category)}
                </span>
            </div>
            <button onclick="removeTask('${t.id}')" class="btn-link-danger">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        `;
        container.appendChild(itemDiv);
    }
}

window.removeTask = function (id) {
    taskList = taskList.filter(t => t.id !== id);
    renderMiniList();
    updateGenerateButtonState();
};

window.clearAllTasks = function () {
    if (taskList.length === 0) return;
    Swal.fire({
        title: 'Temizle?', text: "Liste silinecek.", icon: 'warning',
        showCancelButton: true, confirmButtonColor: '#ef4444', cancelButtonColor: '#cbd5e1', confirmButtonText: 'Sil'
    }).then((result) => {
        if (result.isConfirmed) {
            taskList = [];
            renderMiniList();
            updateGenerateButtonState();
        }
    });
};

function updateGenerateButtonState() {
    const btn = document.getElementById('btnGenerateSchedule');
    if (btn) btn.disabled = taskList.length === 0;
}

function resetForm(focusElement) {
    document.getElementById('taskName').value = '';
    if (focusElement) focusElement.focus();
}

function setLoadingState(isLoading) {
    const btn = document.getElementById('btnGenerateSchedule');
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');

    if (isLoading) {
        btn.disabled = true;
        overlay.classList.remove('d-none');

        const messages = [
            "Biyolojik saatin analiz ediliyor...",
            "Derslerin zorluk seviyeleri dengeleniyor...",
            "Mola aralıkları optimize ediliyor...",
            "En verimli akış hesaplanıyor...",
            "Yapay zeka nöronları çalışıyor..."
        ];

        let msgIndex = 0;
        loadingText.textContent = messages[0];
        loadingText.classList.remove('fade-in');
        void loadingText.offsetWidth;
        loadingText.classList.add('fade-in');

        if (loadingInterval) clearInterval(loadingInterval);

        loadingInterval = setInterval(() => {
            msgIndex = (msgIndex + 1) % messages.length;
            loadingText.classList.remove('fade-in');
            void loadingText.offsetWidth;
            loadingText.textContent = messages[msgIndex];
            loadingText.classList.add('fade-in');
        }, 1800);

    } else {
        btn.disabled = taskList.length === 0;
        overlay.classList.add('d-none');
        if (loadingInterval) clearInterval(loadingInterval);
    }
}

function translateDay(dayName) {
    if (!dayName) return 'Pazartesi';
    const clean = dayName.split('[')[0].trim();
    return dayTranslationMap[clean] || dayTranslationMap[Object.keys(dayTranslationMap).find(k => k.toLowerCase() === clean.toLowerCase())] || clean;
}

function getCategoryLabel(code) {
    const map = { 'MATH': 'Matematik', 'SCI': 'Fen Bil.', 'LIT': 'Edebiyat', 'LANG': 'Dil', 'CS': 'Yazılım', 'OTHER': 'Diğer' };
    return map[code] || code;
}

function fillAnalysisList(elemId, items) {
    const el = document.getElementById(elemId);
    if (!el) return;
    el.innerHTML = '';
    if (!items || items.length === 0) {
        el.innerHTML = '<li>Veri yok.</li>';
        return;
    }
    items.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        el.appendChild(li);
    });
}

function setTextSafe(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function showToast(icon, title) {
    const Toast = Swal.mixin({
        toast: true, position: 'top-end', showConfirmButton: false, timer: 2000, timerProgressBar: true,
        didOpen: (toast) => { toast.onmouseenter = Swal.stopTimer; toast.onmouseleave = Swal.resumeTimer; }
    });
    Toast.fire({ icon: icon, title: title });
}

function generateUUID() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}