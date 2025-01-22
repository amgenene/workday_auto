from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time


class ElementHandler:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait
        self.element_handlers = [
            (self.is_date_input, self.handle_date),
            (self.is_multiselect, self.handle_multiselect),
            (self.is_dropdown, self.answer_dropdown),
            (self.is_radio, self.select_radio),
            (self.is_checkbox, self.select_checkbox),
            (self.is_text_input, self.fill_input),
        ]

    def get_element_handler(self, element: WebElement):
        """Determine appropriate handler based on element type"""
        for detector, handler in self.element_handlers:
            if detector(element):
                return handler

    def click_element(self, element: WebElement, use_js: bool = False) -> bool:
        """Safely click an element with retry logic"""
        try:
            self.wait.until(EC.element_to_be_clickable(element))
            if use_js:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                element.click()
            return True
        except Exception as e:
            print(f"Error clicking element: {e}")
            return False

    @staticmethod
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

    def find_element_safely(self, by: By, value: str, wait: bool = True) -> WebElement:
        """Find element with wait and error handling"""
        try:
            if wait:
                return self.wait.until(EC.presence_of_element_located((by, value)))
            return self.driver.find_element(by, value)
        except Exception as e:
            print(f"Error finding element {value}: {e}")
            return None

    def find_elements_safely(self, by: By, value: str) -> list:
        """Find elements with error handling"""
        try:
            return self.driver.find_elements(by, value)
        except Exception as e:
            print(f"Error finding elements {value}: {e}")
            return []

    def find_next_sibling_safely(
        self, start_element: WebElement, parent: WebElement, max_levels: int = 5
    ):
        """Find next sibling element safely"""
        try:
            current = start_element
            for level in range(max_levels):
                siblings = current.find_elements(
                    By.XPATH,
                    "./following-sibling::div//*[@data-automation-id][position()=1]",
                )
                if siblings:
                    return siblings[0], level, False

                siblings = current.find_elements(
                    By.XPATH, "./following-sibling::div//*[@id][position()=1]"
                )
                if siblings:
                    return siblings[0], level, True

                try:
                    if parent.get_attribute(
                        "data-automation-id"
                    ) == current.get_attribute("data-automation-id"):
                        return None, level, False
                except:
                    pass
                current = current.find_element(By.XPATH, "./..")
            return None, max_levels, False

        except Exception as e:
            print(f"Error in safe navigation: {e}")
            return None, 0, False

    @staticmethod
    def select_checkbox(self, element, data_automation_id):
        radio_button = element.find_element(By.CSS_SELECTOR, f'input[type="checkbox"]')
        self.wait.until(EC.element_to_be_clickable(radio_button))
        radio_button.click()

    @staticmethod
    def is_text_input(self, element: WebElement) -> bool:
        return element.tag_name == "input" and element.get_attribute("type") in [
            "text",
            "email",
            "tel",
            "number",
            "password",
        ]

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def is_dropdown(self, element: WebElement) -> bool:
        return (
            element.tag_name == "button"
            and element.get_attribute("aria-haspopup") == "listbox"
            or "dropdown" in element.get_attribute("data-automation-id").lower()
        )

    @staticmethod
    def is_multiselect(self, element: WebElement) -> bool:
        return (
            element.get_attribute("data-automation-id").lower()
            == "multiselectcontainer"
        )

    @staticmethod
    def is_radio(self, element: WebElement) -> bool:
        return element.get_attribute("data-uxi-widget-type").lower() == "radiogroup"

    @staticmethod
    def is_checkbox(self, element: WebElement) -> bool:
        return (
            element.tag_name == "input" and element.get_attribute("type") == "checkbox"
        )

    @staticmethod
    def is_date_input(self, element: WebElement) -> bool:
        return "date" in element.get_attribute("data-automation-id").lower()
