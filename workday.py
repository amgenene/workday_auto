import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from config import Config
from datetime import datetime
from fuzzywuzzy import fuzz
import os
import re
from StopWords import StopWords
from sentence_transformers import SentenceTransformer, util
from operator import itemgetter
import sys

# Add the project root to the Python path to import from processing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from processing.learner import InteractionLearner
except ImportError:
    # Create a dummy learner if import fails
    class InteractionLearner:
        def __init__(self, *args, **kwargs):
            pass

        def record_failed_attempt(self, *args, **kwargs):
            pass

        def record_question_mapping(self, *args, **kwargs):
            pass

        def find_similar_question(self, *args, **kwargs):
            return None

        def generate_suggestions(self):
            return []

        def save_learning_data(self):
            pass


stopwords = StopWords()


class Workday:
    def __init__(self, url):
        self.url = url
        self.config = Config("./config/profile.yaml")
        self.profile = self.config.profile
        self.driver = webdriver.Chrome()  # You need to have chromedriver installed
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.maximize_window()
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # Initialize the advanced learning system
        try:
            from processing.learner import InteractionLearner

            self.learner = InteractionLearner(self.driver)
            print("Advanced learning system initialized")
        except ImportError as e:
            print(f"Unable to initialize advanced learning: {e}")

            # Fallback to dummy learner
            class DummyLearner:
                def __init__(self):
                    self.learned_questions = []  # Add missing property

                def start_observation(self, *args, **kwargs):
                    pass

                def end_observation(self):
                    pass

                def find_similar_question(self, *args, **kwargs):
                    return None

                def record_failed_attempt(self, *args, **kwargs):
                    pass

            self.learner = DummyLearner()

        # Modified data structure: list of tuples (keywords, action)
        self.questionsToActions = [
            (
                ["how did you hear about us"],
                self.handle_multiselect,
                "LinkedIn",
            ),
            (
                ["Country Phone Code"],
                self.handle_multiselect,
                "United States of America",
            ),
            (
                ["Country"],
                self.handle_multiselect,
                "United States of America",
            ),
            (["Are you legally eligible to work"], self.answer_dropdown, "Yes"),
            (
                [
                    "Do you now or will you in the future require sponsorship for a work visa"
                ],
                self.answer_dropdown,
                "No",
            ),
            (
                ["have you previously been employed", "have you ever worked for"],
                self.select_radio,
                "No",
            ),
            (
                ["first name"],
                self.fill_input,
                self.profile["first_name"],
            ),
            (["last name"], self.fill_input, self.profile["family_name"]),
            (["email"], self.fill_input, self.profile["email"]),
            (["address line 1"], self.fill_input, self.profile["address_line_1"]),
            (["city"], self.fill_input, self.profile["address_city"]),
            (["state"], self.answer_dropdown, ["NY", "New York"]),
            (["postal Code"], self.fill_input, self.profile["address_postal_code"]),
            (["phone device type"], self.answer_dropdown, "Mobile"),
            (["phone number"], self.fill_input, self.profile["phone_number"]),
            (["are you legally authorized"], self.select_radio, "Yes"),
            (["will you now or in the future"], self.answer_dropdown, "No"),
            (["Are you at least 18 years of age?"], self.answer_dropdown, "Yes"),
            (
                [
                    "Do you have an agreement or contract such as a non-disclosure or non-competitive agreement with another employer that might restrict your employment at"
                ],
                self.answer_dropdown,
                "No",
            ),
            (["do you require sponsorship"], self.answer_dropdown, "No"),
            (["disability status"], self.select_radio, "I don't wish to answer"),
            (["veteran status"], self.answer_dropdown, "I am not"),
            (["gender"], self.answer_dropdown, "Male"),
            (
                ["ethnicity"],
                self.answer_dropdown,
                "Black or African American (United States of America)",
            ),
            (
                ["What is your race"],
                self.answer_dropdown,
                "Black or African American (United States of America)",
            ),
            (["hispanic or latino"], self.select_radio, "No"),
            (["date"], self.handle_date, None),
            (
                ["Please check one of the boxes below: "],
                self.select_radio,
                "No, I do not have a disability",
            ),
            (
                ["I understand and acknowledge the terms of use"],
                self.select_checkbox,
                None,
            ),
        ]

    def select_checkbox(self, element, data_automation_id):
        radio_button = element.find_element(By.CSS_SELECTOR, f'input[type="checkbox"]')
        self.wait.until(EC.element_to_be_clickable(radio_button))

        # Click the checkbox
        try:
            radio_button.click()
        except:
            # Try JavaScript click if normal click fails
            self.driver.execute_script("arguments[0].click();", radio_button)

        # Wait for checkbox state to update
        self._wait_for_element_stability(element)

        # Verify the checkbox was clicked successfully
        try:
            is_checked = radio_button.is_selected()
            print(f"Checkbox is {'checked' if is_checked else 'not checked'}")
        except:
            # If we can't verify, continue anyway
            pass

    def handle_date(self, element, _):
        try:
            month_input = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "div[data-automation-id='dateSectionMonth-display']",
                    )
                )
            )
            day_input = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "div[data-automation-id='dateSectionDay-display']",
                    )
                )
            )
            year_input = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "div[data-automation-id='dateSectionYear-display']",
                    )
                )
            )
            month_input.send_keys(datetime.now().strftime("%m"))
            day_input.send_keys(datetime.now().strftime("%d"))
            year_input.send_keys(datetime.now().strftime("%Y"))
        except Exception as e:
            print("Exception: 'No date input'", e)
        return True

    def signup(self):
        print("Signup")
        try:
            redirect = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[text()='Sign Up' or text()='Create Account']",
                    )
                )
            )
            redirect.click()
        except Exception as e:
            print("Exception: 'No button for Sigup'")
        try:
            time.sleep(5)
            form = self.wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
            checkbox = form.find_element(By.XPATH, "//input[@type='checkbox']")
            print("here")
            checkbox.click()
            time.sleep(1)
        except Exception as e:
            print(f"Error: {str(e)}")
        try:
            time.sleep(2)
            self.driver.find_element(
                By.CSS_SELECTOR, "input[type='text'][data-automation-id='email']"
            ).send_keys(self.profile["email"])
            self.driver.find_element(
                By.CSS_SELECTOR, "input[type='password'][data-automation-id='password']"
            ).send_keys(self.profile["password"])
            self.driver.find_element(
                By.CSS_SELECTOR,
                "input[type='password'][data-automation-id='verifyPassword']",
            ).send_keys(self.profile["password"])
            try:
                button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "div[role='button'][aria-label='Create Account'][data-automation-id='click_filter']",
                )
                button.click()
                time.sleep(3)

                # Check for error messages about existing account
                try:
                    error_text = self.driver.find_element(
                        By.XPATH,
                        "//*[contains(text(), 'sign into this account') or contains(text(), 'already in use') or contains(text(), 'already exists')]",
                    )
                    if error_text:
                        print("Account already exists, switching to sign in...")
                        # Look for sign in link/button
                        sign_in_btn = self.driver.find_element(
                            By.XPATH,
                            "//a[contains(text(), 'Sign In')] | //button[contains(text(), 'Sign In')]",
                        )
                        sign_in_btn.click()
                        time.sleep(2)
                        self.signin()
                        return
                except Exception as error_check_e:
                    print(
                        "No error message about existing account found, continuing with signup"
                    )

            except Exception as e:
                print("Exception: 'No button for Create Account'", e)
                button1 = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                print(button1.is_displayed())  # Check if button is visible
                print(button1.is_enabled())  # Check if button is clickable
                self.driver.execute_script("arguments[0].click();", button1)

                # Also check for error messages here
                time.sleep(3)
                try:
                    error_text = self.driver.find_element(
                        By.XPATH,
                        "//*[contains(text(), 'sign into this account') or contains(text(), 'already in use') or contains(text(), 'already exists')]",
                    )
                    if error_text:
                        print("Account already exists, switching to sign in...")
                        # Look for sign in link/button
                        sign_in_btn = self.driver.find_element(
                            By.XPATH,
                            "//a[contains(text(), 'Sign In')] | //button[contains(text(), 'Sign In')]",
                        )
                        sign_in_btn.click()
                        time.sleep(2)
                        self.signin()
                        return
                except Exception as error_check_e:
                    print(
                        "No error message about existing account found, continuing with signup"
                    )

            time.sleep(2)
        except Exception as e:
            print("Exception: 'Signup failed'", e)
            self.signin()

    def signin(self):
        print("Signin")
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Sign In']"))
            )
            self.driver.find_element(By.XPATH, "//button[text()='Sign In']").click()
        except Exception as e:
            print("Exception: 'No button for Sigin'")
        time.sleep(5)
        try:
            form = self.wait.until(EC.presence_of_element_located((By.XPATH, "//form")))
        except Exception as e:
            print(f"Error form error: {str(e)}")
        try:
            time.sleep(2)
            self.driver.find_element(
                By.CSS_SELECTOR, "input[type='text'][data-automation-id='email']"
            ).send_keys(self.profile["email"])
            self.driver.find_element(
                By.CSS_SELECTOR, "input[type='password'][data-automation-id='password']"
            ).send_keys(self.profile["password"])
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
            print("Exception: 'Signin failed'", e)

    def _wait_for_element_stability(self, element, timeout=8, poll_frequency=0.2):
        """
        Wait for an element to become stable (not changing) before proceeding

        Args:
            element: WebElement - The element to monitor
            timeout: int - Maximum time to wait in seconds
            poll_frequency: float - How often to check for stability

        Returns:
            bool: True if element became stable, False if timed out
        """
        try:
            start_time = time.time()
            last_html = ""
            stable_count = 0
            required_stable_checks = (
                5  # Increased number of consecutive stable checks required
            )

            # Wait for page to finish any JavaScript executions first
            self._wait_for_page_load(timeout=3)

            # Get parent element to watch for changes in a wider context
            try:
                # Try to get a wider context by going up several levels
                parent = element.find_element(
                    By.XPATH,
                    "./ancestor::div[contains(@class, 'container') or contains(@class, 'section') or contains(@class, 'page')][1]",
                )
            except:
                try:
                    # Fallback to just parent div
                    parent = element.find_element(
                        By.XPATH, "./ancestor::div[position()=3]"
                    )
                except:
                    parent = element  # Final fallback to watching the element itself

            print(f"Waiting for element stability (timeout: {timeout}s)...")
            while time.time() - start_time < timeout:
                try:
                    # Check that element is still attached to DOM and visible
                    if not element.is_displayed():
                        print(
                            "Element is no longer displayed, resetting stability count"
                        )
                        stable_count = 0

                    # Get current state to compare
                    current_html = parent.get_attribute("outerHTML")

                    if current_html == last_html:
                        stable_count += 1
                        if stable_count >= required_stable_checks:
                            print(
                                "Element is stable after",
                                round(time.time() - start_time, 2),
                                "seconds",
                            )
                            return True
                    else:
                        stable_count = 0  # Reset if content changed

                    last_html = current_html

                except Exception as inner_e:
                    print(f"Error during stability check: {inner_e}")
                    stable_count = 0  # Reset on errors

                time.sleep(poll_frequency)

            print(
                f"Element did not fully stabilize within {timeout} seconds, proceeding anyway"
            )
            # Even if we didn't reach full stability, give it a little more time
            time.sleep(2)
            return True  # Return true anyway to avoid blocking the process

        except Exception as e:
            print(f"Error monitoring element stability: {e}")
            # If we can't monitor stability, better to wait a fixed time than to fail
            time.sleep(3)  # Increased fixed wait time
            return False

    def _detect_element_type(self, element):
        """
        Detect the type of form element to determine appropriate action

        Args:
            element: WebElement - The element to classify

        Returns:
            str: The element type (text, dropdown, radio, checkbox, multiselect, date, unknown)
        """
        try:
            tag_name = element.tag_name.lower()
            element_type = "unknown"

            # Check for various attributes to determine type
            if tag_name == "input":
                input_type = element.get_attribute("type")
                if input_type in ["text", "email", "tel", "number", "password"]:
                    element_type = "text"
                elif input_type == "radio":
                    element_type = "radio"
                elif input_type == "checkbox":
                    element_type = "checkbox"
            elif tag_name == "select":
                element_type = "dropdown"
            elif tag_name == "div":
                # Check for attributes common in Workday's custom elements
                automation_id = element.get_attribute("data-automation-id") or ""
                role = element.get_attribute("role") or ""
                aria_controls = element.get_attribute("aria-controls") or ""

                if "dropdown" in automation_id.lower() or role == "combobox":
                    element_type = "dropdown"
                elif "multiselect" in automation_id.lower():
                    element_type = "multiselect"
                elif "date" in automation_id.lower():
                    element_type = "date"
                elif "radio" in automation_id.lower() or role == "radiogroup":
                    element_type = "radio"
                elif "checkbox" in automation_id.lower():
                    element_type = "checkbox"
                # For Workday's custom dropdown/select elements
                elif role == "button" and "listbox" in aria_controls:
                    element_type = "dropdown"

            # Check for nearby elements that might indicate type
            try:
                # Check for radio inputs nearby
                radio_inputs = element.find_elements(
                    By.XPATH, ".//input[@type='radio']"
                )
                if radio_inputs:
                    element_type = "radio"

                # Check for checkbox inputs nearby
                checkbox_inputs = element.find_elements(
                    By.XPATH, ".//input[@type='checkbox']"
                )
                if checkbox_inputs:
                    element_type = "checkbox"
            except:
                pass

            return element_type
        except Exception as e:
            print(f"Error detecting element type: {e}")
            return "unknown"

    def find_next_sibling_safely(self, start_element, parent, max_levels=5):
        """
        Safely navigate up the DOM tree and find the next sibling div,
        checking for elements at each level before proceeding.

        Args:
            start_element: WebElement - The starting element
            max_levels: int - Maximum number of levels to traverse up

        Returns:
            tuple: (WebElement or None, int) - Found element and levels traversed
        """
        try:
            current = start_element
            for level in range(max_levels):
                print(f"Current level: {current.tag_name, current.text}")
                # First check if there's a sibling at current level
                siblings = current.find_elements(
                    By.XPATH,
                    "./following-sibling::div//*[@data-automation-id][position()=1]",
                )
                if siblings:
                    print(f"Found sibling at level {level}")
                    return siblings[0], level, False
                print("HEREE1")
                if not siblings:
                    print("HEREE")
                    siblings = current.find_elements(
                        By.XPATH, "./following-sibling::div//*[@id][position()=1]"
                    )
                    if siblings:
                        print(
                            f"Found sibling at level {level} sibling container: {siblings[0].tag_name, siblings[0].text}"
                        )
                        return siblings[0], level, True
                # If no siblings, try to go up one level
                try:
                    # Verify we actually moved up (parent should be different from current)
                    if parent.data_automation_id == current.data_automation_id:
                        print(f"Reached same element at level {level}, stopping")
                        return None, level, False
                except:
                    print(f"didn't find parent at level: {level} Continue")
                current = current.find_element(By.XPATH, "./..")
            return None, max_levels, False

        except Exception as e:
            print(f"Error in safe navigation: {e}")
            return None, 0, False

    def fillform_page_1(self):
        try:
            self.driver.find_element(
                By.CSS_SELECTOR, "input[data-automation-id='file-upload-input-ref']"
            ).send_keys(self.profile["resume_path"])
            time.sleep(1)
        except Exception as e:
            print("Exception: 'Missmatch in order'", e)
            return False
        return True

    def handle_questions(self, step):
        # Ensure page is fully loaded before searching for fields
        time.sleep(2)
        self._wait_for_page_load()

        # Find required fields using the asterisk marker
        required_fields = self.driver.find_elements(By.XPATH, "//abbr[text()='*']")
        print(f"\nFound {len(required_fields)} required fields")

        # Additional wait to ensure all elements are stable
        time.sleep(1)

        questions = []
        handled_questions = (
            []
        )  # Keep track of which questions were successfully handled

        # Process all required fields (including the first one, which was previously skipped)
        for field in required_fields:
            # Wrap entire field processing in try-except to continue if one field fails
            try:
                # Get the parent span containing the question text
                question = field.find_element(By.XPATH, "./..")
                question_text = question.text

                # Clean up the question text
                if not question_text:
                    continue

                # Remove asterisks and clean up whitespace
                question_text = question_text.replace("*", "").strip()

                # Skip very short text which is likely not a question
                if len(question_text) < 3:
                    continue
                # Get the parent div that would contain both question and input area
                parent = question.find_element(
                    By.XPATH, "./ancestor::div[@data-automation-id][position()=1]"
                )
                print(
                    f"Parent automation-id: {parent.get_attribute('data-automation-id')}"
                )
                # Before trying to find the input container, make sure the DOM has stabilized
                self._wait_for_element_stability(parent)

                # Question's input container - find the related field for this question
                container, levels_traversed, is_id = self.find_next_sibling_safely(
                    question, parent
                )

                # Skip if we couldn't find the input container
                if not container:
                    print(
                        f"Could not find input container for question: {question_text}"
                    )
                    continue

                print("Question tag name:", question.tag_name, "Text:", question.text)
                print(
                    "Container tag name:",
                    container.tag_name,
                    "Text:",
                    container.text,
                    "Type:",
                    container.get_attribute("type"),
                )

                # Get the automation ID to uniquely identify this element
                automation_id = (
                    container.get_attribute("data-automation-id")
                    if not is_id
                    else container.get_attribute("id")
                )

                # Skip if we couldn't find an automation ID or another identifier
                if not automation_id:
                    print(f"No automation ID found for question: {question_text}")
                    continue
                print(f"\nQuestion: {question_text}")
                print(f"Element automation-id: {automation_id}")
                questions.append((question_text, container, automation_id))
            except Exception as e:
                print(f"Error processing field: {e}")
                continue

        keyword_embeddings = []
        similarity_scores = []
        embeddingsToActions = {}
        # Initialize embeddingsToActions, and get keyword embeddings
        for keywords, action, value in self.questionsToActions:
            keyword_embedding = self.model.encode(keywords, convert_to_tensor=True)
            keyword_embeddings.append(keyword_embedding)
            embeddingsToActions[keyword_embedding] = (action, value)

        for question_text, input_element, automation_id in questions:
            try:
                handled = False
                best_match_score = 0
                best_match_action = None
                best_match_value = None

                # First try exact text matching (case insensitive) as it's more reliable
                question_lower = question_text.lower().strip()
                exact_match_found = False

                # Try to find exact matches first
                for keywords, action, value in self.questionsToActions:
                    for keyword in keywords:
                        if keyword.lower().strip() == question_lower:
                            print(f"EXACT MATCH found for question: '{question_text}'")
                            best_match_action = action
                            best_match_value = value
                            best_match_score = 1.0
                            exact_match_found = True
                            break
                    if exact_match_found:
                        break

                # If exact match wasn't found, try embedding similarity
                if not exact_match_found:
                    print(
                        f"No exact match for '{question_text}', trying semantic matching..."
                    )

                    # Encode the current question
                    question_embedding = self.model.encode(
                        question_text, convert_to_tensor=True
                    )

                    # Calculate similarity scores
                    similarity_scores = [
                        (
                            float(
                                util.pytorch_cos_sim(
                                    question_embedding, keyword_embedding
                                ).mean()
                            ),
                            keyword_embedding,
                        )
                        for keyword_embedding in keyword_embeddings
                    ]

                    # Get the best match
                    max_score, keyword_embedding = max(
                        similarity_scores, key=itemgetter(0)
                    )
                    print(
                        f"Best semantic match score: {max_score:.4f} for '{question_text}'"
                    )
                    print(f"Matched to: {embeddingsToActions[keyword_embedding]}")

                    best_match_score = max_score
                    best_match_action = embeddingsToActions[keyword_embedding][0]
                    best_match_value = embeddingsToActions[keyword_embedding][1]

                # Lower the threshold slightly to handle more questions
                if (
                    best_match_score > 0.55
                ):  # Adjusted threshold for what counts as a "match"
                    print(
                        f"Executing action for question: {question_text} with best match score of: {best_match_score}, {best_match_value}"
                    )
                    action_result = (
                        best_match_action(
                            input_element, automation_id, values=best_match_value
                        )
                        if best_match_value is not None
                        else best_match_action(input_element, automation_id)
                    )
                    time.sleep(3)  # Reduced wait time for better performance
                    if action_result:
                        print(f"Action successful: {best_match_action}")
                        # Track this question as handled
                        handled_questions.append(
                            (
                                question_text,
                                best_match_action.__name__,
                                best_match_value,
                            )
                        )
                    else:
                        print(f"Action failed: {best_match_action}")
                    handled = True
                # Secondary threshold for "likely" matches
                elif best_match_score > 0.4 and step != 4:
                    print(
                        f"Possible match for question: {question_text} with score: {best_match_score}, {best_match_value}"
                    )
                    print("Trying best guess match...")
                    action_result = (
                        best_match_action(
                            input_element, automation_id, values=best_match_value
                        )
                        if best_match_value is not None
                        else best_match_action(input_element, automation_id)
                    )
                    if action_result:
                        print(f"Action successful: {best_match_action}")
                        # Track this question as handled
                        handled_questions.append(
                            (
                                question_text,
                                best_match_action.__name__,
                                best_match_value,
                            )
                        )
                        handled = True
                    else:
                        print(f"Action failed: {best_match_action}")

                # Fallback for common Yes/No questions on the later pages
                if not handled and step == 4:
                    print(f"Using fallback handling for question: {question_text}")
                    action_result = self.answer_dropdown(
                        input_element, automation_id, values="unknown"
                    )
                    if action_result:
                        print(f"Fallback action successful for: {question_text}")
                        handled_questions.append(
                            (question_text, "answer_dropdown_fallback", "unknown")
                        )
                        handled = True

                # Check if we have any learned mappings for this question
                if not handled:
                    learned_mapping = self.learner.find_similar_question(question_text)
                    if learned_mapping:
                        print(f"Found learned mapping for question: '{question_text}'")
                        print(
                            f"  • This was previously answered as: '{learned_mapping.get('value', '')}'"
                        )
                        print(
                            f"  • Element type: {learned_mapping.get('element_type', 'unknown')}"
                        )
                        print(
                            f"  • Action type: {learned_mapping.get('action_type', 'unknown')}"
                        )

                        # Determine the action based on the action type recorded
                        action_name = learned_mapping.get(
                            "action_type", "unknown_action"
                        )
                        value = learned_mapping.get("value", "")

                        # Map the action name to the actual method
                        action_method = None
                        if action_name == "fill_input":
                            action_method = self.fill_input
                        elif action_name in ["select_radio", "radio"]:
                            action_method = self.select_radio
                        elif action_name in ["answer_dropdown", "dropdown"]:
                            action_method = self.answer_dropdown
                        elif action_name in ["handle_multiselect", "multiselect"]:
                            action_method = self.handle_multiselect
                        elif action_name in ["select_checkbox", "checkbox"]:
                            action_method = self.select_checkbox

                        if action_method:
                            print(
                                f"Applying learned action: {action_name} with value: '{value}'"
                            )

                            # Scroll element into view
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                input_element,
                            )

                            try:
                                # Briefly highlight the element to show we're working on it
                                original_style = (
                                    self.driver.execute_script(
                                        "return arguments[0].getAttribute('style');",
                                        input_element,
                                    )
                                    or ""
                                )
                                self.driver.execute_script(
                                    "arguments[0].setAttribute('style', arguments[1] + '; border: 3px solid green; background-color: lightgreen !important; transition: all 0.5s;');",
                                    input_element,
                                    original_style,
                                )

                                # Brief pause to show highlight
                                time.sleep(0.3)

                                # Apply the learned action
                                result = action_method(
                                    input_element, automation_id, value
                                )

                                # Restore original style
                                self.driver.execute_script(
                                    "arguments[0].setAttribute('style', arguments[1]);",
                                    input_element,
                                    original_style,
                                )

                                if result:
                                    print(f"✅ Successfully applied learned action")
                                    handled_questions.append(
                                        (question_text, action_name, value)
                                    )
                                    handled = True
                                else:
                                    print(f"❌ Failed to apply learned action")
                                    self.learner.record_failed_attempt(
                                        question_text, action_name, "Execution failed"
                                    )
                            except Exception as e:
                                print(f"Error applying learned action: {e}")
                                # Restore style if there was an error
                                try:
                                    self.driver.execute_script(
                                        "arguments[0].setAttribute('style', arguments[1]);",
                                        input_element,
                                        original_style,
                                    )
                                except:
                                    pass

                                self.learner.record_failed_attempt(
                                    question_text, action_name, str(e)
                                )

                if not handled:
                    print(
                        f"No matching action found for question: {question_text}. Please fill manually"
                    )

                    # Record that we couldn't handle this question
                    self.learner.record_failed_attempt(
                        question_text, "unknown", "No matching action found"
                    )

                    # Activate learning mode
                    element_type = self._detect_element_type(input_element)
                    print(f"Detected element type: {element_type}")

                    # Start real-time observation
                    self.learner.start_observation(
                        input_element, question_text, element_type
                    )

                    # Scroll to ensure element is visible
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        input_element,
                    )

                    # Highlight the element to make it easier for the user to see
                    original_style = (
                        self.driver.execute_script(
                            "return arguments[0].getAttribute('style');", input_element
                        )
                        or ""
                    )
                    self.driver.execute_script(
                        "arguments[0].setAttribute('style', arguments[1] + '; border: 3px solid red; background-color: lightyellow !important; padding: 3px;');",
                        input_element,
                        original_style,
                    )

                    # Wait for user to interact with the element
                    print(
                        "\nPlease manually fill out this field. Press Enter AFTER you've completed your interaction."
                    )
                    input("\n[Press Enter when you've completed the interaction]")

                    # Restore original style
                    self.driver.execute_script(
                        "arguments[0].setAttribute('style', arguments[1]);",
                        input_element,
                        original_style,
                    )

                    # End observation and analyze changes
                    self.learner.end_observation()

                    # Verify the field was filled
                    print("Checking if field was successfully filled...")

                    # Basic verification (may need enhancement for specific element types)
                    try:
                        if element_type == "text_input":
                            value = input_element.get_attribute("value")
                            if value:
                                print(f"Field filled with: '{value}'")
                            else:
                                print(
                                    "Field appears to be empty. Did you fill it correctly?"
                                )
                                input(
                                    "Press Enter to continue anyway, or Ctrl+C to interrupt."
                                )
                        elif element_type in ["checkbox", "radio"]:
                            checked = input_element.is_selected()
                            print(f"Checkbox/Radio selected: {checked}")
                    except:
                        print("Unable to verify field completion, continuing anyway")
            except Exception as question_error:
                print(f"Error processing question: {question_error}")
                print("Continuing with next question...")
        # Summarize what happened with all questions
        try:
            # Simplify handling check to just count how many items are in handled_questions
            handled_count = len(handled_questions)
            print(f"\n===== Question Processing Summary =====")
            print(f"Found {len(questions)} questions, processed {handled_count}")

            # Display all handled questions first
            print("\n--- Handled Questions: ---")
            for q_text, action_name, value in handled_questions:
                print(
                    f"✅ HANDLED | Action: {action_name} | Q: '{q_text}' | Value: '{value}'"
                )

            # Then show all questions with their status
            print("\n--- All Questions Found: ---")
            for q, i, aid in questions:
                try:
                    # Simple string search in handled_questions
                    matched = False
                    for handled_q, _, _ in handled_questions:
                        # Compare with exact string match
                        if q == handled_q:
                            matched = True
                            break

                    status = "✅ HANDLED" if matched else "❌ NOT HANDLED"
                    print(f"{status} | Q: '{q}' -> automation-id: {aid}")
                except Exception as q_error:
                    print(f"Error displaying question: {q_error}")

            # If any questions might not have been handled, show an informational note
            not_handled_count = len(questions)
            for question_tuple in questions:
                q = question_tuple[0]  # Get the question text from the tuple
                for handled_q, _, _ in handled_questions:
                    if q == handled_q:
                        not_handled_count -= 1
                        break

            if not_handled_count > 0:
                print(f"\n⚠️ INFO: {not_handled_count} questions may need manual review")
                print(
                    "These questions might need manual filling or improved question matching."
                )
        except Exception as summary_error:
            print(f"Error generating summary: {summary_error}")
            print(
                f"Found {len(questions)} questions, processed all of them with some possible errors."
            )

        input("\nPress Enter to continue after reviewing the questions...")
        return True

    def _check_if_job_closed_or_error(self):
        """Check if the current page indicates the job is closed or no longer available"""
        try:
            # Common error messages suggesting the job is closed
            job_closed_messages = [
                "//div[contains(text(), 'no longer accepting applications')]",
                "//div[contains(text(), 'position has been filled')]",
                "//div[contains(text(), 'job posting has closed')]",
                "//div[contains(text(), 'position is no longer available')]",
                "//p[contains(text(), 'no longer accepting')]",
                "//div[contains(text(), 'has been removed')]",
            ]

            # Check for any of these messages
            for message_xpath in job_closed_messages:
                elements = self.driver.find_elements(By.XPATH, message_xpath)
                if elements:
                    print(f"⚠️ JOB POSTING CLOSED: {elements[0].text}")
                    print("The job is no longer accepting applications.")
                    raise Exception("Job posting closed during application process")

            # Also check the page text for indicators
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            closed_phrases = [
                "no longer accepting",
                "position filled",
                "job closed",
                "posting closed",
                "position unavailable",
                "job has been removed",
                "requisition closed",
            ]

            for phrase in closed_phrases:
                if phrase in page_text:
                    print(
                        f"⚠️ JOB POSTING LIKELY CLOSED: Found phrase '{phrase}' on page after clicking Next"
                    )
                    print("This job appears to no longer be accepting applications.")
                    raise Exception("Job posting closed during application process")

        except Exception as e:
            if "Job posting closed" in str(e):
                raise e  # Re-raise the job closed exception
            # Ignore other errors, let the application continue

    def click_next(self):
        """Click the Next/Continue button to proceed to the next page"""
        try:
            # Look specifically for navigation buttons (not Submit)
            button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[text()='Next' or text()='Continue' or text()='Save and Continue']",
                    )
                )
            )
            print(f"Clicking navigation button: '{button.text}'")
            button.click()

            # Wait for page transition
            self._wait_for_page_load()

            # Check for job posting closed messages after clicking next
            self._check_if_job_closed_or_error()

        except Exception as e:
            print(f"Exception: 'No button for Next/Continue': {e}")

        # Check for errors after clicking
        try:
            error_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[data-automation-id='errorBanner']"
            )

            # Check specifically for job posting closed errors in the error banner
            error_text = error_button.text.lower()
            if any(
                phrase in error_text
                for phrase in [
                    "no longer",
                    "position filled",
                    "job closed",
                    "posting closed",
                ]
            ):
                print(
                    "⚠️ ERROR: The job posting appears to have closed during the application process."
                )
                print("This job is no longer accepting applications.")
                raise Exception("Job posting closed during application process")

            print(
                "Exception: 'Errors on page. Please resolve and submit manually. You have 60 seconds to do so!'"
            )
            time.sleep(60)
        except:
            print("No errors detected on page")

    def check_for_submit_button(self):
        """Check if there's a submit button on the page and return True if found"""
        try:
            submit_button = self.driver.find_element(
                By.XPATH,
                "//button[text()='Submit' or text()='Review and Submit' or contains(text(), 'Submit')]",
            )
            return True
        except:
            return False

    def submit_application(self):
        """Click the final submit button to complete the application"""
        try:
            submit_button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[text()='Submit' or text()='Review and Submit' or contains(text(), 'Submit')]",
                    )
                )
            )
            print(f"Clicking submit button: '{submit_button.text}'")
            submit_button.click()

            # Wait for confirmation page
            self._wait_for_page_load()

            # Look for confirmation messages
            try:
                confirmation = self.driver.find_element(
                    By.XPATH,
                    "//*[contains(text(), 'submitted') or contains(text(), 'thank you') or contains(text(), 'confirmation')]",
                )
                print("Application submitted successfully!")
                print(f"Confirmation message: {confirmation.text}")
            except:
                print("No confirmation message found, but submission appears complete")

            return True
        except Exception as e:
            print(f"Error submitting application: {e}")
            return False

    def _wait_for_page_load(self, timeout=10):
        """Wait for page to load completely after navigation"""
        try:
            # Wait for document ready state
            start_time = time.time()
            while time.time() - start_time < timeout:
                page_state = self.driver.execute_script("return document.readyState;")
                if page_state == "complete":
                    # Additional wait for any AJAX operations
                    time.sleep(2)
                    return True
                time.sleep(0.5)
            print("Page did not reach 'complete' state within timeout")
            return False
        except Exception as e:
            print(f"Error waiting for page load: {e}")
            # Fallback to fixed wait
            time.sleep(5)
            return False

    def apply(self):
        try:
            parsed_url = urlparse(self.url)
            print("parsed_url:", parsed_url)
            company = parsed_url.netloc.split(".")[0]
            existing_company = company in self.config.read_companies()
            print("company subdomain:", company)
            self.driver.get(self.url)  # Open a webpage
            time.sleep(4)

            # First check if job is no longer available
            try:
                # Look for common messages indicating the job posting is closed
                job_closed_messages = [
                    "//div[contains(text(), 'no longer accepting applications')]",
                    "//div[contains(text(), 'position has been filled')]",
                    "//div[contains(text(), 'This job is closed')]",
                    "//div[contains(text(), 'job posting has closed')]",
                    "//div[contains(text(), 'job posting has been removed')]",
                    "//div[contains(text(), 'position is no longer available')]",
                    "//div[contains(text(), 'job requisition has been closed')]",
                    "//p[contains(text(), 'no longer accepting applications')]",
                ]

                # Check for any of these messages
                for message_xpath in job_closed_messages:
                    elements = self.driver.find_elements(By.XPATH, message_xpath)
                    if elements:
                        print(f"⚠️ JOB POSTING CLOSED: {elements[0].text}")
                        print("This job is no longer accepting applications.")
                        return False

                # Also check the page text for indicators
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                closed_phrases = [
                    "no longer accepting",
                    "position filled",
                    "job closed",
                    "posting closed",
                    "position unavailable",
                ]
                for phrase in closed_phrases:
                    if phrase in page_text:
                        print(
                            f"⚠️ JOB POSTING LIKELY CLOSED: Found phrase '{phrase}' on page"
                        )
                        print(
                            "This job appears to no longer be accepting applications."
                        )
                        return False

            except Exception as e:
                # If error checking, continue with the application process
                print(f"Error checking if job is closed: {e}")

            # Try to click the Apply button
            try:
                apply_button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "a[role='button'][data-uxi-element-id='Apply_adventureButton']",
                )
                apply_button.click()
                time.sleep(2)
            except Exception as e:
                print("No Apply button found, checking if job might be closed...", e)

                # Additional check - if no Apply button is found, do a more thorough check
                try:
                    # Check if any job-closed indicators are present
                    page_text = self.driver.find_element(
                        By.TAG_NAME, "body"
                    ).text.lower()
                    closed_phrases = [
                        "no longer accepting",
                        "position filled",
                        "job closed",
                        "posting closed",
                        "position unavailable",
                        "removed",
                    ]
                    for phrase in closed_phrases:
                        if phrase in page_text:
                            print(
                                f"⚠️ JOB POSTING LIKELY CLOSED: Found phrase '{phrase}' on page and no Apply button"
                            )
                            print(
                                "This job appears to no longer be accepting applications."
                            )
                            return False

                    print(
                        "No Apply button found, but job doesn't appear to be closed. Continuing..."
                    )
                except:
                    pass

            try:
                already_applied = self.driver.find_element(
                    By.CSS_SELECTOR, "[data-automation-id='alreadyApplied']"
                )
                print("You have already applied to this job.")
                return True
            except Exception as e:
                print("No already applied message found, continuing...", e)
            # Try autofill with resume
            try:
                button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "a[role='button'][data-automation-id='autofillWithResume']",
                )
                button.click()
                time.sleep(2)
            except Exception as e:
                print("No autofill resume button found", e)

            print("existing_company:", existing_company)
            try:
                time.sleep(2)
                if existing_company:
                    self.signin()
                else:
                    self.signup()
                    self.config.write_company(company)
            except Exception as e:
                print(f"Error logging in or creating acct: {e}")
                input("Press Enter when you're ready to continue...")

            time.sleep(6)
            p_tags = self.driver.find_elements(
                By.XPATH, "//p[contains(text(), 'verify')]"
            )
            if len(p_tags) > 0:
                print("Verification needed")
                input(
                    "Please verify your account and press Enter when you're ready to continue..."
                )
            step1 = self.fillform_page_1()
            if not step1:
                input("Press Enter when you're ready to continue with page 1...")
            self.click_next()
            try:
                current_page = 2
                max_pages = 20  # Increased max pages as a safety limit

                # Loop until we find a submit button or reach max pages
                while current_page <= max_pages:
                    print(f"\n--- Processing Page {current_page} ---")

                    # Check if we've reached the submission page
                    if self.check_for_submit_button():
                        print("Found submit button - final page reached!")
                        print(
                            "Immediately submitting without processing additional fields..."
                        )

                        # Submit the application immediately without processing questions
                        print("Submitting application...")
                        submit_result = self.submit_application()

                        if submit_result:
                            print("🎉 Application submitted successfully! 🎉")
                        else:
                            print("⚠️ There may have been an issue with submission")
                            input(
                                "Please check the application status and press Enter to continue..."
                            )

                        break  # Exit the page processing loop

                    # Handle the current page
                    try:
                        # Before processing, check if job posting is still open
                        self._check_if_job_closed_or_error()

                        if current_page == 3:
                            # Some workday forms have a page that just displays resume info
                            print(
                                "Resume information page detected, skipping processing"
                            )
                            success = True
                        else:
                            success = self.handle_questions(current_page)

                        if success:
                            print(f"Successfully completed page {current_page}")
                            self.click_next()  # This also checks for job closed status
                            # Wait additional time for page transition
                            self._wait_for_page_load()
                            current_page += 1
                        else:
                            print(
                                f"Issues on page {current_page}, waiting for manual intervention"
                            )
                            input(
                                "Press Enter when you've fixed the issues and are ready to continue..."
                            )
                            self.click_next()
                            current_page += 1
                    except Exception as e:
                        # Check specifically for job closed exception
                        if "Job posting closed" in str(e):
                            print(
                                "⚠️ Job posting is no longer available. Moving to next job in list."
                            )
                            # Exit the page processing loop and move to the next job
                            break

                        print(f"Exception on page {current_page}: {e}")
                        input(
                            "Press Enter when you've fixed the issues and are ready to continue..."
                        )
                        try:
                            self.click_next()
                            current_page += 1
                        except Exception as next_err:
                            # Check if this is a job closed error
                            if "Job posting closed" in str(next_err):
                                print(
                                    "⚠️ Job posting is no longer available. Moving to next job in list."
                                )
                                # Exit the page processing loop and move to the next job
                                break

                            print(
                                "Unable to continue automatically. Please navigate to the next page manually."
                            )
                            input("Press Enter when you're on the next page...")
                            current_page += 1

                if current_page > max_pages:
                    print("Reached maximum page limit without finding a submit button.")
                    print("Please complete the remaining steps manually.")
                    input("Press Enter when you've finished the application...")

                print("Form completion finished")
                self.driver.quit()
            except Exception as e:
                print(f"Fatal error in form processing: {e}")
                self.driver.quit()
                return False
        except Exception as e:
            print(f"Error in early form processing: {e}")
            self.driver.quit()
            return False
        return True

    def handle_multiselect(self, element, _, values):
        """Handle multi-select dropdowns that require multiple clicks"""
        try:
            # Find the input element
            input_element = element.find_element(By.XPATH, "//div//input")

            # Send the text value
            input_element.send_keys(values)

            # Short pause to let the dropdown options populate
            time.sleep(0.5)

            # Press Enter to confirm selection
            from selenium.webdriver.common.keys import Keys

            input_element.send_keys(Keys.ENTER)

            # Wait for the selection to be confirmed
            self._wait_for_element_stability(element)

            # Verify the selection was successful (if possible)
            try:
                # Look for selected items or pills that indicate a successful selection
                selected_items = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'pill') or contains(@class, 'selected') or contains(@class, 'option')]",
                )
                if selected_items:
                    print(
                        f"Selection confirmed: Found {len(selected_items)} selected items"
                    )
            except:
                # If we can't verify, continue anyway
                pass

            return True
        except Exception as e:
            print(f"Error in handle_multiselect: {e}")
            # Try fallback method
            try:
                return self.answer_dropdown(element, _, values)
            except Exception as e:
                print(f"Error in using answer_dropdown fallback: {e}")
                return False

    def answer_dropdown(self, element, _, values=""):
        """Handle single-select dropdowns"""
        try:
            print("Value being selected:", values)

            # Click to open the dropdown (try multiple methods)
            try:
                # First try regular click
                element.click()
            except:
                # If regular click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", element)

            # Wait for dropdown to fully open and stabilize
            self._wait_for_element_stability(element)

            # Find all options with multiple selectors to be more robust
            try:
                options = self.driver.find_elements(
                    By.CSS_SELECTOR, "ul[role='listbox'] li[role='option'] div"
                )

                if not options:
                    options = self.driver.find_elements(
                        By.CSS_SELECTOR, "ul[role='listbox'] li[role='option']"
                    )

                if not options:
                    # Try another common pattern
                    options = self.driver.find_elements(
                        By.CSS_SELECTOR, "div[role='option']"
                    )

                if not options:
                    # Last resort, look for any items that appeared after clicking
                    options = self.driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class, 'dropdown') or contains(@class, 'select')]//li",
                    )
            except Exception as dropdown_error:
                print(f"Error finding dropdown options: {dropdown_error}")
                return False

            print(f"Found {len(options)} dropdown options")

            if len(options) == 0:
                print("No dropdown options found")
                return False

            if values == "unknown":
                # Just pick the first or last option as a fallback
                try:
                    self.driver.execute_script("arguments[0].click();", options[-1])
                    time.sleep(1)
                    print(f"Selected the last option as fallback")
                    return True
                except Exception as click_error:
                    print(f"Error clicking last option: {click_error}")
                    return False

            # For known values, try to find the best match
            best_match = None
            best_score = 0

            # Convert values to a list if it's not already
            value_list = values if isinstance(values, list) else [values]

            for option in options:
                try:
                    option_text = option.text.strip()

                    # Skip empty options
                    if not option_text:
                        continue

                    # Try each possible value
                    for value in value_list:
                        value_str = str(value).strip()
                        if not value_str:
                            continue

                        print(
                            f"Comparing: '{value_str.lower()}' with '{option_text.lower()}'"
                        )

                        # Check for exact match
                        if option_text.lower() == value_str.lower():
                            best_match = option
                            best_score = 1.0
                            print(f"Exact match found for '{value_str}'")
                            break  # Found exact match, no need to check other values

                        # Check for starts with
                        if option_text.lower().startswith(value_str.lower()):
                            if 0.9 > best_score:  # prefer startswith over contains
                                best_match = option
                                best_score = 0.9
                                print(f"Starts-with match found for '{value_str}'")

                        # Check for contains
                        if value_str.lower() in option_text.lower():
                            if 0.7 > best_score:
                                best_match = option
                                best_score = 0.7
                                print(f"Contains match found for '{value_str}'")

                    # If we found an exact match for this option, break the outer loop too
                    if best_score == 1.0:
                        break
                except Exception as option_error:
                    print(f"Error processing option: {option_error}")
                    continue

            # If we found a good match, click it
            if best_match and best_score > 0:
                try:
                    print(
                        f"Selected option: '{best_match.text}' with score: {best_score}"
                    )
                    self.driver.execute_script("arguments[0].click();", best_match)
                    # Wait for selection to take effect
                    self._wait_for_element_stability(element)
                    return True
                except Exception as click_error:
                    print(f"Error clicking best match: {click_error}")

            # If we get here, we couldn't find a good match
            print(f"Could not find matching option for: {values}")
            print(
                "Available options:", [opt.text for opt in options if opt.text.strip()]
            )

            # As a last resort, select the first non-empty option
            for option in options:
                if option.text.strip():
                    try:
                        print(
                            f"Selecting first available option as fallback: {option.text}"
                        )
                        self.driver.execute_script("arguments[0].click();", option)
                        # Wait for selection to take effect
                        self._wait_for_element_stability(element)
                        return True
                    except:
                        pass

            return False

        except Exception as e:
            print(f"Error in answer_dropdown: {e}")
            return False

    def fill_input(self, element, data_automation_id, values=[]):
        """Handle text input fields"""
        current_value = element.get_attribute("value")
        if current_value == str(values):
            print(f"Field already has correct value: {values}")
            return True
        try:
            print(f"Input value: {values}")
            # Clear the existing value
            element.clear()
            time.sleep(1)
            element = None
            try:
                element = self.driver.find_element(
                    By.CSS_SELECTOR, f"input[data-automation-id='{data_automation_id}']"
                )
            except:
                element = self.driver.find_element(By.ID, f"{data_automation_id}")
            self.wait.until(EC.element_to_be_clickable(element))
            # Send the new value
            element.send_keys(values)
            # Wait for input to be processed
            self._wait_for_element_stability(element)
            return True
        except Exception as e:
            print(f"Error in fill_input: {e}")
            return False

    def select_radio(self, element, data_automation_id, values=""):
        """
        Handle radio button selections with the specific Workday HTML structure
        """
        has_id = False
        try:
            element.get_attribute("id")
            has_id = True
        except Exception as e:
            has_id = False
        try:
            print(
                f"Selecting radio value: {values} for automation-id: {data_automation_id}"
            )

            # Find the container with the radio group
            radio_group = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f'div[data-automation-id="{data_automation_id}"]')
                )
                if not has_id
                else EC.presence_of_element_located((By.ID, f"{data_automation_id}"))
            )
            # Find all radio options within the group
            radio_options = radio_group.find_elements(
                By.CSS_SELECTOR, 'div[class*="css-1utp272"]'
            )

            # Convert values to a list if it's not already
            value_list = values if isinstance(values, list) else [values]

            # Process all possible values
            all_value_tokens = []
            for value in value_list:
                all_value_tokens.extend(str(value).lower().split())

            # Track best match
            best_match_score = 0
            best_match_option = None

            for option in radio_options:
                try:
                    # Get the label text and process it
                    label_element = option.find_element(By.CSS_SELECTOR, "label")
                    label = label_element.text.strip()

                    # Keep original label for display
                    original_label = label

                    # Filter out stopwords but preserve more meaningful words for better matching
                    filtered_label = " ".join(
                        [
                            word
                            for word in re.split("\W+", label.lower())
                            if word.lower() not in stopwords.stopwords
                        ]
                    )

                    # Calculate match score based on token overlap
                    matching_tokens = 0
                    for token in all_value_tokens:
                        if token in filtered_label.lower() or token in label.lower():
                            matching_tokens += 1

                    # Calculate score as percentage of matching tokens
                    if all_value_tokens:
                        score = matching_tokens / len(all_value_tokens)

                        # Check for exact match against any of the provided values
                        for value in value_list:
                            if str(value).lower() == label.lower():
                                score = 1.0
                                break

                        # Keep track of best match
                        if score > best_match_score:
                            best_match_score = score
                            best_match_option = option

                    print(f"Option: '{original_label}', Score: {best_match_score:.2f}")

                    # Check for direct match with any of the provided values
                    direct_match = False
                    for value in value_list:
                        value_str = str(value).lower()
                        if value_str == label.lower() or value_str in label.lower():
                            direct_match = True
                            break

                    # If this is a direct match, select it
                    if direct_match:
                        radio_input = option.find_element(
                            By.CSS_SELECTOR, 'input[type="radio"]'
                        )
                        try:
                            label_element.click()
                        except:
                            self.driver.execute_script(
                                "arguments[0].click();", radio_input
                            )
                        # Wait for radio selection to take effect
                        self._wait_for_element_stability(element)
                        return True

                except Exception as e:
                    print(f"Error with option: {e}")
                    continue

            # If we found a good match but not direct match, use it
            if best_match_score > 0.5 and best_match_option:
                try:
                    label_element = best_match_option.find_element(
                        By.CSS_SELECTOR, "label"
                    )
                    print(
                        f"Using best match: {label_element.text} with score: {best_match_score:.2f}"
                    )
                    try:
                        label_element.click()
                    except:
                        radio_input = best_match_option.find_element(
                            By.CSS_SELECTOR, 'input[type="radio"]'
                        )
                        self.driver.execute_script("arguments[0].click();", radio_input)
                    # Wait for selection to take effect
                    self._wait_for_element_stability(element)
                    return True
                except Exception as e:
                    print(f"Error clicking best match option: {e}")

            # If no match found
            print(f"No matching radio option found for value: {values}")
            print(
                "Available options:",
                [
                    opt.find_element(By.CSS_SELECTOR, "label").text
                    for opt in radio_options
                ],
            )
            return False

        except Exception as e:
            print(f"Error in select_radio: {e}")
            # Fallback - try answer_dropdown as a last resort
            try:
                return self.answer_dropdown(element, data_automation_id, values)
            except:
                return False


