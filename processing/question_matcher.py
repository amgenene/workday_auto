from sentence_transformers import SentenceTransformer, util
from operator import itemgetter


class QuestionMatcher:
    def __init__(self, questions_config):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.question_bank = questions_config.default_questions

    def load_questions(self, questions):
        self.question_bank = [
            (self.model.encode(q, convert_to_tensor=True), a) for q, a in questions
        ]

    def find_best_match(self, keyword_embeddings, question_text, threshold=0.7):
        question_embedding = self.model.encode(question_text, convert_to_tensor=True)
        similarities = [
            (
                float(util.pytorch_cos_sim(question_embedding, q).mean()),
                keyword_embeddings,
            )
        ]
        max_score, matching_embedding = max(similarities, key=itemgetter(0))
        return matching_embedding if max_score > threshold else None
