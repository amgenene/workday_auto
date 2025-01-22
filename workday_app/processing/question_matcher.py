from sentence_transformers import SentenceTransformer, util
from operator import itemgetter
import time
from typing import Tuple, Optional, Any
from config.profile_loader import ProfileLoader
from browser.elements import ElementHandler
from sentence_transformers import SentenceTransformer, util


class QuestionMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the question matcher with a specific model"""
        self.model = SentenceTransformer(model_name)
        self.question_bank = ProfileLoader.questions
        self.load_questions
        self.embedding_to_values = {}

    def load_questions(self, questions: list):
        """Load and encode questions for matching"""
        self.question_bank = [
            (self.model.encode(keywords, convert_to_tensor=True), value)
            for keywords, value in questions
        ]

    def match_question(
        self, question_text: str, threshold: float = 0.5
    ) -> Tuple[Optional[Any], Optional[Any], float]:
        """Match a question to an action using sentence embeddings"""
        if not self.question_bank:
            return None, None, 0

        question_embedding = self.model.encode(question_text, convert_to_tensor=True)
        self.embedding_to_values = {
            self.model.encode(q, convert_to_tensor=True): v
            for q, v in self.question_bank
        }
        similarity_scores = [
            (float(util.pytorch_cos_sim(question_embedding, q_embedding).mean()), value)
            for q_embedding, value in self.embedding_to_values
        ]

        (max_score,) = max(similarity_scores, key=lambda x: x[0])
        if max_score > threshold:
            return value, max_score

        return None, max_score

    def process_question(
        self,
        question_text: str,
        input_element: Any,
        automation_id: str,
        step: Optional[int] = None,
    ) -> bool:
        """Process a single question and execute the matching action"""
        value, score = self.match_question(question_text)
        action = ElementHandler.get_element_handler(input_element)
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
