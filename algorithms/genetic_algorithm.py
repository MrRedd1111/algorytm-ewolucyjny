#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementacja Algorytmu Genetycznego
Część systemu optymalizacji trasy drona
"""

import numpy as np
import random
from deap import base, creator, tools
from drone_path_optimization import (
    GRID_WIDTH, GRID_HEIGHT, NUM_WAYPOINTS, POPULATION_SIZE, GENERATIONS,
    MUTATION_RATE, CROSSOVER_PROB, ELITE_SIZE, BLX_ALPHA,
    calculate_path_length, is_line_intersecting_obstacle,
    repair_individual, repair_waypoint, wind_effect, OBSTACLES
)


class GeneticAlgorithm:
    """Algorytm Genetyczny dla optymalizacji trasy drona"""

    def __init__(self, population_size=POPULATION_SIZE,
                 generations=GENERATIONS,
                 mutation_rate=MUTATION_RATE,
                 crossover_prob=CROSSOVER_PROB):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_prob = crossover_prob
        self.best_fitness = []
        self.avg_fitness = []
        self.toolbox = None

    def setup_deap(self):
        """Konfiguruje framework DEAP"""
        if hasattr(creator, "FitnessMin"):
            del creator.FitnessMin
        if hasattr(creator, "Individual"):
            del creator.Individual

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)

        self.toolbox = base.Toolbox()

        self.toolbox.register("individual", tools.initIterate, creator.Individual,
                              lambda: self._create_individual())
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self._evaluate_fitness)
        self.toolbox.register("mate", self._crossover_blx)
        self.toolbox.register("mutate", self._mutate)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def _create_individual(self):
        """Tworzy osobnika"""
        individual = [[0, 0]]
        for _ in range(NUM_WAYPOINTS - 2):
            individual.append([random.uniform(0, GRID_WIDTH),
                               random.uniform(0, GRID_HEIGHT)])
        individual.append([GRID_WIDTH, GRID_HEIGHT])
        return repair_individual(individual)

    def _evaluate_fitness(self, individual):
        """Ewaluuje fitness osobnika"""
        path_length = calculate_path_length(individual)

        obstacle_penalty = 0.0
        for i in range(len(individual) - 1):
            if is_line_intersecting_obstacle(individual[i], individual[i + 1]):
                obstacle_penalty += 100.0

        wind_penalty = 0.0
        for point in individual:
            affected = wind_effect(point, 5.0, 45)
            drift = np.sqrt((affected[0] - point[0]) ** 2 + (affected[1] - point[1]) ** 2)
            wind_penalty += drift * 0.5

        return (path_length + obstacle_penalty + wind_penalty,)

    def _crossover_blx(self, ind1, ind2):
        """Krzyżowanie BLX-α"""
        if random.random() < self.crossover_prob:
            for i in range(1, len(ind1) - 1):
                x1, y1 = ind1[i]
                x2, y2 = ind2[i]

                d = abs(x2 - x1)
                x_min = max(0, min(x1, x2) - BLX_ALPHA * d)
                x_max = min(GRID_WIDTH, max(x1, x2) + BLX_ALPHA * d)

                d = abs(y2 - y1)
                y_min = max(0, min(y1, y2) - BLX_ALPHA * d)
                y_max = min(GRID_HEIGHT, max(y1, y2) + BLX_ALPHA * d)

                ind1[i] = [random.uniform(x_min, x_max), random.uniform(y_min, y_max)]
                ind2[i] = [random.uniform(x_min, x_max), random.uniform(y_min, y_max)]

        return ind1, ind2

    def _mutate(self, individual):
        """Mutacja osobnika"""
        if random.random() < self.mutation_rate:
            for i in range(1, len(individual) - 1):
                if random.random() < 0.2:
                    mutation_type = random.choice(['gaussian', 'uniform', 'repair'])

                    if mutation_type == 'gaussian':
                        individual[i][0] += random.gauss(0, GRID_WIDTH * 0.05)
                        individual[i][1] += random.gauss(0, GRID_HEIGHT * 0.05)
                    elif mutation_type == 'uniform':
                        individual[i][0] = random.uniform(0, GRID_WIDTH)
                        individual[i][1] = random.uniform(0, GRID_HEIGHT)
                    else:
                        individual[i] = repair_waypoint(individual[i])

                    individual[i][0] = np.clip(individual[i][0], 0, GRID_WIDTH)
                    individual[i][1] = np.clip(individual[i][1], 0, GRID_HEIGHT)

            individual = repair_individual(individual)

        return (individual,)

    def run(self):
        """Uruchamia algorytm"""
        self.setup_deap()
        pop = self.toolbox.population(n=self.population_size)

        for gen in range(self.generations):
            fitnesses = list(map(self.toolbox.evaluate, pop))
            for ind, fit in zip(pop, fitnesses):
                ind.fitness.values = fit

            fits = [ind.fitness.values[0] for ind in pop]
            self.best_fitness.append(min(fits))
            self.avg_fitness.append(np.mean(fits))

            if (gen + 1) % 20 == 0:
                print(f"GA Gen {gen + 1}/{self.generations} - Best: {min(fits):.2f}")

            offspring = self.toolbox.select(pop, len(pop))
            offspring = [self.toolbox.clone(ind) for ind in offspring]

            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                self.toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

            for mutant in offspring:
                self.toolbox.mutate(mutant)
                del mutant.fitness.values

            pop.sort(key=lambda x: x.fitness.values[0])
            offspring = pop[:ELITE_SIZE] + offspring[ELITE_SIZE:]
            pop = offspring

        fitnesses = list(map(self.toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        best_ind = min(pop, key=lambda x: x.fitness.values[0])

        return {
            'best_individual': best_ind,
            'best_fitness': self.best_fitness,
            'avg_fitness': self.avg_fitness,
            'algorithm': 'Genetic Algorithm'
        }