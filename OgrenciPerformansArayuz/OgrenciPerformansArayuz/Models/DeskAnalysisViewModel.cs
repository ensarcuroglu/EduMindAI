using System.Text.Json.Serialization;

namespace OgrenciPerformansArayuz.Models
{
    public class DeskAnalysisViewModel
    {
        public bool IsSuccess { get; set; } = false;
        public string ErrorMessage { get; set; }

        [JsonPropertyName("scores")]
        public DeskScores Scores { get; set; }

        [JsonPropertyName("meta")]
        public DeskMeta Meta { get; set; }

        [JsonPropertyName("recommendations")]
        public List<string> Recommendations { get; set; }

        [JsonPropertyName("processed_image_base64")]
        public string ProcessedImageBase64 { get; set; }
    }

    public class DeskScores
    {
        [JsonPropertyName("overall_focus")]
        public int OverallFocus { get; set; }

        [JsonPropertyName("lighting")]
        public int Lighting { get; set; }

        // API V8.1 "clutter_free" gönderiyor, "cognitive" yerine bu geldi.
        [JsonPropertyName("clutter_free")]
        public int ClutterFree { get; set; }

        [JsonPropertyName("ergonomics")]
        public int Ergonomics { get; set; }

        // API V8.1 "wellness" gönderiyor, "health" değil.
        [JsonPropertyName("wellness")]
        public int Wellness { get; set; }
    }

    public class DeskMeta
    {
        [JsonPropertyName("confidence")]
        public int Confidence { get; set; }

        // API "work_mode" gönderiyor
        [JsonPropertyName("work_mode")]
        public string WorkMode { get; set; }

        // V8.1 ile gelen yeni özellikler
        [JsonPropertyName("light_mood")]
        public string LightMood { get; set; }

        [JsonPropertyName("detected_items")]
        public List<string> DetectedItems { get; set; }

        [JsonPropertyName("active_screens")]
        public int ActiveScreens { get; set; }
    }
}