def show_learning_suggestions(workday):
    """Display suggestions for improving the automation based on learning data"""
    try:
        suggestions = workday.learner.generate_suggestions()
        if suggestions:
            print("\n" + "=" * 80)
            print("LEARNING SUGGESTIONS")
            print("=" * 80)
            for suggestion in suggestions:
                print(suggestion)
            print("\nThese suggestions can help improve the automation in future runs.")
            print(
                "Consider adding these mappings to the questionsToActions list in workday.py."
            )
            print("=" * 80)
    except Exception as e:
        print(f"Error generating learning suggestions: {e}")


def main():
    # Path to jobs.txt file
    jobs_file = os.path.join(os.path.dirname(__file__), "config", "jobs.txt")

    if not os.path.exists(jobs_file):
        print(f"Error: {jobs_file} not found!")
        return

    # Read and process URLs from jobs.txt
    with open(jobs_file, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        print("No URLs found in jobs.txt. Please add some job URLs to the file.")
        return

    print(f"Found {len(urls)} jobs to apply for:")
    for i, url in enumerate(urls, 1):
        print(f"{i}. {url}")

    print("\nStarting application process...")

    # Keep a reference to the last workday instance for showing suggestions
    last_workday = None

    for i, url in enumerate(urls, 1):
        print(f"\nProcessing job {i}/{len(urls)}: {url}")
        try:
            workday = Workday(url)
            last_workday = workday
            workday.apply()
            print(f"Completed job {i}/{len(urls)}")
        except Exception as e:
            print(f"Error processing job {url}: {e}")
        print("\nWaiting 30 seconds before next application...")
        time.sleep(30)

    print("\nAll jobs processed!")

    # Show learning suggestions after all jobs are processed
    if last_workday:
        show_learning_suggestions(last_workday)


if __name__ == "__main__":
    main()
