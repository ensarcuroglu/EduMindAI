# optimizer.py
import numpy as np
import pandas as pd
import copy
import random
from typing import Any, Dict, List, Union, Tuple

# ==========================================
# 🎯 DEĞİŞKEN AYARLARI (DNA)
# ==========================================
MUTABLE_FEATURES = {
    'study_hours_per_day': (0.0, 12.0, 0.5),
    'social_media_hours': (0.0, 10.0, 0.5),
    'netflix_hours': (0.0, 8.0, 0.5),
    'sleep_hours': (5.0, 10.0, 0.5),
    'attendance_percentage': (0.0, 100.0, 5.0),  # Adım aralığı 5
    'diet_quality': ['Poor', 'Fair', 'Good']
}

COST_WEIGHTS = {
    'study_hours_per_day': 3.0,
    'sleep_hours': 1.0,
    'social_media_hours': 1.2,
    'netflix_hours': 1.0,
    'attendance_percentage': 0.05,
    'diet_quality': 10.0
}

TIME_CONSUMING = ['study_hours_per_day', 'sleep_hours']
TIME_SOURCE = ['social_media_hours', 'netflix_hours']


class AcademicOptimizer:
    def __init__(self, advisor: Any):
        self.advisor = advisor

    def _calculate_attendance_hours(self, percentage: float) -> float:
        return (percentage / 100.0) * 6.0

    def _calculate_fitness(self, original: dict, candidate: dict, target_score: float) -> float:
        """
        Genetik Algoritma için 'Fitness' (Uygunluk) Fonksiyonu.
        Amaç: Hedef puana yakınlık + Düşük Maliyet + Fizik Kurallarına Uyum.
        Daha yüksek Fitness = Daha iyi çözüm.
        """
        # 1. Tahmin Puanı
        enriched = self.advisor._calculate_derived(candidate)
        pred_score = self.advisor.predict(enriched)

        # Puan Farkı Cezası (Hedefe ulaşamadıysa ceza büyük)
        score_diff = target_score - pred_score
        score_penalty = 0
        if score_diff > 0:
            # Hedefin altındaysa karesel ceza (Hedefe yaklaşmayı zorla)
            score_penalty = (score_diff ** 2) * 10

        # 2. Efor/Değişim Maliyeti (Cost)
        effort_cost = self._calculate_effort_cost(original, candidate)

        # Fitness = (Büyük Sabit) - Ceza - Maliyet
        # Ne kadar yüksekse o kadar iyi.
        return 100000 - score_penalty - effort_cost, pred_score

    def _calculate_effort_cost(self, original: dict, candidate: dict) -> float:
        total_cost = 0.0

        # --- ZOMBİ KONTROLÜ ---
        orig_sleep = original.get('sleep_hours', 0)
        new_sleep = candidate.get('sleep_hours', 0)
        if orig_sleep < 6.0 and new_sleep < 6.0: return 99999.0
        if new_sleep < 5.0: return 99999.0

        # --- FİZİK (ZAMAN) KONTROLÜ ---
        orig_school = self._calculate_attendance_hours(original.get('attendance_percentage', 0))
        new_school = self._calculate_attendance_hours(candidate.get('attendance_percentage', 0))

        added_time = (new_school - orig_school)
        removed_time = 0.0

        for feat in MUTABLE_FEATURES.keys():
            if feat not in candidate or feat == 'diet_quality': continue
            diff = candidate[feat] - original[feat]

            if feat in TIME_CONSUMING:
                if diff > 0:
                    added_time += diff
                elif diff < 0:
                    removed_time += abs(diff)
            elif feat in TIME_SOURCE:
                if diff < 0:
                    removed_time += abs(diff)
                elif diff > 0:
                    added_time += diff

        time_gap = added_time - removed_time
        if time_gap > 0.5:
            total_cost += 1000.0 * (time_gap ** 2)

        # --- DEĞİŞİM MALİYETİ ---
        for feat, weight in COST_WEIGHTS.items():
            if feat not in original or feat not in candidate: continue

            # --- DİYET KORUMASI (YENİ) ---
            if feat == 'diet_quality':
                levels = MUTABLE_FEATURES['diet_quality']
                try:
                    old_idx = levels.index(original[feat])
                    new_idx = levels.index(candidate[feat])

                    if new_idx < old_idx:
                        # Diyet kalitesi düşüyorsa -> İMKANSIZ
                        total_cost += 99999.0
                    elif new_idx > old_idx:
                        # İyileşiyorsa -> Maliyet
                        total_cost += (new_idx - old_idx) * weight
                except:
                    pass
                continue

            diff = candidate[feat] - original[feat]

            if feat == 'study_hours_per_day' and diff > 0:
                total_cost += diff * weight
            elif feat in TIME_SOURCE and diff < 0:
                total_cost += abs(diff) * weight
            elif feat == 'sleep_hours':
                total_cost += abs(diff) * weight * 0.5

            # --- DEVAMSIZLIK KORUMASI (YENİ) ---
            elif feat == 'attendance_percentage':
                if diff < 0:
                    # Devamsızlık düşüyorsa (okulu asıyorsa) -> İMKANSIZ
                    total_cost += 99999.0
                elif diff > 0:
                    total_cost += diff * weight

        return total_cost

    def _crossover(self, parent1: dict, parent2: dict, frozen_features: List[str]) -> dict:
        """İki çözümden yeni bir çözüm üretir, ancak kilitli genleri korur."""
        child = parent1.copy()
        for feat in MUTABLE_FEATURES.keys():
            # EĞER ÖZELLİK KİLİTLİYSE KARIŞTIRMA YAPMA, PARENT1 (ORİJİNAL)'DE KALSIN
            if feat in frozen_features:
                continue

            if random.random() < 0.5:
                child[feat] = parent2[feat]
        return child

    def _mutate(self, candidate: dict, frozen_features: List[str]) -> dict:
        """Rastgele mutasyon."""
        mutant = candidate.copy()

        # Zombi Kurtarma Refleksi
        if 'sleep_hours' not in frozen_features and mutant.get('sleep_hours', 0) < 6.0 and random.random() < 0.5:
            mutant['sleep_hours'] = random.choice([6.0, 6.5, 7.0])
            return mutant

        mutation_type = random.random()

        # --- TAKAS MUTASYONU ---
        if mutation_type < 0.6:
            available_consumers = [f for f in TIME_CONSUMING if f not in frozen_features]
            available_sources = [f for f in TIME_SOURCE if f not in frozen_features]

            if available_consumers and available_sources:
                consumer = random.choice(available_consumers)
                source = random.choice(available_sources)

                bounds_c = MUTABLE_FEATURES[consumer]
                val_c = mutant[consumer] + bounds_c[2]
                mutant[consumer] = min(bounds_c[1], val_c)

                bounds_s = MUTABLE_FEATURES[source]
                val_s = mutant[source] - bounds_s[2]
                mutant[source] = max(bounds_s[0], val_s)
                return mutant

        # --- TEKLİ MUTASYON ---
        available_feats = [f for f in MUTABLE_FEATURES.keys() if f not in frozen_features]
        if not available_feats: return mutant

        feature = random.choice(available_feats)
        bounds = MUTABLE_FEATURES[feature]

        # --- DİYET MUTASYONU (Sadece İleri) ---
        if feature == 'diet_quality':
            curr_idx = bounds.index(mutant[feature])
            # Sadece yukarı gitmesine izin ver (curr_idx + 1)
            if curr_idx < len(bounds) - 1:
                mutant[feature] = bounds[curr_idx + 1]
            # Zaten en iyiyse (Good), değişim yapma.

        # --- DEVAMSIZLIK MUTASYONU (Sadece İleri) ---
        elif feature == 'attendance_percentage':
            current_val = mutant[feature]
            max_v = bounds[1]
            step_v = bounds[2]
            # Sadece yukarı yönlü (+step) hareket et
            val = current_val + step_v
            mutant[feature] = min(max_v, val)

        # --- DİĞERLERİ (Normal) ---
        else:
            min_v, max_v, step_v = bounds
            change = random.choice([-step_v, step_v])
            val = mutant[feature] + change
            mutant[feature] = max(min_v, min(max_v, val))

        return mutant

    def find_optimal_path(self, student_data: dict, target_score: float,
                          frozen_features: List[str] = [],
                          population_size=60, generations=50):

        print(f"🧬 Genetik Optimizasyon Başlıyor... (Hedef: {target_score:.1f}, Kilitli: {frozen_features})")

        population = [student_data.copy() for _ in range(population_size)]

        for i in range(1, population_size):
            for _ in range(5):
                population[i] = self._mutate(population[i], frozen_features)

        best_solution = None
        best_fitness = -float('inf')

        for gen in range(generations):
            scored_population = []
            for indiv in population:
                fitness, pred_score = self._calculate_fitness(student_data, indiv, target_score)
                scored_population.append((fitness, indiv, pred_score))

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_solution = indiv

            scored_population.sort(key=lambda x: x[0], reverse=True)

            next_gen = []
            next_gen.extend([x[1] for x in scored_population[:3]])

            while len(next_gen) < population_size:
                selection_pool_size = max(3, int(population_size * 0.4))  # Popülasyonun %40'ı
                parent1 = random.choice(scored_population[:selection_pool_size])[1]
                parent2 = random.choice(scored_population[:selection_pool_size])[1]

                # GÜNCELLEME: frozen_features parametresi eklendi
                child = self._crossover(parent1, parent2, frozen_features)

                if random.random() < 0.15:
                    child = self._mutate(child, frozen_features)

                # GÜNCELLEME: Zorunlu Kilit (Safety Net)
                # Kilitli özelliklerin değişmediğinden %100 emin olmak için:
                for locked_feat in frozen_features:
                    child[locked_feat] = student_data[locked_feat]

                next_gen.append(child)

            population = next_gen

        enriched_final = self.advisor._calculate_derived(best_solution)
        final_score = self.advisor.predict(enriched_final)
        final_cost = self._calculate_effort_cost(student_data, best_solution)

        if final_cost > 5000:
            return {"status": "Impossible", "msg": "Hedefe ulaşmak fiziksel olarak imkansız (Gün yetmiyor)."}

        if final_score < target_score - 0.5:
            return {"status": "Impossible", "msg": "Mevcut kısıtlamalarla bu puana ulaşılamadı."}

        return self._generate_report(student_data, best_solution, target_score, frozen_features)

    def _generate_report(self, original, optimized, target, frozen):
        changes = []
        enriched_final = self.advisor._calculate_derived(optimized)
        final_score = self.advisor.predict(enriched_final)

        for feat in MUTABLE_FEATURES.keys():
            if feat not in original or feat not in optimized: continue
            if feat in frozen: continue

            orig_val = original[feat]
            opt_val = optimized[feat]

            if feat == 'diet_quality':
                if orig_val != opt_val:
                    changes.append({
                        "feature": feat, "old": orig_val, "new": opt_val, "diff": 0,
                        "text": f"🥗 Diet Quality: {orig_val} -> {opt_val}"
                    })
                continue

            if abs(opt_val - orig_val) > 0.01:
                diff = opt_val - orig_val
                icon = "📈" if diff > 0 else "📉"
                changes.append({
                    "feature": feat,
                    "old": orig_val,
                    "new": opt_val,
                    "diff": diff,
                    "text": f"{icon} {feat.replace('_', ' ').title()}: {orig_val:.1f} -> {opt_val:.1f} ({diff:+.1f})"
                })

        return {
            "status": "Success",
            "original_score": self.advisor.predict(self.advisor._calculate_derived(original)),
            "target_score": target,
            "achieved_score": final_score,
            "changes": changes,
            "optimized_data": optimized
        }