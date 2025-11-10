import nltk
import spacy
import re
from langdetect import detect
from googletrans import Translator

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

class TextPreprocessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.translator = Translator()
        self.stop_words = set(nltk.corpus.stopwords.words('english'))
    
    def detect_language(self, text):
        try:
            return detect(text)
        except:
            return 'en'
    
    def translate_text(self, text, target_lang='en'):
        try:
            if len(text) > 5000:  # Google Translate limit
                text = text[:5000]
            result = self.translator.translate(text, dest=target_lang)
            return result.text
        except:
            return text
    
    def clean_text(self, text):
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Remove mentions and hashtags
        text = re.sub(r'@\w+|#\w+', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def preprocess(self, text):
        # Detect language
        original_lang = self.detect_language(text)
        
        # Translate if not English
        if original_lang != 'en':
            text = self.translate_text(text)
        
        # Clean text
        text = self.clean_text(text)
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Remove stop words and punctuation, lemmatize
        processed_tokens = [
            token.lemma_.lower() for token in doc
            if not token.is_stop and not token.is_punct and len(token.text) > 2
        ]
        
        return ' '.join(processed_tokens), original_lang