"""
nlp/sentiment_analyzer.py

Integrated sentiment analysis for review data
Supports multiple NLP backends: VADER, TextBlob, Transformers
"""

import logging
from typing import List, Dict, Optional, Tuple
from collections import Counter
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing NLP libraries
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER not installed. Install: pip install vaderSentiment")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not installed. Install: pip install textblob")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not installed. Install: pip install transformers")


class SentimentAnalyzer:
    """Multi-backend sentiment analyzer"""
    
    def __init__(self, backend: str = "vader"):
        """
        Initialize sentiment analyzer
        
        Args:
            backend: "vader", "textblob", or "transformers"
        """
        self.backend = backend.lower()
        self.analyzer = None
        
        if self.backend == "vader" and VADER_AVAILABLE:
            self.analyzer = SentimentIntensityAnalyzer()
            logger.info("Using VADER for sentiment analysis")
        elif self.backend == "textblob" and TEXTBLOB_AVAILABLE:
            logger.info("Using TextBlob for sentiment analysis")
        elif self.backend == "transformers" and TRANSFORMERS_AVAILABLE:
            try:
                self.analyzer = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english"
                )
                logger.info("Using Transformers for sentiment analysis")
            except Exception as e:
                logger.warning(f"Transformers init failed: {e}")
                self.analyzer = None
        else:
            logger.warning(f"Backend '{backend}' not available, using fallback")
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text
        
        Returns:
            {
                'sentiment': 'positive'|'negative'|'neutral',
                'score': float,  # -1 to 1
                'confidence': float  # 0 to 1
            }
        """
        if not text or len(text.strip()) < 5:
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0
            }
        
        if self.backend == "vader" and self.analyzer:
            return self._analyze_vader(text)
        elif self.backend == "textblob" and TEXTBLOB_AVAILABLE:
            return self._analyze_textblob(text)
        elif self.backend == "transformers" and self.analyzer:
            return self._analyze_transformers(text)
        else:
            return self._analyze_fallback(text)
    
    def _analyze_vader(self, text: str) -> Dict:
        """VADER sentiment analysis"""
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        
        # Classify sentiment
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Calculate confidence
        confidence = abs(compound)
        
        return {
            'sentiment': sentiment,
            'score': compound,
            'confidence': confidence,
            'details': scores
        }
    
    def _analyze_textblob(self, text: str) -> Dict:
        """TextBlob sentiment analysis"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to 1
        
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'score': polarity,
            'confidence': abs(polarity)
        }
    
    def _analyze_transformers(self, text: str) -> Dict:
        """Transformers sentiment analysis"""
        try:
            # Truncate long text
            text = text[:512]
            result = self.analyzer(text)[0]
            
            label = result['label'].lower()
            confidence = result['score']
            
            # Map label to sentiment
            if 'pos' in label:
                sentiment = 'positive'
                score = confidence
            elif 'neg' in label:
                sentiment = 'negative'
                score = -confidence
            else:
                sentiment = 'neutral'
                score = 0.0
            
            return {
                'sentiment': sentiment,
                'score': score,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Transformers analysis error: {e}")
            return self._analyze_fallback(text)
    
    def _analyze_fallback(self, text: str) -> Dict:
        """Simple rule-based fallback sentiment analysis"""
        text_lower = text.lower()
        
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'love', 'best',
            'perfect', 'awesome', 'fantastic', 'wonderful', 'recommend',
            'happy', 'satisfied', 'quality'
        ]
        
        negative_words = [
            'bad', 'poor', 'terrible', 'awful', 'hate', 'worst',
            'disappointing', 'disappointed', 'waste', 'defective',
            'broken', 'useless', 'not recommend', 'refund'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = 'positive'
            score = min(pos_count * 0.2, 1.0)
        elif neg_count > pos_count:
            sentiment = 'negative'
            score = -min(neg_count * 0.2, 1.0)
        else:
            sentiment = 'neutral'
            score = 0.0
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': abs(score)
        }
    
    def analyze_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """
        Add sentiment analysis to list of reviews
        
        Args:
            reviews: List of review dictionaries
        
        Returns:
            Reviews with added 'sentiment_analysis' field
        """
        analyzed_reviews = []
        
        for review in reviews:
            review_copy = review.copy()
            
            # Analyze review text
            text = review.get('review_text', '')
            sentiment_result = self.analyze_text(text)
            
            review_copy['sentiment_analysis'] = sentiment_result
            analyzed_reviews.append(review_copy)
        
        logger.info(f"Analyzed sentiment for {len(analyzed_reviews)} reviews")
        return analyzed_reviews
    
    def generate_summary(self, reviews: List[Dict]) -> Dict:
        """
        Generate summary statistics and insights from analyzed reviews
        
        Args:
            reviews: List of reviews with sentiment_analysis field
        
        Returns:
            Summary dictionary with statistics and insights
        """
        if not reviews:
            return {
                'total_reviews': 0,
                'sentiment_distribution': {},
                'average_rating': 0.0,
                'summary_text': "No reviews available."
            }
        
        # Count sentiments
        sentiments = []
        scores = []
        ratings = []
        
        for review in reviews:
            sentiment_data = review.get('sentiment_analysis', {})
            sentiment = sentiment_data.get('sentiment', 'neutral')
            score = sentiment_data.get('score', 0.0)
            rating = review.get('rating', 3.0)
            
            sentiments.append(sentiment)
            scores.append(score)
            ratings.append(rating)
        
        sentiment_counts = Counter(sentiments)
        total = len(reviews)
        
        # Calculate percentages
        sentiment_dist = {
            'positive': (sentiment_counts.get('positive', 0) / total) * 100,
            'neutral': (sentiment_counts.get('neutral', 0) / total) * 100,
            'negative': (sentiment_counts.get('negative', 0) / total) * 100
        }
        
        avg_sentiment_score = sum(scores) / len(scores) if scores else 0.0
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            sentiment_dist,
            avg_rating,
            avg_sentiment_score,
            total
        )
        
        # Extract key themes
        positive_themes, negative_themes = self._extract_themes(reviews)
        
        return {
            'total_reviews': total,
            'sentiment_distribution': sentiment_dist,
            'sentiment_counts': dict(sentiment_counts),
            'average_rating': round(avg_rating, 2),
            'average_sentiment_score': round(avg_sentiment_score, 3),
            'summary_text': summary_text,
            'positive_themes': positive_themes,
            'negative_themes': negative_themes
        }
    
    def _generate_summary_text(
        self,
        sentiment_dist: Dict,
        avg_rating: float,
        avg_sentiment_score: float,
        total: int
    ) -> str:
        """Generate human-readable summary"""
        pos_pct = sentiment_dist['positive']
        neu_pct = sentiment_dist['neutral']
        neg_pct = sentiment_dist['negative']
        
        # Determine overall sentiment
        if pos_pct >= 60:
            overall = "overwhelmingly positive"
        elif pos_pct >= 45:
            overall = "mostly positive"
        elif neg_pct >= 45:
            overall = "mostly negative"
        elif neg_pct >= 30:
            overall = "mixed with concerns"
        else:
            overall = "mixed"
        
        # Rating assessment
        if avg_rating >= 4.5:
            rating_desc = "excellent"
        elif avg_rating >= 4.0:
            rating_desc = "very good"
        elif avg_rating >= 3.5:
            rating_desc = "good"
        elif avg_rating >= 3.0:
            rating_desc = "average"
        else:
            rating_desc = "below average"
        
        summary = f"Based on {total} reviews, customer sentiment is {overall}. "
        summary += f"{pos_pct:.1f}% of reviews are positive, {neu_pct:.1f}% are neutral, and {neg_pct:.1f}% are negative. "
        summary += f"The average rating is {avg_rating:.1f}/5.0 ({rating_desc}). "
        
        # Add interpretation
        if pos_pct > 60:
            summary += "Customers generally love this product and recommend it highly."
        elif pos_pct > 45 and neg_pct < 20:
            summary += "Most customers are satisfied, though there are some areas for improvement."
        elif neg_pct > 40:
            summary += "Many customers express dissatisfaction. Significant improvements may be needed."
        else:
            summary += "Customer opinions are divided. The product works well for some but not others."
        
        return summary
    
    def _extract_themes(self, reviews: List[Dict]) -> Tuple[List[str], List[str]]:
        """Extract common themes from positive and negative reviews"""
        positive_reviews = [
            r['review_text'] for r in reviews
            if r.get('sentiment_analysis', {}).get('sentiment') == 'positive'
        ]
        
        negative_reviews = [
            r['review_text'] for r in reviews
            if r.get('sentiment_analysis', {}).get('sentiment') == 'negative'
        ]
        
        # Common positive keywords
        pos_keywords = [
            'quality', 'fast', 'great', 'excellent', 'perfect',
            'durable', 'value', 'recommend', 'easy', 'love'
        ]
        
        # Common negative keywords
        neg_keywords = [
            'broken', 'defective', 'poor', 'slow', 'expensive',
            'waste', 'disappointed', 'not work', 'cheap', 'bad'
        ]
        
        positive_themes = []
        for keyword in pos_keywords:
            count = sum(1 for text in positive_reviews if keyword in text.lower())
            if count > len(positive_reviews) * 0.1:  # 10% threshold
                positive_themes.append(keyword)
        
        negative_themes = []
        for keyword in neg_keywords:
            count = sum(1 for text in negative_reviews if keyword in text.lower())
            if count > len(negative_reviews) * 0.1:
                negative_themes.append(keyword)
        
        return positive_themes[:5], negative_themes[:5]


