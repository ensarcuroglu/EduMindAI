import os
import warnings

# =============================================================================
# 0. UYARI VE LOG YÖNETİMİ (Konsol Temizliği İçin)
# =============================================================================
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['GRPC_VERBOSITY'] = 'ERROR'

warnings.filterwarnings("ignore", message="X does not have valid feature names")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", module="google.generativeai")

import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import pandas as pd
import numpy as np
import traceback
import sys
import base64
import cv2
import joblib  # EKLENDİ: Model yükleme için gerekli
from dotenv import load_dotenv

# Sklearn ayarları
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import set_config

set_config(transform_output="pandas")

# .env yükle
load_dotenv()


# =============================================================================
# 1. SINIF TANIMLAMALARI (JOBLIB YÜKLEME GÜVENLİĞİ İÇİN)
# =============================================================================

class OutlierCapper(BaseEstimator, TransformerMixin):
    def __init__(self, factor=1.5):
        self.factor = factor
        self.lower_bounds_ = {}
        self.upper_bounds_ = {}
        self.columns_to_cap = ['study_hours_per_day', 'social_media_hours', 'netflix_hours', 'sleep_hours']

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if not isinstance(X, pd.DataFrame): return X
        X_ = X.copy()
        if hasattr(self, 'lower_bounds_') and self.lower_bounds_:
            for col, lower in self.lower_bounds_.items():
                if col in X_.columns:
                    upper = self.upper_bounds_.get(col, np.inf)
                    X_[col] = np.clip(X_[col], lower, upper)
        return X_


class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if not isinstance(X, pd.DataFrame): return X
        X_ = X.copy()

        X_['total_distraction_hours'] = X_.get('social_media_hours', 0) + X_.get('netflix_hours', 0)
        study = X_.get('study_hours_per_day', 0)
        sleep = X_.get('sleep_hours', 0)

        X_['focus_ratio'] = study / (X_['total_distraction_hours'] + 1)
        X_['lifestyle_balance'] = sleep / (study + 1)
        X_['study_efficiency'] = study * X_.get('mental_health_rating', 5)

        att = X_.get('attendance_percentage', 0)
        X_['academic_engagement'] = att * study
        X_['log_total_distraction'] = np.log1p(X_['total_distraction_hours'])

        ex = X_.get('exercise_frequency', 0)
        X_['vitality_score'] = (sleep ** 1.2) * (ex + 1)

        pt_job = X_.get('part_time_job', 'No')
        if isinstance(pt_job, pd.Series):
            X_['burnout_risk'] = study * np.where(pt_job == 'Yes', 1.5, 1.0)
        else:
            val = 1.5 if pt_job == 'Yes' else 1.0
            X_['burnout_risk'] = study * val

        ec_part = X_.get('extracurricular_participation', 'No')
        if isinstance(ec_part, pd.Series):
            X_['dedication_level'] = att * np.where(ec_part == 'Yes', 1.2, 1.0)
        else:
            val = 1.2 if ec_part == 'Yes' else 1.0
            X_['dedication_level'] = att * val

        return X_


# =============================================================================
# 2. MODÜL ENTEGRASYONLARI
# =============================================================================

try:
    from oneri_motoru_V2 import SmartAdvisor
except ImportError:
    print("❌ KRİTİK HATA: 'oneri_motoru_V2.py' bulunamadı!")
    sys.exit(1)

try:
    from optimizer import AcademicOptimizer
except ImportError:
    print("⚠️ UYARI: 'optimizer.py' bulunamadı. Pazarlık modu devre dışı.")
    AcademicOptimizer = None

# Mevcut Mentor (Statik Mesajlar İçin)
try:
    import mentor
except ImportError:
    print("⚠️ UYARI: 'mentor.py' bulunamadı. Statik mentör mesajları devre dışı.")
    mentor = None

# --- YENİ AI CHAT MENTOR (Dinamik Sohbet İçin) ---
try:
    from ai_mentor_service import AIMentorService
except ImportError:
    print("⚠️ UYARI: 'ai_mentor_service.py' bulunamadı. Sohbet botu devre dışı.")
    AIMentorService = None

# --- MASA ANALİZİ MODÜLÜ (V8.1) ---
try:
    from desk_analyzer import DeskAgentSovereignAPI
except ImportError:
    print("⚠️ UYARI: 'desk_analyzer.py' bulunamadı veya 'ultralytics' yüklü değil. Görüntü analizi devre dışı.")
    DeskAgentSovereignAPI = None

