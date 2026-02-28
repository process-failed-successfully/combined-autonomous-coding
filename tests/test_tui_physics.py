import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, Static
from shared.tui_physics import PhysicsLabTab

class TestPhysicsLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch PhysicsLabManager
        self.patcher = patch("shared.tui_physics.PhysicsLabManager")
        self.MockManager = self.patcher.start()

        self.tab = PhysicsLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        # Mock UI methods
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    def test_calculate_velocity(self):
        dist_input = MagicMock(spec=Input)
        dist_input.value = "100"
        time_input = MagicMock(spec=Input)
        time_input.value = "10"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-phys-dist": return dist_input
            if selector == "#input-phys-time": return time_input
            if selector == "#lbl-phys-velocity-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_velocity.return_value = "Velocity: 10.0000 m/s"

        self.tab.calculate_velocity()

        self.mock_manager.calculate_velocity.assert_called_with(100.0, 10.0)
        lbl.update.assert_called()
        self.assertIn("10.0000 m/s", lbl.update.call_args[0][0])

    def test_calculate_acceleration(self):
        vi_input = MagicMock(spec=Input)
        vi_input.value = "0"
        vf_input = MagicMock(spec=Input)
        vf_input.value = "20"
        t_input = MagicMock(spec=Input)
        t_input.value = "4"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-phys-vi": return vi_input
            if selector == "#input-phys-vf": return vf_input
            if selector == "#input-phys-acc-time": return t_input
            if selector == "#lbl-phys-acceleration-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_acceleration.return_value = "Acceleration: 5.0000 m/s²"

        self.tab.calculate_acceleration()

        self.mock_manager.calculate_acceleration.assert_called_with(0.0, 20.0, 4.0)
        lbl.update.assert_called()
        self.assertIn("5.0000 m/s²", lbl.update.call_args[0][0])

    def test_calculate_force(self):
        m_input = MagicMock(spec=Input)
        m_input.value = "5"
        a_input = MagicMock(spec=Input)
        a_input.value = "9.8"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-phys-mass": return m_input
            if selector == "#input-phys-acc": return a_input
            if selector == "#lbl-phys-force-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_force.return_value = "Force: 49.0000 N"

        self.tab.calculate_force()

        self.mock_manager.calculate_force.assert_called_with(5.0, 9.8)
        lbl.update.assert_called()
        self.assertIn("49.0000 N", lbl.update.call_args[0][0])

    def test_calculate_kinetic_energy(self):
        m_input = MagicMock(spec=Input)
        m_input.value = "2"
        v_input = MagicMock(spec=Input)
        v_input.value = "10"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-phys-ke-mass": return m_input
            if selector == "#input-phys-ke-vel": return v_input
            if selector == "#lbl-phys-energy-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_kinetic_energy.return_value = "Kinetic Energy: 100.0000 J"

        self.tab.calculate_kinetic_energy()

        self.mock_manager.calculate_kinetic_energy.assert_called_with(2.0, 10.0)
        lbl.update.assert_called()
        self.assertIn("100.0000 J", lbl.update.call_args[0][0])

    def test_calculate_potential_energy(self):
        m_input = MagicMock(spec=Input)
        m_input.value = "2"
        h_input = MagicMock(spec=Input)
        h_input.value = "10"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-phys-pe-mass": return m_input
            if selector == "#input-phys-pe-height": return h_input
            if selector == "#lbl-phys-energy-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_potential_energy.return_value = "Potential Energy: 196.2000 J"

        self.tab.calculate_potential_energy()

        self.mock_manager.calculate_potential_energy.assert_called_with(2.0, 10.0)
        lbl.update.assert_called()
        self.assertIn("196.2000 J", lbl.update.call_args[0][0])

    def test_invalid_input(self):
        dist_input = MagicMock(spec=Input)
        dist_input.value = "abc"
        time_input = MagicMock(spec=Input)
        time_input.value = "10"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-phys-dist": return dist_input
            if selector == "#input-phys-time": return time_input
            if selector == "#lbl-phys-velocity-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.tab.calculate_velocity()

        lbl.update.assert_called()
        self.assertIn("Invalid numeric input", lbl.update.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
