from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from datetime import datetime

class WorkdayFormHandler:
    def __init__(self, web_element_handler, stopwords=None):
        self.web_handler = web_element_handler
        self.stopwords = stopwords or set()

    def handle_date(self, element, _):
        """Handle date input fields"""
        try:
            month_input = self.web_handler.wait_for_clickable(
                By.CSS_SELECTOR,
                "div[data-automation-id='dateSectionMonth-display']"
            )
            day_input = self.web_handler.wait_for_clickable(
                By.CSS_SELECTOR,
                "div[data-automation-id='dateSectionDay-display']"
            )
            year_input = self.web_handler.wait_for_clickable(
                By.CSS_SELECTOR,
                "div[data-automation-id='dateSectionYear-display']"
            )

            if all([month_input, day_input, year_input]):
                month_input.send_keys(datetime.now().strftime("%m"))
                day_input.send_keys(datetime.now().strftime("%d"))
                year_input.send_keys(datetime.now().strftime("%Y"))
                return True
        except Exception as e:
            print(f"Error handling date: {e}")
        return False

    def select_checkbox(self, element, data_automation_id):
        """Handle checkbox selection"""
        try:
            checkbox = element.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
            return self.web_handler.click_element(checkbox)
        except Exception as e:
            print(f"Error selecting checkbox: {e}")
            return False

    def handle_multiselect(self, element, _, values):
        """Handle multi-select dropdowns"""
        try:
            input_element = element.find_element(By.XPATH, "//div//input")
            return self.web_handler.fill_input_field(input_element, values)
        except Exception as e:
            print(f"Error in handle_multiselect: {e}")
            try:
                return self.answer_dropdown(element, _, values)
            except Exception as e:
                print(f"Error in fallback dropdown: {e}")
                return False

    def answer_dropdown(self, element, _, values=""):
        """Handle dropdown selection"""
        try:
            self.web_handler.click_element(element, use_js=True)
            time.sleep(1)

            options = self.web_handler.find_elements_safely(
                By.CSS_SELECTOR,
                "ul[role='listbox'] li[role='option'] div"
            )

            if values != "unknown":
                for option in options:
                    if (option.text.lower() == values.lower() or
                        option.text.lower().startswith(values.lower())):
                        return self.web_handler.click_element(option, use_js=True)
            else:
                if options:
                    return self.web_handler.click_element(options[-1], use_js=True)

            print(f"No matching option found for: {values}")
            print("Available options:", [opt.text for opt in options])
            return False

        except Exception as e:
            print(f"Error in answer_dropdown: {e}")
            return False

    def fill_input(self, element, data_automation_id, values=[]):
        """Handle text input fields"""
        return self.web_handler.fill_input_field(element, values, data_automation_id)

    def select_radio(self, element, data_automation_id, values=""):
        """Handle radio button selection"""
        try:
            radio_group = self.web_handler.find_element_safely(
                By.CSS_SELECTOR if not element.get_attribute("id") else By.ID,
                f'div[data-automation-id="{data_automation_id}"]' if not element.get_attribute("id") else data_automation_id
            )

            if not radio_group:
                return False

            radio_options = radio_group.find_elements(
                By.CSS_SELECTOR,
                'div[class*="css-1utp272"]'
            )

            for option in radio_options:
                try:
                    label = option.find_element(By.CSS_SELECTOR, "label").text.strip()
                    label = " ".join([
                        word for word in re.split("\W+", label)
                        if word.lower() not in self.stopwords
                    ])

                    if any(value in l for value in values.lower() for l in label.lower()):
                        radio_input = option.find_element(
                            By.CSS_SELECTOR,
                            'input[type="radio"]'
                        )

                        try:
                            label_element = option.find_element(By.CSS_SELECTOR, "label")
                            return self.web_handler.click_element(label_element)
                        except:
                            return self.web_handler.click_element(radio_input, use_js=True)

                except Exception as e:
                    print(f"Error with radio option: {e}")
                    continue

            print(f"No matching radio option found for: {values}")
            return False

        except Exception as e:
            print(f"Error in select_radio: {e}")
            return False

    def fillform_page_1(self, profile):
        """Handle the first page of the form (resume upload)"""
        try:
            resume_input = self.web_handler.find_element_safely(
                By.CSS_SELECTOR,
                "input[data-automation-id='file-upload-input-ref']"
            )
            if resume_input:
                resume_input.send_keys(profile["resume_path"])
                time.sleep(1)
                return True
        except Exception as e:
            print(f"Error uploading resume: {e}")
        return False

    def get_required_fields(self):
        """Get all required fields on the current page"""
        return self.web_handler.find_elements_safely(By.XPATH, "//abbr[text()='*']")