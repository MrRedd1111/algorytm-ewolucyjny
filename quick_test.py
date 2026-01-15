#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Szybki test algorytmu - dla weryfikacji instalacji
Wersja uproszczona do testowania bez wizualizacji
"""

import sys
import numpy as np
from drone_path_optimization import (
    run_algorithm, calculate_path_length,
    visualize_results, save_results, OBSTACLES,
    GRID_WIDTH, GRID_HEIGHT,
    POPULATION_SIZE, GENERATIONS
)


def quick_test():
    """Uruchamia szybki test z mniejszymi parametrami"""

    print("╔════════════════════════════════════════════════════════════╗")
    print("║         SZYBKI TEST - ALGORYTM GENETYCZNY                  ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    print("Parametry testu:")
    print("  - Populacja: 50 osobników")
    print("  - Generacje: 50")
    print("  - Waypoints: 8")
    print(f"  - Przeszkody: {len(OBSTACLES)}")
    print(f"  - Siatka: {GRID_WIDTH}x{GRID_HEIGHT}\n")

    print("Uruchamianie...", end='', flush=True)

    # Import lokalny do zmiany parametrów na czas testu
    import drone_path_optimization as dpo

    # Zmniejszenie parametrów na czas testu
    old_pop = dpo.POPULATION_SIZE
    old_gen = dpo.GENERATIONS

    # Zmiana w module
    dpo.POPULATION_SIZE = 50
    dpo.GENERATIONS = 50

    try:
        # Uruchom algorytm
        results = run_algorithm()

        print(" ✓\n")

        # Wyniki
        print("\n" + "=" * 60)
        print("WYNIKI TESTU")
        print("=" * 60)

        best_ind = results['best_individual']
        best_fitness = results['best_fitness']

        best = min(best_fitness)
        worst = max(best_fitness)
        avg = np.mean(best_fitness)

        print(f"\nNajlepszy fitness:     {best:.2f}")
        print(f"Najgorszy fitness:     {worst:.2f}")
        print(f"Średni fitness:        {avg:.2f}")
        print(f"Odchylenie std:        {np.std(best_fitness):.4f}")

        # Długość trasy
        path_length = calculate_path_length(best_ind)
        print(f"\nDługość najlepszej trasy: {path_length:.2f}")
        print(f"Liczba waypoints: {len(best_ind)}")

        # Zbieżność
        print(f"\nZbieżność:")
        print(f"  Fitness początkowy:  {best_fitness[0]:.2f}")
        print(f"  Fitness końcowy:     {best_fitness[-1]:.2f}")
        improvement = (best_fitness[0] - best_fitness[-1]) / best_fitness[0] * 100
        print(f"  Poprawa:             {improvement:.1f}%")

        # Waypointy
        print(f"\nWaypoints najlepszej trasy:")
        for i, wp in enumerate(best_ind[:5]):  # Pokaż pierwszych 5
            print(f"  {i}: ({wp[0]:.2f}, {wp[1]:.2f})")
        if len(best_ind) > 5:
            print(f"  ... ({len(best_ind) - 5} więcej)")

        print("\n" + "=" * 60)
        print("✓ TEST PRZEBIEGŁ POMYŚLNIE!")
        print("=" * 60)
        print("\nTeraz możesz uruchomić pełny algorytm:")
        print("  python drone_path_optimization.py")

        return True

    except Exception as e:
        print(f" ✗\n\nBŁĄD: {e}\n")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Przywrócenie parametrów
        dpo.POPULATION_SIZE = old_pop
        dpo.GENERATIONS = old_gen


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)