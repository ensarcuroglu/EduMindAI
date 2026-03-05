using Microsoft.AspNetCore.Mvc;
using OgrenciPerformansArayuz.Models;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization; // Enum Converter için gerekli
using System.Net.Http;

namespace OgrenciPerformansArayuz.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly JsonSerializerOptions _jsonOptions;

        // Python API Base URL
        private const string ApiBaseUrl = "http://127.0.0.1:8000/";

        public HomeController(ILogger<HomeController> logger, IHttpClientFactory httpClientFactory)
        {
            _logger = logger;
            _httpClientFactory = httpClientFactory;

            // Python API ile tam uyumlu JSON ayarlarý
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower, // camelCase -> snake_case
                PropertyNameCaseInsensitive = true,
                WriteIndented = true,
                NumberHandling = JsonNumberHandling.AllowReadingFromString,
                // KRÝTÝK: Enum'larý (Priority, Category vb.) sayý yerine String olarak gönderir.
                Converters = { new JsonStringEnumConverter() }
            };
        }

        [HttpGet]
        public IActionResult Index()
        {
            return View(new StudentInputModel());
        }

        // ==================================================================================
        // 1. MASA ANALÝZÝ (VISION V8.1)
        // ==================================================================================

        [HttpGet]
        public IActionResult DeskAnalyze()
        {
            return View(new DeskAnalysisViewModel());
        }

        [HttpPost]
        public async Task<IActionResult> AnalyzeDesk(IFormFile deskImage)
        {
            if (deskImage == null || deskImage.Length == 0)
            {
                ViewBag.ErrorMessage = "Lütfen geçerli bir fotoðraf dosyasý seçin.";
                return View("DeskAnalyze");
            }

            if (deskImage.Length > 10 * 1024 * 1024)
            {
                ViewBag.ErrorMessage = "Dosya boyutu çok büyük (Maksimum 10MB).";
                return View("DeskAnalyze");
            }

            try
            {
                var client = _httpClientFactory.CreateClient();
                client.BaseAddress = new Uri(ApiBaseUrl);
                client.Timeout = TimeSpan.FromSeconds(90); // Görüntü iþleme uzun sürebilir

                using (var content = new MultipartFormDataContent())
                {
                    using (var stream = deskImage.OpenReadStream())
                    {
                        var fileContent = new StreamContent(stream);
                        fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(deskImage.ContentType);
                        content.Add(fileContent, "file", deskImage.FileName);

                        var response = await client.PostAsync("analyze/desk", content);
                        var responseString = await response.Content.ReadAsStringAsync();

                        if (response.IsSuccessStatusCode)
                        {
                            var viewModel = JsonSerializer.Deserialize<DeskAnalysisViewModel>(responseString, _jsonOptions);
                            if (viewModel != null)
                            {
                                viewModel.IsSuccess = true;
                                return View("DeskAnalyze", viewModel);
                            }
                        }

                        ViewBag.ErrorMessage = $"Yapay Zeka Analiz Hatasý: {response.StatusCode}";
                        return View("DeskAnalyze");
                    }
                }
            }
            catch (Exception ex)
            {
                ViewBag.ErrorMessage = $"Sistem Baðlantý Hatasý: {ex.Message}";
                return View("DeskAnalyze");
            }
        }

        // ==================================================================================
        // 2. PERFORMANS TAHMÝNÝ (ML PREDICTION)
        // ==================================================================================

        [HttpPost]
        public async Task<IActionResult> Analyze(StudentInputModel model)
        {
            if (!ModelState.IsValid) return View("Index", model);

            try
            {
                var client = _httpClientFactory.CreateClient();
                client.BaseAddress = new Uri(ApiBaseUrl);
                client.Timeout = TimeSpan.FromSeconds(30);

                var jsonContent = JsonSerializer.Serialize(model, _jsonOptions);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                var response = await client.PostAsync("predict", content);
                var responseString = await response.Content.ReadAsStringAsync();

                if (response.IsSuccessStatusCode)
                {
                    var result = JsonSerializer.Deserialize<PredictionResponseModel>(responseString, _jsonOptions);
                    ViewBag.StudentDataJson = jsonContent;
                    return View("Result", result);
                }
                else
                {
                    ModelState.AddModelError("", $"API Hatasý ({response.StatusCode}): {responseString}");
                    return View("Index", model);
                }
            }
            catch (Exception ex)
            {
                ModelState.AddModelError("", $"Sistem Hatasý: {ex.Message}");
                return View("Index", model);
            }
        }

        [HttpPost]
        public async Task<IActionResult> Negotiate([FromBody] NegotiationViewModel request)
        {
            if (request == null || request.StudentData == null)
                return BadRequest(new { error = "Veri eksik." });

            try
            {
                var client = _httpClientFactory.CreateClient();
                client.BaseAddress = new Uri(ApiBaseUrl);

                var payload = new
                {
                    student_data = request.StudentData,
                    target_score = request.TargetScore,
                    frozen_features = request.FrozenFeatures ?? new List<string>()
                };

                var jsonContent = JsonSerializer.Serialize(payload, _jsonOptions);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                var response = await client.PostAsync("negotiate", content);
                var responseString = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    return StatusCode((int)response.StatusCode, new { error = responseString });
                }

                return Content(responseString, "application/json");
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { error = ex.Message });
            }
        }

        public IActionResult Result(PredictionResponseModel result)
        {
            if (result == null || string.IsNullOrEmpty(result.StudentId))
            {
                return RedirectToAction("Index");
            }
            return View(result);
        }

        // ==================================================================================
        // 3. POMODORO VE JEST KONTROLÜ
        // ==================================================================================

        [HttpGet]
        public IActionResult Pomodoro()
        {
            return View();
        }

        [HttpPost]
        public async Task<IActionResult> UpdateGestureConfig([FromBody] GestureConfigViewModel model)
        {
            try
            {
                var client = _httpClientFactory.CreateClient();
                client.BaseAddress = new Uri(ApiBaseUrl);

                var jsonContent = JsonSerializer.Serialize(model, _jsonOptions);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                var response = await client.PostAsync("gesture/config", content);
                var responseString = await response.Content.ReadAsStringAsync();

                if (response.IsSuccessStatusCode)
                {
                    return Ok(new { success = true, message = "Jest ayarlarý güncellendi." });
                }
                else
                {
                    return BadRequest(new { success = false, message = responseString });
                }
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { success = false, message = ex.Message });
            }
        }

        // ==================================================================================
        // 4. AKILLI DERS PLANLAYICI (FLUX SCHEDULER) - YENÝ
        // ==================================================================================

        // DÜZELTME: Metot adý View dosyasý ile (GenerateSchedule.cshtml) eþleþmeli.
        [HttpGet]
        public IActionResult GenerateSchedule()
        {
            // Planlayýcý arayüzünü açar
            return View();
        }

        [HttpPost]
        public async Task<IActionResult> GenerateSchedule([FromBody] SchedulerRequestModel request)
        {
            if (request == null)
            {
                return BadRequest(new { success = false, message = "Ýstek verisi alýnamadý." });
            }

            try
            {
                var client = _httpClientFactory.CreateClient();
                client.BaseAddress = new Uri(ApiBaseUrl);
                // Planlama algoritmasý (PuLP) bazen 15-20 saniye sürebilir, timeout'u artýrýyoruz.
                client.Timeout = TimeSpan.FromSeconds(120);

                var jsonContent = JsonSerializer.Serialize(request, _jsonOptions);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                // Python API: /schedule endpointine istek atýyoruz
                var response = await client.PostAsync("schedule", content);
                var responseString = await response.Content.ReadAsStringAsync();

                if (response.IsSuccessStatusCode)
                {
                    // API'den dönen SchedulerResponseModel'i JS tarafýna iletiyoruz
                    var result = JsonSerializer.Deserialize<SchedulerResponseModel>(responseString, _jsonOptions);
                    return Ok(result);
                }
                else
                {
                    // API hata mesajýný (örn: "Çözüm bulunamadý") iletiyoruz
                    return StatusCode((int)response.StatusCode, new { success = false, message = responseString });
                }
            }
            catch (Exception ex)
            {
                return StatusCode(500, new { success = false, message = $"Sunucu Baðlantý Hatasý: {ex.Message}" });
            }
        }

        // ==================================================================================
        // 5. AI MENTOR CHAT (GEMINI ENTEGRASYONU)
        // ==================================================================================

        [HttpPost]
        public async Task<IActionResult> ChatWithMentor([FromBody] ChatRequestViewModel request)
        {
            // 1. Basit Doðrulama
            if (request == null || string.IsNullOrWhiteSpace(request.UserMessage))
            {
                return BadRequest(new { success = false, message = "Mesaj boþ olamaz." });
            }

            try
            {
                // 2. HTTP Client Hazýrlýðý
                var client = _httpClientFactory.CreateClient();
                client.BaseAddress = new Uri(ApiBaseUrl);
                client.Timeout = TimeSpan.FromSeconds(60); // AI cevabý bazen düþünebilir

                // 3. Veriyi JSON'a Çevir (Python API formatýna uygun: snake_case)
                var jsonContent = JsonSerializer.Serialize(request, _jsonOptions);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                // 4. Python API'ye Ýstek At (/ai/chat)
                var response = await client.PostAsync("ai/chat", content);
                var responseString = await response.Content.ReadAsStringAsync();

                if (response.IsSuccessStatusCode)
                {
                    // Baþarýlýysa Python'dan gelen cevabý direkt Frontend'e dön
                    // Python Cevabý: { "response": "..." }
                    return Content(responseString, "application/json");
                }
                else
                {
                    // Hata varsa logla ve kullanýcýya bildir
                    _logger.LogError($"AI Mentor API Hatasý: {response.StatusCode} - {responseString}");
                    return StatusCode((int)response.StatusCode, new { success = false, message = "AI Mentör þu an meþgul." });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Chat Exception: {ex.Message}");
                return StatusCode(500, new { success = false, message = $"Baðlantý Hatasý: {ex.Message}" });
            }
        }


        // ==================================================================================
        // 6. ÖÐRENME STÝLÝ ANALÝZÝ (YENÝ MODÜL)
        // ==================================================================================

        [HttpGet]
        public IActionResult LearnStyle()
        {
            return View();
        }

        [HttpPost]
        public async Task<IActionResult> AnalyzeLearningStyle([FromBody] LearningStyleInputModel request)
        {
            if (request == null)
            {
                return BadRequest(new { success = false, message = "Veri alýnamadý." });
            }

            try
            {
                var client = _httpClientFactory.CreateClient();
                client.BaseAddress = new Uri(ApiBaseUrl);
                client.Timeout = TimeSpan.FromSeconds(45);

                // KRÝTÝK NOKTA:
                // Global _jsonOptions nesnesi, tüm property'leri "snake_case"e (örn: study_hours) çeviriyor.
                // Ancak Learning Style modülünün Python tarafýndaki Pydantic modeli (api_V2.py -> LearningStyleInput),
                // "StudyHours" gibi PascalCase isimlendirme bekliyor.
                // Bu yüzden burada _jsonOptions KULLANMIYORUZ. Varsayýlan (PascalCase) serileþtiriciyi kullanýyoruz.

                var jsonContent = JsonSerializer.Serialize(request);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");

                var response = await client.PostAsync("analyze/learning-style", content);
                var responseString = await response.Content.ReadAsStringAsync();

                if (response.IsSuccessStatusCode)
                {
                    // Baþarýlý yanýtý direkt frontend'e iletiyoruz.
                    return Content(responseString, "application/json");
                }
                else
                {
                    _logger.LogError($"Learning Style API Hatasý: {response.StatusCode} - {responseString}");
                    return StatusCode((int)response.StatusCode, new { success = false, message = "Analiz servisi yanýt vermedi." });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError($"Learning Style Exception: {ex.Message}");
                return StatusCode(500, new { success = false, message = $"Baðlantý Hatasý: {ex.Message}" });
            }
        }





        // ==================================================================================
        // 7. DÝÐER SAYFALAR
        // ==================================================================================
        public IActionResult Product() => View();
        public IActionResult Social() => View();
        public IActionResult Goals() => View();
        public IActionResult PerformanceAnalytics() => View();
        public IActionResult ProductiveBreak() => View();
        public IActionResult Reports() => View();
        public IActionResult AiMentor() => View();
        public IActionResult Profile() => View();
        public IActionResult Settings() => View();
        public IActionResult Abonelik() => View();
        public IActionResult Login() => View();
        public IActionResult Privacy() => View();

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }

    public class NegotiationViewModel
    {
        public StudentInputModel StudentData { get; set; }
        public double TargetScore { get; set; }
        public List<string> FrozenFeatures { get; set; }
    }


    // AI Chat için gerekli modeller
    public class ChatRequestViewModel
    {
        public string UserMessage { get; set; }
        public List<ChatHistoryItem> History { get; set; } = new List<ChatHistoryItem>();
    }

    public class ChatHistoryItem
    {
        public string Role { get; set; } // "user" veya "model"
        public string Message { get; set; }
    }
}