# Example usage
if __name__ == "__main__":
    # Test sentiment analyzer
    analyzer = SentimentAnalyzer(backend="vader")
    
    test_reviews = [
        {
            "product_name": "Test Product",
            "review_text": "This product is absolutely amazing! Best purchase ever!",
            "rating": 5.0,
            "source": "Test"
        },
        {
            "product_name": "Test Product",
            "review_text": "Terrible quality. Broke after one day. Don't buy!",
            "rating": 1.0,
            "source": "Test"
        },
        {
            "product_name": "Test Product",
            "review_text": "It's okay. Does what it's supposed to do.",
            "rating": 3.0,
            "source": "Test"
        }
    ]
    
    # Analyze reviews
    analyzed = analyzer.analyze_reviews(test_reviews)
    
    # Generate summary
    summary = analyzer.generate_summary(analyzed)
    
    print("\n=== Analysis Results ===")
    for review in analyzed:
        sentiment = review['sentiment_analysis']
        print(f"\nReview: {review['review_text'][:50]}...")
        print(f"Sentiment: {sentiment['sentiment']} (score: {sentiment['score']:.2f})")
    
    print("\n=== Summary ===")
    print(summary['summary_text'])
    print(f"\nPositive themes: {summary['positive_themes']}")
    print(f"Negative themes: {summary['negative_themes']}")