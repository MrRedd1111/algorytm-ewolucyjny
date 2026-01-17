#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optymalizacja trasy drona przy pomocy algorytmu genetycznego.
Projekt dla WSZIB-u.

Autorzy: Marek Marszałek, Mateusz Bierowiec
Data: 2026-01-15
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle
import os
import random
from datetime import datetime
import pickle
import warnings
from deap import base, creator, tools, algorithms

warnings.filterwarnings('ignore')

# ============================================================================
# KONFIGURACJA (wbudowana)
# ============================================================================

POPULATION_SIZE = 100
GENERATIONS = 200
MUTATION_RATE = 0.1
CROSSOVER_PROB = 0.9
ELITE_SIZE = 10
GRID_WIDTH = 100
GRID_HEIGHT = 100
NUM_WAYPOINTS = 8
WIND_SPEED = 5.0
WIND_DIRECTION = 45
BLX_ALPHA = 0.1
REPAIR_RATIO = 0.3
WAYPOINT_SAFETY_DISTANCE = 2.0

# ============================================================================
# GLOBAL CONSTANTS
# ============================================================================

# Przeszkody jako lista słowników
OBSTACLES = [
    {'type': 'circle', 'center': (30, 30), 'radius': 8},
    {'type': 'circle', 'center': (70, 70), 'radius': 10},
    {'type': 'rect', 'x': 20, 'y': 60, 'width': 15, 'height': 15},
    {'type': 'rect', 'x': 60, 'y': 20, 'width': 12, 'height': 20}
]


# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def wind_effect(position, wind_speed, wind_direction):
    """Oblicza wpływ wiatru na pozycję drona."""
    wind_rad = np.radians(wind_direction)
    wind_x = wind_speed * np.cos(wind_rad)
    wind_y = wind_speed * np.sin(wind_rad)
    return np.array([position[0] + wind_x, position[1] + wind_y])


