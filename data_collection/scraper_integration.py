"""
data_collection/scraper_integration.py

Integration layer for scrapers with database storage
"""

import logging
from typing import Dict, List
from database.connection import get_database_connection
from data_collection.unified_review_fetcher import UnifiedReviewFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewCollector:
    """Collect reviews and store them in the database"""
    
    def __init__(self):
        self.fetcher = None
    
    def collect_and_store(
        self, 
        product_url: str, 
        source: str, 
        max_reviews: int = 50
    ) -> Dict:
        """
        Collect reviews from a source and store in database
        
        Args:
            product_url: Product URL
            source: 'Amazon' or 'Flipkart'
            max_reviews: Maximum reviews to collect
        
        Returns:
            Dict with results
        """
        try:
            # Initialize fetcher
            self.fetcher = UnifiedReviewFetcher(
                use_selenium=True,
                headless=True,
                sentiment_backend="vader",
                use_real_social_apis=False
            )
            
            # Fetch reviews
            logger.info(f"Fetching reviews from {source}: {product_url}")
            results = self.fetcher.fetch_and_analyze_from_url(product_url, max_reviews)
            
            reviews = results.get('reviews', [])
            
            if not reviews:
                return {
                    'error': 'No reviews found',
                    'total_scraped': 0,
                    'success_count': 0,
                    'failed_count': 0
                }
            
            # Store reviews in database
            success_count = 0
            failed_count = 0
            
            for review in reviews:
                if self.store_review_in_db(review, product_url, source):
                    success_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"Stored {success_count}/{len(reviews)} reviews in database")
            
            return {
                'total_scraped': len(reviews),
                'success_count': success_count,
                'failed_count': failed_count,
                'product_url': product_url,
                'source': source
            }
            
        except Exception as e:
            logger.error(f"Error in collect_and_store: {str(e)}")
            return {
                'error': str(e),
                'total_scraped': 0,
                'success_count': 0,
                'failed_count': 0
            }
        
        finally:
            if self.fetcher:
                self.fetcher.close()
    
    def store_review_in_db(
        self, 
        review_data: Dict, 
        product_url: str, 
        source_name: str
    ) -> bool:
        """
        Store a single review in the database
        
        Args:
            review_data: Review dictionary
            product_url: Product URL (CRITICAL for filtering)
            source_name: Source name
        
        Returns:
            True if successful, False otherwise
        """
        conn = get_database_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Get or create source_id
            cursor.execute("SELECT id FROM data_sources WHERE name = %s", (source_name,))
            result = cursor.fetchone()
            if result:
                source_id = result[0]
            else:
                cursor.execute("INSERT INTO data_sources (name) VALUES (%s)", (source_name,))
                source_id = cursor.lastrowid
            
            # CRITICAL: Store product_url along with review
            insert_query = """
            INSERT INTO raw_reviews 
            (product_name, product_url, review_text, rating, reviewer, 
             review_date, source_id, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                review_data.get('product_name'),
                product_url,  # CRITICAL: Store the URL
                review_data.get('review_text'),
                review_data.get('rating'),
                review_data.get('reviewer', 'Anonymous'),
                review_data.get('review_date'),
                source_id,
                review_data.get('language', 'en')
            ))
            
            review_id = cursor.lastrowid
            
            # Store sentiment analysis
            sentiment = review_data.get('sentiment_analysis', {})
            if sentiment:
                # Extract keywords
                pos_keywords = sentiment.get('positive_keywords', [])
                neg_keywords = sentiment.get('negative_keywords', [])
                
                analysis_query = """
                INSERT INTO analysis_results 
                (review_id, sentiment, sentiment_score, positive_words, negative_words)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(analysis_query, (
                    review_id,
                    sentiment.get('sentiment'),
                    sentiment.get('score'),
                    ','.join(pos_keywords) if pos_keywords else None,
                    ','.join(neg_keywords) if neg_keywords else None
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing review: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()