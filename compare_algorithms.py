#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Porównanie trzech algorytmów optymalizacji trasy drona
"""

import time
import numpy as np
import sys
import os

# Dodaj folder algorithms do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'algorithms'))

from drone_path_optimization import (
    GRID_WIDTH, GRID_HEIGHT, NUM_WAYPOINTS,
    create_individual, evaluate_fitness, repair_individual,
    calculate_path_length, OBSTACLES
)


def run_genetic_algorithm_simple(generations=100, population_size=50):
    """Prosty algorytm genetyczny"""
    print("  Inicjalizacja populacji...", end="", flush=True)

    # Inicjata populacji
    population = [create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)
                  for _ in range(population_size)]
    fitness_vals = []

    # Ocena fitness
    for ind in population:
        ind_repaired = repair_individual(ind)
        fitness_vals.append(evaluate_fitness(ind_repaired)[0])

    best_fitness = min(fitness_vals)
    print(f" OK")

    # Ewolucja
    for gen in range(generations):
        # Selekcja i reprodukcja
        sorted_indices = sorted(range(len(fitness_vals)), key=lambda x: fitness_vals[x])
        elite_indices = sorted_indices[:5]
        elite = [population[i] for i in elite_indices]

        # Krzyżowanie i mutacja
        new_pop = [population[i] for i in elite_indices]
        new_fitness = [fitness_vals[i] for i in elite_indices]

        while len(new_pop) < population_size:
            parent1 = elite[np.random.randint(0, len(elite))]
            parent2 = elite[np.random.randint(0, len(elite))]

            # Krzyżowanie
            child = [
                [(parent1[i][j] + parent2[i][j]) / 2 + np.random.normal(0, 0.5)
                 for j in range(2)]
                for i in range(NUM_WAYPOINTS)
            ]

            child_rep = repair_individual(child)
            child_fitness = evaluate_fitness(child_rep)[0]
            new_pop.append(child_rep)
            new_fitness.append(child_fitness)

        population = new_pop[:population_size]
        fitness_vals = new_fitness[:population_size]

        current_best = min(fitness_vals)
        if current_best < best_fitness:
            best_fitness = current_best

        if (gen + 1) % 20 == 0:
            print(f"    Gen {gen + 1}/{generations} - Best: {best_fitness:.2f}")

    best_idx = fitness_vals.index(min(fitness_vals))
    best_individual = population[best_idx]
    return best_fitness, best_individual


def run_pso_simple(generations=100, population_size=50):
    """Prosty algorytm PSO"""
    print("  Inicjalizacja cząstek...", end="", flush=True)

    # Inicjata cząstek
    particles = [create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)
                 for _ in range(population_size)]
    velocities = [[np.random.uniform(-1, 1, 2) for _ in range(NUM_WAYPOINTS)]
                  for _ in range(population_size)]

    # Ocena fitness
    fitness_vals = []
    best_positions = []
    best_fitnesses = []

    for i, particle in enumerate(particles):
        particle_rep = repair_individual(particle)
        fitness = evaluate_fitness(particle_rep)[0]
        fitness_vals.append(fitness)
        best_positions.append([row[:] for row in particle])
        best_fitnesses.append(fitness)

    global_best_idx = fitness_vals.index(min(fitness_vals))
    global_best = [row[:] for row in particles[global_best_idx]]
    best_fitness = fitness_vals[global_best_idx]
    print(f" OK")

    # Iteracje
    w = 0.7
    c1, c2 = 1.5, 1.5

    for gen in range(generations):
        for i, particle in enumerate(particles):
            # Update velocity
            for j in range(NUM_WAYPOINTS):
                for k in range(2):
                    r1, r2 = np.random.random(), np.random.random()
                    velocities[i][j][k] = (
                            w * velocities[i][j][k] +
                            c1 * r1 * (best_positions[i][j][k] - particle[j][k]) +
                            c2 * r2 * (global_best[j][k] - particle[j][k])
                    )

            # Update position
            for j in range(NUM_WAYPOINTS):
                for k in range(2):
                    particle[j][k] += velocities[i][j][k]

            # Evaluation
            particle_rep = repair_individual(particle)
            fitness = evaluate_fitness(particle_rep)[0]
            fitness_vals[i] = fitness

            if fitness < best_fitnesses[i]:
                best_positions[i] = [row[:] for row in particle]
                best_fitnesses[i] = fitness

                if fitness < best_fitness:
                    best_fitness = fitness
                    global_best = [row[:] for row in particle]

        if (gen + 1) % 20 == 0:
            print(f"    Gen {gen + 1}/{generations} - Best: {best_fitness:.2f}")

    return best_fitness, global_best


def run_sa_simple(iterations=5000):
    """Prosty Simulated Annealing"""
    print("  Inicjalizacja rozwiązania...", end="", flush=True)

    current = create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)
    current_rep = repair_individual(current)
    current_fitness = evaluate_fitness(current_rep)[0]

    best = [row[:] for row in current]
    best_fitness = current_fitness

    T = 100.0
    cooling_rate = 0.995
    print(f" OK")

    for iteration in range(iterations):
        # Generuj sąsiada
        neighbor = [row[:] for row in current]
        i = np.random.randint(0, NUM_WAYPOINTS)
        neighbor[i] = [
            neighbor[i][0] + np.random.normal(0, 2),
            neighbor[i][1] + np.random.normal(0, 2)
        ]

        neighbor_rep = repair_individual(neighbor)
        neighbor_fitness = evaluate_fitness(neighbor_rep)[0]

        # Metropolis acceptance
        delta = neighbor_fitness - current_fitness
        if delta < 0 or np.random.random() < np.exp(-delta / T):
            current = neighbor
            current_fitness = neighbor_fitness

            if current_fitness < best_fitness:
                best = [row[:] for row in current]
                best_fitness = current_fitness

        T *= cooling_rate

        if (iteration + 1) % 1000 == 0:
            print(f"    Iter {iteration + 1}/{iterations} - Best: {best_fitness:.2f}")

    return best_fitness, best


def main():
    """Główna funkcja"""
    print("\n" + "=" * 75)
    print("PORÓWNANIE ALGORYTMÓW OPTYMALIZACJI TRASY DRONA")
    print("=" * 75)
    print(f"Siatka: {GRID_WIDTH}x{GRID_HEIGHT}")
    print(f"Waypoints: {NUM_WAYPOINTS}")
    print(f"Przeszkody: {len(OBSTACLES)}\n")

    results = []

    # 1. Algorytm Genetyczny
    print("1. Algorytm Genetyczny")
    start = time.time()
    ga_fitness, ga_path = run_genetic_algorithm_simple(generations=100, population_size=50)
    ga_time = time.time() - start
    ga_length = calculate_path_length(ga_path)
    results.append(('GA', ga_fitness, ga_time, ga_length))
    print(f"   ✓ Wynik: Fitness={ga_fitness:.2f}, Czas={ga_time:.2f}s\n")

    # 2. PSO
    print("2. Particle Swarm Optimization (PSO)")
    start = time.time()
    pso_fitness, pso_path = run_pso_simple(generations=100, population_size=50)
    pso_time = time.time() - start
    pso_length = calculate_path_length(pso_path)
    results.append(('PSO', pso_fitness, pso_time, pso_length))
    print(f"   ✓ Wynik: Fitness={pso_fitness:.2f}, Czas={pso_time:.2f}s\n")

    # 3. Simulated Annealing
    print("3. Simulated Annealing (SA)")
    start = time.time()
    sa_fitness, sa_path = run_sa_simple(iterations=5000)
    sa_time = time.time() - start
    sa_length = calculate_path_length(sa_path)
    results.append(('SA', sa_fitness, sa_time, sa_length))
    print(f"   ✓ Wynik: Fitness={sa_fitness:.2f}, Czas={sa_time:.2f}s\n")

    # Tabela wyników
    print("\n" + "=" * 80)
    print("TABELA PORÓWNANIA")
    print("=" * 80)
    print(f"{'Algoritm':<15} {'Fitness':<15} {'Czas [s]':<15} {'Trasa [j]':<15}")
    print("-" * 80)

    for name, fitness, duration, length in results:
        print(f"{name:<15} {fitness:<15.2f} {duration:<15.4f} {length:<15.2f}")

    print("=" * 80)

    # Zwycięzca
    best = min(results, key=lambda x: x[1])
    print(f"\n🏆 ZWYCIĘZCA: {best[0]} (Fitness: {best[1]:.2f})")

    # Ranking
    print("\n📊 RANKING:")
    for i, (name, fitness, duration, length) in enumerate(sorted(results, key=lambda x: x[1]), 1):
        improvement = ((results[0][1] - fitness) / results[0][1] * 100) if results[0][1] > 0 else 0
        print(f"  {i}. {name:<10} - Fitness: {fitness:.2f} (Poprawa: {improvement:+.1f}%)")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
