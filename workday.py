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
            (["state"], self.answer_dropdown, self.profile["address_state"]),
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
        radio_button.click()

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
            except Exception as e:
                print("Exception: 'No button for Create Account'", e)
                button1 = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
                )
                print(button1.is_displayed())  # Check if button is visible
                print(button1.is_enabled())  # Check if button is clickable
                self.driver.execute_script("arguments[0].click();", button1)
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
        required_fields = self.driver.find_elements(By.XPATH, "//abbr[text()='*']")
        questions = []
        print(f"\nFound {len(required_fields)} required fields")

        for field in required_fields[1:]:
            try:
                # Get the parent span containing the question text
                question = field.find_element(By.XPATH, "./..")
                question_text = question.text
                if not question_text:
                    continue
                # Get the parent div that would contain both question and input area
                parent = question.find_element(
                    By.XPATH, "./ancestor::div[@data-automation-id][position()=1]"
                )
                print(
                    f"Parent automation-id: {parent.get_attribute('data-automation-id')}"
                )
                # question's input container
                container, levels_traversed, is_id = self.find_next_sibling_safely(
                    question, parent
                )
                print("question tag name", question.tag_name, question.text)
                print(
                    container.tag_name, container.text, container.get_attribute("type")
                )
                automation_id = (
                    container.get_attribute("data-automation-id")
                    if not is_id
                    else container.get_attribute("id")
                )
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
            handled = False
            best_match_score = 0
            best_match_action = None
            best_match_value = None

            question_embedding = self.model.encode(
                question_text, convert_to_tensor=True
            )
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
            max_score, keyword_embedding = max(similarity_scores, key=itemgetter(0))
            print("keyword_embedding to action", embeddingsToActions[keyword_embedding])
            if max_score > best_match_score:
                best_match_score = max_score
                best_match_action = embeddingsToActions[keyword_embedding][0]
                best_match_value = embeddingsToActions[keyword_embedding][1]
            print("best_match_score", best_match_score)
            if (
                best_match_score > 0.5
            ):  # Set a threshold for what you consider a "match"
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
                time.sleep(6)
                if action_result:
                    print(f"Action successful: {best_match_action}")
                else:
                    print(f"Action failed: {best_match_action}")
                handled = True
            if not handled and step == 4:
                action_result = self.answer_dropdown(
                    input_element, automation_id, values="unknown"
                )

            if not handled:
                print(
                    f"No matching action found for question: {question_text}. Please fill manually"
                )
        print(f"\nSuccessfully processed {len(questions)} questions")
        print("\nQuestions found:")
        for q, i, aid in questions:
            print(f"Q: {q} -> automation-id: {aid}")
        input("Press Enter to continue after reviewing the questions...")
        return True

    def click_next(self):
        try:
            button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[text()='Next' or text()='Continue' or text()='Submit' or text()='Save and Continue' or text()='Review and Submit']",
                    )
                )
            )
            button.click()
        except Exception as e:
            print("Exception: 'No button for Next please continue'")
        time.sleep(5)
        try:
            error_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[data-automation-id='errorBanner']"
            )
            print(
                "Exception: 'Errors on page. Please resolve and submit manually. You have 60 seconds to do so!'"
            )
            time.sleep(60)
        except:
            print("No Errors")
        time.sleep(10)

    def apply(self):
        try:
            parsed_url = urlparse(self.url)
            print("parsed_url:", parsed_url)
            company = parsed_url.netloc.split(".")[0]
            existing_company = company in self.config.read_companies()
            print("company subdomain:", company)
            self.driver.get(self.url)  # Open a webpage
            time.sleep(4)

            # Try to click the Apply button
            try:
                apply_button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "a[role='button'][data-uxi-element-id='Apply_adventureButton']",
                )
                apply_button.click()
                time.sleep(2)
            except Exception as e:
                print("No Apply button found, continuing...", e)
            try:
                already_applied = self.driver.find_element(
                    By.CSS_SELECTOR, "[data-automation-id='alreadyApplied']"
                )
                return True
            except Exception as e:
                print("No already applied found, continuing...", e)
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
                max_pages = 5  # Set this to your maximum number of pages

                while current_page <= max_pages:
                    time.sleep(2)  # Brief pause between pages

                    try:
                        if current_page == 3:
                            success = True  # skip page 3 because it's just reading from the resume
                        else:
                            success = self.handle_questions(current_page)
                        if success:
                            print(f"Successfully completed page {current_page}")
                            self.click_next()
                            current_page += 1
                        else:
                            print(
                                f"Issues on page {current_page}, waiting for manual intervention"
                            )
                            input(
                                "Press Enter when you've fixed the issues and are ready to continue..."
                            )
                            # Don't increment page counter if there were issues

                    except Exception as e:
                        print(f"Exception on page {current_page}: {e}")
                        input(
                            "Press Enter when you've fixed the issues and are ready to continue..."
                        )
                        # Optionally, you might want to retry the same page:
                        continue

                # After all pages are done
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
            input_element = element.find_element(By.XPATH, "//div//input")
            input_element.send_keys(values)
            # self.driver.execute_script("arguments[0].click();", input_element)
            time.sleep(1)
            # Click to open the dropdown
            # element.click()
            # time.sleep(1)

            # # Click each selection in order
            # for selection in values:
            #     self.driver.find_element(
            #         By.XPATH, f"//div[text()='{selection}']"
            #     ).click()
            #     time.sleep(1)
            return True
        except Exception as e:
            print(f"Error in handle_multiselect: {e}")
        try:
            self.answer_dropdown(element, _, values)
        except Exception as e:
            print(f"Error in using answer_dropdown: {e}")
            return False

    def answer_dropdown(self, element, _, values=""):
        """Handle single-select dropdowns"""
        try:
            print("value being selected", values)
            # Click to open the dropdown
            self.driver.execute_script("arguments[0].click();", element)
            time.sleep(1)

            # Find all options and look for a case-insensitive match
            options = self.driver.find_elements(
                By.CSS_SELECTOR, "ul[role='listbox'] li[role='option'] div"
            )
            if values != "unknown":
                for option in options:
                    print("values:", values.lower(), option.text.lower())
                    if (
                        option.text.lower() == values.lower()
                        or option.text.lower().startswith(values.lower())
                    ):
                        self.driver.execute_script("arguments[0].click();", option)
                    time.sleep(1)
                    return True
            else:
                self.driver.execute_script("arguments[0].click();", options[-1])
                time.sleep(1)
                print(f"Could not find option so selected the last option...: {values}")
                print("Available options:", [opt.text for opt in options])
                return False

        except Exception as e:
            print(f"Error in answer_dropdown: {e}")
            # Fallback try to call select_radio if this fails
            # self.select_radio(element, _, values)
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
            time.sleep(1)
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
            for option in radio_options:
                try:
                    print("option.text", option.text)
                    # Get the label text to match against our value
                    label = option.find_element(By.CSS_SELECTOR, "label").text.strip()
                    label = " ".join(
                        [
                            word
                            for word in re.split("\W+", label)
                            if word.lower() not in stopwords.stopwords
                        ]
                    )
                    if any(
                        value in l for value in values.lower() for l in label.lower()
                    ):
                        # Find the actual radio input within this option
                        radio_input = option.find_element(
                            By.CSS_SELECTOR, 'input[type="radio"]'
                        )

                        # Try to click the label first (often more reliable than clicking the input directly)
                        try:
                            option.find_element(By.CSS_SELECTOR, "label").click()
                        except:
                            # If label click fails, try JavaScript click on the input
                            self.driver.execute_script(
                                "arguments[0].click();", radio_input
                            )

                        time.sleep(1)
                        return True
                except Exception as e:
                    print(f"Error with option: {e}")
                    continue

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
            # self.answer_dropdown(element, data_automation_id, values)
            return False


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

    for i, url in enumerate(urls, 1):
        print(f"\nProcessing job {i}/{len(urls)}: {url}")
        try:
            workday = Workday(url)
            workday.apply()
            print(f"Completed job {i}/{len(urls)}")
        except Exception as e:
            print(f"Error processing job {url}: {e}")
        print("\nWaiting 30 seconds before next application...")
        time.sleep(30)

    print("\nAll jobs processed!")


if __name__ == "__main__":
    main()
