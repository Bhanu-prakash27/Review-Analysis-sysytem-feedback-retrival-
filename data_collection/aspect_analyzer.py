"""
Flipkart Review Analyzer - FIXED VERSION
Corrected aspect detection with lemmatization and improved matching
"""

import json
import re
from collections import defaultdict
from typing import List, Dict, Tuple
from textblob import TextBlob
import logging

# Setup logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NLTK setup with lemmatization support
try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('taggers/averaged_perceptron_tagger')
        nltk.data.find('corpora/wordnet')
    except LookupError:
        logger.info("Downloading required NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
    NLTK_AVAILABLE = True
    lemmatizer = WordNetLemmatizer()
except Exception as e:
    NLTK_AVAILABLE = False
    lemmatizer = None
    logger.warning(f"NLTK not available: {e}")


# Category and competitor mapping
BRAND_TO_CATEGORY = {
    "Samsung": "mobile", "Realme": "mobile", "Vivo": "mobile", "Oppo": "mobile",
    "OnePlus": "mobile", "Apple": "mobile", "Motorola": "mobile", "Xiaomi": "mobile",
    "HP": "laptop", "Dell": "laptop", "Lenovo": "laptop", "Asus": "laptop", "Acer": "laptop",
    "Sony": "television", "LG": "television", "TCL": "television",
    "Boat": "audio", "Noise": "audio", "JBL": "audio",
    "Bata": "footwear", "Sparx": "footwear", "Puma": "footwear", "Nike": "footwear",
    "Whirlpool": "home_appliance", "Godrej": "home_appliance", "Haier": "home_appliance"
}

COMPETITOR_MAP = {
    "mobile": ["Samsung", "Realme", "Vivo", "Oppo", "OnePlus", "Apple", "Motorola", "Xiaomi"],
    "laptop": ["HP", "Dell", "Lenovo", "Asus", "Acer", "Apple"],
    "television": ["Sony", "LG", "TCL", "Samsung", "Mi"],
    "audio": ["Boat", "Noise", "JBL", "Sony", "Realme"],
    "footwear": ["Bata", "Sparx", "Puma", "Nike", "Adidas", "Campus"],
    "fashion": ["Zara", "H&M", "Max", "Allen Solly", "Peter England"],
    "home_appliance": ["Whirlpool", "Godrej", "Haier", "LG", "Samsung"],
}


def detect_product_category(product_name: str) -> str:
    """Infer product category from product name"""
    name = product_name.lower()
    
    # Check brand first
    for brand, category in BRAND_TO_CATEGORY.items():
        if brand.lower() in name:
            return category if isinstance(category, str) else category[0]
    
    # Check keywords
    if any(k in name for k in ["phone", "mobile", "smartphone", "5g"]):
        return "mobile"
    elif any(k in name for k in ["laptop", "notebook", "macbook", "chromebook"]):
        return "laptop"
    elif any(k in name for k in ["tv", "television", "smart tv", "qled"]):
        return "television"
    elif any(k in name for k in ["earphone", "headphone", "earbud", "speaker", "soundbar"]):
        return "audio"
    elif any(k in name for k in ["shoe", "slipper", "sandal", "boot", "sneaker"]):
        return "footwear"
    elif any(k in name for k in ["shirt", "pant", "jean", "dress", "tshirt", "kurti"]):
        return "fashion"
    elif any(k in name for k in ["refrigerator", "washing", "microwave", "ac", "cooler"]):
        return "home_appliance"
    else:
        return "general"


def recommend_competitors(product_name: str) -> Dict:
    """Suggest competitor brands based on detected category"""
    category = detect_product_category(product_name)
    competitors = COMPETITOR_MAP.get(category, [])
    
    # Remove same brand if detected
    detected_brand = None
    for brand in BRAND_TO_CATEGORY.keys():
        if brand.lower() in product_name.lower():
            detected_brand = brand
            break
    
    if detected_brand:
        competitors = [c for c in competitors if c.lower() != detected_brand.lower()]
    
    return {
        "category": category,
        "detected_brand": detected_brand,
        "competitors": competitors[:5]
    }


class FlipkartReviewAnalyzer:
    """Enhanced Flipkart review analyzer with FIXED aspect detection"""
    
    def __init__(self):
        # EXPANDED aspect keywords with variations and lemmatized forms
        self.aspect_keywords = {
            'battery': ['battery', 'batteries', 'charge', 'charges', 'charging', 'charged', 
                       'backup', 'power', 'mah', 'juice', 'drain', 'draining', 'life'],
            'display': ['display', 'displays', 'screen', 'screens', 'brightness', 'bright',
                       'touch', 'resolution', 'amoled', 'lcd', 'oled', 'refresh', 'panel'],
            'performance': ['performance', 'perform', 'performs', 'speed', 'fast', 'faster', 
                          'slow', 'slower', 'lag', 'lags', 'lagging', 'laggy', 'processor', 
                          'ram', 'smooth', 'smoothly', 'multitask', 'multitasking', 'hang', 'hangs'],
            'design': ['design', 'designed', 'look', 'looks', 'looking', 'build', 'built', 
                      'quality', 'premium', 'body', 'finish', 'finishing', 'aesthetic', 
                      'aesthetics', 'appearance', 'sleek'],
            'camera': ['camera', 'cameras', 'photo', 'photos', 'picture', 'pictures', 'pic', 
                      'video', 'videos', 'selfie', 'selfies', 'lens', 'megapixel', 'mp',
                      'clarity', 'zoom', 'zooming', 'shot', 'shots'],
            'sound': ['sound', 'sounds', 'audio', 'speaker', 'speakers', 'music', 'volume', 
                     'loud', 'loudness', 'headphone', 'headphones', 'bass', 'treble', 'clarity'],
            'price': ['price', 'prices', 'priced', 'value', 'worth', 'money', 'expensive', 
                     'cheap', 'cheaper', 'affordable', 'cost', 'costs', 'costly', 'vfm', 
                     'overpriced', 'budget'],
            'software': ['software', 'ui', 'update', 'updates', 'updated', 'android', 'ios',
                        'interface', 'app', 'apps', 'system', 'bloatware', 'os'],
            'heating': ['heat', 'heats', 'heated', 'heating', 'warm', 'warmer', 'hot', 
                       'hotter', 'temperature', 'thermal', 'overheat', 'overheating'],
            'durability': ['durable', 'durability', 'lasting', 'last', 'lasts', 'sturdy', 
                          'fragile', 'break', 'breaks', 'broken', 'scratch', 'scratches', 
                          'scratched'],
            'delivery': ['delivery', 'delivered', 'shipping', 'shipped', 'packaging', 
                        'package', 'packed', 'box', 'boxed', 'received', 'receive'],
            'service': ['service', 'services', 'support', 'warranty', 'replacement', 
                       'replace', 'customer', 'care', 'helpline']
        }
        
        # Category-specific aspect activation map
        # Only aspects listed for a category will be considered during detection
        # This prevents irrelevant aspects (e.g., 'camera' for ACs) from appearing
        self.category_aspects = {
            'mobile': [
                'battery', 'display', 'performance', 'design', 'camera', 'sound',
                'price', 'software', 'heating', 'durability', 'delivery', 'service'
            ],
            'laptop': [
                'battery', 'display', 'performance', 'design', 'sound', 'price',
                'software', 'heating', 'durability', 'delivery', 'service'
            ],
            'television': [
                'display', 'sound', 'price', 'design', 'durability', 'delivery', 'service'
            ],
            'audio': [
                'sound', 'price', 'design', 'durability', 'delivery', 'service'
            ],
            'footwear': [
                'price', 'design', 'durability', 'delivery', 'service'
            ],
            'fashion': [
                'price', 'design', 'durability', 'delivery', 'service'
            ],
            # Home appliances (e.g., AC, refrigerator, washer) use appliance-specific aspects below
            'home_appliance': [
                'cooling', 'power_consumption', 'noise', 'installation', 'service',
                'durability', 'price', 'design', 'delivery'
            ],
            'general': [
                'price', 'design', 'durability', 'delivery', 'service'
            ]
        }
        
        # Add appliance-specific aspects and keywords (e.g., for ACs)
        self.aspect_keywords.update({
            'cooling': ['cool', 'cooling', 'chill', 'chilling', 'cold', 'temperature', 'hot room', 'heat wave'],
            'power_consumption': ['power', 'electricity', 'units', 'consumption', 'energy', 'efficient', 'inverter', 'star rating'],
            'noise': ['noise', 'noisy', 'silent', 'quiet', 'sound', 'humming', 'vibration'],
            'installation': ['install', 'installation', 'installed', 'technician', 'fitting', 'mounting', 'pipes', 'drain', 'outdoor unit'],
            'remote': ['remote', 'remote control', 'buttons', 'display panel', 'led panel'],
            'airflow': ['airflow', 'swing', 'throw', 'vent', 'air throw', 'fan speed'],
            'compressor': ['compressor', 'coolant', 'gas', 'refrigerant', 'condenser', 'evaporator']
        })
        
        # Enhanced sentiment words
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'fantastic', 'love', 'loved', 'best',
            'awesome', 'perfect', 'superb', 'outstanding', 'brilliant', 'nice', 'satisfied',
            'happy', 'impressed', 'impressive', 'recommend', 'recommended', 'solid', 'worth', 
            'pleased', 'delighted', 'wonderful', 'fabulous', 'incredible', 'superior', 'top'
        }
        
        self.negative_words = {
            'bad', 'poor', 'terrible', 'worst', 'awful', 'disappointing', 'disappointed', 
            'useless', 'waste', 'pathetic', 'horrible', 'issue', 'issues', 'problem', 
            'problems', 'defect', 'defective', 'broken', 'regret', 'avoid', 'faulty', 
            'damaged', 'fail', 'fails', 'failed', 'cheap', 'hate', 'hated', 'never', 'not'
        }
    
    def _lemmatize_text(self, text: str) -> str:
        """
        Lemmatize text to normalize word forms
        FIX: This ensures "charging" matches "charge", etc.
        """
        if not NLTK_AVAILABLE or not lemmatizer:
            return text
        
        try:
            tokens = nltk.word_tokenize(text.lower())
            lemmatized = [lemmatizer.lemmatize(token) for token in tokens]
            return ' '.join(lemmatized)
        except Exception as e:
            logger.debug(f"Lemmatization failed: {e}")
            return text.lower()
    
    def analyze_reviews(self, product_name: str, reviews: List) -> Dict:
        """Main analysis function with enhanced error handling"""
        if not reviews:
            return self._empty_analysis(product_name)
        
        # Detect category and competitors
        rec_data = recommend_competitors(product_name)
        category = rec_data["category"]
        competitors = rec_data["competitors"]
        
        logger.info(f"Analyzing {product_name} | Category: {category} | Reviews: {len(reviews)}")
        
        # Clean and normalize reviews
        clean_reviews = self._clean_reviews(reviews)
        logger.info(f"Cleaned reviews: {len(clean_reviews)}")
        
        # Extract aspects and sentiments (filtered by category)
        aspect_sentiments = self._analyze_aspects(clean_reviews, category)
        logger.info(f"Detected aspects: {list(aspect_sentiments.keys())}")
        
        # Generate overall feedback
        overall_feedback = self._generate_overall_feedback(clean_reviews, aspect_sentiments)
        
        # Extract key themes
        key_themes = self._extract_key_themes(clean_reviews)
        
        # Generate competitor recommendations
        competitors_data = self._build_competitor_recommendations(
            product_name, category, competitors, aspect_sentiments
        )
        
        # Build structured response
        return {
            "product_name": product_name,
            "category": category,
            "overall_feedback": overall_feedback,
            "aspects": aspect_sentiments,
            "summary": self._build_summary(aspect_sentiments),
            "key_themes": key_themes,
            "recommended_products": competitors_data,
            "review_count": len(clean_reviews),
            "analysis_confidence": self._calculate_confidence(clean_reviews, aspect_sentiments)
        }
    
    def _clean_reviews(self, reviews: List) -> List[str]:
        clean = []
        for r in reviews:
            text = ""
            if isinstance(r, dict):
            # Try all possible field names that might hold text
                text = (
                    r.get("review_text")
                    or r.get("review")
                    or r.get("text")
                    or r.get("body")
                    or r.get("content")
                    or ""
                )
            else:
                text = str(r)

            text = str(text).strip()
            if text:
                clean.append(text)
        return clean

    def _analyze_aspects(self, reviews: List[str], category: str = None) -> Dict:
        """
        FIXED aspect extraction with improved detection
        FIX #1: Removed minimum threshold (was >= 2, now >= 1)
        FIX #2: Added lemmatization for better keyword matching
        FIX #3: Added detailed logging for debugging
        """
        aspect_data = defaultdict(lambda: {
            'positive': 0, 'negative': 0, 'neutral': 0, 'mentions': []
        })
        
        logger.info("=" * 60)
        logger.info("STARTING ASPECT ANALYSIS")
        logger.info("=" * 60)
        
        # Determine active aspects for this category
        active_aspects = set(self.aspect_keywords.keys())
        if category and category in self.category_aspects:
            active_aspects = set(self.category_aspects[category])
        
        for idx, review in enumerate(reviews):
            if not review:
                continue
            
            review_lower = review.lower()
            # FIX: Apply lemmatization to normalize word forms
            review_lemmatized = self._lemmatize_text(review)
            
            # Calculate review-level sentiment
            review_sentiment = self._get_sentence_sentiment(review)
            logger.info(f"\nReview #{idx + 1}: '{review[:80]}...'")
            logger.info(f"  Sentiment: {review_sentiment}")
            
            detected_in_review = []
            
            # Method 1: Enhanced keyword-based detection with lemmatization
            for aspect_name, keywords in self.aspect_keywords.items():
                if aspect_name not in active_aspects:
                    continue
                # FIX: Check both original and lemmatized versions
                matched = False
                matched_keyword = None
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    # Check in original text
                    if keyword_lower in review_lower:
                        matched = True
                        matched_keyword = keyword
                        break
                    # Check in lemmatized text
                    if keyword_lower in review_lemmatized:
                        matched = True
                        matched_keyword = keyword
                        break
                
                if matched:
                    aspect_data[aspect_name][review_sentiment] += 1
                    aspect_data[aspect_name]['mentions'].append(review[:150])
                    detected_in_review.append(f"{aspect_name}({matched_keyword})")
            
            if detected_in_review:
                logger.info(f"  Detected aspects: {', '.join(detected_in_review)}")
            else:
                logger.info(f"  No aspects detected")
            
            # Method 2: POS tagging (if NLTK available)
            if NLTK_AVAILABLE:
                try:
                    pos_aspects = self._extract_pos_aspects(review)
                    for aspect, sentiment in pos_aspects:
                        aspect_data[aspect][sentiment] += 1
                        aspect_data[aspect]['mentions'].append(review[:150])
                        logger.info(f"  POS detected: {aspect} ({sentiment})")
                except Exception as e:
                    logger.debug(f"POS tagging failed: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("ASPECT DETECTION SUMMARY")
        logger.info("=" * 60)
        
        # Convert to final format
        final_aspects = {}
        for aspect, data in aspect_data.items():
            total = data['positive'] + data['negative'] + data['neutral']
            # FIX: Changed threshold from >= 2 to >= 1 (detect even single mentions)
            if total >= 1:
                logger.info(f"{aspect.capitalize()}: {total} mentions "
                          f"(+{data['positive']} -{data['negative']} ={data['neutral']})")
                final_aspects[aspect.capitalize()] = self._format_aspect_result(aspect, data)
        
        # FIX: Only add "General" if NO aspects were detected
        if not final_aspects:
            logger.warning("No aspects detected in any reviews!")
            final_aspects["General"] = {
                "sentiment": "neutral",
                "reason": "No specific aspects identified in reviews"
            }
        else:
            logger.info(f"\nTotal aspects detected: {len(final_aspects)}")
        
        logger.info("=" * 60 + "\n")
        
        return final_aspects
    
    def _extract_pos_aspects(self, text: str) -> List[Tuple[str, str]]:
        """Extract aspects using POS tagging"""
        aspects = []
        clean_text = re.sub(r"[^a-zA-Z0-9\s]", "", text.lower())
        
        try:
            tokens = nltk.word_tokenize(clean_text)
            pos_tags = nltk.pos_tag(tokens)
            
            # Look for adjective + noun patterns
            for i in range(len(pos_tags) - 1):
                word, tag = pos_tags[i]
                next_word, next_tag = pos_tags[i + 1]
                
                if tag.startswith("JJ") and next_tag.startswith("NN"):
                    # Determine sentiment from adjective
                    if word in self.positive_words:
                        aspects.append((next_word, 'positive'))
                    elif word in self.negative_words:
                        aspects.append((next_word, 'negative'))
        except Exception as e:
            logger.debug(f"POS extraction error: {e}")
        
        return aspects
    
    def _format_aspect_result(self, aspect_name: str, data: Dict) -> Dict:
        """Format aspect data into consistent structure"""
        total = data['positive'] + data['negative'] + data['neutral']
        if total == 0:
            return {"sentiment": "neutral", "reason": "Not mentioned", "count": 0}
        
        pos_ratio = data['positive'] / total
        neg_ratio = data['negative'] / total
        
        # FIX: Adjusted thresholds for better sentiment classification
        if pos_ratio > 0.5:  # Changed from 0.6 to 0.5
            sentiment = "positive"
        elif neg_ratio > 0.5:  # Changed from 0.6 to 0.5
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        reason = self._generate_aspect_reason(aspect_name, sentiment, data)
        
        return {
            "sentiment": sentiment,
            "reason": reason,
            "count": total,
            "distribution": {
                "positive": data['positive'],
                "negative": data['negative'],
                "neutral": data['neutral']
            }
        }
    
    def _generate_aspect_reason(self, aspect: str, sentiment: str, data: Dict) -> str:
        """Generate natural language reason for aspect sentiment"""
        total = data['positive'] + data['negative'] + data['neutral']
        
        templates = {
            "positive": f"Users praised {aspect} in {data['positive']}/{total} mentions",
            "negative": f"Users complained about {aspect} in {data['negative']}/{total} mentions",
            "neutral": f"Mixed opinions on {aspect} across {total} mentions"
        }
        
        return templates.get(sentiment, f"Mentioned {total} times")
    
    def _get_sentence_sentiment(self, text: str) -> str:
        """
        Enhanced sentiment detection with better accuracy
        FIX: Improved word boundary detection and negation handling
        """
        if isinstance(text, dict):
            text = text.get("review", "")
        
        text_lower = text.lower()
        
        # FIX: Use word boundaries for better matching
        words = re.findall(r'\b\w+\b', text_lower)
        
        pos_count = sum(1 for word in words if word in self.positive_words)
        neg_count = sum(1 for word in words if word in self.negative_words)
        
        # Use TextBlob as additional signal
        polarity = TextBlob(text).sentiment.polarity
        
        # FIX: Improved decision logic
        if pos_count > neg_count and polarity >= 0:
            return 'positive'
        elif neg_count > pos_count and polarity <= 0:
            return 'negative'
        elif polarity > 0.2:
            return 'positive'
        elif polarity < -0.2:
            return 'negative'
        else:
            return 'neutral'
    
    def _generate_overall_feedback(self, reviews: List[str], aspects: Dict) -> str:
        """Generate comprehensive overall feedback"""
        sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for r in reviews:
            sent = self._get_sentence_sentiment(r)
            sentiments[sent] += 1
        
        total = sum(sentiments.values()) or 1
        pos_pct = sentiments['positive'] / total * 100
        neg_pct = sentiments['negative'] / total * 100
        
        positives = [k for k, v in aspects.items() if v['sentiment'] == 'positive']
        negatives = [k for k, v in aspects.items() if v['sentiment'] == 'negative']
        
        if pos_pct > 60:
            feedback = f"Highly recommended product with {pos_pct:.0f}% positive reviews. "
            if positives:
                feedback += f"Strong points: {', '.join(positives[:3])}. "
            if negatives:
                feedback += f"Minor concerns: {', '.join(negatives[:2])}."
        elif neg_pct > 50:
            feedback = f"Product has significant issues ({neg_pct:.0f}% negative reviews). "
            if negatives:
                feedback += f"Main problems: {', '.join(negatives[:3])}. "
            feedback += "Consider alternatives carefully."
        else:
            feedback = f"Mixed reviews ({pos_pct:.0f}% positive, {neg_pct:.0f}% negative). "
            if positives:
                feedback += f"Strengths: {', '.join(positives[:2])}. "
            if negatives:
                feedback += f"Weaknesses: {', '.join(negatives[:2])}."
        
        return feedback.strip()
    
    def _build_summary(self, aspects: Dict) -> str:
        """Build readable summary from aspects"""
        lines = []
        for aspect, data in sorted(aspects.items(), 
                                   key=lambda x: x[1].get('count', 0), 
                                   reverse=True)[:5]:
            sentiment = data['sentiment'].capitalize()
            reason = data['reason']
            lines.append(f"• {aspect}: {sentiment} - {reason}")
        
        return "\n".join(lines) if lines else "Limited feedback available"
    
    def _extract_key_themes(self, reviews: List[str]) -> List[Dict]:
        """Extract common feedback themes"""
        themes = []
        theme_patterns = {
            "Value for Money": ["value", "price", "worth", "money", "vfm"],
            "Build Quality": ["quality", "build", "premium", "material", "construction"],
            "User Experience": ["experience", "easy", "user", "interface", "usability"],
            "Reliability": ["reliable", "durable", "lasting", "trust", "dependable"],
            "After Sales": ["service", "support", "warranty", "replacement", "customer"]
        }
        
        for name, keywords in theme_patterns.items():
            mentions = [r for r in reviews if any(k in r.lower() for k in keywords)]
            # FIX: Changed from >= 2 to >= 1
            if len(mentions) >= 1:
                sentiment = self._analyze_theme_sentiment(mentions)
                themes.append({
                    "theme": name,
                    "sentiment": sentiment["sentiment"],
                    "reason": sentiment["reason"],
                    "mention_count": len(mentions)
                })
        
        return sorted(themes, key=lambda x: x['mention_count'], reverse=True)[:5]
    
    def _analyze_theme_sentiment(self, mentions: List[str]) -> Dict:
        """Analyze sentiment for a theme"""
        sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
        for m in mentions:
            sent = self._get_sentence_sentiment(m)
            sentiments[sent] += 1
        
        total = sum(sentiments.values())
        if sentiments['positive'] > sentiments['negative']:
            return {
                "sentiment": "positive",
                "reason": f"Positive feedback in {sentiments['positive']}/{total} reviews"
            }
        elif sentiments['negative'] > sentiments['positive']:
            return {
                "sentiment": "negative",
                "reason": f"Concerns raised in {sentiments['negative']}/{total} reviews"
            }
        else:
            return {
                "sentiment": "neutral",
                "reason": f"Mixed opinions across {total} reviews"
            }
    
    def _build_competitor_recommendations(self, product_name: str, category: str, 
                                         competitors: List[str], aspects: Dict) -> List[Dict]:
        """Build intelligent competitor recommendations"""
        recommendations = []
        
        # Identify weak areas
        weak_aspects = [k.lower() for k, v in aspects.items() if v['sentiment'] == 'negative']
        
        for i, comp in enumerate(competitors[:4]):
            reason = self._generate_competitor_reason(comp, category, weak_aspects, i)
            recommendations.append({
                "name": f"{comp} {category.replace('_', ' ').title()} Series",
                "reason": reason,
                "category": category
            })
        
        return recommendations
    
    def _generate_competitor_reason(self, brand: str, category: str, 
                                   weak_aspects: List[str], index: int) -> str:
        """Generate contextual recommendation reason"""
        reasons = {
            0: f"Alternative {category} option with established brand reputation",
            1: f"Known for reliability in the {category} segment",
            2: f"Popular choice offering competitive features",
            3: f"Budget-friendly alternative in {category} category"
        }
        
        base_reason = reasons.get(index, f"Alternative {category} option")
        
        # Add aspect-specific recommendation if applicable
        if 'battery' in weak_aspects:
            base_reason += " - known for better battery performance"
        elif 'camera' in weak_aspects:
            base_reason += " - strong camera capabilities"
        elif 'performance' in weak_aspects:
            base_reason += " - superior processing power"
        
        return base_reason
    
    def _calculate_confidence(self, reviews: List[str], aspects: Dict) -> str:
        """Calculate analysis confidence level"""
        review_count = len(reviews)
        aspect_count = len([a for a in aspects.keys() if a != "General"])
        
        if review_count >= 20 and aspect_count >= 5:
            return "High"
        elif review_count >= 10 and aspect_count >= 3:
            return "Medium"
        else:
            return "Low"
    
    def _empty_analysis(self, product_name: str) -> Dict:
        """Return structure for products with no reviews"""
        return {
            "product_name": product_name,
            "category": detect_product_category(product_name),
            "overall_feedback": "No reviews available for analysis",
            "aspects": {},
            "summary": "No customer feedback found",
            "key_themes": [],
            "recommended_products": [],
            "review_count": 0,
            "analysis_confidence": "None"
        }


# Example usage and testing
if __name__ == "__main__":
    analyzer = FlipkartReviewAnalyzer()
    
    # Test case
    product = "Samsung Galaxy M34 5G"
    sample_reviews = [
        "Excellent battery life! Lasts 2 days easily with moderate use.",
        "Display is vibrant and bright. AMOLED quality is superb.",
        "Performance is smooth for daily tasks but heats during heavy gaming.",
        "Good value for money. Camera quality could be better though.",
        "Build quality feels premium. Very satisfied with purchase.",
        "Charging speed is decent but not the fastest.",
        "UI is clean but comes with some bloatware apps.",
        "Speaker sound quality is average, not great for media consumption."
    ]
    
    print("\n" + "="*70)
    print("TESTING FIXED FLIPKART REVIEW ANALYZER")
    print("="*70 + "\n")
    
    result = analyzer.analyze_reviews(product, sample_reviews)
    
    print("\n" + "="*70)
    print("FINAL ANALYSIS RESULT")
    print("="*70)
    print(json.dumps(result, indent=2))
    
    print("\n" + "="*70)
    print("ASPECTS DETECTED:")
    print("="*70)
    for aspect, data in result['aspects'].items():
        print(f"\n{aspect}:")
        print(f"  Sentiment: {data['sentiment']}")
        print(f"  Reason: {data['reason']}")
        if 'count' in data:
            print(f"  Mentions: {data['count']}")