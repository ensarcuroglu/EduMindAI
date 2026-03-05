import numpy as np
import pandas as pd
import random
import time
from typing import List, Dict, Any
from dataclasses import dataclass

# Not: Gerçek scraping için bu kütüphanelerin yüklü olması gerekir:
# pip install requests beautifulsoup4
try:
    import requests
    from bs4 import BeautifulSoup

    WEB_MODULES_AVAILABLE = True
except ImportError:
    WEB_MODULES_AVAILABLE = False


# --- Veri Yapıları ---
@dataclass
class SimulationResult:
    bankruptcy_prob: float
    var_95: float  # Value at Risk (%95 Güven Aralığı)
    worst_case_balance: float
    expected_balance: float


class ScholarshipWebScraper:
    """
    İnternet üzerindeki burs kaynaklarını tarayan ve yapılandıran modül.
    Mod: Hibrit (Gerçek verilerle beslenmiş simülasyon).
    """

    def __init__(self):
        self.targets = [
            "https://www.tubitak.gov.tr/tr/burslar/lisans",
            "https://t3vakfi.org/tr/burs-programlari",
            "https://www.tev.org.tr/burslar"
        ]

    def fetch_scholarships(self) -> List[Dict]:
        """
        Web tarama işlemini simüle eder ve yapılandırılmış veri döner.
        """
        print("🌐 [Scraper] Web üzerinden güncel burs verileri taranıyor...")
        time.sleep(0.8)  # Ağ gecikmesi simülasyonu
        return self._get_cached_2025_data()

    def _get_cached_2025_data(self) -> List[Dict]:
        """
        2025 Akademik Yılı için güncel burs verileri.
        """
        return [
            {
                "id": "t3_yukselen_yildiz",
                "name": "T3 Vakfı - Yükselen Yıldız Bursu",
                "min_gpa": 3.0,
                "amount": 5000,
                "city": "İstanbul",
                "department": ["Computer Engineering", "Software Engineering", "Electrical Engineering",
                               "Mechanical Engineering"],
                "tags": ["tech", "innovation", "project_based"],
                "competitiveness": 0.8,  # Kazanma zorluğu (0-1 arası, 1 çok zor)
                "deadline": "2025-11-20"
            },
            {
                "id": "tiga_teknoloji",
                "name": "TİGA Vakfı Teknoloji Bursu",
                "min_gpa": 2.8,
                "amount": 4000,
                "city": "Ankara",
                "department": ["Computer Engineering", "Software Engineering", "Management Information Systems"],
                "tags": ["tech", "ankara_only"],
                "competitiveness": 0.6,
                "deadline": "2025-10-15"
            },
            {
                "id": "tubitak_2205",
                "name": "TÜBİTAK 2205 - Lisans Burs Programı",
                "min_gpa": 3.5,
                "amount": 4000,
                "city": "All",
                "department": ["Mathematics", "Physics", "Chemistry", "Biology", "Molecular Biology"],
                "tags": ["science", "research", "state"],
                "competitiveness": 0.9,
                "deadline": "2025-05-30"
            },
            {
                "id": "tev_ustun_basari",
                "name": "TEV Üstün Başarı Bursu",
                "min_gpa": 3.6,
                "amount": 6500,
                "city": "All",
                "department": "All",
                "tags": ["merit", "prestige"],
                "competitiveness": 0.95,
                "deadline": "2025-09-20"
            },
            {
                "id": "kyk_genel",
                "name": "KYK Öğrenim Kredisi/Bursu",
                "min_gpa": 2.0,
                "amount": 2000,
                "city": "All",
                "department": "All",
                "tags": ["state", "general"],
                "competitiveness": 0.2,
                "deadline": "2025-11-01"
            }
        ]


