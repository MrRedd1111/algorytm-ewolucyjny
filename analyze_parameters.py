#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analiza parametrów algorytmu genetycznego
"""

import numpy as np
import matplotlib.pyplot as plt
from algorithms.genetic_algorithm import GeneticAlgorithm


def analyze_mutation_rate():
    """Analizuje wpływ współczynnika mutacji"""
    print("\nAnaliza współczynnika mutacji...")
    mutation_rates = [0.05, 0.1, 0.15, 0.2, 0.25]
    results = {}

    for mr in mutation_rates:
        print(f"  Testowanie mutation_rate={mr}...", end='', flush=True)
        ga = GeneticAlgorithm(population_size=50, generations=50,
                              mutation_rate=mr)
        result = ga.run()
        results[mr] = result['best_fitness'][-1]
        print(f" ✓ (Fitness: {results[mr]:.2f})")

    return mutation_rates, list(results.values())


def analyze_crossover_prob():
    """Analizuje wpływ prawdopodobieństwa krzyżowania"""
    print("\nAnaliza prawdopodobieństwa krzyżowania...")
    crossover_probs = [0.7, 0.8, 0.9, 0.95, 1.0]
    results = {}

    for cp in crossover_probs:
        print(f"  Testowanie crossover_prob={cp}...", end='', flush=True)
        ga = GeneticAlgorithm(population_size=50, generations=50,
                              crossover_prob=cp)
        result = ga.run()
        results[cp] = result['best_fitness'][-1]
        print(f" ✓ (Fitness: {results[cp]:.2f})")

    return crossover_probs, list(results.values())


def analyze_population_size():
    """Analizuje wpływ rozmiaru populacji"""
    print("\nAnaliza rozmiaru populacji...")
    pop_sizes = [25, 50, 75, 100, 150]
    results = {}

    for ps in pop_sizes:
        print(f"  Testowanie population_size={ps}...", end='', flush=True)
        ga = GeneticAlgorithm(population_size=ps, generations=50)
        result = ga.run()
        results[ps] = result['best_fitness'][-1]
        print(f" ✓ (Fitness: {results[ps]:.2f})")

    return pop_sizes, list(results.values())


def visualize_analysis():
    """Wizualizuje wyniki analizy"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    # Analiza mutacji
    mr, mr_results = analyze_mutation_rate()
    axes[0].plot(mr, mr_results, 'o-', linewidth=2, markersize=8, color='#FF6B6B')
    axes[0].set_xlabel('Współczynnik Mutacji')
    axes[0].set_ylabel('Fitness')
    axes[0].set_title('Wpływ Współczynnika Mutacji')
    axes[0].grid(True, alpha=0.3)

    # Analiza krzyżowania
    cp, cp_results = analyze_crossover_prob()
    axes[1].plot(cp, cp_results, 'o-', linewidth=2, markersize=8, color='#4ECDC4')
    axes[1].set_xlabel('Prawdopodobieństwo Krzyżowania')
    axes[1].set_ylabel('Fitness')
    axes[1].set_title('Wpływ Prawdopodobieństwa Krzyżowania')
    axes[1].grid(True, alpha=0.3)

    # Analiza populacji
    ps, ps_results = analyze_population_size()
    axes[2].plot(ps, ps_results, 'o-', linewidth=2, markersize=8, color='#45B7D1')
    axes[2].set_xlabel('Rozmiar Populacji')
    axes[2].set_ylabel('Fitness')
    axes[2].set_title('Wpływ Rozmiaru Populacji')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def main():
    """Główna funkcja"""
    print("=" * 70)
    print("ANALIZA PARAMETRÓW ALGORYTMU GENETYCZNEGO")
    print("=" * 70)

    fig = visualize_analysis()
    fig.savefig('parameter_analysis.png', dpi=150, bbox_inches='tight')
    print("\n✓ Wykres: parameter_analysis.png")
    plt.show()


if __name__ == "__main__":
    main()