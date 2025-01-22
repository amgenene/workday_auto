from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

class BrowserManager:
    def __init__(self, config=None):
        self.config = config
        self.driver = None
        self.wait = None

    def start_driver(self):
        """Initialize and configure the Chrome WebDriver"""
        options = Options()
        if self.config and self.config.get('browser_options'):
            for option in self.config['browser_options']:
                options.add_argument(option)

        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 15)
        return self.driver, self.wait

    def quit(self):
        """Safely quit the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.wait = None