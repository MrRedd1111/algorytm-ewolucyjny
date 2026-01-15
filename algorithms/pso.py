#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Particle Swarm Optimization dla optymalizacji trasy drona
"""

import numpy as np
import random
from drone_path_optimization import (
    GRID_WIDTH, GRID_HEIGHT, NUM_WAYPOINTS, POPULATION_SIZE, GENERATIONS,
    calculate_path_length, is_line_intersecting_obstacle,
    repair_individual, repair_waypoint, wind_effect, OBSTACLES
)


class ParticleSwarmOptimization:
    """PSO dla optymalizacji trasy drona"""

    def __init__(self, population_size=POPULATION_SIZE,
                 generations=GENERATIONS,
                 w=0.7, c1=1.5, c2=1.5):
        self.population_size = population_size
        self.generations = generations
        self.w = w  # Inertia weight
        self.c1 = c1  # Cognitive parameter
        self.c2 = c2  # Social parameter
        self.best_fitness = []
        self.avg_fitness = []

    def _create_particle(self):
        """Tworzy cząstkę (pozycję)"""
        particle = [[0, 0]]
        for _ in range(NUM_WAYPOINTS - 2):
            particle.append([random.uniform(0, GRID_WIDTH),
                             random.uniform(0, GRID_HEIGHT)])
        particle.append([GRID_WIDTH, GRID_HEIGHT])
        return repair_individual(particle)

    def _evaluate_fitness(self, particle):
        """Ewaluuje fitness cząstki"""
        path_length = calculate_path_length(particle)

        obstacle_penalty = 0.0
        for i in range(len(particle) - 1):
            if is_line_intersecting_obstacle(particle[i], particle[i + 1]):
                obstacle_penalty += 100.0

        wind_penalty = 0.0
        for point in particle:
            affected = wind_effect(point, 5.0, 45)
            drift = np.sqrt((affected[0] - point[0]) ** 2 + (affected[1] - point[1]) ** 2)
            wind_penalty += drift * 0.5

        return path_length + obstacle_penalty + wind_penalty

    def _update_velocity(self, particle, velocity, best_particle, best_global):
        """Aktualizuje prędkość cząstki"""
        new_velocity = []
        for i in range(len(particle)):
            if i == 0 or i == len(particle) - 1:
                new_velocity.append([0, 0])
                continue

            r1, r2 = random.random(), random.random()
            vx = (self.w * velocity[i][0] +
                  self.c1 * r1 * (best_particle[i][0] - particle[i][0]) +
                  self.c2 * r2 * (best_global[i][0] - particle[i][0]))
            vy = (self.w * velocity[i][1] +
                  self.c1 * r1 * (best_particle[i][1] - particle[i][1]) +
                  self.c2 * r2 * (best_global[i][1] - particle[i][1]))

            new_velocity.append([vx, vy])

        return new_velocity

    def _update_position(self, particle, velocity):
        """Aktualizuje pozycję cząstki"""
        new_particle = [[0, 0]]
        for i in range(1, len(particle) - 1):
            x = np.clip(particle[i][0] + velocity[i][0], 0, GRID_WIDTH)
            y = np.clip(particle[i][1] + velocity[i][1], 0, GRID_HEIGHT)
            new_particle.append([x, y])
        new_particle.append([GRID_WIDTH, GRID_HEIGHT])
        return repair_individual(new_particle)

    def run(self):
        """Uruchamia algorytm PSO"""
        # Inicjalizuj cząstki i prędkości
        particles = [self._create_particle() for _ in range(self.population_size)]
        velocities = [[[random.uniform(-1, 1), random.uniform(-1, 1)]
                       for _ in range(NUM_WAYPOINTS)]
                      for _ in range(self.population_size)]

        # Najlepsze pozycje cząstek
        best_particles = [p[:] for p in particles]
        best_fitnesses = [self._evaluate_fitness(p) for p in particles]

        # Globalne najlepsze
        best_idx = np.argmin(best_fitnesses)
        best_global = best_particles[best_idx][:]
        best_global_fitness = best_fitnesses[best_idx]

        # Główna pętla
        for gen in range(self.generations):
            fitnesses = [self._evaluate_fitness(p) for p in particles]

            self.best_fitness.append(best_global_fitness)
            self.avg_fitness.append(np.mean(fitnesses))

            if (gen + 1) % 20 == 0:
                print(f"PSO Gen {gen + 1}/{self.generations} - Best: {best_global_fitness:.2f}")

            # Aktualizuj najlepsze pozycje
            for i in range(self.population_size):
                if fitnesses[i] < best_fitnesses[i]:
                    best_particles[i] = particles[i][:]
                    best_fitnesses[i] = fitnesses[i]

                if fitnesses[i] < best_global_fitness:
                    best_global = particles[i][:]
                    best_global_fitness = fitnesses[i]

            # Aktualizuj prędkości i pozycje
            for i in range(self.population_size):
                velocities[i] = self._update_velocity(particles[i], velocities[i],
                                                      best_particles[i], best_global)
                particles[i] = self._update_position(particles[i], velocities[i])

        return {
            'best_individual': best_global,
            'best_fitness': self.best_fitness,
            'avg_fitness': self.avg_fitness,
            'algorithm': 'Particle Swarm Optimization'
        }