def is_point_in_circle(point, center, radius):
    """Sprawdza czy punkt jest wewnątrz koła."""
    distance = np.sqrt((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2)
    return distance < radius


def is_point_in_rect(point, x, y, width, height):
    """Sprawdza czy punkt jest wewnątrz prostokąta."""
    return (x <= point[0] <= x + width) and (y <= point[1] <= y + height)


def is_point_in_obstacle(point, obstacles=None):
    """Sprawdza czy punkt jest w jakiejś przeszkodzie."""
    if obstacles is None:
        obstacles = OBSTACLES

    for obs in obstacles:
        if obs['type'] == 'circle':
            if is_point_in_circle(point, obs['center'], obs['radius']):
                return True
        elif obs['type'] == 'rect':
            if is_point_in_rect(point, obs['x'], obs['y'], obs['width'], obs['height']):
                return True
    return False


def is_line_intersecting_obstacle(p1, p2, obstacles=None):
    """Sprawdza czy linia między p1 a p2 przecina przeszkodę."""
    if obstacles is None:
        obstacles = OBSTACLES

    num_checks = 20
    for i in range(1, num_checks):
        t = i / num_checks
        point = np.array([
            p1[0] + t * (p2[0] - p1[0]),
            p1[1] + t * (p2[1] - p1[1])
        ])
        if is_point_in_obstacle(point, obstacles):
            return True
    return False


def calculate_path_length(waypoints):
    """Oblicza całkowitą długość trasy."""
    length = 0.0
    for i in range(len(waypoints) - 1):
        dx = waypoints[i + 1][0] - waypoints[i][0]
        dy = waypoints[i + 1][1] - waypoints[i][1]
        length += np.sqrt(dx ** 2 + dy ** 2)
    return length


def check_path_validity(path, obstacles=None):
    """Sprawdza czy cała ścieżka jest prawidłowa."""
    if obstacles is None:
        obstacles = OBSTACLES

    # Sprawdź punkty drogi
    for point in path:
        if is_point_in_obstacle(point, obstacles):
            return False

    # Sprawdź linie między punktami
    for i in range(len(path) - 1):
        if is_line_intersecting_obstacle(path[i], path[i + 1], obstacles):
            return False

    return True


def repair_waypoint(waypoint, obstacles=None, grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT):
    """Naprawia pojedynczy waypoint, jeśli jest w przeszkodzie."""
    if obstacles is None:
        obstacles = OBSTACLES

    x, y = waypoint

    # Ogranicz do granic siatki
    x = np.clip(x, 0, grid_width)
    y = np.clip(y, 0, grid_height)

    # Jeśli punkt jest w przeszkodzie, przesuń go
    if is_point_in_obstacle((x, y), obstacles):
        # Spróbuj znaleźć najbliższy bezpieczny punkt
        for angle in np.linspace(0, 2 * np.pi, 16):
            for distance in np.linspace(WAYPOINT_SAFETY_DISTANCE, 20, 10):
                new_x = x + distance * np.cos(angle)
                new_y = y + distance * np.sin(angle)

                # Sprawdź granice
                if 0 <= new_x <= grid_width and 0 <= new_y <= grid_height:
                    # Sprawdź przeszkody
                    if not is_point_in_obstacle((new_x, new_y), obstacles):
                        return [new_x, new_y]

        # Jeśli nie znaleziono bezpiecznego punktu, wróć do punktu startowego
        return [WAYPOINT_SAFETY_DISTANCE, WAYPOINT_SAFETY_DISTANCE]

    return [x, y]


def repair_individual(individual, grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT):
    """Naprawia całego osobnika (reparacja konwencjonalna)."""
    repaired = []

    # Pierwszy punkt = start
    start = [0, 0]
    repaired.append(start)

    # Napraw punkty pośrednie
    for i in range(1, len(individual) - 1):
        x = np.clip(individual[i][0], 0, grid_width)
        y = np.clip(individual[i][1], 0, grid_height)
        waypoint = repair_waypoint([x, y], grid_width=grid_width, grid_height=grid_height)
        repaired.append(waypoint)

    # Ostatni punkt = meta
    end = [grid_width, grid_height]
    repaired.append(end)

    return repaired


def create_individual(num_waypoints=NUM_WAYPOINTS, grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT):
    """Tworzy losowego osobnika."""
    individual = []

    # Punkt startowy
    individual.append([0, 0])

    # Losowe punkty pośrednie
    for _ in range(num_waypoints - 2):
        x = random.uniform(0, grid_width)
        y = random.uniform(0, grid_height)
        individual.append([x, y])

    # Punkt docelowy
    individual.append([grid_width, grid_height])

    # Napraw osobnika
    individual = repair_individual(individual, grid_width, grid_height)

    return individual


def evaluate_fitness(individual, obstacles=None, wind_speed=WIND_SPEED,
                     wind_direction=WIND_DIRECTION):
    """Ewaluuje funkcję dostosowania osobnika."""
    if obstacles is None:
        obstacles = OBSTACLES

    path_length = calculate_path_length(individual)

    # Kara za przeszkody
    obstacle_penalty = 0.0
    for i in range(len(individual) - 1):
        if is_line_intersecting_obstacle(individual[i], individual[i + 1], obstacles):
            obstacle_penalty += 100.0

    # Kara za wpływ wiatru (dryf)
    wind_penalty = 0.0
    for point in individual:
        affected = wind_effect(point, wind_speed, wind_direction)
        drift = np.sqrt((affected[0] - point[0]) ** 2 + (affected[1] - point[1]) ** 2)
        wind_penalty += drift * 0.5

    # Fitness = suma kar + długość ścieżki
    fitness = path_length + obstacle_penalty + wind_penalty

    return (fitness,)


def setup_deap():
    """Konfiguruje framework DEAP."""
    # Wyczyść istniejące klasy jeśli istnieją
    if hasattr(creator, "FitnessMin"):
        del creator.FitnessMin
    if hasattr(creator, "Individual"):
        del creator.Individual

    # Utwórz nowe klasy
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    # Stwórz toolbox
    toolbox = base.Toolbox()

    # Rejestruj operatory genetyczne
    toolbox.register("individual", tools.initIterate, creator.Individual,
                     lambda: create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate_fitness)
    toolbox.register("mate", crossover_blx)
    toolbox.register("mutate", mutate_individual)
    toolbox.register("select", tools.selTournament, tournsize=3)

    return toolbox


def crossover_blx(ind1, ind2, alpha=BLX_ALPHA):
    """Krzyżowanie BLX-α dla waypoints."""
    if random.random() < CROSSOVER_PROB:
        # Krzyż punkty pośrednie (nie start i koniec)
        for i in range(1, len(ind1) - 1):
            x1, y1 = ind1[i]
            x2, y2 = ind2[i]

            # BLX-α dla współrzędnej x
            d = abs(x2 - x1)
            x_min = min(x1, x2) - alpha * d
            x_max = max(x1, x2) + alpha * d
            x_min = max(0, x_min)
            x_max = min(GRID_WIDTH, x_max)
            new_x = random.uniform(x_min, x_max)

            # BLX-α dla współrzędnej y
            d = abs(y2 - y1)
            y_min = min(y1, y2) - alpha * d
            y_max = max(y1, y2) + alpha * d
            y_min = max(0, y_min)
            y_max = min(GRID_HEIGHT, y_max)
            new_y = random.uniform(y_min, y_max)

            ind1[i] = [new_x, new_y]
            ind2[i] = [random.uniform(x_min, x_max), random.uniform(y_min, y_max)]

    return ind1, ind2


def mutate_individual(individual, indpb=0.2):
    """Mutacja osobnika."""
    if random.random() < MUTATION_RATE:
        # Mutuj losowe punkty pośrednie
        for i in range(1, len(individual) - 1):
            if random.random() < indpb:
                # Wybierz typ mutacji
                mutation_type = random.choice(['gaussian', 'uniform', 'repair'])

                if mutation_type == 'gaussian':
                    # Mutacja gaussowska
                    individual[i][0] += random.gauss(0, GRID_WIDTH * 0.05)
                    individual[i][1] += random.gauss(0, GRID_HEIGHT * 0.05)

                elif mutation_type == 'uniform':
                    # Mutacja uniformna
                    individual[i][0] = random.uniform(0, GRID_WIDTH)
                    individual[i][1] = random.uniform(0, GRID_HEIGHT)

                elif mutation_type == 'repair':
                    # Mutacja + naprawa
                    individual[i][0] += random.gauss(0, GRID_WIDTH * 0.03)
                    individual[i][1] += random.gauss(0, GRID_HEIGHT * 0.03)
                    individual[i] = repair_waypoint(individual[i])

                # Ogranicz do granic
                individual[i][0] = np.clip(individual[i][0], 0, GRID_WIDTH)
                individual[i][1] = np.clip(individual[i][1], 0, GRID_HEIGHT)

        # Napraw przeszkody
        individual = repair_individual(individual, GRID_WIDTH, GRID_HEIGHT)

    return (individual,)


def run_algorithm():
    """Główna funkcja algorytmu genetycznego."""
    print("=" * 70)
    print("Optymalizacja Trasy Drona - Algorytm Genetyczny")
    print("=" * 70)
    print(f"Populacja: {POPULATION_SIZE}")
    print(f"Generacje: {GENERATIONS}")
    print(f"Współczynnik mutacji: {MUTATION_RATE}")
    print(f"Prawdopodobieństwo krzyżowania: {CROSSOVER_PROB}")
    print(f"Liczba waypoints: {NUM_WAYPOINTS}")
    print(f"Wiatr: kierunek {WIND_DIRECTION}°, prędkość {WIND_SPEED}")
    print("=" * 70)

    # Konfiguruj DEAP
    toolbox = setup_deap()

    # Utwórz populację
    pop = toolbox.population(n=POPULATION_SIZE)

    # Listy do śledzenia najlepszego fitness
    best_fitness = []
    avg_fitness = []

    # Główna pętla algorytmu
    for gen in range(GENERATIONS):
        # Ewaluuj populację
        fitnesses = list(map(toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        # Zapamiętaj statystyki
        fits = [ind.fitness.values[0] for ind in pop]
        best_fitness.append(min(fits))
        avg_fitness.append(np.mean(fits))

        if (gen + 1) % 20 == 0:
            print(f"Generacja {gen + 1}/{GENERATIONS} - Najlepsze: {min(fits):.2f}, Średnie: {np.mean(fits):.2f}")

        # Selekcja
        offspring = toolbox.select(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        # Krzyżowanie
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            toolbox.mate(child1, child2)
            del child1.fitness.values
            del child2.fitness.values

        # Mutacja
        for mutant in offspring:
            toolbox.mutate(mutant)
            del mutant.fitness.values

        # Elityzm
        pop.sort(key=lambda x: x.fitness.values[0])
        offspring = pop[:ELITE_SIZE] + offspring[ELITE_SIZE:]
        pop = offspring

    # Ostateczna ewaluacja
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # Znajdź najlepszego osobnika
    best_ind = min(pop, key=lambda x: x.fitness.values[0])

    print("\n" + "=" * 70)
    print("WYNIKI")
    print("=" * 70)
    print(f"Najlepszy fitness: {best_ind.fitness.values[0]:.2f}")
    print(f"Długość trasy: {calculate_path_length(best_ind):.2f}")
    print(f"Liczba waypoints: {len(best_ind)}")
    print("=" * 70)

    return {
        'best_individual': best_ind,
        'population': pop,
        'best_fitness': best_fitness,
        'avg_fitness': avg_fitness,
        'generations': GENERATIONS
    }


def visualize_results(results):
    """Wizualizuje wyniki algorytmu."""
    best_ind = results['best_individual']
    best_fitness = results['best_fitness']
    avg_fitness = results['avg_fitness']

    # Twórz figurę z dwoma subplot'ami
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # === Subplot 1: Zbieżność ===
    generations = range(1, len(best_fitness) + 1)
    ax1.plot(generations, best_fitness, 'b-', label='Najlepszy fitness', linewidth=2)
    ax1.plot(generations, avg_fitness, 'r--', label='Średni fitness', linewidth=2)
    ax1.set_xlabel('Generacja')
    ax1.set_ylabel('Fitness')
    ax1.set_title('Zbieżność Algorytmu Genetycznego')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # === Subplot 2: Trasa drona ===
    # Rysuj siatkę
    ax2.set_xlim(-5, GRID_WIDTH + 5)
    ax2.set_ylim(-5, GRID_HEIGHT + 5)
    ax2.set_aspect('equal')
    ax2.grid(True, alpha=0.2)

    # Rysuj przeszkody
    for obs in OBSTACLES:
        if obs['type'] == 'circle':
            circle = Circle(obs['center'], obs['radius'],
                            fill=True, alpha=0.3, color='red',
                            edgecolor='darkred', linewidth=2)
            ax2.add_patch(circle)
        elif obs['type'] == 'rect':
            rect = Rectangle((obs['x'], obs['y']), obs['width'], obs['height'],
                             fill=True, alpha=0.3, color='red',
                             edgecolor='darkred', linewidth=2)
            ax2.add_patch(rect)

    # Rysuj trasę
    waypoints = np.array(best_ind)
    ax2.plot(waypoints[:, 0], waypoints[:, 1], 'b-', linewidth=2, label='Trasa')
    ax2.plot(waypoints[:, 0], waypoints[:, 1], 'bo', markersize=6)

    # Zaznacz start i koniec
    ax2.plot(0, 0, 'g*', markersize=20, label='Start')
    ax2.plot(GRID_WIDTH, GRID_HEIGHT, 'r*', markersize=20, label='Meta')

    ax2.set_xlabel('X [jednostki]')
    ax2.set_ylabel('Y [jednostki]')
    ax2.set_title('Optymalna Trasa Drona')
    ax2.legend(loc='upper left')

    plt.tight_layout()
    return fig


def save_results(results):
    """Zapisuje wyniki do pliku."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Zapisz raport tekstowy
    report_file = f"raport_wyniki_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("RAPORT OPTYMALIZACJI TRASY DRONA\n")
        f.write("=" * 70 + "\n\n")

        best_ind = results['best_individual']
        f.write(f"Najlepszy fitness: {best_ind.fitness.values[0]:.2f}\n")
        f.write(f"Długość trasy: {calculate_path_length(best_ind):.2f}\n")
        f.write(f"Liczba waypoints: {len(best_ind)}\n")
        f.write(f"Generacje: {results['generations']}\n\n")

        f.write("Waypoints trasy:\n")
        for i, wp in enumerate(best_ind):
            f.write(f"  {i}: ({wp[0]:.2f}, {wp[1]:.2f})\n")

    # Zapisz dane surowe
    pkl_file = f"wyniki_{timestamp}.pkl"
    with open(pkl_file, 'wb') as f:
        pickle.dump(results, f)

    print(f"\n✓ Raport: {report_file}")
    print(f"✓ Dane: {pkl_file}")


def main():
    """Główna funkcja programu."""
    try:
        # Uruchom algorytm
        results = run_algorithm()

        # Wizualizuj wyniki
        fig = visualize_results(results)
        fig.savefig('zbieznosc_i_trasa.png', dpi=150, bbox_inches='tight')
        print("✓ Wykres: zbieznosc_i_trasa.png")
        plt.show()

        # Zapisz wyniki
        save_results(results)

        print("\n✓ Algorytm zakończonył pracę pomyślnie!")

    except Exception as e:
        print(f"\n✗ Błąd: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
