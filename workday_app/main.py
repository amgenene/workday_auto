import os
import time
from typing import List
from browser.driver_manager import BrowserManager
from browser.elements import ElementHandler
from processing.question_matcher import QuestionMatcher
from processing.form_processor import FormProcessor
from processing.workflow import ApplicationWorkflow
from config.profile_loader import ProfileLoader
from utils.logger import Logger

class WorkdayApplication:
    def __init__(self):
        """Initialize the Workday application"""
        self.logger = Logger()
        self.profile_loader = ProfileLoader()
        self.browser_manager = BrowserManager()
        self.question_matcher = QuestionMatcher()

        # Load questions configuration
        self.question_matcher.load_questions(self.profile_loader.questions)

    def run(self):
        """Run the application process for all jobs"""
        urls = self._load_jobs_urls()
        if not urls:
            self.logger.error("No job URLs found")
            return

        self.logger.info(f"Found {len(urls)} jobs to process")

        for i, url in enumerate(urls, 1):
            self.logger.info(f"Processing job {i}/{len(urls)}: {url}")
            self._process_job(url)

            if i < len(urls):
                self.logger.info("Waiting 30 seconds before next application...")
                time.sleep(30)

        self.logger.info("All jobs processed")

    def _process_job(self, url: str):
        """Process a single job application"""
        driver, wait = None, None
        try:
            # Initialize browser
            driver, wait = self.browser_manager.start_driver()

            # Initialize handlers
            element_handler = ElementHandler(driver, wait)
            form_processor = FormProcessor(
                driver,
                wait,
                element_handler,
                self.question_matcher
            )

            # Initialize and run workflow
            workflow = ApplicationWorkflow(
                driver,
                wait,
                self.profile_loader,
                form_processor,
                element_handler
            )

            if workflow.run(url):
                self.logger.info(f"Successfully processed {url}")
            else:
                self.logger.error(f"Failed to process {url}")

        except Exception as e:
            self.logger.error(f"Error processing {url}", exc_info=e)

        finally:
            if driver:
                self.browser_manager.quit()

    def _load_jobs_urls(self) -> List[str]:
        """Load job URLs from the configuration file"""
        jobs_file = os.path.join("config", "jobs.txt")

        if not os.path.exists(jobs_file):
            self.logger.error(f"Jobs file not found: {jobs_file}")
            return []

        try:
            with open(jobs_file, "r") as f:
                return [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
        except Exception as e:
            self.logger.error("Error loading jobs file", exc_info=e)
            return []

def main():
    """Main entry point"""
    app = WorkdayApplication()
    app.run()

if __name__ == "__main__":
    main()