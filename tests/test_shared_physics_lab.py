import unittest
import sys
from unittest.mock import MagicMock
from shared.physics_lab import PhysicsLabManager, run_physics_lab_logic

class TestPhysicsLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = PhysicsLabManager()

    def test_calculate_velocity(self):
        self.assertEqual(self.manager.calculate_velocity(100, 10), "Velocity: 10.0000 m/s")
        self.assertEqual(self.manager.calculate_velocity(100, 0), "Error: Time cannot be zero.")

    def test_calculate_acceleration(self):
        self.assertEqual(self.manager.calculate_acceleration(0, 20, 5), "Acceleration: 4.0000 m/s²")
        self.assertEqual(self.manager.calculate_acceleration(10, 20, 0), "Error: Time cannot be zero.")

    def test_calculate_force(self):
        self.assertEqual(self.manager.calculate_force(10, 9.8), "Force: 98.0000 N")

    def test_calculate_kinetic_energy(self):
        self.assertEqual(self.manager.calculate_kinetic_energy(2, 3), "Kinetic Energy: 9.0000 J")

    def test_calculate_potential_energy(self):
        self.assertEqual(self.manager.calculate_potential_energy(5, 10), "Potential Energy: 490.5000 J (g=9.81 m/s²)")
        self.assertEqual(self.manager.calculate_potential_energy(5, 10, 10), "Potential Energy: 500.0000 J (g=10 m/s²)")

class TestPhysicsLabLogic(unittest.TestCase):

    def test_run_logic_velocity(self):
        args = MagicMock()
        args.action = "velocity"
        args.distance = 100
        args.time = 10
        self.assertTrue(run_physics_lab_logic(args))

    def test_run_logic_force(self):
        args = MagicMock()
        args.action = "force"
        args.mass = 10
        args.acceleration = 5
        self.assertTrue(run_physics_lab_logic(args))
