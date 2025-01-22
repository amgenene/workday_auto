from sentence_transformers import SentenceTransformer, util
from operator import itemgetter
import time
from typing import Tuple, Optional, Any

class QuestionMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the question matcher with a specific model"""
        self.model = SentenceTransformer(model_name)
        self.question_bank = []

    def load_questions(self, questions: list):
        """Load and encode questions for matching"""
        self.question_bank = [
            (self.model.encode(keywords, convert_to_tensor=True), action, value)
            for keywords, action, value in questions
        ]

    def match_question(self, question_text: str, threshold: float = 0.5) -> Tuple[Optional[Any], Optional[Any], float]:
        """Match a question to an action using sentence embeddings"""
        if not self.question_bank:
            return None, None, 0

        question_embedding = self.model.encode(question_text, convert_to_tensor=True)

        similarity_scores = [
            (
                float(util.pytorch_cos_sim(question_embedding, q_embedding).mean()),
                action,
                value
            )
            for q_embedding, action, value in self.question_bank
        ]

        max_score, action, value = max(similarity_scores, key=lambda x: x[0])

        if max_score > threshold:
            return action, value, max_score

        return None, None, max_score

    def process_question(self, question_text: str, input_element: Any, automation_id: str, step: Optional[int] = None) -> bool:
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

        print(f"No matching action found for question: {question_text}")
        return False