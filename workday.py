import time

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from config import Config
from datetime import datetime
from typing import List, Tuple, Optional
import os
import re
from StopWords import StopWords
from sentence_transformers import SentenceTransformer, util
from operator import itemgetter
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

stopwords = StopWords()


class Workday:
    def __init__(self, url):
        self.url = url
        self.config = Config("./config/profile.yaml")
        self.profile = self.config.profile
        self.page = None
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

    @classmethod
    async def create(cls, url: str):
        """Factory method to create and initialize an AsyncWorkday instance"""
        self = cls(url)
        await self.initialize()
        return self

    async def initialize(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        await self.page.set_viewport_size({"width": 1800, "height": 1964})

    async def close_browser(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def wait_for_navigation(self):
        try:
            await self.page.wait_for_load_state("networkidle")
        except PlaywrightTimeout:
            pass

    async def select_checkbox(self, element, data_automation_id):
        radio_button = element.query_selector(f'input[type="checkbox"]')
        await radio_button.wait_for_element_state("enabled")
        await radio_button.click()

    async def handle_date(self, element, _):
        try:
            month_input = await self.page.query_selector(
                "div[data-automation-id='dateSectionMonth-display']",
            )

            day_input = await self.page.query_selector(
                "div[data-automation-id='dateSectionDay-display']",
            )

            year_input = await self.page.query_selector(
                "div[data-automation-id='dateSectionYear-display']",
            )
            await month_input.wait_for_element_state("enabled")
            await month_input.type(datetime.now().strftime("%m"))
            await month_input.click()
            await asyncio.sleep(1)
            await day_input.wait_for_element_state("enabled")
            await day_input.click()
            await day_input.type(datetime.now().strftime("%d"))
            await asyncio.sleep(1)
            await year_input.wait_for_element_state("enabled")
            await year_input.click()
            await year_input.type(datetime.now().strftime("%Y"))
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(1)
        except Exception as e:
            print("Exception: 'No date input'", e)
        return True

    async def signup(self):
        print("Signup")
        try:
            redirect = await self.page.query_selector(
                "xpath=//button[text()='Sign Up' or text()='Create Account']",
            )
            await redirect.wait_for_element_state("enabled")
            await redirect.click()
        except Exception as e:
            print("Exception: 'No button for Sigup'")
        try:
            await asyncio.sleep(5)
            form = await self.page.query_selector("xpath=//form")
            await form.wait_for_element_state("visible")
            checkbox = await form.query_selector("xpath=//input[@type='checkbox']")
            print("here")
            await checkbox.click()
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error: {str(e)}")
        try:
            await asyncio.sleep(2)
            email = await self.page.query_selector(
                "input[type='text'][data-automation-id='email']"
            )
            await email.fill(self.profile["email"])
            password = await self.page.query_selector(
                "input[type='password'][data-automation-id='password']"
            )
            await password.fill(self.profile["password"])
            verify_password = await self.page.query_selector(
                "input[type='password'][data-automation-id='verifyPassword']"
            )
            await verify_password.fill(self.profile["password"])
            try:
                button = await self.page.query_selector(
                    "div[role='button'][aria-label='Create Account'][data-automation-id='click_filter']",
                )
                await button.click()
            except Exception as e:
                print("Exception: 'No button for Create Account'", e)
                button1 = await self.page.query_selector(
                    "xpath=//button[@type='submit']"
                )

                await button1.wait_for_element_state("enabled")
                self.page.execute_script("arguments[0].click();", button1)
            await asyncio.sleep(2)
        except Exception as e:
            print("Exception: 'Signup failed'", e)
            self.signin()

    async def signin(self):
        print("Signin")
        try:
            button = await self.page.query_selector("xpath=//button[text()='Sign In']")
            await button.wait_for_element_state("enabled")
            await button.click()

        except Exception as e:
            print("Exception: 'No button for Sigin'")
        await asyncio.sleep(5)
        try:
            form = await self.page.query_selector("xpath=//form")
            await form.wait_for_element_state("visible")
        except Exception as e:
            print(f"Error form error: {str(e)}")
        try:
            await asyncio.sleep(2)
            email = await self.page.query_selector(
                "input[type='text'][data-automation-id='email']"
            )
            await email.fill(self.profile["email"])
            password = await self.page.query_selector(
                "input[type='password'][data-automation-id='password']"
            )
            await password.fill(self.profile["password"])
            button = await self.page.query_selector(
                "div[role='button'][aria-label='Sign In'][data-automation-id='click_filter']"
            )
            await asyncio.sleep(1)
            await button.click()
        except Exception as e:
            print("Exception: 'Signin failed'", e)

    async def find_next_sibling_safely(self, start_element, parent, max_levels=5):
        """
        Safely navigate up the DOM tree and find the next sibling div using Playwright
        """
        try:
            current = start_element
            for level in range(max_levels):
                print(
                    f"Current level: {await current.evaluate('el => `${el.tagName}, ${el.textContent}`')}"
                )

            # Check for siblings at current level
            siblings = await current.query_selector_all(
                "xpath=./following-sibling::div//*[@data-automation-id][position()=1]"
            )
            if siblings and len(siblings) > 0:
                print(f"Found sibling at level {level}")
                return siblings[0], level, False

            if not siblings:
                siblings = await current.query_selector_all(
                    "xpath=./following-sibling::div//*[@id][position()=1]"
                )
                if siblings and len(siblings) > 0:
                    print(
                        f"Found sibling at level {level} sibling container: {await siblings[0].evaluate('el => `${el.tagName}, ${el.textContent}`')}"
                    )
                    return siblings[0], level, True

            # Try to go up one level
            try:
                # Get parent element
                parent_automation_id = await parent.get_attribute("data-automation-id")
                current_automation_id = await current.get_attribute(
                    "data-automation-id"
                )

                if parent_automation_id == current_automation_id:
                    print(f"Reached same element at level {level}, stopping")
                    return None
            except:
                print(f"didn't find parent at level: {level} Continue")

            current = await current.query_selector("xpath=./..")

        except Exception as e:
            print(f"Error in safe navigation: {e}")
            return None
        return None

    async def fillform_page_1(self):
        try:
            resume_input = await self.page.query_selector(
                "input[data-automation-id='file-upload-input-ref']"
            )
            await resume_input.set_input_files(self.profile["resume_path"])
            await asyncio.sleep(1)
        except Exception as e:
            print("Exception: 'Missmatch in order'", e)
            return False
        return True

    async def handle_questions(self, step):
        required_fields = await self.page.query_selector_all("xpath=//abbr[text()='*']")
        questions = []
        print(f"\nFound {len(required_fields)} required fields")

        for field in required_fields[1:]:
            try:
                # Get the parent span containing the question text
                question = field.query_selector("xpath=./..")
                question_text = question.text_content()
                if not question_text:
                    continue
                # Get the parent div that would contain both question and input area
                parent = question.query_selector(
                    "xpath=./ancestor::div[@data-automation-id][position()=1]"
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
                await asyncio.sleep(6)
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

    async def click_next(self):
        try:
            button = await self.page.query_selector(
                "xpath=//button[text()='Next' or text()='Continue' or text()='Submit' or text()='Save and Continue' or text()='Review and Submit']",
            )
            await button.wait_for_element_state("enabled")
            await button.click()
        except Exception as e:
            print("Exception: 'No button for Next please continue'")
        await asyncio.sleep(5)
        try:
            error_button = await self.page.query_selector(
                "button[data-automation-id='errorBanner']"
            )
            print(
                "Exception: 'Errors on page. Please resolve and submit manually. You have 60 seconds to do so!'"
            )
            await asyncio.sleep(60)
        except:
            print("No Errors")
        await asyncio.sleep(10)

    async def apply(self):
        try:
            parsed_url = urlparse(self.url)
            print("parsed_url:", parsed_url)
            company = parsed_url.netloc.split(".")[0]
            existing_company = company in self.config.read_companies()
            print("company subdomain:", company)
            await self.page.goto(self.url)  # Open a webpage
            await asyncio.sleep(4)

            # Try to click the Apply button
            try:
                apply_button = await self.page.query_selector(
                    "a[role='button'][data-uxi-element-id='Apply_adventureButton']",
                )
                await apply_button.wait_for_element_state("enabled")
                await apply_button.click()
                await asyncio.sleep(2)
            except Exception as e:
                print("No Apply button found, continuing...", e)
            try:
                print("Try already applied")
                already_applied = await self.page.query_selector(
                    "[data-automation-id='alreadyApplied']"
                )
                return True
            except Exception as e:
                print("No already applied found, continuing...", e)
            # Try autofill with resume
            try:
                print("Try autofill with resume")
                button = await self.page.query_selector(
                    "a[role='button'][data-automation-id='autofillWithResume']",
                )
                await button.click()
                asyncio.sleep(2)
            except Exception as e:
                print("No autofill resume button found", e)

            print("existing_company:", existing_company)
            try:
                await asyncio.sleep(2)
                if existing_company:
                    self.signin()
                else:
                    self.signup()
                    self.config.write_company(company)
            except Exception as e:
                print(f"Error logging in or creating acct: {e}")
                input("Press Enter when you're ready to continue...")

            await asyncio.sleep(6)
            p_tags = await self.page.query_selectors(
                "xpath=//p[contains(text(), 'verify')]"
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
                    await asyncio.sleep(2)  # Brief pause between pages

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
                self.page.quit()
            except Exception as e:
                print(f"Fatal error in form processing: {e}")
                self.page.quit()
                return False
        except Exception as e:
            print(f"Error in early form processing: {e}")
            self.page.quit()
            return False
        return True

    async def handle_multiselect(self, element, _, values):
        """Handle multi-select dropdowns that require multiple clicks"""
        try:
            await element.click()
            await asyncio.sleep(0.5)
            await self.page.keyboard.type(values)
            await asyncio.sleep(0.5)
            await self.page.keyboard.press("Enter")
            return True
        except Exception as e:
            print(f"Error in handle_multiselect: {e}")
            try:
                self.answer_dropdown(element, _, values)
            except Exception as e:
                print(f"Error in using answer_dropdown: {e}")
                return False

    async def answer_dropdown(self, element, _, values=""):
        """Handle single-select dropdowns"""
        try:
            await element.click()
            await asyncio.sleep(0.5)

            options = await self.page.query_selector_all(
                "ul[role='listbox'] li[role='option'] div"
            )
            if values != "unknown":
                for option in options:
                    option_text = await option.text_content()
                    if (
                        option_text.lower() == values.lower()
                        or option_text.lower().startswith(values.lower())
                    ):
                        await option.click()
                        return True
            else:
                await options[-1].click()
            return False
        except Exception as e:
            print(f"Error in answer_dropdown: {e}")
            return False
        except Exception as e:
            print(f"Error in answer_dropdown: {e}")
            # Fallback try to call select_radio if this fails
            # self.select_radio(element, _, values)
            return False

    async def fill_input(self, element, data_automation_id, values=[]):
        """Handle text input fields"""
        current_value = element.get_attribute("value")
        if current_value == str(values):
            print(f"Field already has correct value: {values}")
            return True
        try:
            print(f"Input value: {values}")
            # Clear the existing value
            element.clear()
            await asyncio.sleep(1)
            element = None
            try:
                element = await self.page.query_selector(
                    f"input[data-automation-id='{data_automation_id}']"
                )
            except:
                element = await self.page.query_selector(f"#{data_automation_id}")
                await element.wait_for_element_state("enabled")
                # Send the new value
                await element.fill(values)
                await asyncio.sleep(1)
                return True
        except Exception as e:
            print(f"Error in fill_input: {e}")
            return False

    async def select_radio(self, element, data_automation_id, values=""):
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
                    (f'div[data-automation-id="{data_automation_id}"]')
                )
                if not has_id
                else EC.presence_of_element_located((By.ID, f"{data_automation_id}"))
            )
            # Find all radio options within the group
            radio_options = radio_group.query_selectors('div[class*="css-1utp272"]')
            for option in radio_options:
                try:
                    print("option.text", option.text)
                    # Get the label text to match against our value
                    label = option.query_selector("label").text.strip()
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
                        radio_input = option.query_selector('input[type="radio"]')

                        # Try to click the label first (often more reliable than clicking the input directly)
                        try:
                            await option.query_selector("label").click()
                        except:
                            # If label click fails, try JavaScript click on the input
                            self.page.execute_script(
                                "arguments[0].click();", radio_input
                            )

                        await asyncio.sleep(1)
                        return True
                except Exception as e:
                    print(f"Error with option: {e}")
                    continue

            print(f"No matching radio option found for value: {values}")
            print(
                "Available options:",
                [opt.query_selector("label").text for opt in radio_options],
            )
            return False

        except Exception as e:
            print(f"Error in select_radio: {e}")
            # self.answer_dropdown(element, data_automation_id, values)
            return False


async def main():
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
            workday = await Workday(url).create(url)
            await workday.apply()
            print(f"Completed job {i}/{len(urls)}")
        except Exception as e:
            print(f"Error processing job {url}: {e}")
        print("\nWaiting 30 seconds before next application...")
        input("Press Enter to continue...")

    print("\nAll jobs processed!")


if __name__ == "__main__":
    asyncio.run(main())
