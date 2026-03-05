using System.Text.Json.Serialization;

namespace OgrenciPerformansArayuz.Models
{
    // --- GİRİŞ MODELLERİ (Input - API'ye Giden) ---
    public class AkademikIzlemeRequest
    {
        [JsonPropertyName("denemeler")]
        public List<DenemeSinaviInput> Denemeler { get; set; } = new List<DenemeSinaviInput>();
    }

    public class DenemeSinaviInput
    {
        [JsonPropertyName("ad")]
        public string Ad { get; set; } = string.Empty;

        [JsonPropertyName("tarih")]
        public string Tarih { get; set; } = string.Empty; // Format: "dd.MM.yyyy"

        [JsonPropertyName("dersler")]
        public List<DersSonucInput> Dersler { get; set; } = new List<DersSonucInput>();
    }

    public class DersSonucInput
    {
        [JsonPropertyName("ders_adi")]
        public string DersAdi { get; set; } = string.Empty;

        [JsonPropertyName("dogru")]
        public int Dogru { get; set; }

        [JsonPropertyName("yanlis")]
        public int Yanlis { get; set; }

        [JsonPropertyName("bos")]
        public int Bos { get; set; }
    }

    // --- ÇIKIŞ MODELLERİ (Response - API'den Gelen) ---
    public class TrackingResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; }

        [JsonPropertyName("summary_text")]
        public string SummaryText { get; set; } // API'den gelen sözel özet

        [JsonPropertyName("data")]
        public AnalysisData Data { get; set; }
    }

    public class AnalysisData
    {
        [JsonPropertyName("genel_performans")]
        public GenelPerformans GenelPerformans { get; set; }

        [JsonPropertyName("gelecek_projeksiyonu")]
        public GelecekProjeksiyonu GelecekProjeksiyonu { get; set; }

        // Ders detayları dinamik anahtarlara sahip olduğu için Dictionary kullanıyoruz
        [JsonPropertyName("ders_analizleri")]
        public Dictionary<string, DersAnalizDetay> DersAnalizleri { get; set; }
    }

    public class GenelPerformans
    {
        [JsonPropertyName("net_gecmisi")]
        public List<double> NetGecmisi { get; set; }

        [JsonPropertyName("deneme_isimleri")]
        public List<string> DenemeIsimleri { get; set; }

        [JsonPropertyName("son_durum")]
        public SonDurum SonDurum { get; set; }
    }

    public class SonDurum
    {
        [JsonPropertyName("son_net")]
        public double SonNet { get; set; }

        [JsonPropertyName("momentum_serisi")]
        public int MomentumSerisi { get; set; }
    }

    public class GelecekProjeksiyonu
    {
        [JsonPropertyName("beklenen_gelecek_net")]
        public double? BeklenenGelecekNet { get; set; }

        [JsonPropertyName("guven_araligi")]
        public GuvenAraligi GuvenAraligi { get; set; }
    }

    public class GuvenAraligi
    {
        [JsonPropertyName("alt")]
        public double? Alt { get; set; }

        [JsonPropertyName("ust")]
        public double? Ust { get; set; }
    }

    public class DersAnalizDetay
    {
        [JsonPropertyName("trend_egimi")]
        public double TrendEgimi { get; set; }

        [JsonPropertyName("ortalama_basari_orani")]
        public double OrtalamaBasariOrani { get; set; }

        // Grafik çizimi ve detaylı analiz için eklenen alanlar
        [JsonPropertyName("son_net")]
        public double SonNet { get; set; }

        [JsonPropertyName("net_gecmisi")]
        public List<double> NetGecmisi { get; set; }

        [JsonPropertyName("istatistikler")]
        public IstatistikDetay Istatistikler { get; set; }
    }

    public class IstatistikDetay
    {
        [JsonPropertyName("Ortalama")]
        public double Ortalama { get; set; }

        [JsonPropertyName("StdSapma")]
        public double StdSapma { get; set; }

        [JsonPropertyName("Min")]
        public double Min { get; set; }

        [JsonPropertyName("Max")]
        public double Max { get; set; }
    }
}