from sentence_transformers import SentenceTransformer, util
from operator import itemgetter
import time

class QuestionMatcher:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.questions_to_actions = []

    def set_questions_to_actions(self, questions_to_actions):
        """Set the questions to actions mapping"""
        self.questions_to_actions = questions_to_actions

    def match_question(self, question_text, threshold=0.5):
        """Match a question to an action using sentence embeddings"""
        keyword_embeddings = []
        embeddings_to_actions = {}

        # Initialize embeddings and actions mapping
        for keywords, action, value in self.questions_to_actions:
            keyword_embedding = self.model.encode(keywords, convert_to_tensor=True)
            keyword_embeddings.append(keyword_embedding)
            embeddings_to_actions[keyword_embedding] = (action, value)

        # Encode the question
        question_embedding = self.model.encode(question_text, convert_to_tensor=True)

        # Calculate similarity scores
        similarity_scores = [
            (
                float(util.pytorch_cos_sim(question_embedding, keyword_embedding).mean()),
                keyword_embedding
            )
            for keyword_embedding in keyword_embeddings
        ]

        # Get best match
        if not similarity_scores:
            return None, None, 0

        max_score, keyword_embedding = max(similarity_scores, key=itemgetter(0))

        if max_score > threshold:
            action, value = embeddings_to_actions[keyword_embedding]
            return action, value, max_score

        return None, None, max_score

    def process_question(self, question_text, input_element, automation_id, step=None):
        """Process a single question and execute the matching action"""
        action, value, score = self.match_question(question_text)

        if action and score > 0.5:
            print(f"Executing action for question: {question_text} with score: {score}")
            try:
                result = (
                    action(input_element, automation_id, values=value)
                    if value is not None
                    else action(input_element, automation_id)
                )
                time.sleep(6)
                return result
            except Exception as e:
                print(f"Error executing action: {e}")
                return False

        if step == 4:  # Special handling for step 4
            try:
                from workday_form_handler import WorkdayFormHandler
                handler = WorkdayFormHandler(None)  # This is not ideal, should be refactored
                return handler.answer_dropdown(input_element, automation_id, values="unknown")
            except Exception as e:
                print(f"Error in fallback handling: {e}")

        print(f"No matching action found for question: {question_text}")
        return False