# --- JEST KONTROL MODÜLÜ (V3.0) ---
try:
    from gesture_control import PomodoroGestureController
except ImportError:
    print("⚠️ UYARI: 'gesture_control.py' bulunamadı veya 'mediapipe' yüklü değil. Jest kontrolü devre dışı.")
    PomodoroGestureController = None

# --- FLUX SCHEDULER MODÜLÜ (YENİ) ---
try:
    from constraint_scheduler import (
        FluxScheduler, CalendarService, TimeSlotConfig,
        SchedulerConfig, StudyTask, UserProfile, TaskPriority, UserHistory
    )
except ImportError:
    print("⚠️ UYARI: 'constraint_scheduler.py' veya 'pulp' bulunamadı. Akıllı planlayıcı devre dışı.")
    FluxScheduler = None

# --- ÖĞRENME STİLİ ANALİZİ MODÜLÜ (YENİ EKLENDİ) ---
try:
    import learning_style_ai_service as learning_service
except ImportError:
    print("⚠️ UYARI: 'learning_style_ai_service.py' bulunamadı. Öğrenme stili analizi devre dışı.")
    learning_service = None

# --- AKADEMİK İZLEME MODÜLÜ (V3.0) ---
try:
    from akademik_izleme_modulu_V2 import AnalizMotoru, DenemeSinavi, DersSonuc, GrafikRaporlayici, OzetMotoru
except ImportError:
    print("⚠️ UYARI: 'akademik_izleme_modulu_V2.py' bulunamadı. Deneme takip modülü devre dışı.")
    AnalizMotoru = None

# =============================================================================
# 3. UYGULAMA VE MODEL BAŞLATMA
# =============================================================================

app = FastAPI(title="Student AI Advisor API", version="3.4")  # Versiyon güncellendi

# Regresyon Modeli Yükleme
model_path = "artifacts/student_score_xgb_pipeline_v2.joblib"
if not os.path.exists(model_path):
    print(f"⚠️ UYARI: Model dosyası '{model_path}' bulunamadı.")

advisor = SmartAdvisor(model_path=model_path)
optimizer_engine = AcademicOptimizer(advisor) if AcademicOptimizer else None

# AI Sohbet Ajanı Yükleme
chat_agent = None
if AIMentorService:
    try:
        print("💬 AI Chat Mentor (Gemini 2.0/1.5) Başlatılıyor...")
        chat_agent = AIMentorService()
    except Exception as e:
        print(f"⚠️ Chat Agent başlatılamadı: {e}")

# Görüntü İşleme Modeli Yükleme
desk_agent = None
if DeskAgentSovereignAPI:
    try:
        print("👁️ Desk Agent V8.1 (Omniscient Architect) Başlatılıyor...")
        desk_agent = DeskAgentSovereignAPI(model_path='yolov8x.pt')
    except Exception as e:
        print(f"⚠️ Desk Agent başlatılamadı: {e}")

# Jest Kontrolcüsü Yükleme
gesture_controller = None
if PomodoroGestureController:
    try:
        print("✋ Gesture Controller V3.0 Başlatılıyor...")
        gesture_controller = PomodoroGestureController()
        gesture_controller.set_gesture_config({
            "PAUSE": "SHAKA",
            "START": "GUN",
            "SHORT_BREAK": "ROCK"
        })
    except Exception as e:
        print(f"⚠️ Gesture Controller başlatılamadı: {e}")

# Öğrenme Stili Modeli Yükleme (YENİ)
learning_style_model = None
learning_style_features = None

if learning_service:
    try:
        if os.path.exists(learning_service.MODEL_PATH) and os.path.exists(learning_service.FEATURES_PATH):
            learning_style_model = joblib.load(learning_service.MODEL_PATH)
            learning_style_features = joblib.load(learning_service.FEATURES_PATH)
            print("🧠 Learning Style Modeli ve Özellikleri Başarıyla Yüklendi.")
        else:
            print(f"⚠️ UYARI: Learning style model dosyaları bulunamadı: {learning_service.MODEL_PATH}")
    except Exception as e:
        print(f"⚠️ Learning Style Modeli yüklenirken hata: {e}")


# =============================================================================
# 4. YARDIMCI FONKSİYONLAR
# =============================================================================

def convert_numpy_to_python(obj):
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(i) for i in obj]
    else:
        return obj


