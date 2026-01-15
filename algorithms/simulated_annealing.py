#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulated Annealing dla optymalizacji trasy drona
"""

import numpy as np
import random
import math
from drone_path_optimization import (
    GRID_WIDTH, GRID_HEIGHT, NUM_WAYPOINTS, GENERATIONS,
    calculate_path_length, is_line_intersecting_obstacle,
    repair_individual, repair_waypoint, wind_effect, OBSTACLES
)


class SimulatedAnnealing:
    """Simulated Annealing dla optymalizacji trasy drona"""

    def __init__(self, generations=GENERATIONS,
                 initial_temp=100.0,
                 cooling_rate=0.95):
        self.generations = generations
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.best_fitness = []
        self.avg_fitness = []

    def _create_solution(self):
        """Tworzy losowe rozwiązanie"""
        solution = [[0, 0]]
        for _ in range(NUM_WAYPOINTS - 2):
            solution.append([random.uniform(0, GRID_WIDTH),
                             random.uniform(0, GRID_HEIGHT)])
        solution.append([GRID_WIDTH, GRID_HEIGHT])
        return repair_individual(solution)

    def _evaluate_fitness(self, solution):
        """Ewaluuje fitness rozwiązania"""
        path_length = calculate_path_length(solution)

        obstacle_penalty = 0.0
        for i in range(len(solution) - 1):
            if is_line_intersecting_obstacle(solution[i], solution[i + 1]):
                obstacle_penalty += 100.0

        wind_penalty = 0.0
        for point in solution:
            affected = wind_effect(point, 5.0, 45)
            drift = np.sqrt((affected[0] - point[0]) ** 2 + (affected[1] - point[1]) ** 2)
            wind_penalty += drift * 0.5

        return path_length + obstacle_penalty + wind_penalty

    def _generate_neighbor(self, solution):
        """Generuje sąsiednie rozwiązanie"""
        neighbor = [row[:] for row in solution]

        # Zmień jeden losowy punkt
        idx = random.randint(1, len(neighbor) - 2)
        neighbor[idx][0] = np.clip(neighbor[idx][0] + random.gauss(0, 5), 0, GRID_WIDTH)
        neighbor[idx][1] = np.clip(neighbor[idx][1] + random.gauss(0, 5), 0, GRID_HEIGHT)

        return repair_individual(neighbor)

    def run(self):
        """Uruchamia algorytm Simulated Annealing"""
        # Inicjalizuj rozwiązanie
        current = self._create_solution()
        current_fitness = self._evaluate_fitness(current)

        best = current[:]
        best_fitness = current_fitness

        temperature = self.initial_temp

        for gen in range(self.generations):
            # Generuj sąsiednie rozwiązanie
            neighbor = self._generate_neighbor(current)
            neighbor_fitness = self._evaluate_fitness(neighbor)

            # Oblicz różnicę
            delta = neighbor_fitness - current_fitness

            # Akceptuj lub odrzuć
            if delta < 0 or random.random() < math.exp(-delta / temperature):
                current = neighbor
                current_fitness = neighbor_fitness

            # Aktualizuj najlepsze
            if current_fitness < best_fitness:
                best = current[:]
                best_fitness = current_fitness

            self.best_fitness.append(best_fitness)
            self.avg_fitness.append(current_fitness)

            if (gen + 1) % 20 == 0:
                print(f"SA Gen {gen + 1}/{self.generations} - Best: {best_fitness:.2f} (T={temperature:.2f})")

            # Schłodź
            temperature *= self.cooling_rate

        return {
            'best_individual': best,
            'best_fitness': self.best_fitness,
            'avg_fitness': self.avg_fitness,
            'algorithm': 'Simulated Annealing'
        }