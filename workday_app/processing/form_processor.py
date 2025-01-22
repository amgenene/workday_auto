from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Tuple, Any
import time

class FormProcessor:
    def __init__(self, driver, wait, element_handler, question_matcher):
        self.driver = driver
        self.wait = wait
        self.element_handler = element_handler
        self.question_matcher = question_matcher

    def process_page(self, page_number: int) -> bool:
        """Process all required fields on the current page"""
        required_fields = self._find_required_fields()
        if not required_fields:
            print(f"No required fields found on page {page_number}")
            return False

        questions = self._extract_questions(required_fields)
        return self._handle_questions(questions, page_number)

    def _find_required_fields(self) -> List[Any]:
        """Find all required fields on the current page"""
        return self.element_handler.find_elements_safely(
            By.XPATH,
            "//abbr[text()='*']"
        )

    def _extract_questions(self, fields: List[Any]) -> List[Tuple[str, Any, str]]:
        """Extract questions and their corresponding elements"""
        questions = []
        for field in fields[1:]:  # Skip first field as it's usually a header
            try:
                question = field.find_element(By.XPATH, "./..")
                question_text = question.text.strip()
                if not question_text:
                    continue

                parent = question.find_element(
                    By.XPATH,
                    "./ancestor::div[@data-automation-id][position()=1]"
                )

                container, _, is_id = self.element_handler.find_next_sibling_safely(
                    question,
                    parent
                )

                if container:
                    automation_id = (
                        container.get_attribute("id") if is_id
                        else container.get_attribute("data-automation-id")
                    )
                    questions.append((question_text, container, automation_id))

            except Exception as e:
                print(f"Error extracting question: {e}")
                continue

        return questions

    def _handle_questions(self, questions: List[Tuple[str, Any, str]], step: int) -> bool:
        """Process each question with the question matcher"""
        success = True
        for question_text, element, automation_id in questions:
            if not self.question_matcher.process_question(
                question_text,
                element,
                automation_id,
                step
            ):
                success = False
                print(f"Failed to process question: {question_text}")

        return success