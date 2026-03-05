using Microsoft.AspNetCore.Mvc;
using System.Text;
using System.Text.Json;
using OgrenciPerformansArayuz.Models; // ViewModel namespace'i

namespace OgrenciPerformansArayuz.Controllers
{
    public class AcademicController : Controller
    {
        private readonly HttpClient _httpClient;

        public AcademicController(IHttpClientFactory httpClientFactory)
        {
            _httpClient = httpClientFactory.CreateClient();
            // Python API adresiniz (api_V2.py çalışırken bu adresi dinler)
            _httpClient.BaseAddress = new Uri("http://127.0.0.1:8000");
        }

        // 1. Veri Giriş Sayfası
        public IActionResult Index()
        {
            return View();
        }

        // 2. Analiz İsteği Gönderen Action (AJAX ile çağrılır)
        [HttpPost]
        public async Task<IActionResult> Analyze([FromBody] AkademikIzlemeRequest request)
        {
            try
            {
                var jsonContent = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");

                // Python API'deki endpoint: /analyze/exams
                var response = await _httpClient.PostAsync("/analyze/exams", jsonContent);

                if (response.IsSuccessStatusCode)
                {
                    var responseString = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<TrackingResponse>(responseString);

                    return Json(new { success = true, data = result });
                }
                else
                {
                    var error = await response.Content.ReadAsStringAsync();
                    return Json(new { success = false, message = "API Hatası: " + error });
                }
            }
            catch (Exception ex)
            {
                return Json(new { success = false, message = "Sunucu Hatası: " + ex.Message });
            }
        }
    }
}