# =============================================================================
# 5. VERİ MODELLERİ (PYDANTIC)
# =============================================================================

class StudentData(BaseModel):
    student_id: str = "Unknown"
    age: int = Field(..., ge=10, le=100)
    gender: str
    study_hours_per_day: float = Field(..., ge=0, le=24)
    social_media_hours: float = Field(..., ge=0, le=24)
    netflix_hours: float = Field(..., ge=0, le=24)
    attendance_percentage: float = Field(..., ge=0, le=100)
    sleep_hours: float = Field(..., ge=0, le=24)
    diet_quality: str
    mental_health_rating: int = Field(..., ge=1, le=10)
    internet_quality: str
    parental_education_level: str
    exercise_frequency: int = Field(..., ge=0, le=7)
    part_time_job: str
    extracurricular_participation: str


class NegotiationRequest(BaseModel):
    student_data: StudentData
    target_score: float = Field(..., ge=0, le=100)
    frozen_features: List[str] = []


class GestureConfig(BaseModel):
    config: Dict[str, str]


# --- YENİ CHAT MODELİ ---
class ChatRequest(BaseModel):
    user_message: str
    history: List[Dict[str, str]] = []  # [{'role': 'user', 'message': '...'}, ...]


# --- SCHEDULER MODELLERİ (YENİ) ---
class TaskInput(BaseModel):
    id: str
    name: str
    duration_minutes: int
    difficulty: int = Field(..., ge=1, le=10)
    category: str
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    deadline_day: Optional[int] = None
    fixed_start_slot: Optional[int] = None
    prerequisites: List[str] = []

    # Yeni özellikler (Opsiyonel, client göndermezse default)
    is_new_topic: bool = False
    repetition_count: int = 0
    postpone_count: int = 0


class BusyInterval(BaseModel):
    day_idx: int
    start_hour: float
    end_hour: float


class SchedulerHistoryInput(BaseModel):
    last_week_completion_rate: float = 1.0
    failed_task_ids: List[str] = []
    actual_work_hours: List[int] = []  # Örn: [22, 23, 0]
    consecutive_lazy_days: int = 0
    early_finish_accumulated_minutes: int = 0
    cancelled_slots: List[int] = []
    # manual_override_hotspots API'den basitçe gelmesi zor, şimdilik geçiyoruz


class SchedulerRequest(BaseModel):
    tasks: List[TaskInput]
    user_profile: str = "STANDARD"  # STANDARD, EARLY_BIRD, NIGHT_OWL, POWER_GRINDER
    busy_intervals: List[BusyInterval] = []
    user_history: Optional[SchedulerHistoryInput] = None

    # Durumlar
    is_exam_week: bool = False
    lazy_mode: bool = False
    user_mood_score: int = 5

    horizon_days: int = 7


# --- ÖĞRENME STİLİ MODELİ (YENİ EKLENDİ) ---
class LearningStyleInput(BaseModel):
    # Veri setinde max 44 (haftalık). Biz 168 (7x24) ile üst sınır koyuyoruz ki hata vermesin.
    StudyHours: float = Field(..., ge=0, le=168)
    Attendance: float = Field(..., ge=0, le=100)
    # DÜZELTME: Veri setinde max 2 (0: Düşük, 1: Orta, 2: Yüksek)
    Resources: float = Field(..., ge=0, le=2)
    Extracurricular: int = Field(..., ge=0, le=1)
    # DÜZELTME: Veri setinde max 2 (0, 1, 2)
    Motivation: int = Field(..., ge=0, le=2)
    Internet: int = Field(..., ge=0, le=1)
    Gender: int = Field(..., ge=0, le=1)
    Age: int = Field(..., ge=10, le=100)
    OnlineCourses: int = Field(..., ge=0, le=20)
    Discussions: int = Field(..., ge=0, le=1)
    AssignmentCompletion: float = Field(..., ge=0, le=100)
    EduTech: int = Field(..., ge=0, le=1)
    StressLevel: int = Field(..., ge=0, le=2)


# --- AKADEMİK İZLEME MODELLERİ ---
class DersSonucInput(BaseModel):
    ders_adi: str
    dogru: int
    yanlis: int
    bos: int

class DenemeSinaviInput(BaseModel):
    ad: str
    tarih: str  # Format: "GG.AA.YYYY"
    dersler: List[DersSonucInput]

class AkademikIzlemeRequest(BaseModel):
    denemeler: List[DenemeSinaviInput]


