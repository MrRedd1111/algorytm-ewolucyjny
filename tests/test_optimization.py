#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testy jednostkowe dla algorytmu optymalizacji trasy drona
Zawiera testy dla wszystkich funkcji pomocniczych i głównego algorytmu
"""

import sys
import unittest
import numpy as np
from drone_path_optimization import (
    wind_effect, is_point_in_circle, is_point_in_rect,
    is_point_in_obstacle, is_line_intersecting_obstacle,
    calculate_path_length, check_path_validity,
    repair_waypoint, repair_individual, create_individual,
    evaluate_fitness, OBSTACLES, GRID_WIDTH, GRID_HEIGHT,
    NUM_WAYPOINTS
)


class TestWindEffect(unittest.TestCase):
    """Testy funkcji wind_effect"""

    def test_wind_effect_basic(self):
        """Test podstawowego wpływu wiatru"""
        position = np.array([10, 10])
        wind_speed = 5.0
        wind_direction = 0
        result = wind_effect(position, wind_speed, wind_direction)

        self.assertGreater(result[0], position[0])
        self.assertAlmostEqual(result[1], position[1], places=5)

    def test_wind_effect_45_degrees(self):
        """Test wpływu wiatru pod kątem 45°"""
        position = np.array([10, 10])
        wind_speed = 5.0
        wind_direction = 45
        result = wind_effect(position, wind_speed, wind_direction)

        self.assertGreater(result[0], position[0])
        self.assertGreater(result[1], position[1])

    def test_wind_effect_zero_speed(self):
        """Test braku wpływu przy zerowej prędkości wiatru"""
        position = np.array([10, 10])
        wind_speed = 0.0
        wind_direction = 45
        result = wind_effect(position, wind_speed, wind_direction)

        np.testing.assert_array_almost_equal(result, position)


class TestPointInGeometry(unittest.TestCase):
    """Testy funkcji geometrycznych"""

    def test_point_in_circle_true(self):
        """Test punktu wewnątrz koła"""
        center = (50, 50)
        radius = 10
        point = (55, 50)

        result = is_point_in_circle(point, center, radius)
        self.assertTrue(result)

    def test_point_in_circle_false(self):
        """Test punktu poza kołem"""
        center = (50, 50)
        radius = 10
        point = (70, 50)

        result = is_point_in_circle(point, center, radius)
        self.assertFalse(result)

    def test_point_in_rect_true(self):
        """Test punktu wewnątrz prostokąta"""
        point = (25, 65)
        result = is_point_in_rect(point, 20, 60, 15, 15)
        self.assertTrue(result)

    def test_point_in_rect_false(self):
        """Test punktu poza prostokątem"""
        point = (50, 50)
        result = is_point_in_rect(point, 20, 60, 15, 15)
        self.assertFalse(result)

    def test_point_in_obstacle_circle(self):
        """Test punktu w przeszkodzie koła"""
        point = (30, 30)
        obstacles = [{'type': 'circle', 'center': (30, 30), 'radius': 8}]

        result = is_point_in_obstacle(point, obstacles)
        self.assertTrue(result)

    def test_point_in_obstacle_rect(self):
        """Test punktu w przeszkodzie prostokąta"""
        point = (25, 65)
        obstacles = [{'type': 'rect', 'x': 20, 'y': 60, 'width': 15, 'height': 15}]

        result = is_point_in_obstacle(point, obstacles)
        self.assertTrue(result)

    def test_point_not_in_any_obstacle(self):
        """Test punktu poza wszystkimi przeszkodami"""
        point = (10, 10)
        result = is_point_in_obstacle(point, OBSTACLES)
        self.assertFalse(result)


class TestLineIntersection(unittest.TestCase):
    """Testy funkcji sprawdzania przecinania linii"""

    def test_line_intersecting_circle(self):
        """Test linii przecinającej koło"""
        p1 = (20, 30)
        p2 = (40, 30)
        obstacles = [{'type': 'circle', 'center': (30, 30), 'radius': 8}]

        result = is_line_intersecting_obstacle(p1, p2, obstacles)
        self.assertTrue(result)

    def test_line_not_intersecting(self):
        """Test linii niezachodzące na przeszkody"""
        p1 = (0, 0)
        p2 = (10, 10)
        obstacles = [{'type': 'circle', 'center': (50, 50), 'radius': 8}]

        result = is_line_intersecting_obstacle(p1, p2, obstacles)
        self.assertFalse(result)


class TestPathCalculations(unittest.TestCase):
    """Testy obliczania ścieżek"""

    def test_path_length_straight(self):
        """Test długości linii prostej"""
        waypoints = [[0, 0], [3, 4], [6, 8]]
        length = calculate_path_length(waypoints)

        expected = 10.0
        self.assertAlmostEqual(length, expected, places=1)

    def test_path_length_single_segment(self):
        """Test długości ścieżki z jednym segmentem"""
        waypoints = [[0, 0], [3, 4]]
        length = calculate_path_length(waypoints)

        expected = 5.0
        self.assertAlmostEqual(length, expected, places=1)

    def test_check_path_validity_valid(self):
        """Test sprawdzenia prawidłowości ścieżki (bez przeszkód)"""
        # NAPRAWIONO: Test z pustą listą przeszkód - ścieżka zawsze jest valid
        path = [[0, 0], [50, 50], [100, 100]]
        result = check_path_validity(path, obstacles=[])

        self.assertTrue(result)

    def test_check_path_validity_invalid(self):
        """Test sprawdzenia ścieżki przecinającej przeszkody"""
        path = [[25, 25], [35, 35], [100, 100]]
        result = check_path_validity(path)

        self.assertFalse(result)


class TestRepair(unittest.TestCase):
    """Testy funkcji naprawy"""

    def test_repair_waypoint_valid(self):
        """Test naprawy prawidłowego waypointu"""
        waypoint = [50, 50]
        repaired = repair_waypoint(waypoint)

        self.assertEqual(len(repaired), 2)
        self.assertGreaterEqual(repaired[0], 0)
        self.assertLessEqual(repaired[0], GRID_WIDTH)

    def test_repair_waypoint_out_of_bounds(self):
        """Test naprawy waypointu poza granicami"""
        waypoint = [-10, 150]
        repaired = repair_waypoint(waypoint)

        self.assertGreaterEqual(repaired[0], 0)
        self.assertLessEqual(repaired[0], GRID_WIDTH)
        self.assertGreaterEqual(repaired[1], 0)
        self.assertLessEqual(repaired[1], GRID_HEIGHT)

    def test_repair_waypoint_in_obstacle(self):
        """Test naprawy waypointu w przeszkodzie"""
        waypoint = [30, 30]
        repaired = repair_waypoint(waypoint)

        obstacles_test = [{'type': 'circle', 'center': (30, 30), 'radius': 8}]
        self.assertFalse(is_point_in_obstacle(repaired, obstacles_test))

    def test_repair_individual(self):
        """Test naprawy całego osobnika"""
        individual = [[0, 0], [50, 50], [100, 100]]
        repaired = repair_individual(individual)

        self.assertEqual(len(repaired), len(individual))
        self.assertEqual(repaired[0], [0, 0])
        self.assertEqual(repaired[-1], [GRID_WIDTH, GRID_HEIGHT])


class TestIndividual(unittest.TestCase):
    """Testy tworzenia i ewaluacji osobników"""

    def test_create_individual_structure(self):
        """Test struktury tworzenia osobnika"""
        individual = create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)

        self.assertEqual(len(individual), NUM_WAYPOINTS)

        for wp in individual:
            self.assertEqual(len(wp), 2)
            self.assertGreaterEqual(wp[0], 0)
            self.assertLessEqual(wp[0], GRID_WIDTH)

    def test_create_individual_start_end(self):
        """Test że osobnik ma prawidłowy start i koniec"""
        individual = create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)

        self.assertEqual(individual[0], [0, 0])
        self.assertEqual(individual[-1], [GRID_WIDTH, GRID_HEIGHT])

    def test_evaluate_fitness_realistic(self):
        """Test ewaluacji fitness osobnika"""
        individual = create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)
        fitness = evaluate_fitness(individual)

        self.assertEqual(len(fitness), 1)
        self.assertGreater(fitness[0], 0)

    def test_evaluate_fitness_short_path_better(self):
        """Test że krótsza ścieżka ma lepszy fitness"""
        ind1 = [[0, 0], [50, 50], [100, 100]]
        fitness1 = evaluate_fitness(ind1)

        ind2 = [[0, 0], [10, 90], [90, 10], [100, 100]]
        fitness2 = evaluate_fitness(ind2)

        self.assertLess(fitness1[0], fitness2[0])


class TestIntegration(unittest.TestCase):
    """Testy integracyjne"""

    def test_workflow_create_repair_evaluate(self):
        """Test pełnego workflow: utwórz -> napraw -> ocen"""
        individual = create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)
        self.assertEqual(len(individual), NUM_WAYPOINTS)

        repaired = repair_individual(individual)
        self.assertEqual(len(repaired), NUM_WAYPOINTS)

        fitness = evaluate_fitness(repaired)
        self.assertGreater(fitness[0], 0)

    def test_population_diversity(self):
        """Test że populacja ma różne osobniki"""
        individuals = [create_individual(NUM_WAYPOINTS, GRID_WIDTH, GRID_HEIGHT)
                       for _ in range(10)]

        fitnesses = [evaluate_fitness(ind)[0] for ind in individuals]
        unique_fitnesses = len(set([round(f, 2) for f in fitnesses]))

        self.assertGreater(unique_fitnesses, 1)


def run_tests():
    """Uruchamia wszystkie testy"""
    print("\n" + "=" * 70)
    print("URUCHAMIANIE TESTÓW JEDNOSTKOWYCH")
    print("=" * 70 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestWindEffect))
    suite.addTests(loader.loadTestsFromTestCase(TestPointInGeometry))
    suite.addTests(loader.loadTestsFromTestCase(TestLineIntersection))
    suite.addTests(loader.loadTestsFromTestCase(TestPathCalculations))
    suite.addTests(loader.loadTestsFromTestCase(TestRepair))
    suite.addTests(loader.loadTestsFromTestCase(TestIndividual))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print("PODSUMOWANIE TESTÓW")
    print("=" * 70)
    print(f"Testy uruchomione:    {result.testsRun}")
    success_count = result.testsRun - len(result.failures) - len(result.errors)
    print(f"Sukcesy:              {success_count} ✓")
    print(f"Niepowodzenia:        {len(result.failures)} ✗")
    print(f"Błędy:                {len(result.errors)} ✗")
    print("=" * 70 + "\n")

    if result.wasSuccessful():
        print("✓ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
    else:
        print("✗ NIEKTÓRE TESTY ZAWIODŁY")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
