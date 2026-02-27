import unittest
from shared.chemistry_lab import ChemistryLabManager, ELEMENTS

class TestChemistryLab(unittest.TestCase):
    def setUp(self):
        self.manager = ChemistryLabManager()

    def test_get_element_by_symbol(self):
        el = self.manager.get_element("H")
        self.assertIsNotNone(el)
        self.assertEqual(el["name"], "Hydrogen")
        self.assertEqual(el["atomic_number"], 1)

    def test_get_element_by_name(self):
        el = self.manager.get_element("Carbon")
        self.assertIsNotNone(el)
        self.assertEqual(el["symbol"], "C")
        self.assertEqual(el["atomic_number"], 6)

    def test_get_element_by_number(self):
        el = self.manager.get_element(8)
        self.assertIsNotNone(el)
        self.assertEqual(el["name"], "Oxygen")
        self.assertEqual(el["symbol"], "O")

    def test_get_element_invalid(self):
        el = self.manager.get_element("Unobtanium")
        self.assertIsNone(el)
        el = self.manager.get_element(999)
        self.assertIsNone(el)

    def test_search_elements(self):
        results = self.manager.search_elements("noble")
        # Helium, Neon, Argon, Krypton, Xenon, Radon, Oganesson (7)
        self.assertTrue(len(results) >= 6)
        names = [r["name"] for r in results]
        self.assertIn("Helium", names)
        self.assertIn("Neon", names)

    def test_molar_mass_simple(self):
        # H2O: 2*1.008 + 15.999 = 2.016 + 15.999 = 18.015
        mass = self.manager.calculate_molar_mass("H2O")
        self.assertIsInstance(mass, float)
        self.assertAlmostEqual(mass, 18.015, places=3)

    def test_molar_mass_single(self):
        # C: 12.011
        mass = self.manager.calculate_molar_mass("C")
        self.assertAlmostEqual(mass, 12.011, places=3)

    def test_molar_mass_complex(self):
        # C6H12O6: 6*12.011 + 12*1.008 + 6*15.999
        # = 72.066 + 12.096 + 95.994 = 180.156
        mass = self.manager.calculate_molar_mass("C6H12O6")
        self.assertAlmostEqual(mass, 180.156, places=3)

    def test_molar_mass_parens(self):
        # Ca(OH)2: Ca=40.078, O=15.999, H=1.008
        # 40.078 + 2 * (15.999 + 1.008) = 40.078 + 2 * 17.007 = 40.078 + 34.014 = 74.092
        mass = self.manager.calculate_molar_mass("Ca(OH)2")
        self.assertAlmostEqual(mass, 74.092, places=3)

    def test_molar_mass_nested_parens(self):
        # (NH4)2SO4: N=14.007, H=1.008, S=32.06, O=15.999
        # NH4 = 14.007 + 4*1.008 = 18.039
        # (NH4)2 = 36.078
        # SO4 = 32.06 + 4*15.999 = 32.06 + 63.996 = 96.056
        # Total = 36.078 + 96.056 = 132.134
        mass = self.manager.calculate_molar_mass("(NH4)2SO4")
        self.assertAlmostEqual(mass, 132.134, places=3)

    def test_molar_mass_invalid(self):
        res = self.manager.calculate_molar_mass("Junk")
        self.assertTrue(isinstance(res, str) and "Error" in res)

        res = self.manager.calculate_molar_mass("H2O)")
        self.assertTrue(isinstance(res, str) and "Error" in res)

        res = self.manager.calculate_molar_mass("(H2O")
        self.assertTrue(isinstance(res, str) and "Error" in res)

if __name__ == "__main__":
    unittest.main()
