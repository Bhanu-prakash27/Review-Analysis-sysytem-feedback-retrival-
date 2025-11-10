"""
data_collection/cache.py

Caching layer for review data to minimize repeated scraping
Supports both SQLite and in-memory caching
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from sqlalchemy import create_engine, Column, String, Text, DateTime
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logging.warning("SQLAlchemy not installed. Using in-memory cache only.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if SQLALCHEMY_AVAILABLE:
    class CachedReview(Base):
        """SQLAlchemy model for cached reviews"""
        __tablename__ = 'cached_reviews'
        
        cache_key = Column(String(64), primary_key=True)
        source = Column(String(50))
        identifier = Column(Text)
        reviews_json = Column(Text)
        created_at = Column(DateTime, default=datetime.now)
        expires_at = Column(DateTime)


class ReviewCache:
    """
    Caching system for review data
    
    Features:
    - SQLite backend for persistent caching
    - In-memory fallback when SQLite unavailable
    - Automatic expiration (default: 24 hours)
    - Hash-based cache keys
    """
    
    def __init__(self, db_url: str = "sqlite:///reviews_cache.db", 
                 expiry_hours: int = 24):
        """
        Initialize cache
        
        Args:
            db_url: Database URL (SQLite by default)
            expiry_hours: Hours before cache expires
        """
        self.expiry_hours = expiry_hours
        self.use_db = SQLALCHEMY_AVAILABLE
        self.memory_cache = {}  # Fallback in-memory cache
        
        if self.use_db:
            try:
                self.engine = create_engine(db_url)
                Base.metadata.create_all(self.engine)
                Session = sessionmaker(bind=self.engine)
                self.session = Session()
                logger.info(f"Cache initialized with database: {db_url}")
            except Exception as e:
                logger.warning(f"Database init failed, using in-memory cache: {e}")
                self.use_db = False
        else:
            logger.info("Using in-memory cache")
    
    def _generate_key(self, identifier: str, source: str) -> str:
        """Generate unique cache key"""
        combined = f"{source}:{identifier}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_cached(self, identifier: str, source: str) -> Optional[List[Dict]]:
        """
        Retrieve cached reviews if available and not expired
        
        Args:
            identifier: URL or search term
            source: Review source (amazon, flipkart, twitter, etc.)
        
        Returns:
            List of reviews or None if not cached/expired
        """
        cache_key = self._generate_key(identifier, source)
        
        if self.use_db:
            return self._get_from_db(cache_key)
        else:
            return self._get_from_memory(cache_key)
    
    def set_cached(self, identifier: str, source: str, reviews: List[Dict]):
        """
        Store reviews in cache
        
        Args:
            identifier: URL or search term
            source: Review source
            reviews: List of review dictionaries
        """
        if not reviews:
            return
        
        cache_key = self._generate_key(identifier, source)
        
        if self.use_db:
            self._set_in_db(cache_key, source, identifier, reviews)
        else:
            self._set_in_memory(cache_key, reviews)
        
        logger.info(f"Cached {len(reviews)} reviews for {source}:{identifier[:50]}")
    
    def _get_from_db(self, cache_key: str) -> Optional[List[Dict]]:
        """Get from SQLite database"""
        try:
            cached = self.session.query(CachedReview).filter_by(
                cache_key=cache_key
            ).first()
            
            if not cached:
                return None
            
            # Check expiration
            if cached.expires_at < datetime.now():
                logger.info(f"Cache expired for key {cache_key}")
                self.session.delete(cached)
                self.session.commit()
                return None
            
            # Parse and return reviews
            reviews = json.loads(cached.reviews_json)
            logger.info(f"Cache hit: {len(reviews)} reviews from {cached.source}")
            return reviews
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    def _set_in_db(self, cache_key: str, source: str, identifier: str, 
                   reviews: List[Dict]):
        """Store in SQLite database"""
        try:
            # Convert date objects to strings for JSON serialization
            serializable_reviews = []
            for review in reviews:
                review_copy = review.copy()
                if 'review_date' in review_copy:
                    date_obj = review_copy['review_date']
                    if hasattr(date_obj, 'isoformat'):
                        review_copy['review_date'] = date_obj.isoformat()
                serializable_reviews.append(review_copy)
            
            reviews_json = json.dumps(serializable_reviews, ensure_ascii=False)
            expires_at = datetime.now() + timedelta(hours=self.expiry_hours)
            
            # Check if exists
            existing = self.session.query(CachedReview).filter_by(
                cache_key=cache_key
            ).first()
            
            if existing:
                # Update existing
                existing.reviews_json = reviews_json
                existing.created_at = datetime.now()
                existing.expires_at = expires_at
            else:
                # Create new
                cached = CachedReview(
                    cache_key=cache_key,
                    source=source,
                    identifier=identifier,
                    reviews_json=reviews_json,
                    expires_at=expires_at
                )
                self.session.add(cached)
            
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            self.session.rollback()
    
    def _get_from_memory(self, cache_key: str) -> Optional[List[Dict]]:
        """Get from in-memory cache"""
        if cache_key not in self.memory_cache:
            return None
        
        cached_data = self.memory_cache[cache_key]
        
        # Check expiration
        if cached_data['expires_at'] < datetime.now():
            logger.info(f"Memory cache expired for key {cache_key}")
            del self.memory_cache[cache_key]
            return None
        
        logger.info(f"Memory cache hit: {len(cached_data['reviews'])} reviews")
        return cached_data['reviews']
    
    def _set_in_memory(self, cache_key: str, reviews: List[Dict]):
        """Store in memory cache"""
        self.memory_cache[cache_key] = {
            'reviews': reviews,
            'expires_at': datetime.now() + timedelta(hours=self.expiry_hours)
        }
    
    def clear_cache(self, source: Optional[str] = None):
        """
        Clear cache
        
        Args:
            source: If specified, clear only this source. Otherwise clear all.
        """
        if self.use_db:
            try:
                if source:
                    self.session.query(CachedReview).filter_by(source=source).delete()
                else:
                    self.session.query(CachedReview).delete()
                self.session.commit()
                logger.info(f"Database cache cleared for: {source or 'all'}")
            except Exception as e:
                logger.error(f"Cache clear error: {e}")
                self.session.rollback()
        
        # Clear memory cache
        if source:
            keys_to_delete = [k for k, v in self.memory_cache.items() 
                            if source in str(v)]
            for key in keys_to_delete:
                del self.memory_cache[key]
        else:
            self.memory_cache.clear()
        
        logger.info("Memory cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            'backend': 'database' if self.use_db else 'memory',
            'expiry_hours': self.expiry_hours,
            'memory_entries': len(self.memory_cache)
        }
        
        if self.use_db:
            try:
                total = self.session.query(CachedReview).count()
                expired = self.session.query(CachedReview).filter(
                    CachedReview.expires_at < datetime.now()
                ).count()
                
                stats['database_entries'] = total
                stats['expired_entries'] = expired
                stats['active_entries'] = total - expired
            except Exception as e:
                logger.error(f"Stats error: {e}")
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.use_db and hasattr(self, 'session'):
            try:
                self.session.close()
                logger.info("Cache session closed")
            except Exception as e:
                logger.error(f"Error closing cache: {e}")


# Example usage
if __name__ == "__main__":
    # Test cache
    cache = ReviewCache(expiry_hours=24)
    
    # Test data
    test_reviews = [
        {
            'product_name': 'Test Product',
            'review_text': 'Great product!',
            'rating': 5.0,
            'review_date': datetime.now().date(),
            'source': 'Amazon'
        }
    ]
    
    # Store
    cache.set_cached('https://test.com/product', 'amazon', test_reviews)
    
    # Retrieve
    cached = cache.get_cached('https://test.com/product', 'amazon')
    print(f"Retrieved {len(cached)} cached reviews" if cached else "No cache found")
    
    # Stats
    print(f"Cache stats: {cache.get_cache_stats()}")
    
    # Clean up
    cache.close()