"""
data_collection/social_media_collector.py

Unified social media collector for Twitter/X, Instagram, etc.
Returns standardized review format
"""

import os
import re
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logging.warning("tweepy not installed. Twitter collection disabled.")

try:
    import instaloader
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False
    logging.warning("instaloader not installed. Instagram collection disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocialMediaCollector:
    """Collect reviews/posts from social media platforms"""
    
    def __init__(self):
        self.twitter_api = None
        self.instagram_loader = None
        
        if TWEEPY_AVAILABLE:
            self._setup_twitter()
        
        if INSTALOADER_AVAILABLE:
            self._setup_instagram()
    
    def _setup_twitter(self):
        """Setup Twitter API v2"""
        try:
            # Twitter API v2 credentials
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            api_key = os.getenv('TWITTER_API_KEY')
            api_secret = os.getenv('TWITTER_API_SECRET')
            access_token = os.getenv('TWITTER_ACCESS_TOKEN')
            access_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            
            if bearer_token:
                # Use API v2 client
                self.twitter_api = tweepy.Client(
                    bearer_token=bearer_token,
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret,
                    wait_on_rate_limit=True
                )
                logger.info("Twitter API v2 initialized")
            else:
                logger.warning("Twitter API credentials not configured")
        except Exception as e:
            logger.error(f"Twitter setup failed: {e}")
            self.twitter_api = None
    
    def _setup_instagram(self):
        """Setup Instagram loader"""
        try:
            self.instagram_loader = instaloader.Instaloader()
            logger.info("Instagram loader initialized")
        except Exception as e:
            logger.error(f"Instagram setup failed: {e}")
            self.instagram_loader = None
    
    def collect_twitter_reviews(
        self, 
        query: str, 
        max_reviews: int = 50,
        product_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Collect tweets as reviews
        
        Args:
            query: Search query (e.g., "iPhone 15 review", "#GalaxyS24")
            max_reviews: Maximum number of tweets to collect
            product_name: Product name for the reviews
        
        Returns:
            List of standardized review dictionaries
        """
        if not self.twitter_api:
            logger.warning("Twitter API not available")
            return []
        
        reviews = []
        product_name = product_name or query
        
        try:
            # Search recent tweets using API v2
            tweets = self.twitter_api.search_recent_tweets(
                query=query,
                max_results=min(max_reviews, 100),  # API limit per request
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang'],
                expansions=['author_id'],
                user_fields=['username', 'name']
            )
            
            if not tweets.data:
                logger.info(f"No tweets found for query: {query}")
                return reviews
            
            # Create user lookup
            users = {u.id: u for u in tweets.includes.get('users', [])}
            
            for tweet in tweets.data:
                try:
                    # Extract sentiment from engagement metrics
                    metrics = tweet.public_metrics
                    likes = metrics.get('like_count', 0)
                    retweets = metrics.get('retweet_count', 0)
                    
                    # Estimate rating based on engagement
                    # High engagement = likely positive
                    engagement = likes + (retweets * 2)
                    if engagement > 100:
                        rating = 5.0
                    elif engagement > 50:
                        rating = 4.0
                    elif engagement > 10:
                        rating = 3.5
                    else:
                        rating = 3.0
                    
                    # Get author info
                    author = users.get(tweet.author_id)
                    reviewer = author.username if author else "Twitter User"
                    
                    reviews.append({
                        "product_name": product_name,
                        "review_text": tweet.text,
                        "rating": rating,
                        "reviewer": f"@{reviewer}",
                        "review_date": tweet.created_at.date() if hasattr(tweet.created_at, 'date') else datetime.now().date(),
                        "source": "Twitter",
                        "language": tweet.lang or "en",
                        "images": [],
                        "engagement": {
                            "likes": likes,
                            "retweets": retweets
                        }
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing tweet: {e}")
                    continue
            
            logger.info(f"Twitter: Collected {len(reviews)} tweets")
            
        except Exception as e:
            logger.error(f"Twitter collection error: {e}")
        
        return reviews
    
    def collect_instagram_reviews(
        self,
        hashtag: str,
        max_reviews: int = 50,
        product_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Collect Instagram posts as reviews
        
        Args:
            hashtag: Hashtag to search (without #)
            max_reviews: Maximum posts to collect
            product_name: Product name
        
        Returns:
            List of standardized review dictionaries
        """
        if not self.instagram_loader:
            logger.warning("Instagram loader not available")
            return []
        
        reviews = []
        product_name = product_name or f"#{hashtag}"
        
        try:
            posts = instaloader.Hashtag.from_name(
                self.instagram_loader.context, 
                hashtag
            ).get_posts()
            
            count = 0
            for post in posts:
                if count >= max_reviews:
                    break
                
                try:
                    # Extract caption
                    caption = post.caption or ""
                    
                    # Skip if too short
                    if len(caption) < 20:
                        continue
                    
                    # Estimate rating from likes
                    likes = post.likes
                    if likes > 1000:
                        rating = 5.0
                    elif likes > 500:
                        rating = 4.5
                    elif likes > 100:
                        rating = 4.0
                    else:
                        rating = 3.5
                    
                    reviews.append({
                        "product_name": product_name,
                        "review_text": caption,
                        "rating": rating,
                        "reviewer": f"@{post.owner_username}",
                        "review_date": post.date.date() if hasattr(post.date, 'date') else datetime.now().date(),
                        "source": "Instagram",
                        "language": "en",  # Instagram doesn't provide language
                        "images": [post.url] if post.url else [],
                        "engagement": {
                            "likes": likes,
                            "comments": post.comments
                        }
                    })
                    
                    count += 1
                    
                except Exception as e:
                    logger.debug(f"Error parsing Instagram post: {e}")
                    continue
            
            logger.info(f"Instagram: Collected {len(reviews)} posts")
            
        except Exception as e:
            logger.error(f"Instagram collection error: {e}")
        
        return reviews
    
    def collect_from_keyword(
        self,
        keyword: str,
        platform: str = "twitter",
        max_reviews: int = 50,
        product_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Unified method to collect from any platform
        
        Args:
            keyword: Search keyword or hashtag
            platform: "twitter" or "instagram"
            max_reviews: Maximum reviews to collect
            product_name: Product name
        
        Returns:
            List of standardized reviews
        """
        platform = platform.lower()
        
        if platform == "twitter":
            return self.collect_twitter_reviews(keyword, max_reviews, product_name)
        elif platform == "instagram":
            # Remove # if present
            hashtag = keyword.lstrip('#')
            return self.collect_instagram_reviews(hashtag, max_reviews, product_name)
        else:
            logger.warning(f"Unknown platform: {platform}")
            return []


# Mock data generator for testing when APIs are not available
class MockSocialMediaCollector(SocialMediaCollector):
    """Mock collector for testing without API credentials"""
    
    def __init__(self):
        self.twitter_api = None
        self.instagram_loader = None
    
    def collect_twitter_reviews(self, query: str, max_reviews: int = 50, product_name: Optional[str] = None) -> List[Dict]:
        """Generate mock Twitter reviews"""
        product_name = product_name or query
        reviews = []
        
        mock_tweets = [
            ("Just got the new product! Absolutely loving it. Best purchase this year! #amazing", 5.0),
            ("Pretty good but had some issues with setup. Customer service was helpful though.", 3.5),
            ("Not impressed. Expected better quality for the price.", 2.0),
            ("Works as advertised. No complaints so far.", 4.0),
            ("Game changer! Everyone should get this.", 5.0),
        ]
        
        for i, (text, rating) in enumerate(mock_tweets[:max_reviews]):
            reviews.append({
                "product_name": product_name,
                "review_text": text,
                "rating": rating,
                "reviewer": f"@user{i+1}",
                "review_date": datetime.now().date(),
                "source": "Twitter",
                "language": "en",
                "images": [],
                "engagement": {"likes": 10 * (i+1), "retweets": 2 * (i+1)}
            })
        
        logger.info(f"Mock Twitter: Generated {len(reviews)} reviews")
        return reviews