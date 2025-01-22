from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

class WebElementHandler:
    def __init__(self, driver, wait_time=10):
        self.driver = driver
        self.wait = WebDriverWait(driver, wait_time)

    def click_element(self, element, use_js=False):
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

    def fill_input_field(self, element, value, automation_id=None):
        """Fill an input field with given value"""
        try:
            if automation_id:
                try:
                    element = self.driver.find_element(
                        By.CSS_SELECTOR, f"input[data-automation-id='{automation_id}']"
                    )
                except:
                    element = self.driver.find_element(By.ID, f"{automation_id}")

            self.wait.until(EC.element_to_be_clickable(element))
            element.clear()
            time.sleep(1)
            element.send_keys(value)
            return True
        except Exception as e:
            print(f"Error filling input: {e}")
            return False

    def find_element_safely(self, by, value, wait=True):
        """Find element with wait and error handling"""
        try:
            if wait:
                return self.wait.until(EC.presence_of_element_located((by, value)))
            return self.driver.find_element(by, value)
        except Exception as e:
            print(f"Error finding element {value}: {e}")
            return None

    def find_elements_safely(self, by, value):
        """Find elements with error handling"""
        try:
            return self.driver.find_elements(by, value)
        except Exception as e:
            print(f"Error finding elements {value}: {e}")
            return []

    def wait_for_clickable(self, by, value):
        """Wait for element to be clickable"""
        try:
            return self.wait.until(EC.element_to_be_clickable((by, value)))
        except Exception as e:
            print(f"Error waiting for clickable {value}: {e}")
            return None

    def find_next_sibling_safely(self, start_element, parent, max_levels=5):
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
                    if parent.get_attribute('data-automation-id') == current.get_attribute('data-automation-id'):
                        return None, level, False
                except:
                    pass
                current = current.find_element(By.XPATH, "./..")
            return None, max_levels, False

        except Exception as e:
            print(f"Error in safe navigation: {e}")
            return None, 0, False