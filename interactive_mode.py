#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tryb interaktywny - ustal parametry i uruchom algorytm
"""

import numpy as np
import matplotlib.pyplot as plt
from algorithms.genetic_algorithm import GeneticAlgorithm
from drone_path_optimization import (
    visualize_results as original_visualize, save_results,
    calculate_path_length, OBSTACLES, GRID_WIDTH, GRID_HEIGHT
)


def input_integer(prompt, default=None):
    """Wczytaj liczbę całkowitą"""
    while True:
        try:
            val = input(prompt)
            if val == '' and default is not None:
                return default
            return int(val)
        except ValueError:
            print("❌ Wpisz liczbę całkowitą!")


def input_float(prompt, default=None):
    """Wczytaj liczbę zmiennoprzecinkową"""
    while True:
        try:
            val = input(prompt)
            if val == '' and default is not None:
                return default
            return float(val)
        except ValueError:
            print("❌ Wpisz liczbę!")


def interactive_menu():
    """Menu interaktywne"""
    print("\n" + "=" * 70)
    print("OPTYMALIZACJA TRASY DRONA - MODE INTERAKTYWNY")
    print("=" * 70)

    print("\n📊 PARAMETRY ALGORYTMU GENETYCZNEGO\n")

    # Populacja
    pop = input_integer(
        "Rozmiar populacji [100]: ",
        default=100
    )

    # Generacje
    gen = input_integer(
        "Liczba generacji [200]: ",
        default=200
    )

    # Mutacja
    mut = input_float(
        "Współczynnik mutacji [0.1]: ",
        default=0.1
    )

    # Krzyżowanie
    cross = input_float(
        "Prawdopodobieństwo krzyżowania [0.9]: ",
        default=0.9
    )

    # Wiatr
    print("\n🌬️  PARAMETRY WIATRU\n")

    wind_speed = input_float(
        "Prędkość wiatru [5.0]: ",
        default=5.0
    )

    wind_direction = input_integer(
        "Kierunek wiatru w stopniach [45]: ",
        default=45
    )

    # Potwierdzenie
    print("\n" + "=" * 70)
    print("PARAMETRY:")
    print("=" * 70)
    print(f"Populacja: {pop}")
    print(f"Generacje: {gen}")
    print(f"Mutacja: {mut}")
    print(f"Krzyżowanie: {cross}")
    print(f"Wiatr: {wind_speed} m/s, kierunek {wind_direction}°")
    print("=" * 70)

    confirm = input("\n✓ Czy parametry są OK? (y/n): ").lower()
    if confirm != 'y':
        print("❌ Anulowano.")
        return None

    return {
        'population_size': pop,
        'generations': gen,
        'mutation_rate': mut,
        'crossover_prob': cross,
        'wind_speed': wind_speed,
        'wind_direction': wind_direction
    }


def run_with_custom_params(params):
    """Uruchamia GA z niestandardowymi parametrami"""
    print("\n" + "=" * 70)
    print("🚀 URUCHAMIANIE ALGORYTMU GENETYCZNEGO")
    print("=" * 70 + "\n")

    ga = GeneticAlgorithm(
        population_size=params['population_size'],
        generations=params['generations'],
        mutation_rate=params['mutation_rate'],
        crossover_prob=params['crossover_prob']
    )

    result = ga.run()

    print("\n" + "=" * 70)
    print("✅ WYNIKI")
    print("=" * 70)

    best_ind = result['best_individual']
    print(f"Najlepszy fitness: {best_ind.fitness.values[0]:.2f}")
    print(f"Długość trasy: {calculate_path_length(best_ind):.2f}")
    print(f"Liczba waypoints: {len(best_ind)}")
    print(f"Poprawa: {(result['best_fitness'][0] - result['best_fitness'][-1]) / result['best_fitness'][0] * 100:.1f}%")

    # Wizualizuj
    print("\n📊 Generuję wykresy...")

    # Przygotuj dane do wizualizacji
    viz_result = {
        'best_individual': best_ind,
        'best_fitness': result['best_fitness'],
        'avg_fitness': result['avg_fitness'],
        'generations': params['generations']
    }

    fig = original_visualize(viz_result)
    fig.savefig('custom_result.png', dpi=150, bbox_inches='tight')
    print("✓ Wykres: custom_result.png")

    # Zapisz wyniki
    save_results(viz_result)

    plt.show()

    return result


def main():
    """Główna funkcja"""
    params = interactive_menu()

    if params:
        run_with_custom_params(params)

        print("\n" + "=" * 70)
        print("✅ ZAKOŃCZONO POMYŚLNIE!")
        print("=" * 70)
        print("\nZapisane pliki:")
        print("  - custom_result.png")
        print("  - raport_wyniki_*.txt")
        print("  - wyniki_*.pkl")


if __name__ == "__main__":
    main()
