from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class WorkdayAuth:
    def __init__(self, driver, wait, web_element_handler, profile):
        self.driver = driver
        self.wait = wait
        self.web_handler = web_element_handler
        self.profile = profile

    def signup(self):
        """Handle the signup process"""
        print("Signup")
        try:
            # Click signup button
            redirect = self.web_handler.wait_for_clickable(
                By.XPATH,
                "//button[text()='Sign Up' or text()='Create Account']"
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
            self.signin()

    def signin(self):
        """Handle the signin process"""
        print("Signin")
        try:
            # Click signin button
            signin_button = self.web_handler.wait_for_clickable(
                By.XPATH,
                "//button[text()='Sign In']"
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
            self.web_handler.fill_input_field(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='text'][data-automation-id='email']"
                ),
                self.profile["email"]
            )

            self.web_handler.fill_input_field(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='password'][data-automation-id='password']"
                ),
                self.profile["password"]
            )

            self.web_handler.fill_input_field(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='password'][data-automation-id='verifyPassword']"
                ),
                self.profile["password"]
            )

            # Try to click create account button
            try:
                button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "div[role='button'][aria-label='Create Account'][data-automation-id='click_filter']"
                )
                button.click()
            except:
                button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
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
            self.web_handler.fill_input_field(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='text'][data-automation-id='email']"
                ),
                self.profile["email"]
            )

            self.web_handler.fill_input_field(
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[type='password'][data-automation-id='password']"
                ),
                self.profile["password"]
            )

            # Click signin button
            button = self.wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "div[role='button'][aria-label='Sign In'][data-automation-id='click_filter']"
                ))
            )
            time.sleep(1)
            button.click()

        except Exception as e:
            print(f"Error filling signin form: {e}")
            raise