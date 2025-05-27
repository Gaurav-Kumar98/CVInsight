from typing import Dict, Any, Type, List, Tuple
from pydantic import BaseModel
from ...plugins.base import ExtractorPlugin, PluginMetadata, PluginCategory
from ...models import ResumeWorkExperience
from datetime import date
import logging

class ExperienceExtractorPlugin(ExtractorPlugin):
    """Extractor plugin for work experience information."""
    
    def __init__(self, llm_service):
        """Initialize the plugin with an LLM service."""
        self.llm_service = llm_service
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="experience_extractor",
            version="1.0.0",
            description="Extracts work experience history with companies, roles, and dates",
            category=PluginCategory.BASE,
            author="Resume Analysis Team"
        )
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        logging.info(f"Initializing {self.metadata.name}")
    
    def get_model(self) -> Type[BaseModel]:
        """Get the Pydantic model for the extractor."""
        return ResumeWorkExperience
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for the extractor."""
        return """
You are an expert resume parser. Your task is to extract work experience details from the resume text provided below. For each work experience entry, extract the following details:
- Company
- Start Date: in dd/mm/yyyy format. If the resume does not provide the day or month, default the missing parts to "01". If you encounter Present then use the current date, i.e. {today}.
- End Date: in dd/mm/yyyy format. If the resume does not provide the day or month, default the missing parts to "01". If you encounter Present then use the current date, i.e. {today}.
- Location
- Role: Extract ONLY the job title (e.g., "Data Engineer", "Software Developer", "Project Manager"). Do NOT include project information or descriptions in this field - just the official job title.
- Responsibilities: Extract a list of key responsibilities or achievements for the role. This should be a list of strings. If no specific responsibilities are listed, return an empty list.

IMPORTANT: Create only ONE entry per company, even if the person worked on multiple projects or had multiple roles at the same company. If there were multiple positions at the same company, use the most senior or most recent role in the Role field. The earliest start date and the latest end date should be used for the company's overall employment period.

Only focus on Work Experience section of the below text. If you cannot find anything, return null.

Return your output as a JSON object with the below schema.
{format_instructions}

Text:
{text}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["text", "today"]
    
    def prepare_input_data(self, extracted_text: str) -> Dict[str, Any]:
        """Prepare the input data for the LLM."""
        return {
            "text": extracted_text,
            "today": date.today().strftime("%d/%m/%Y")
        }
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract work experience information from text.
        
        Args:
            text: The text to extract information from.
            
        Returns:
            A tuple of (extracted_data, token_usage)
        """
        # Prepare prompt from template
        prompt_template = self.get_prompt_template()
        input_data = self.prepare_input_data(text)
        input_variables = self.get_input_variables()
        model = self.get_model()
        
        # Call LLM service
        result, token_usage = self.llm_service.extract_with_llm(
            model,
            prompt_template,
            input_variables,
            input_data
        )
        
        # Add extractor name to token usage
        token_usage["extractor"] = self.metadata.name
        
        # Process the result to ensure it's a dict with the expected keys
        if isinstance(result, dict):
            processed_result = {
                "work_experiences": result.get("work_experiences", [])
            }
        else:
            # If result is a Pydantic model, convert to dict
            processed_result = {
                "work_experiences": getattr(result, "work_experiences", [])
            }
        
        # Ensure each work experience entry has expected fields
        for exp in processed_result["work_experiences"]:
            if isinstance(exp, dict):
                # Set default values for missing fields
                exp["company"] = exp.get("company") or ""
                exp["start_date"] = exp.get("start_date") or ""
                exp["end_date"] = exp.get("end_date") or ""
                exp["location"] = exp.get("location")  # Can be None
                exp["role"] = exp.get("role") or ""
                exp["responsibilities"] = exp.get("responsibilities") or []
        
        return processed_result, token_usage 