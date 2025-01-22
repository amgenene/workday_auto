from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class ApplicationWorkflow:
    def __init__(self, driver, wait, config, form_processor, element_handler):
        self.driver = driver
        self.wait = wait
        self.config = config
        self.form_processor = form_processor
        self.element_handler = element_handler

    def run(self, url: str) -> bool:
        """Run the complete application workflow"""
        try:
            self.driver.get(url)
            time.sleep(4)

            if not self._initial_application_check():
                return False

            if not self._handle_authentication(url):
                return False

            return self._process_application_form()

        except Exception as e:
            print(f"Error in application workflow: {e}")
            return False

    def _initial_application_check(self) -> bool:
        """Check if we can proceed with the application"""
        try:
            # Check if already applied
            if self._check_already_applied():
                print("Already applied to this position")
                return False

            # Click apply button
            apply_button = self.element_handler.find_element_safely(
                By.CSS_SELECTOR,
                "a[role='button'][data-uxi-element-id='Apply_adventureButton']"
            )
            if apply_button:
                self.element_handler.click_element(apply_button)
                time.sleep(2)

            return True

        except Exception as e:
            print(f"Error in initial application check: {e}")
            return False

    def _handle_authentication(self, url: str) -> bool:
        """Handle the authentication process"""
        try:
            company = urlparse(url).netloc.split(".")[0]
            existing_company = company in self.config.get('companies', [])

            if existing_company:
                return self._signin()
            else:
                success = self._signup()
                if success:
                    self.config.add_company(company)
                return success

        except Exception as e:
            print(f"Error in authentication: {e}")
            return False

    def _process_application_form(self) -> bool:
        """Process all pages of the application form"""
        current_page = 2
        max_pages = 5

        while current_page <= max_pages:
            time.sleep(2)
            try:
                if not self.form_processor.process_page(current_page):
                    print(f"Issues on page {current_page}")
                    return False

                if not self._click_next():
                    print(f"Failed to proceed to next page from {current_page}")
                    return False

                current_page += 1

            except Exception as e:
                print(f"Error on page {current_page}: {e}")
                return False

        return True

    def _check_already_applied(self) -> bool:
        """Check if already applied to this position"""
        already_applied = self.element_handler.find_element_safely(
            By.CSS_SELECTOR,
            "[data-automation-id='alreadyApplied']"
        )
        return bool(already_applied)

    def _click_next(self) -> bool:
        """Click the next/continue button"""
        try:
            button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[text()='Next' or text()='Continue' or text()='Submit']"
                ))
            )
            button.click()
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Error clicking next: {e}")
            return False