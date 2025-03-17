class StopWords:
    def __init__(self):
        # Reduced stopword list focusing only on most common stopwords
        # that don't affect question meaning in application forms
        self.stopwords = [
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "of",
            "at",
            "by",
            "for",
            "with",
            "about",
            "in",
            "on",
            "to",
            "from",
        ]
