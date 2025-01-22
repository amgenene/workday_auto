import yaml
from typing import Dict, Any, List
import os


class ProfileLoader:
    def __init__(self, config_path: str = "./config/"):
        self.config_path = config_path
        self.profile = self._load_profile()
        self.companies = set(self._load_companies())

    def _load_profile(self) -> Dict[str, Any]:
        """Load profile configuration from YAML file"""
        try:
            with open(
                os.path.join(os.path.dirname(self.config_path), "profile.yaml"), "r"
            ) as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading profile: {e}")
            return {}

    def _load_companies(self) -> List[str]:
        """Load list of companies from companies file"""
        companies_path = os.path.join(
            os.path.dirname(self.config_path), "companies.txt"
        )
        try:
            if os.path.exists(companies_path):
                with open(companies_path, "r") as f:
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
            os.path.dirname(self.config_path), "companies.txt"
        )
        try:
            with open(companies_path, "w") as f:
                for company in sorted(self.companies):
                    f.write(f"{company}\n")
        except Exception as e:
            print(f"Error saving companies: {e}")

    @property
    def questions(self) -> List[tuple]:
        """Get the questions configuration"""
        return [
            (
                ["how did you hear about us"],
                "LinkedIn",
            ),
            (
                ["Country Phone Code"],
                "United States of America",
            ),
            (["Are you legally eligible to work"], "Yes"),
            (
                [
                    "Do you now or will you in the future require sponsorship for a work visa"
                ],
                "No",
            ),
            (
                ["have you previously been employed", "have you ever worked for"],
                "No",
            ),
            (
                ["first name"],
                self.profile["first_name"],
            ),
            (["last name"], self.profile["family_name"]),
            (["email"], self.profile["email"]),
            (["address line 1"], self.profile["address_line_1"]),
            (["city"], self.profile["address_city"]),
            (["state"], self.profile["address_state"]),
            (["postal Code"], self.profile["address_postal_code"]),
            (["phone device type"], "Mobile"),
            (["phone number"], self.profile["phone_number"]),
            (["are you legally authorized"], "Yes"),
            (["will you now or in the future"], "No"),
            (["Are you at least 18 years of age?"], "Yes"),
            (
                [
                    "Do you have an agreement or contract such as a non-disclosure or non-competitive agreement with another employer that might restrict your employment at"
                ],
                "No",
            ),
            (["do you require sponsorship"], "No"),
            (["disability status"], "I don't wish to answer"),
            (["veteran status"], "I am not"),
            (["gender"], "Male"),
            (
                ["ethnicity"],
                "Black or African American (United States of America)",
            ),
            (
                ["What is your race"],
                "Black or African American (United States of America)",
            ),
            (["hispanic or latino"], "No"),
            (["date"], None),
            (
                ["Please check one of the boxes below: "],
                "No, I do not have a disability",
            ),
            (
                ["I understand and acknowledge the terms of use"],
                None,
            ),
        ]
