import yaml
from typing import Dict, Any, List
import os

class ProfileLoader:
    def __init__(self, config_path: str = "./config/profile.yaml"):
        self.config_path = config_path
        self.profile = self._load_profile()
        self.companies = set(self._load_companies())

    def _load_profile(self) -> Dict[str, Any]:
        """Load profile configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")
            return {}

    def _load_companies(self) -> List[str]:
        """Load list of companies from companies file"""
        companies_path = os.path.join(
            os.path.dirname(self.config_path),
            'companies.txt'
        )
        try:
            if os.path.exists(companies_path):
                with open(companies_path, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
            return []
        except Exception as e:
            print(f"Error loading companies: {e}")
            return []

    def add_company(self, company: str):
        """Add a new company to the list"""
        if company not in self.companies:
            self.companies.add(company)
            self._save_companies()

    def _save_companies(self):
        """Save companies list to file"""
        companies_path = os.path.join(
            os.path.dirname(self.config_path),
            'companies.txt'
        )
        try:
            with open(companies_path, 'w') as f:
                for company in sorted(self.companies):
                    f.write(f"{company}\n")
        except Exception as e:
            print(f"Error saving companies: {e}")

    @property
    def questions(self) -> List[tuple]:
        """Get the questions configuration"""
        return [
            (["how did you hear about us"], "LinkedIn"),
            (["Country Phone Code"], "United States of America"),
            (["Are you legally eligible to work"], "Yes"),
            (["Do you now or will you in the future require sponsorship"], "No"),
            # Add more question/answer pairs as needed
        ]