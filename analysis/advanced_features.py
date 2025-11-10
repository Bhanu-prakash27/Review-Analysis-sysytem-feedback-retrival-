# analysis/advanced_features.py
"""
Advanced Features: Multilingual Support, Geographic Analysis, Voice Commands, Image Analysis
"""
from googletrans import Translator
from langdetect import detect
import speech_recognition as sr
from typing import Dict, List, Tuple
import re
import folium
from folium.plugins import HeatMap
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import torch
from transformers import CLIPProcessor, CLIPModel
import warnings
warnings.filterwarnings('ignore')


class MultilingualProcessor:
    """Handle multi-language reviews with auto-translation"""
    
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = {
            'en': 'English', 'hi': 'Hindi', 'es': 'Spanish', 
            'fr': 'French', 'de': 'German', 'ja': 'Japanese',
            'zh-cn': 'Chinese', 'ar': 'Arabic', 'pt': 'Portuguese',
            'ru': 'Russian', 'ko': 'Korean', 'it': 'Italian'
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the text"""
        try:
            lang = detect(text)
            return lang
        except:
            return 'en'
    
    def translate_to_english(self, text: str, source_lang: str = None) -> Dict:
        """
        Translate text to English
        Returns: {'original_text': str, 'translated_text': str, 'source_lang': str, 'confidence': float}
        """
        if not text or len(text.strip()) < 3:
            return {
                'original_text': text,
                'translated_text': text,
                'source_lang': 'en',
                'confidence': 1.0
            }
        
        try:
            # Auto-detect if not provided
            if not source_lang:
                source_lang = self.detect_language(text)
            
            # Skip translation if already English
            if source_lang == 'en':
                return {
                    'original_text': text,
                    'translated_text': text,
                    'source_lang': 'en',
                    'confidence': 1.0
                }
            
            # Translate
            translation = self.translator.translate(text, src=source_lang, dest='en')
            
            return {
                'original_text': text,
                'translated_text': translation.text,
                'source_lang': source_lang,
                'confidence': 0.95
            }
        
        except Exception as e:
            print(f"Translation error: {e}")
            return {
                'original_text': text,
                'translated_text': text,
                'source_lang': 'unknown',
                'confidence': 0.0
            }
    
    def batch_translate(self, texts: List[str]) -> List[Dict]:
        """Translate multiple texts"""
        results = []
        for text in texts:
            results.append(self.translate_to_english(text))
        return results


class GeographicAnalyzer:
    """Analyze sentiment by geographic location"""
    
    def __init__(self):
        self.location_patterns = {
            'US': r'\b(US|USA|United States|America)\b',
            'UK': r'\b(UK|United Kingdom|Britain|England)\b',
            'India': r'\b(India|Indian)\b',
            'China': r'\b(China|Chinese)\b',
            'Japan': r'\b(Japan|Japanese)\b',
            'Germany': r'\b(Germany|German)\b',
            'France': r'\b(France|French)\b',
            'Canada': r'\b(Canada|Canadian)\b',
            'Australia': r'\b(Australia|Australian)\b'
        }
        
        # Coordinates for major countries (approximate centers)
        self.country_coords = {
            'US': [37.0902, -95.7129],
            'UK': [55.3781, -3.4360],
            'India': [20.5937, 78.9629],
            'China': [35.8617, 104.1954],
            'Japan': [36.2048, 138.2529],
            'Germany': [51.1657, 10.4515],
            'France': [46.2276, 2.2137],
            'Canada': [56.1304, -106.3468],
            'Australia': [-25.2744, 133.7751]
        }
    
    def extract_location(self, text: str) -> str:
        """Extract location from review text"""
        text_upper = text.upper()
        
        for country, pattern in self.location_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return country
        
        return 'Unknown'
    
    def analyze_geographic_sentiment(self, reviews_df: pd.DataFrame) -> Dict:
        """
        Analyze sentiment distribution by location
        Returns: {'by_country': Dict, 'map_data': List}
        """
        if reviews_df.empty:
            return {'by_country': {}, 'map_data': []}
        
        # Extract locations
        reviews_df['location'] = reviews_df['review_text'].apply(self.extract_location)
        
        # Group by location and sentiment
        location_sentiment = reviews_df.groupby(['location', 'sentiment']).size().unstack(fill_value=0)
        
        by_country = {}
        map_data = []
        
        for country in location_sentiment.index:
            if country == 'Unknown':
                continue
            
            pos = location_sentiment.loc[country].get('positive', 0)
            neg = location_sentiment.loc[country].get('negative', 0)
            neu = location_sentiment.loc[country].get('neutral', 0)
            total = pos + neg + neu
            
            if total > 0:
                sentiment_score = (pos - neg) / total
                
                by_country[country] = {
                    'positive': int(pos),
                    'negative': int(neg),
                    'neutral': int(neu),
                    'total': int(total),
                    'sentiment_score': round(sentiment_score, 3)
                }
                
                # Add to map data
                if country in self.country_coords:
                    coords = self.country_coords[country]
                    # Intensity based on total reviews
                    intensity = min(total / 10.0, 1.0)
                    map_data.append({
                        'lat': coords[0],
                        'lon': coords[1],
                        'country': country,
                        'intensity': intensity,
                        'sentiment_score': sentiment_score
                    })
        
        return {
            'by_country': by_country,
            'map_data': map_data
        }
    
    def create_sentiment_heatmap(self, map_data: List[Dict], save_path: str = 'sentiment_map.html'):
        """Create an interactive heatmap of sentiments"""
        if not map_data:
            return None
        
        # Create base map
        m = folium.Map(location=[20, 0], zoom_start=2)
        
        # Add markers for each country
        for point in map_data:
            color = 'green' if point['sentiment_score'] > 0.2 else 'red' if point['sentiment_score'] < -0.2 else 'orange'
            
            folium.CircleMarker(
                location=[point['lat'], point['lon']],
                radius=point['intensity'] * 20,
                popup=f"{point['country']}<br>Sentiment: {point['sentiment_score']:.2f}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6
            ).add_to(m)
        
        # Save map
        m.save(save_path)
        return save_path


class VoiceCommandProcessor:
    """Process voice commands for hands-free interaction"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.commands = {
            'analyze': ['analyze', 'analyse', 'search', 'find', 'show'],
            'product': ['product', 'item', 'reviews for'],
            'filter': ['filter', 'only show', 'display only'],
            'positive': ['positive', 'good', 'happy'],
            'negative': ['negative', 'bad', 'complaints']
        }
    
    def listen(self, timeout: int = 5) -> str:
        """
        Listen to microphone and convert speech to text
        Returns: transcribed text or empty string
        """
        try:
            with sr.Microphone() as source:
                print("Listening... (speak now)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)
                
                print("Processing speech...")
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text.lower()
        
        except sr.WaitTimeoutError:
            print("No speech detected")
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except Exception as e:
            print(f"Error: {e}")
            return ""
    
    def parse_command(self, text: str) -> Dict:
        """
        Parse voice command into structured query
        Returns: {'action': str, 'product': str, 'filters': Dict}
        """
        text_lower = text.lower()
        
        command = {
            'action': 'search',
            'product': '',
            'filters': {
                'sentiment': None,
                'source': None
            }
        }
        
        # Detect action
        for action, keywords in self.commands.items():
            if action == 'analyze' and any(kw in text_lower for kw in keywords):
                command['action'] = 'analyze'
                break
        
        # Extract product name
        # Remove command words to isolate product
        cleaned = text_lower
        for keywords in self.commands.values():
            for kw in keywords:
                cleaned = cleaned.replace(kw, '')
        
        # Clean up and extract product
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        command['product'] = cleaned
        
        # Detect sentiment filter
        if any(kw in text_lower for kw in self.commands['positive']):
            command['filters']['sentiment'] = 'positive'
        elif any(kw in text_lower for kw in self.commands['negative']):
            command['filters']['sentiment'] = 'negative'
        
        return command
    
    def process_voice_search(self) -> Dict:
        """
        Complete voice search flow
        Returns: parsed command dictionary
        """
        text = self.listen()
        if text:
            return self.parse_command(text)
        return {'action': None, 'product': '', 'filters': {}}


class ImageAnalyzer:
    """Analyze images from reviews using CLIP"""
    
    def __init__(self):
        try:
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.available = True
            print("Image analyzer loaded successfully")
        except Exception as e:
            print(f"Could not load CLIP model: {e}")
            self.available = False
    
    def analyze_image_sentiment(self, image_url: str) -> Dict:
        """
        Analyze sentiment from product images
        Returns: {'sentiment': str, 'confidence': float, 'categories': Dict}
        """
        if not self.available:
            return {'sentiment': 'neutral', 'confidence': 0.0, 'categories': {}}
        
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            image = Image.open(BytesIO(response.content))
            
            # Define sentiment labels
            labels = [
                "happy customer with product",
                "disappointed customer with product",
                "damaged product",
                "high quality product",
                "poor quality product",
                "satisfied user"
            ]
            
            # Process with CLIP
            inputs = self.processor(
                text=labels,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
            
            # Get results
            scores = probs[0].tolist()
            categories = {label: round(score, 3) for label, score in zip(labels, scores)}
            
            # Determine overall sentiment
            positive_score = sum([
                categories.get("happy customer with product", 0),
                categories.get("high quality product", 0),
                categories.get("satisfied user", 0)
            ])
            
            negative_score = sum([
                categories.get("disappointed customer with product", 0),
                categories.get("damaged product", 0),
                categories.get("poor quality product", 0)
            ])
            
            if positive_score > negative_score:
                sentiment = "positive"
                confidence = positive_score
            else:
                sentiment = "negative"
                confidence = negative_score
            
            return {
                'sentiment': sentiment,
                'confidence': round(confidence, 3),
                'categories': categories
            }
        
        except Exception as e:
            print(f"Image analysis error: {e}")
            return {'sentiment': 'neutral', 'confidence': 0.0, 'categories': {}}
    
    def detect_objects(self, image_url: str, categories: List[str]) -> Dict:
        """
        Detect specific objects in image
        Returns: {'detected': List[str], 'scores': Dict}
        """
        if not self.available:
            return {'detected': [], 'scores': {}}
        
        try:
            response = requests.get(image_url, timeout=10)
            image = Image.open(BytesIO(response.content))
            
            inputs = self.processor(
                text=categories,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            outputs = self.model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1)[0]
            
            scores = {cat: round(prob.item(), 3) for cat, prob in zip(categories, probs)}
            detected = [cat for cat, score in scores.items() if score > 0.3]
            
            return {
                'detected': detected,
                'scores': scores
            }
        
        except Exception as e:
            print(f"Object detection error: {e}")
            return {'detected': [], 'scores': {}}


# Testing
if __name__ == "__main__":
    print("Testing Advanced Features...\n")
    
    # Test multilingual
    print("1. Testing Multilingual Processor")
    ml_processor = MultilingualProcessor()
    result = ml_processor.translate_to_english("Este producto es excelente")
    print(f"Translation: {result['translated_text']}")
    print(f"Source language: {result['source_lang']}\n")
    
    # Test geographic
    print("2. Testing Geographic Analyzer")
    geo_analyzer = GeographicAnalyzer()
    sample_df = pd.DataFrame({
        'review_text': [
            'Great product in the US',
            'Love it from India',
            'Bad quality in UK'
        ],
        'sentiment': ['positive', 'positive', 'negative']
    })
    geo_results = geo_analyzer.analyze_geographic_sentiment(sample_df)
    print(f"Geographic analysis: {geo_results['by_country']}\n")
    
    # Test voice (commented out - requires microphone)
    # print("3. Testing Voice Command Processor")
    # voice_processor = VoiceCommandProcessor()
    # print("Say: 'Analyze iPhone 15 reviews'")
    # command = voice_processor.process_voice_search()
    # print(f"Parsed command: {command}")