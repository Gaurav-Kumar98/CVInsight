import unittest
from unittest.mock import MagicMock
from datetime import date

from cvinsight.base_plugins.experience_extractor import ExperienceExtractorPlugin
from cvinsight.models import ResumeWorkExperience # This is the model used by the plugin

class TestExperienceExtractorPlugin(unittest.TestCase):

    def setUp(self):
        self.mock_llm_service = MagicMock()
        self.plugin = ExperienceExtractorPlugin(llm_service=self.mock_llm_service)
        self.sample_text = "Some resume text"
        self.today_str = date.today().strftime("%d/%m/%Y")

    def test_extract_responsibilities_present(self):
        """Test extraction when responsibilities are present."""
        mock_output = {
            "work_experiences": [
                {
                    "company": "TestCorp",
                    "role": "Developer",
                    "start_date": "01/01/2020",
                    "end_date": "01/01/2021",
                    "location": "Remote",
                    "responsibilities": ["coded stuff", "fixed bugs"]
                }
            ]
        }
        mock_token_usage = {"total_tokens": 100, "extractor": "experience_extractor"}
        
        # The llm_service.extract_with_llm returns a tuple (result_model_instance, token_usage_dict)
        # The result_model_instance should be an instance of ResumeWorkExperience
        # For testing, we can mock this by creating a ResumeWorkExperience instance from the dict
        self.mock_llm_service.extract_with_llm.return_value = (
            ResumeWorkExperience(**mock_output),
            {"total_tokens": 100} # The plugin adds "extractor" key later
        )

        result, token_usage = self.plugin.extract(self.sample_text)

        self.assertEqual(len(result["work_experiences"]), 1)
        experience = result["work_experiences"][0]
        self.assertEqual(experience["company"], "TestCorp")
        self.assertEqual(experience["role"], "Developer")
        self.assertEqual(experience["responsibilities"], ["coded stuff", "fixed bugs"])
        self.assertEqual(token_usage["extractor"], "experience_extractor") # Check plugin adds its name
        self.mock_llm_service.extract_with_llm.assert_called_once()

    def test_extract_responsibilities_absent_or_null(self):
        """Test extraction when responsibilities are absent or null."""
        mock_output = {
            "work_experiences": [
                {
                    "company": "NoRespCorp",
                    "role": "Tester",
                    "start_date": "01/02/2020",
                    "end_date": "01/02/2021",
                    "location": "Office",
                    "responsibilities": None # Scenario: LLM returns null
                },
                {
                    "company": "MissingRespCorp",
                    "role": "Analyst",
                    "start_date": "01/03/2020",
                    "end_date": "01/03/2021",
                    "location": "WFH"
                    # Responsibilities field completely missing
                }
            ]
        }
        self.mock_llm_service.extract_with_llm.return_value = (
            ResumeWorkExperience(**mock_output),
            {"total_tokens": 150}
        )

        result, _ = self.plugin.extract(self.sample_text)

        self.assertEqual(len(result["work_experiences"]), 2)
        self.assertEqual(result["work_experiences"][0]["company"], "NoRespCorp")
        self.assertEqual(result["work_experiences"][0]["responsibilities"], []) # Should default to empty list
        
        self.assertEqual(result["work_experiences"][1]["company"], "MissingRespCorp")
        self.assertEqual(result["work_experiences"][1]["responsibilities"], []) # Should default to empty list

    def test_extract_responsibilities_mixed_multiple_entries(self):
        """Test with multiple entries, some with and some without responsibilities."""
        mock_output = {
            "work_experiences": [
                {
                    "company": "Alpha Inc",
                    "role": "Engineer",
                    "start_date": "01/01/2022",
                    "end_date": self.today_str, # Test "Present" date formatting
                    "location": "New York",
                    "responsibilities": ["developed features", "led a team"]
                },
                {
                    "company": "Beta LLC",
                    "role": "Junior Dev",
                    "start_date": "01/05/2021",
                    "end_date": "31/12/2021",
                    "location": "San Francisco",
                    "responsibilities": None # Null responsibilities
                },
                {
                    "company": "Gamma Co",
                    "role": "Support",
                    "start_date": "01/08/2020",
                    "end_date": "30/04/2021",
                    "location": "Remote" 
                    # Responsibilities field completely missing
                }
            ]
        }
        self.mock_llm_service.extract_with_llm.return_value = (
            ResumeWorkExperience(**mock_output),
            {"total_tokens": 200}
        )

        result, _ = self.plugin.extract(self.sample_text)

        self.assertEqual(len(result["work_experiences"]), 3)
        
        # Entry 1: Responsibilities present
        self.assertEqual(result["work_experiences"][0]["company"], "Alpha Inc")
        self.assertEqual(result["work_experiences"][0]["responsibilities"], ["developed features", "led a team"])
        
        # Entry 2: Responsibilities is None
        self.assertEqual(result["work_experiences"][1]["company"], "Beta LLC")
        self.assertEqual(result["work_experiences"][1]["responsibilities"], [])
        
        # Entry 3: Responsibilities field missing
        self.assertEqual(result["work_experiences"][2]["company"], "Gamma Co")
        self.assertEqual(result["work_experiences"][2]["responsibilities"], [])

if __name__ == '__main__':
    unittest.main()