# =============================================================================
# 6. ENDPOINTLER
# =============================================================================

@app.get("/")
def health_check():
    status = {
        "status": "active",
        "version": "3.4",
        "modules": {
            "prediction": True,
            "optimization": optimizer_engine is not None,
            "vision": desk_agent is not None,
            "gesture": gesture_controller is not None,
            "scheduler": FluxScheduler is not None,
            "ai_chat": chat_agent is not None,
            "learning_style": learning_style_model is not None,
            "exam_tracking": AnalizMotoru is not None
        }
    }
    return status


@app.post("/predict")
def predict_performance(data: StudentData):
    try:
        student_dict = data.model_dump()
        raw_result = advisor.generate_advice(student_dict)
        return convert_numpy_to_python(raw_result)
    except Exception as e:
        print(f"❌ /predict Hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction Error: {str(e)}")


@app.post("/negotiate")
def negotiate_score(request: NegotiationRequest):
    if not optimizer_engine:
        raise HTTPException(status_code=503, detail="Optimizer modülü yüklü değil.")

    try:
        s_data = request.student_data.model_dump()
        target = request.target_score
        frozen = request.frozen_features

        print(f"🧬 /negotiate: Hedef={target}, Kilitli={frozen}")
        plan = optimizer_engine.find_optimal_path(s_data, target, frozen_features=frozen)

        if plan.get("status") != "Success":
            return {
                "status": "fail",
                "message": plan.get("msg", "Hedefe ulaşılamadı."),
                "achieved_score": convert_numpy_to_python(plan.get("achieved_score", 0))
            }

        mentor_note = "Mentör pasif."
        if mentor:
            changes = plan.get('changes', [])
            top_suggestion = "Genel iyileştirme"
            if changes:
                main_change = max(changes, key=lambda x: abs(x.get('diff', 0)))
                top_suggestion = f"{main_change['feature'].replace('_', ' ')} değerini {main_change['new']:.1f} yap"

            opt_sleep = plan['optimized_data'].get('sleep_hours', 0)
            mentor_note = mentor.generate_mentor_advice(
                student_name=s_data.get('student_id', 'Öğrenci'),
                predicted_score=plan.get('achieved_score'),
                sleep_hours=opt_sleep,
                is_zombie=(opt_sleep < 6.0),
                top_suggestion=top_suggestion
            )

        response = {
            "status": "success",
            "original_score": plan.get("original_score"),
            "target_score": target,
            "achieved_score": plan.get("achieved_score"),
            "required_changes": plan.get("changes", []),
            "mentor_message": mentor_note,
            "optimized_values": plan.get("optimized_data", {})
        }

        return convert_numpy_to_python(response)

    except Exception as e:
        print(f"❌ /negotiate Hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Negotiation Error: {str(e)}")


# =============================================================================
# 7. AI CHAT ENDPOINT (YENİ)
# =============================================================================

@app.post("/ai/chat")
def chat_with_mentor(request: ChatRequest):
    """
    ASP.NET MVC'den gelen sohbet isteklerini karşılar.
    """
    if not chat_agent:
        raise HTTPException(status_code=503, detail="AI Mentor servisi (Gemini) aktif değil.")

    try:
        # Servis üzerinden cevabı al
        response_text = chat_agent.get_chat_response(
            user_message=request.user_message,
            history=request.history
        )
        return {"response": response_text}

    except Exception as e:
        print(f"❌ /ai/chat Hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat Error: {str(e)}")


@app.post("/analyze/desk")
async def analyze_desk(file: UploadFile = File(...)):
    """
    Öğrenci çalışma masasının fotoğrafını analiz eder (V8.1).
    """
    if not desk_agent:
        raise HTTPException(status_code=503, detail="Görüntü işleme modülü (Desk Agent V8.1) aktif değil.")

    try:
        contents = await file.read()
        result = desk_agent.process_image(contents)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return convert_numpy_to_python(result)

    except Exception as e:
        print(f"❌ /analyze/desk Hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image Analysis Error: {str(e)}")


# =============================================================================
# 8. JEST KONTROL ENDPOINTLERİ (V3.0)
# =============================================================================

