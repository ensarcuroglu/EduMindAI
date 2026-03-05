using System.Text.Json.Serialization;

namespace OgrenciPerformansArayuz.Models
{
    public class PredictionResponseModel
    {
        [JsonPropertyName("student_id")]
        public string StudentId { get; set; }

        [JsonPropertyName("current_score")]
        public double CurrentScore { get; set; }

        [JsonPropertyName("potential_score")]
        public double PotentialScore { get; set; }

        [JsonPropertyName("recommendations")]
        public List<RecommendationModel> Recommendations { get; set; } = new List<RecommendationModel>();

        [JsonPropertyName("root_causes")]
        public List<RootCauseModel> RootCauses { get; set; } = new List<RootCauseModel>();

        [JsonPropertyName("total_opportunities")]
        public int TotalOpportunities { get; set; }

        [JsonPropertyName("time_budget_used")]
        public double TimeBudgetUsed { get; set; }
    }

    public class RecommendationModel
    {
        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("category")]
        public string Category { get; set; }

        [JsonPropertyName("difficulty")]
        public string Difficulty { get; set; }

        [JsonPropertyName("text")]
        public string Text { get; set; }

        [JsonPropertyName("calculated_impact")]
        public double CalculatedImpact { get; set; }

        [JsonPropertyName("time_cost")]
        public double TimeCost { get; set; }

        [JsonPropertyName("simulation")]
        public SimulationModel Simulation { get; set; }
    }

    public class SimulationModel
    {
        [JsonPropertyName("feature")]
        public string Feature { get; set; }

        [JsonPropertyName("operation")]
        public string Operation { get; set; }

        // DÜZELTME BURADA YAPILDI:
        // Eskiden: public double Value { get; set; }
        // Yeni: public object Value { get; set; }
        // Neden? Çünkü API bazen 2.5 (sayı), bazen "Good" (yazı) gönderiyor.
        [JsonPropertyName("value")]
        public object Value { get; set; }
    }

    public class RootCauseModel
    {
        [JsonPropertyName("feature")]
        public string Feature { get; set; }

        [JsonPropertyName("impact")]
        public double Impact { get; set; }
    }
}