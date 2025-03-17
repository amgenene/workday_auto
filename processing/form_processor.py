from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class FormProcessor:
    def __init__(self, driver, wait, element_handler, question_matcher):
        self.driver = driver
        self.wait = wait
        self.element_handler = element_handler
        self.question_matcher = question_matcher

    def _find_required_fields(self):
        return self.driver.find_elements(By.XPATH, "//abbr[text()='*']")

    def process_page(self, page_number):
        required_fields = self._find_required_fields()
        questions = self._extract_questions(required_fields)
        try:
            self._handle_questions(questions, page_number)
        except Exception as e:
            print("Exception: 'Error processing questions'", e)
            return False
        return True

    def _extract_questions(self, fields):
        questions = []
        fields = self.find_required_fields()
        for field in fields[1:]:
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
        for keywords, value in self.question_matcher.question_bank:
            keyword_embedding = self.model.encode(keywords, convert_to_tensor=True)
            keyword_embeddings.append(keyword_embedding)
            embeddingsToActions[keyword_embedding] = value

        for question_text, input_element, automation_id in questions:
            handled = False
            best_match_score = 0
            best_match_action = None
            best_match_value = None

            matching_embedding = question_matcher.find_best_match(
                keyword_embeddings, question_text
            )

            print("keyword_embedding to action", embeddingsToActions[keyword_embedding])
            if matching_embedding:
                best_match_score = max_score
                best_match_value = embeddingsToActions[matching_embedding]
                best_match_action = 
            print("best_match_score", best_match_score)
            if (
                best_match_score > 0.5
            ):  # Set a threshold for what you consider a "match"
                print(
                    f"Executing action for question: {question_text} with best match score of: {best_match_score}, {best_match_value}"
                )
                handler = self.get_element_handler(input_element)
                action_result = (
                    handler(input_element, automation_id, values=best_match_value)
                    if best_match_value is not None
                    else handler(input_element, automation_id)
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

        return questions

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

    def _handle_questions(self, questions, step):
        for q_text, element, automation_id in questions:
            pass

    # Add other form processing methods
