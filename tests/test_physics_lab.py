import unittest
from unittest.mock import MagicMock, patch
import sys
from io import StringIO
from shared.physics_lab import PhysicsLabManager, run_physics_lab_logic

class TestPhysicsLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = PhysicsLabManager()

    def test_calculate_velocity(self):
        self.assertEqual(self.manager.calculate_velocity(100, 10), "Velocity: 10.0000 m/s")
        self.assertEqual(self.manager.calculate_velocity(100, 0), "Error: Time cannot be zero.")

    def test_calculate_acceleration(self):
        self.assertEqual(self.manager.calculate_acceleration(0, 10, 2), "Acceleration: 5.0000 m/s²")
        self.assertEqual(self.manager.calculate_acceleration(10, 0, 0), "Error: Time cannot be zero.")

    def test_calculate_force(self):
        self.assertEqual(self.manager.calculate_force(5, 10), "Force: 50.0000 N")
        self.assertEqual(self.manager.calculate_force(-5, 10), "Error: Mass cannot be negative.")

    def test_calculate_kinetic_energy(self):
        self.assertEqual(self.manager.calculate_kinetic_energy(2, 10), "Kinetic Energy: 100.0000 J")
        self.assertEqual(self.manager.calculate_kinetic_energy(-2, 10), "Error: Mass cannot be negative.")

    def test_calculate_potential_energy(self):
        self.assertEqual(self.manager.calculate_potential_energy(2, 10), "Potential Energy: 196.2000 J")
        self.assertEqual(self.manager.calculate_potential_energy(-2, 10), "Error: Mass cannot be negative.")

class TestPhysicsLabCLI(unittest.TestCase):
    def test_velocity_cli(self):
        args = MagicMock()
        args.action = "velocity"
        args.distance = 100.0
        args.time = 5.0

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            result = run_physics_lab_logic(args)
            output = out.getvalue().strip()
            self.assertTrue(result)
            self.assertEqual(output, "Velocity: 20.0000 m/s")
        finally:
            sys.stdout = saved_stdout

    def test_acceleration_cli(self):
        args = MagicMock()
        args.action = "acceleration"
        args.v_initial = 10.0
        args.v_final = 20.0
        args.time = 2.0

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            result = run_physics_lab_logic(args)
            output = out.getvalue().strip()
            self.assertTrue(result)
            self.assertEqual(output, "Acceleration: 5.0000 m/s²")
        finally:
            sys.stdout = saved_stdout

    def test_force_cli(self):
        args = MagicMock()
        args.action = "force"
        args.mass = 5.0
        args.acceleration = 10.0

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            result = run_physics_lab_logic(args)
            output = out.getvalue().strip()
            self.assertTrue(result)
            self.assertEqual(output, "Force: 50.0000 N")
        finally:
            sys.stdout = saved_stdout

    def test_kinetic_energy_cli(self):
        args = MagicMock()
        args.action = "kinetic-energy"
        args.mass = 2.0
        args.velocity = 5.0

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            result = run_physics_lab_logic(args)
            output = out.getvalue().strip()
            self.assertTrue(result)
            self.assertEqual(output, "Kinetic Energy: 25.0000 J")
        finally:
            sys.stdout = saved_stdout

    def test_potential_energy_cli(self):
        args = MagicMock()
        args.action = "potential-energy"
        args.mass = 2.0
        args.height = 10.0

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            result = run_physics_lab_logic(args)
            output = out.getvalue().strip()
            self.assertTrue(result)
            self.assertEqual(output, "Potential Energy: 196.2000 J")
        finally:
            sys.stdout = saved_stdout

    def test_missing_args_cli(self):
        args = MagicMock()
        args.action = "velocity"
        args.distance = None
        args.time = None

        saved_stderr = sys.stderr
        try:
            err = StringIO()
            sys.stderr = err
            result = run_physics_lab_logic(args)
            output = err.getvalue().strip()
            self.assertFalse(result)
            self.assertIn("Error:", output)
        finally:
            sys.stderr = saved_stderr

if __name__ == '__main__':
    unittest.main()