@app.post("/gesture/config")
def update_gesture_config(data: GestureConfig):
    if not gesture_controller:
        raise HTTPException(status_code=503, detail="Jest kontrol modülü aktif değil.")
    try:
        gesture_controller.set_gesture_config(data.config)
        return {"status": "success", "message": "Jest ayarları güncellendi."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/gesture-control")
async def websocket_gesture(websocket: WebSocket):
    if not gesture_controller:
        await websocket.close(code=1008, reason="Jest Modülü Yüklü Değil")
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            frame = cv2.flip(frame, 1)
            # V5.3 uyumlu: 3 değer dönüyor
            processed_frame, command, warning = gesture_controller.detect_action(frame)

            _, buffer = cv2.imencode('.jpg', processed_frame)
            img_base64 = base64.b64encode(buffer).decode('utf-8')

            response = {
                "command": command,
                "image": img_base64,
                "warning": warning
            }
            await websocket.send_json(response)

    except WebSocketDisconnect:
        print("🔌 WebSocket bağlantısı istemci tarafından kapatıldı.")
    except Exception as e:
        print(f"❌ WebSocket Hatası: {e}")
        try:
            await websocket.close()
        except:
            pass


# =============================================================================
# 9. SCHEDULER ENDPOINT (V6.0 ENTEGRASYONU)
# =============================================================================

@app.post("/schedule")
def generate_schedule(request: SchedulerRequest):
    """
    Flux Scheduler (Next-Gen Coach Edition) kullanarak ders programı oluşturur.
    """
    if not FluxScheduler:
        raise HTTPException(status_code=503, detail="Scheduler modülü aktif değil.")

    try:
        # 1. Konfigürasyon ve Profil
        time_cfg = TimeSlotConfig(horizon_days=request.horizon_days)

        # SchedulerConfig - Client verilerine göre
        sched_cfg = SchedulerConfig(
            is_exam_week=request.is_exam_week,
            lazy_mode=request.lazy_mode,
            user_mood_score=request.user_mood_score
        )

        try:
            user_profile = UserProfile[request.user_profile]
        except KeyError:
            user_profile = UserProfile.STANDARD

        # 2. Takvim Servisi
        cal_service = CalendarService(time_cfg)
        cal_service.apply_student_constraints()  # Okul/Gece kısıtları
        cal_service.apply_dynamic_sleep(user_profile)  # Profile özel uyku

        # Ekstra Meşguliyetler
        for interval in request.busy_intervals:
            cal_service.block_interval(interval.day_idx, interval.start_hour, interval.end_hour)

        # 3. Geçmiş Verisi (History)
        history = UserHistory()
        if request.user_history:
            h = request.user_history
            history.last_week_completion_rate = h.last_week_completion_rate
            history.failed_task_ids = h.failed_task_ids
            history.actual_work_hours = h.actual_work_hours
            history.consecutive_lazy_days = h.consecutive_lazy_days
            history.early_finish_accumulated_minutes = h.early_finish_accumulated_minutes
            history.cancelled_slots = h.cancelled_slots

        # 4. Görevleri Hazırla
        tasks = []
        for t_in in request.tasks:
            try:
                priority = TaskPriority[t_in.priority]
            except KeyError:
                priority = TaskPriority.MEDIUM

            tasks.append(StudyTask(
                id=t_in.id,
                name=t_in.name,
                duration_minutes=t_in.duration_minutes,
                difficulty=t_in.difficulty,
                category=t_in.category,
                priority=priority,
                deadline_day=t_in.deadline_day,
                fixed_start_slot=t_in.fixed_start_slot,
                prerequisites=t_in.prerequisites,
                # Yeni özellikler
                is_new_topic=t_in.is_new_topic,
                repetition_count=t_in.repetition_count,
                postpone_count=t_in.postpone_count
            ))

        # 5. Çözücüyü Başlat ve Çalıştır
        scheduler = FluxScheduler(
            tasks=tasks,
            calendar=cal_service,
            config=sched_cfg,
            time_config=time_cfg,
            user_profile=user_profile,
            user_history=history
        )

        print(f"📅 Scheduler Başlatılıyor... Profil: {user_profile.name}")
        result = scheduler.solve()

        if not result:
            return {
                "status": "fail",
                "message": "Çözüm bulunamadı. Kısıtlar çok sıkı veya zaman yetersiz."
            }

        return {
            "status": "success",
            "schedule": result,
            "coach_notes": scheduler.coach_notes,
            "ai_rationale": scheduler.ai_rationale,
            "profile_used": scheduler.user_profile.name,  # Adaptif olarak değişmiş olabilir
            "total_tasks_scheduled": len(result)
        }

    except Exception as e:
        print(f"❌ /schedule Hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scheduling Error: {str(e)}")


# =============================================================================
# 10. ÖĞRENME STİLİ ENDPOINT (YENİ EKLENDİ)
# =============================================================================

@app.post("/analyze/learning-style")
def analyze_learning_style(data: LearningStyleInput):
    """
    Öğrencinin özelliklerine göre öğrenme stilini tahmin eder ve Gemini ile tavsiye üretir.
    """
    if not learning_service or not learning_style_model:
        raise HTTPException(status_code=503, detail="Learning Style AI servisi veya modeli yüklü değil.")

    try:
        # 1. Pydantic modelini sözlüğe, sonra DataFrame'e çevir
        input_data = data.model_dump()
        raw_columns = ['StudyHours', 'Attendance', 'Resources', 'Extracurricular', 'Motivation', 'Internet', 'Gender',
                       'Age', 'OnlineCourses', 'Discussions', 'AssignmentCompletion', 'EduTech', 'StressLevel']

        # DataFrame oluştur (Tek satırlık)
        df = pd.DataFrame([input_data])

        # Eğer sütun sırası önemliyse (model_features.joblib sıralaması)
        # engineer_features içinde zaten handle ediliyor ama garanti olsun:
        # df = df[raw_columns] # Gerekirse açılabilir

        # 2. Özellik Mühendisliği
        df_eng = learning_service.engineer_features(df)

        # 3. Model Tahmini
        # learning_style_features yüklü ise sadece o sütunları seç, yoksa hata alabilir
        if learning_style_features is not None:
            X_pred = df_eng[learning_style_features]
        else:
            # Fallback (riskli olabilir ama features_path yüklenemediyse dener)
            X_pred = df_eng

        probs = learning_style_model.predict_proba(X_pred)[0]
        style_names = ['Görsel (Visual)', 'İşitsel (Auditory)', 'Okuma/Yazma (Read/Write)', 'Kinestetik (Kinesthetic)']

        # Yüzdeleri hesapla
        pred_dict = {style: prob * 100 for style, prob in zip(style_names, probs)}

        # 4. Gemini Tavsiyesi Al
        advice_text = learning_service.get_gemini_advice(input_data, pred_dict)

        return {
            "status": "success",
            "predictions": pred_dict,
            "advice": advice_text,
            "dominant_style": max(pred_dict, key=pred_dict.get)
        }

    except Exception as e:
        print(f"❌ /analyze/learning-style Hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Learning Style Analysis Error: {str(e)}")


# =============================================================================
# 11. AKADEMİK İZLEME ENDPOINT (YENİ EKLENDİ)
# =============================================================================

@app.post("/analyze/exams")
def analyze_exams(request: AkademikIzlemeRequest):
    """
    Öğrencinin girdiği deneme sınavlarını analiz eder, trendleri ve gelecek tahminini çıkarır.
    """
    if not AnalizMotoru:
        raise HTTPException(status_code=503, detail="Akademik izleme modülü aktif değil.")

    try:
        # 1. Pydantic verisini modülün kendi sınıf yapısına dönüştür
        deneme_listesi = []
        for d_in in request.denemeler:
            deneme = DenemeSinavi(d_in.ad, d_in.tarih)
            for ders_in in d_in.dersler:
                deneme.ders_ekle(DersSonuc(
                    ders_in.ders_adi,
                    ders_in.dogru,
                    ders_in.yanlis,
                    ders_in.bos
                ))
            deneme_listesi.append(deneme)

        # 2. Analiz Motorunu Çalıştır
        motor = AnalizMotoru(deneme_listesi)

        # 3. JSON Çıktısını Al
        analiz_sonuclari = motor.get_api_response_model()

        if "error" in analiz_sonuclari:
            raise HTTPException(status_code=400, detail=analiz_sonuclari["error"])

        # 4. Sözel Özet Raporu (Opsiyonel: Frontend'de göstermek için text olarak da dönüyoruz)
        ozet_metni = OzetMotoru.genel_ozet_raporu_olustur(motor)

        return {
            "status": "success",
            "data": convert_numpy_to_python(analiz_sonuclari),  # Numpy tiplerini temizle
            "summary_text": ozet_metni
        }

    except Exception as e:
        print(f"❌ /analyze/exams Hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Exam Analysis Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 API Servisi Başlatılıyor...")
    uvicorn.run(app, host="127.0.0.1", port=8000)