# processing/data_processor.py
"""
Complete data processing pipeline: Collection -> Analysis -> Storage
"""
import sys
import os
from datetime import datetime
from typing import List, Dict
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_database_connection
from analysis.sentiment_analyzer import SentimentAnalyzer, FakeReviewDetector


class DataProcessor:
    """Process and store reviews with NLP analysis"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.fake_detector = FakeReviewDetector()
        self.source_map = self._load_source_map()
    
    def _load_source_map(self) -> Dict[str, int]:
        """Load data source IDs from database"""
        conn = get_database_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM data_sources")
            results = cursor.fetchall()
            return {name.lower(): id for id, name in results}
        except Exception as e:
            print(f"Error loading source map: {e}")
            return {}
        finally:
            conn.close()
    
    def process_and_store_reviews(self, reviews: List[Dict], source_name: str) -> Dict:
        """
        Process reviews with NLP and store in database
        Returns: {success_count, failed_count, errors}
        """
        source_id = self.source_map.get(source_name.lower())
        if not source_id:
            return {
                'success_count': 0,
                'failed_count': len(reviews),
                'error': f"Unknown source: {source_name}"
            }
        
        success_count = 0
        failed_count = 0
        errors = []
        
        conn = get_database_connection()
        if not conn:
            return {
                'success_count': 0,
                'failed_count': len(reviews),
                'error': "Database connection failed"
            }
        
        try:
            cursor = conn.cursor()
            
            for review_data in reviews:
                try:
                    # Extract review fields
                    product_name = review_data.get('product_name', 'Unknown Product')
                    review_text = review_data.get('review_text', '')
                    rating = review_data.get('rating', 0)
                    review_date = review_data.get('review_date', datetime.now().date())
                    language = review_data.get('language', 'en')
                    
                    # Skip empty reviews
                    if not review_text or len(review_text.strip()) < 5:
                        failed_count += 1
                        continue
                    
                    # Insert raw review
                    cursor.execute("""
                        INSERT INTO raw_reviews 
                        (source_id, product_name, review_text, rating, review_date, language)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (source_id, product_name, review_text, rating, review_date, language))
                    
                    review_id = cursor.lastrowid
                    
                    # Perform sentiment analysis
                    sentiment_result = self.sentiment_analyzer.analyze_sentiment(review_text)
                    
                    # Perform aspect analysis
                    aspect_results = self.sentiment_analyzer.analyze_aspects(review_text)
                    
                    # Convert aspects to JSON
                    topics_json = json.dumps(aspect_results) if aspect_results else None
                    
                    # Detect fake reviews
                    fake_result = self.fake_detector.detect_fake(
                        review_text, 
                        rating, 
                        review_length=len(review_text)
                    )
                    
                    # Insert analysis results
                    cursor.execute("""
                        INSERT INTO analysis_results 
                        (review_id, sentiment, sentiment_score, positive_words, 
                         negative_words, topics)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        review_id,
                        sentiment_result['sentiment'],
                        sentiment_result['sentiment_score'],
                        sentiment_result['positive_words'],
                        sentiment_result['negative_words'],
                        topics_json
                    ))
                    
                    # Store fake detection results in metadata (optional separate table)
                    # For now, we'll just log it
                    if fake_result['is_fake']:
                        print(f"⚠️ Potential fake review detected: {fake_result['label']}")
                    
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(str(e))
                    print(f"Error processing review: {e}")
                    continue
            
            conn.commit()
            
        except Exception as e:
            errors.append(str(e))
            print(f"Database error: {e}")
        finally:
            conn.close()
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors[:10]  # Return first 10 errors
        }
    
    def get_competitor_suggestions(self, product_name: str) -> List[str]:
        """
        Get competitor product suggestions based on product name
        Uses predefined mappings and keyword matching
        """
        # Predefined competitor mapping
        competitor_map = {
            'iphone': ['samsung galaxy', 'google pixel', 'oneplus'],
            'samsung galaxy': ['iphone', 'google pixel', 'xiaomi'],
            'nike': ['adidas', 'puma', 'reebok'],
            'adidas': ['nike', 'puma', 'under armour'],
            'macbook': ['dell xps', 'hp spectre', 'lenovo thinkpad'],
            'airpods': ['sony wh', 'bose', 'jabra'],
            'kindle': ['kobo', 'nook', 'tablet'],
        }
        
        product_lower = product_name.lower()
        
        # Check for direct matches
        for key, competitors in competitor_map.items():
            if key in product_lower:
                return competitors
        
        # Generic suggestions based on category keywords
        if any(term in product_lower for term in ['phone', 'mobile', 'smartphone']):
            return ['iphone', 'samsung galaxy', 'google pixel']
        elif any(term in product_lower for term in ['laptop', 'notebook']):
            return ['macbook', 'dell xps', 'hp spectre']
        elif any(term in product_lower for term in ['shoe', 'sneaker']):
            return ['nike', 'adidas', 'puma']
        elif any(term in product_lower for term in ['headphone', 'earphone', 'earbud']):
            return ['airpods', 'sony wh', 'bose']
        
        return []
    
    def compare_products(self, product1: str, product2: str) -> Dict:
        """
        Compare two products based on aspect-level sentiment analysis
        Returns comparative analysis across all aspects
        """
        conn = get_database_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Get reviews for both products
            comparison = {
                'product1': {'name': product1, 'aspects': {}},
                'product2': {'name': product2, 'aspects': {}},
                'winner_by_aspect': {}
            }
            
            for product, key in [(product1, 'product1'), (product2, 'product2')]:
                cursor.execute("""
                    SELECT a.topics, a.sentiment_score
                    FROM analysis_results a
                    JOIN raw_reviews r ON a.review_id = r.id
                    WHERE r.product_name LIKE %s
                """, (f"%{product}%",))
                
                results = cursor.fetchall()
                
                # Aggregate aspect scores
                aspect_scores = {}
                aspect_counts = {}
                
                for topics_json, sentiment_score in results:
                    if topics_json:
                        try:
                            topics = json.loads(topics_json)
                            for aspect, data in topics.items():
                                if aspect not in aspect_scores:
                                    aspect_scores[aspect] = 0
                                    aspect_counts[aspect] = 0
                                aspect_scores[aspect] += data['score']
                                aspect_counts[aspect] += 1
                        except:
                            continue
                
                # Calculate averages
                for aspect in aspect_scores:
                    avg_score = aspect_scores[aspect] / aspect_counts[aspect]
                    comparison[key]['aspects'][aspect] = {
                        'score': round(avg_score, 3),
                        'count': aspect_counts[aspect]
                    }
            
            # Determine winner for each aspect
            all_aspects = set(
                list(comparison['product1']['aspects'].keys()) + 
                list(comparison['product2']['aspects'].keys())
            )
            
            for aspect in all_aspects:
                score1 = comparison['product1']['aspects'].get(aspect, {}).get('score', 0)
                score2 = comparison['product2']['aspects'].get(aspect, {}).get('score', 0)
                
                if score1 > score2:
                    comparison['winner_by_aspect'][aspect] = product1
                elif score2 > score1:
                    comparison['winner_by_aspect'][aspect] = product2
                else:
                    comparison['winner_by_aspect'][aspect] = 'tie'
            
            return comparison
            
        except Exception as e:
            print(f"Error comparing products: {e}")
            return {}
        finally:
            conn.close()


class TrendAnalyzer:
    """Analyze trends and detect spikes in review activity"""
    
    def __init__(self):
        self.threshold_multiplier = 2.5  # Alert when volume is 2.5x average
    
    def detect_trends(self, product_name: str, days: int = 7) -> Dict:
        """
        Detect review volume trends and sentiment shifts
        Returns alerts if unusual activity is detected
        """
        conn = get_database_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Get daily review counts and sentiment
            cursor.execute("""
                SELECT 
                    DATE(r.review_date) as date,
                    COUNT(*) as review_count,
                    AVG(a.sentiment_score) as avg_sentiment,
                    SUM(CASE WHEN a.sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN a.sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count
                FROM raw_reviews r
                JOIN analysis_results a ON r.id = a.review_id
                WHERE r.product_name LIKE %s
                    AND r.review_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE(r.review_date)
                ORDER BY date DESC
            """, (f"%{product_name}%", days))
            
            results = cursor.fetchall()
            
            if not results:
                return {'alerts': [], 'trend': 'no_data'}
            
            # Calculate statistics
            review_counts = [r[1] for r in results]
            avg_volume = sum(review_counts) / len(review_counts)
            
            alerts = []
            
            # Check for volume spike
            latest_volume = review_counts[0]
            if latest_volume > avg_volume * self.threshold_multiplier:
                alerts.append({
                    'type': 'volume_spike',
                    'message': f"Review volume spike detected: {latest_volume} reviews (avg: {avg_volume:.1f})",
                    'severity': 'high'
                })
            
            # Check for sentiment shift
            sentiment_scores = [r[2] for r in results if r[2] is not None]
            if len(sentiment_scores) >= 2:
                recent_sentiment = sentiment_scores[0]
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                
                if abs(recent_sentiment - avg_sentiment) > 0.3:
                    direction = "positive" if recent_sentiment > avg_sentiment else "negative"
                    alerts.append({
                        'type': 'sentiment_shift',
                        'message': f"Significant {direction} sentiment shift detected",
                        'severity': 'medium'
                    })
            
            return {
                'alerts': alerts,
                'avg_volume': round(avg_volume, 1),
                'latest_volume': latest_volume,
                'trend': 'increasing' if len(review_counts) >= 2 and review_counts[0] > review_counts[-1] else 'stable'
            }
            
        except Exception as e:
            print(f"Error detecting trends: {e}")
            return {}
        finally:
            conn.close()


# Example usage and testing
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Test with sample data
    sample_reviews = [
        {
            'product_name': 'iPhone 15 Pro',
            'review_text': 'Amazing camera quality but battery drains fast',
            'rating': 4.0,
            'review_date': datetime.now().date(),
            'language': 'en'
        }
    ]
    
    result = processor.process_and_store_reviews(sample_reviews, 'Amazon')
    print("Processing result:", result)
    
    # Test competitor suggestions
    competitors = processor.get_competitor_suggestions('iPhone 15')
    print("Competitors:", competitors)
    
    # Test trend detection
    trend_analyzer = TrendAnalyzer()
    trends = trend_analyzer.detect_trends('iPhone', days=7)
    print("Trends:", trends)