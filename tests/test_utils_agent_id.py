import unittest
from shared.utils import generate_agent_id

class TestAgentIdGeneration(unittest.TestCase):
    def test_generate_agent_id_basic(self):
        project_name = "my_project"
        spec_content = "some spec content"
        agent_type = "gemini"

        agent_id = generate_agent_id(project_name, spec_content, agent_type)

        # Expected: gemini_agent_my_project_{hash}
        self.assertTrue(agent_id.startswith("gemini_agent_my_project_"))
        self.assertLessEqual(len(agent_id), 50) # Ensure reasonable length

    def test_generate_agent_id_consistency(self):
        project_name = "my_project"
        spec_content = "some spec content"
        agent_type = "gemini"

        id1 = generate_agent_id(project_name, spec_content, agent_type)
        id2 = generate_agent_id(project_name, spec_content, agent_type)

        self.assertEqual(id1, id2)

    def test_generate_agent_id_different_inputs(self):
        id1 = generate_agent_id("p1", "spec1", "gemini")
        id2 = generate_agent_id("p1", "spec2", "gemini")

        self.assertNotEqual(id1, id2)

    def test_truncation(self):
         # Even with long inputs, ID should be short
         long_spec = "a" * 10000
         agent_id = generate_agent_id("p1", long_spec, "gemini")
         self.assertTrue(len(agent_id) < 50)

if __name__ == '__main__':
    unittest.main()
