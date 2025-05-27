from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import os

class ResumeProfile(BaseModel):
    """Model for basic profile information"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    current_title: Optional[str] = None
    summary: Optional[str] = None

class ResumeSkills(BaseModel):
    """Model for skills"""
    skills: Dict[str, List[str]]

class Skills(BaseModel):
    """Simple skills model for backward compatibility"""
    skills: List[str] = Field(
        ...,
        description="A list of skills extracted from the resume text."
    )

class Education(BaseModel):
    """Model for an education entry"""
    degree: str
    location: Optional[str] = None
    institution: str
    start_date: str
    end_date: str

class ResumeEducation(BaseModel):
    """Model for education information"""
    educations: List[Education]

class Experience(BaseModel):
    """Model for a work experience entry"""
    company: str
    role: str
    location: Optional[str] = None
    start_date: str
    end_date: str
    responsibilities: Optional[List[str]] = Field(default_factory=list)

class ResumeWorkExperience(BaseModel):
    """Model for work experience information"""
    work_experiences: List[Experience]

class WorkDates(BaseModel):
    """Model for work dates information"""
    oldest_working_date: str
    newest_working_date: str
    total_experience: Optional[str] = None

class Resume(BaseModel):
    """A complete resume with all extracted information."""
    # Profile information
    name: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    
    # Skills
    skills: List[str] = Field(default_factory=list)
    
    # Education
    educations: List[Education] = Field(default_factory=list)
    
    # Work Experience
    work_experiences: List[Experience] = Field(default_factory=list)
    
    # Years of Experience
    YoE: Optional[str] = None
    
    # File information
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    
    # Token usage information
    token_usage: Dict[str, Any] = Field(default_factory=dict)
    
    # Plugin data for custom extractors
    plugin_data: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def from_extractors_output(cls, profile: Dict[str, Any], skills: Dict[str, Any], 
                             education: Dict[str, Any], experience: Dict[str, Any], 
                             yoe: Dict[str, Any], file_path: str, 
                             token_usage: Optional[Dict[str, int]] = None) -> 'Resume':
        """
        Create a Resume instance from the output of various extractors.
        
        Args:
            profile: Output from the profile extractor
            skills: Output from the skills extractor
            education: Output from the education extractor
            experience: Output from the experience extractor
            yoe: Output from the years of experience extractor
            file_path: Path to the resume file
            token_usage: Dictionary containing token usage information
            
        Returns:
            A Resume instance with all the extracted information
        """
        file_name = os.path.basename(file_path)
        
        return cls(
            name=profile.get('name'),
            contact_number=profile.get('phone'),  # Updated to match ResumeProfile
            email=profile.get('email'),
            skills=skills.get('skills', []),
            educations=education.get('educations', []),
            work_experiences=experience.get('work_experiences', []),
            YoE=yoe.get('YoE'),
            file_path=file_path,
            file_name=file_name,
            token_usage=token_usage or {}
        )
        
    def add_plugin_data(self, plugin_name: str, data: Dict[str, Any]) -> None:
        """
        Add data from a plugin extractor.
        
        Args:
            plugin_name: Name of the plugin
            data: Data extracted by the plugin
        """
        self.plugin_data[plugin_name] = data
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Resume instance to a dictionary.
        
        Returns:
            A dictionary representation of the Resume
        """
        return self.model_dump(exclude={'file_path', 'token_usage'}) 