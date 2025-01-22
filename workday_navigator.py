from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class WorkdayNavigator:
    def __init__(self, driver, wait, web_element_handler):
        self.driver = driver
        self.wait = wait
        self.web_handler = web_element_handler

    def click_next(self):
        """Click the next/continue/submit button"""
        try:
            button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[text()='Next' or text()='Continue' or text()='Submit' or text()='Save and Continue' or text()='Review and Submit']"
                ))
            )
            button.click()
            time.sleep(5)

            # Check for errors
            self._check_for_errors()

        except Exception as e:
            print(f"Error clicking next: {e}")
            return False

        time.sleep(10)
        return True

    def _check_for_errors(self):
        """Check for error banner and handle it"""
        try:
            error_button = self.driver.find_element(
                By.CSS_SELECTOR,
                "button[data-automation-id='errorBanner']"
            )
            print("Errors found on page. Please resolve manually. You have 60 seconds.")
            time.sleep(60)
        except:
            print("No errors found")

    def click_apply(self):
        """Click the initial apply button"""
        try:
            apply_button = self.web_handler.find_element_safely(
                By.CSS_SELECTOR,
                "a[role='button'][data-uxi-element-id='Apply_adventureButton']"
            )
            if apply_button:
                apply_button.click()
                time.sleep(2)
            return True
        except Exception as e:
            print(f"No Apply button found: {e}")
            return False

    def check_already_applied(self):
        """Check if already applied to this position"""
        try:
            already_applied = self.web_handler.find_element_safely(
                By.CSS_SELECTOR,
                "[data-automation-id='alreadyApplied']"
            )
            return bool(already_applied)
        except:
            return False

    def click_autofill_resume(self):
        """Click the autofill with resume button"""
        try:
            button = self.web_handler.find_element_safely(
                By.CSS_SELECTOR,
                "a[role='button'][data-automation-id='autofillWithResume']"
            )
            if button:
                button.click()
                time.sleep(2)
            return True
        except Exception as e:
            print(f"No autofill resume button found: {e}")
            return False

    def check_verification_needed(self):
        """Check if verification is needed"""
        p_tags = self.web_handler.find_elements_safely(
            By.XPATH,
            "//p[contains(text(), 'verify')]"
        )
        return len(p_tags) > 0