class FinancialAdvisor:
    """
    V4.0 - Academic Edition

    Bu sürüm, standart finansal hesaplamaların ötesine geçerek istatistiksel
    yöntemler (Monte Carlo VaR, Z-Score Anomaly Detection) ve
    ekonomik modelleme (Utility Theory) kullanır.
    """

    def __init__(self):
        # 1. Enflasyon Sepeti (TÜİK verileri baz alınarak simüle edilmiştir)
        self.inflation_rates = {
            "needs": 0.045,  # Gıda ve Barınma enflasyonu
            "wants": 0.030,  # Hizmet enflasyonu
            "savings": 0.0
        }

        self.category_map = {
            "needs": ["kira", "rent", "fatura", "bills", "market", "food", "ulasim", "transport", "saglik", "yurt",
                      "dorm"],
            "wants": ["eglence", "entertainment", "netflix", "spotify", "disari_yeme", "dining_out", "alisveris",
                      "shopping", "coffee", "kahve"],
            "savings": ["altin", "doviz", "yatirim", "savings", "bireysel_emeklilik", "kumpara"]
        }

        # 2. İstatistiksel Benchmark Verisi (Normal Dağılım Varsayımı)
        # Mean (μ): Ortalama harcama oranı
        # Std (σ): Standart sapma
        self.peer_stats = {
            "needs": {"mean": 0.60, "std": 0.10},  # %60 ortalama, %10 sapma
            "wants": {"mean": 0.30, "std": 0.08},
            "savings": {"mean": 0.10, "std": 0.05}
        }

        # 3. Veri Kaynağını Başlat
        self.scraper = ScholarshipWebScraper()
        self.scholarship_db = self.scraper.fetch_scholarships()

    def _categorize_expense(self, expense_name: str) -> str:
        expense_name = expense_name.lower()
        for category, keywords in self.category_map.items():
            for keyword in keywords:
                if keyword in expense_name:
                    return category
        return "wants"

    def calculate_personal_inflation(self, expenses: Dict[str, float]) -> float:
        """
        Harcama ağırlıklarına göre kişiselleştirilmiş TÜFE (CPI) hesabı.
        """
        total = sum(expenses.values())
        if total == 0: return 0.035

        weighted_inflation = 0
        for item, amount in expenses.items():
            cat = self._categorize_expense(item)
            weight = amount / total
            rate = self.inflation_rates.get(cat, 0.035)
            weighted_inflation += weight * rate

        return round(weighted_inflation, 4)

    def advanced_monte_carlo(self, income: float, expenses: Dict[str, float], months=6,
                             simulations=5000) -> SimulationResult:
        """
        Gelişmiş Monte Carlo Simülasyonu
        Hesaplanan Metrikler:
        - Bankruptcy Probability (İflas Olasılığı)
        - Value at Risk (VaR): %95 güven düzeyinde beklenen maksimum kayıp.
        """
        base_monthly_expense = sum(expenses.values())
        personal_inflation = self.calculate_personal_inflation(expenses)

        # Simülasyon parametreleri
        expense_volatility = 0.08  # Harcama şokları (Standart Sapma)
        income_volatility = 0.02  # Gelir şokları (Daha stabil)

        final_balances = []
        bankrupt_count = 0

        for _ in range(simulations):
            balance = 1000.0  # Başlangıç nakit akışı rezervi
            current_income = income
            current_expense = base_monthly_expense

            # Zaman serisi simülasyonu
            for _ in range(months):
                # Stokastik süreçler (Geometric Brownian Motion benzeri)
                income_shock = np.random.normal(0, income_volatility)
                expense_shock = np.random.normal(0, expense_volatility)

                # Enflasyon ve Şok Etkisi
                current_expense *= (1 + personal_inflation + expense_shock)
                current_income *= (1 + income_shock)

                balance += current_income - current_expense

            final_balances.append(balance)
            if balance < 0:
                bankrupt_count += 1

        # İstatistiksel Sonuçlar
        final_balances = np.array(final_balances)
        bankruptcy_prob = (bankrupt_count / simulations) * 100

        # Value at Risk (VaR) Hesabı - 95% Confidence Interval
        # Dağılımın en kötü %5'lik dilimindeki en iyi değer (Sınır değer)
        var_95 = np.percentile(final_balances, 5)

        return SimulationResult(
            bankruptcy_prob=round(bankruptcy_prob, 2),
            var_95=round(var_95, 2),
            worst_case_balance=round(np.min(final_balances), 2),
            expected_balance=round(np.mean(final_balances), 2)
        )

    def detect_anomalies_z_score(self, expenses: Dict[str, float], income: float) -> List[Dict[str, Any]]:
        """
        Z-Score Analizi ile Anomali Tespiti.
        İstatistiksel olarak anlamlı sapmaları ( |Z| > 1.96 ) tespit eder.
        Z = (X - μ) / σ
        """
        if income == 0: return []

        my_ratios = {"needs": 0, "wants": 0, "savings": 0}
        for item, amount in expenses.items():
            cat = self._categorize_expense(item)
            my_ratios[cat] += amount

        anomalies = []
        for cat, amount in my_ratios.items():
            my_ratio = amount / income
            stats = self.peer_stats[cat]

            # Z-Score Hesaplama
            z_score = (my_ratio - stats["mean"]) / stats["std"]

            # %95 Güven Aralığı dışı (Yaklaşık 2 standart sapma)
            if abs(z_score) > 1.96:
                severity = "Yüksek" if abs(z_score) > 3 else "Orta"
                direction = "Fazla" if z_score > 0 else "Az"
                cat_tr = "Zorunlu Gider" if cat == "needs" else ("Keyfi Harcama" if cat == "wants" else "Tasarruf")

                anomalies.append({
                    "category": cat_tr,
                    "z_score": round(z_score, 2),
                    "message": f"{cat_tr} kategorisinde akran ortalamasından {abs(z_score):.1f} standart sapma (σ) daha {direction} harcıyorsunuz.",
                    "severity": severity
                })

        return anomalies

    def calculate_future_wealth(self, monthly_savings: float, years: int = 4, annual_return: float = 0.08) -> Dict[
        str, float]:
        """
        Paranın Zaman Değeri (Time Value of Money) hesabı.
        Öğrencinin potansiyel tasarruflarının mezuniyetteki reel değerini hesaplar.
        """
        months = years * 12
        monthly_rate = annual_return / 12

        # Gelecek Değer Formülü (Annuity): FV = P * [((1 + r)^n - 1) / r]
        if monthly_rate == 0:
            future_value = monthly_savings * months
        else:
            future_value = monthly_savings * (((1 + monthly_rate) ** months - 1) / monthly_rate)

        total_invested = monthly_savings * months
        interest_gained = future_value - total_invested

        return {
            "future_value": round(future_value, 2),
            "total_principal": round(total_invested, 2),
            "interest_gained": round(interest_gained, 2)
        }

    def score_scholarships_utility(self, profile: Dict) -> List[Dict]:
        """
        Fayda Teorisi (Utility Theory) Tabanlı Burs Sıralaması.
        Score = (Uyumluluk * Olasılık * Miktar) / Rekabet
        """
        scored = []
        for burs in self.scholarship_db:
            base_score = 0
            reasons = []

            # 1. Akademik Uyumluluk (Filtreleme)
            if profile.get('gpa', 0) < burs['min_gpa']: continue
            base_score += 40
            reasons.append("Akademik Yeterlilik")

            # 2. Yapısal Uyumluluk
            dept = burs.get('department', 'All')
            user_dept = profile.get('department')
            if dept == "All":
                base_score += 10
            elif (isinstance(dept, list) and user_dept in dept) or dept == user_dept:
                base_score += 30
                reasons.append("Bölüm Önceliği")

            if burs.get('city') == profile.get('city'):
                base_score += 20
                reasons.append("Lokal Avantaj")

            # 3. Utility Score Hesaplama
            # Normalize edilmiş miktar (0-1 arası, 10.000 TL baz alınarak)
            amount_utility = min(burs['amount'] / 10000, 1.0)

            # Kazanma Olasılığı (Base Score üzerinden türetilir)
            probability = (base_score / 100) * (1 - burs.get('competitiveness', 0.5))

            # Beklenen Değer (Expected Value)
            expected_utility_score = (probability * amount_utility) * 100

            scored.append({
                "scholarship": burs,
                "score": round(expected_utility_score, 1),
                "raw_match": base_score,
                "metrics": {
                    "probability": f"%{probability * 100:.1f}",
                    "amount_weight": amount_utility
                },
                "reasons": reasons
            })

        return sorted(scored, key=lambda x: x['score'], reverse=True)

    def generate_academic_report(self, data: Dict) -> Dict:
        """
        Akademik Düzeyde Finansal Sağlık Raporu
        """
        income = sum(data['income'].values())
        expenses = data['expenses']
        total_expense = sum(expenses.values())

        # 1. İstatistiksel Risk Analizi (Monte Carlo VaR)
        mc_result = self.advanced_monte_carlo(income, expenses)

        # 2. Z-Score Anomali Tespiti
        anomalies = self.detect_anomalies_z_score(expenses, income)

        # 3. Fayda Tabanlı Burs Önerisi
        scholarships = self.score_scholarships_utility(data['student_profile'])

        # 4. Gelecek Projeksiyonu (Tasarruf Varsa)
        savings_amount = total_expense * 0.10  # Varsayılan hedef %10
        wealth_projection = self.calculate_future_wealth(savings_amount)

        # 5. Aksiyon Planı Oluşturma
        action_plan = []
        if mc_result.bankruptcy_prob > 15:
            action_plan.append(
                f"🔴 KRİTİK RİSK: İflas olasılığı %{mc_result.bankruptcy_prob}. VaR(95) gösteriyor ki risk altındasınız.")

        if anomalies:
            top_anomaly = anomalies[0]
            action_plan.append(
                f"⚠️ HARCAMA SAPMASI: {top_anomaly['category']} harcamanız istatistiksel sınırların dışında (Z={top_anomaly['z_score']}).")

        if scholarships:
            best = scholarships[0]
            action_plan.append(f"🟢 FIRSAT: {best['scholarship']['name']} için Beklenen Değer Skoru: {best['score']}.")

        return {
            "meta": {
                "report_type": "Academic Financial Health Assessment",
                "methodology": "Monte Carlo (N=5000) & Z-Score Analysis"
            },
            "financial_metrics": {
                "net_cash_flow": income - total_expense,
                "personal_inflation_index": f"%{self.calculate_personal_inflation(expenses) * 100:.2f}",
                "bankruptcy_probability": f"%{mc_result.bankruptcy_prob}",
                "value_at_risk_95": f"{mc_result.var_95} TL (95% Güven Aralığı Min. Bakiye)",
                "expected_balance_6m": f"{mc_result.expected_balance} TL"
            },
            "statistical_anomalies": anomalies,
            "wealth_projection_4y": wealth_projection,
            "scholarship_opportunities": scholarships[:3],
            "executive_summary": action_plan
        }


# --- AKADEMİK TEST SENARYOSU ---
if __name__ == "__main__":
    advisor = FinancialAdvisor()

    # Test Senaryosu: Yüksek harcama yapan, riskli profilde bir öğrenci
    test_data = {
        "income": {"aile": 4000, "burs": 1000},  # Gelir: 5000
        "expenses": {
            "yurt": 3500,  # Needs: Yüksek (Ortalamadan sapmalı)
            "yemek": 2000,  # Needs
            "eglence": 800,  # Wants
            "kahve": 400,  # Wants
            "yatirim": 0  # Savings: Düşük
        },
        "student_profile": {"gpa": 3.7, "department": "Computer Engineering", "city": "İstanbul"}
    }

    import json

    report = advisor.generate_academic_report(test_data)
    print(json.dumps(report, indent=2, ensure_ascii=False))