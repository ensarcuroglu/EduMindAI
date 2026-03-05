using System.Text.Json.Serialization;

namespace OgrenciPerformansArayuz.Models
{
    public class GestureConfigViewModel
    {
        // Python API: {"config": {"PAUSE": "SHAKA", ...}}
        [JsonPropertyName("config")]
        public Dictionary<string, string> Config { get; set; }
    }
}