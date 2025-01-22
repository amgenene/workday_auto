from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time

class ElementHandler:
    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

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

    def fill_input_field(self, element: WebElement, value: str, automation_id: str = None) -> bool:
        """Fill an input field with given value"""
        try:
            if automation_id:
                element = self._find_input_by_automation_id(automation_id)

            if not element:
                return False

            self.wait.until(EC.element_to_be_clickable(element))
            element.clear()
            time.sleep(1)
            element.send_keys(value)
            return True
        except Exception as e:
            print(f"Error filling input: {e}")
            return False

    def _find_input_by_automation_id(self, automation_id: str) -> WebElement:
        """Find input element by automation ID"""
        try:
            return self.driver.find_element(
                By.CSS_SELECTOR,
                f"input[data-automation-id='{automation_id}']"
            )
        except:
            try:
                return self.driver.find_element(By.ID, automation_id)
            except:
                return None

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

    def find_next_sibling_safely(self, start_element: WebElement, parent: WebElement, max_levels: int = 5):
        """Find next sibling element safely"""
        try:
            current = start_element
            for level in range(max_levels):
                siblings = current.find_elements(
                    By.XPATH,
                    "./following-sibling::div//*[@data-automation-id][position()=1]"
                )
                if siblings:
                    return siblings[0], level, False

                siblings = current.find_elements(
                    By.XPATH,
                    "./following-sibling::div//*[@id][position()=1]"
                )
                if siblings:
                    return siblings[0], level, True

                try:
                    if parent.get_attribute('data-automation-id') == current.get_attribute('data-automation-id'):
                        return None, level, False
                except:
                    pass
                current = current.find_element(By.XPATH, "./..")
            return None, max_levels, False

        except Exception as e:
            print(f"Error in safe navigation: {e}")
            return None, 0, False

    @staticmethod
    def is_text_input(element: WebElement) -> bool:
        """Check if element is a text input"""
        return element.tag_name == "input" and element.get_attribute("type") in [
            "text", "email", "tel", "number", "password"
        ]

    @staticmethod
    def is_dropdown(element: WebElement) -> bool:
        """Check if element is a dropdown"""
        return element.get_attribute("role") in ["combobox", "button"]