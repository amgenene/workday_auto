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

    def _signup(self):
        """Handle the signup process"""
        print("Signup")
        try:
            # Click signup button
            redirect = self.wait.until(
                EC.element_to_be_clickable(
                    By.XPATH,
                    "//button[text()='Sign Up' or text()='Create Account']",
                ),
            )
            if redirect:
                redirect.click()

            # Handle checkbox
            time.sleep(5)
            form = self.wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
            checkbox = form.find_element(By.XPATH, "//input[@type='checkbox']")
            checkbox.click()
            time.sleep(1)

            # Fill in credentials
            self._fill_signup_form()

        except Exception as e:
            print(f"Signup failed: {e}")
            self._signin()

    def _signin(self):
        """Handle the signin process"""
        print("Signin")
        try:
            # Click signin button
            signin_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Sign In']"))
            )
            if signin_button:
                signin_button.click()

            time.sleep(5)

            # Wait for form and fill credentials
            form = self.wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
            self._fill_signin_form()

        except Exception as e:
            print(f"Signin failed: {e}")

    def _fill_signup_form(self):
        """Fill the signup form"""
        try:
            # Fill email and password fields
            self.element_handler.fill_input(
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[type='text'][data-automation-id='email']"
                ),
                self.profile["email"],
            )

            self.element_handler.fill_input(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='password'][data-automation-id='password']",
                ),
                self.profile["password"],
            )

            self.element_handler.fill_input(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='password'][data-automation-id='verifyPassword']",
                ),
                self.profile["password"],
            )

            # Try to click create account button
            try:
                button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "div[role='button'][aria-label='Create Account'][data-automation-id='click_filter']",
                )
                button.click()
            except:
                button = self.wait.until(
                    EC.element_to_be_clickable(By.XPATH, "//button[@type='submit']")
                )
                self.driver.execute_script("arguments[0].click();", button)

            time.sleep(2)

        except Exception as e:
            print(f"Error filling signup form: {e}")
            raise

    def _fill_signin_form(self):
        """Fill the signin form"""
        try:
            # Fill email and password
            self.element_handler.fill_input(
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[type='text'][data-automation-id='email']"
                ),
                self.profile["email"],
            )

            self.element_handler.fill_input(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='password'][data-automation-id='password']",
                ),
                self.profile["password"],
            )

            # Click signin button
            button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "div[role='button'][aria-label='Sign In'][data-automation-id='click_filter']",
                    )
                )
            )
            time.sleep(1)
            button.click()

        except Exception as e:
            print(f"Error filling signin form: {e}")
            raise

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

            # Click apply button
            apply_button = self.element_handler.find_element_safely(
                By.CSS_SELECTOR,
                "a[role='button'][data-uxi-element-id='Apply_adventureButton']",
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
            existing_company = company in self.config.companies

            if existing_company:
                return self._signin()
            if self._check_already_applied():
                print("Already applied to this position")
                return False
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
            By.CSS_SELECTOR, "[data-automation-id='alreadyApplied']"
        )
        return bool(already_applied)

    def _click_next(self) -> bool:
        """Click the next/continue button"""
        try:
            button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[text()='Next' or text()='Continue' or text()='Submit']",
                    )
                )
            )
            button.click()
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Error clicking next: {e}")
            return False
