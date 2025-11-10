"""
data_collection/unified_review_fetcher.py

Complete unified system for collecting and analyzing reviews
from Amazon, Flipkart, and social media platforms - COMPLETE VERSION
"""
from data_collection.aspect_analyzer import FlipkartReviewAnalyzer
import logging
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse
import pandas as pd
from datetime import datetime

# Import scrapers
from data_collection.optimized_scrapers import FlipkartScraper
from data_collection.social_media_collector import SocialMediaCollector, MockSocialMediaCollector
from nlp.sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedReviewFetcher:
    """
    Unified system to fetch reviews from multiple sources and analyze sentiment
    
    Features:
    - Amazon & Flipkart web scraping
    - Twitter & Instagram collection
    - Sentiment analysis
    - Summary generation
    """
    
    def __init__(
        self,
        use_selenium: bool = True,
        headless: bool = True,
        sentiment_backend: str = "vader",
        use_real_social_apis: bool = True
        
    ):
        """
        Initialize the unified fetcher - FIXED VERSION
        
        Args:
            use_selenium: Use Selenium for Amazon (vs requests fallback)
            headless: Run browser in headless mode (only for Selenium)
            sentiment_backend: "vader", "textblob", or "transformers"
            use_real_social_apis: Use real social media APIs (requires credentials)
        """
        # Initialize scrapers with proper parameters
        self.flipkart_scraper = FlipkartScraper()
        self.aspect_analyzer = FlipkartReviewAnalyzer()

        # Initialize social media collector
        if use_real_social_apis:
            self.social_collector = SocialMediaCollector()
        else:
            self.social_collector = MockSocialMediaCollector()
            logger.info("Using mock social media collector (no API credentials)")
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentAnalyzer(backend=sentiment_backend)
        
        logger.info("UnifiedReviewFetcher initialized successfully")
    
    def fetch_reviews(
        self,
        source: str,
        identifier: str,
        max_reviews: int = 50,
        product_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch reviews from a specific source
        
        Args:
            source: "amazon", "flipkart", "twitter", or "instagram"
            identifier: URL for Amazon/Flipkart, keyword/hashtag for social media
            max_reviews: Maximum number of reviews to fetch
            product_name: Optional product name (used for social media)
        
        Returns:
            List of review dictionaries
        """
        source = source.lower()
        
        logger.info(f"Fetching reviews from {source}: {identifier}")

        
        if source == "flipkart":
            reviews = self.flipkart_scraper.get_flipkart_reviews(identifier, max_reviews)
        
        elif source == "twitter":
            reviews = self.social_collector.collect_twitter_reviews(
                identifier, max_reviews, product_name
            )
        
        elif source == "instagram":
            hashtag = identifier.lstrip('#')
            reviews = self.social_collector.collect_instagram_reviews(
                hashtag, max_reviews, product_name
            )
        
        else:
            logger.error(f"Unknown source: {source}")
            reviews = []
        
        logger.info(f"Fetched {len(reviews)} reviews from {source}")
        return reviews
    
    def fetch_from_url(self, url: str, max_reviews: int = 50) -> List[Dict]:
        """
        Automatically detect source from URL and fetch reviews
        
        Args:
            url: Product URL (Amazon or Flipkart)
            max_reviews: Maximum reviews to fetch
        
        Returns:
            List of reviews
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if 'flipkart' in domain:
            return self.fetch_reviews("flipkart", url, max_reviews)
        else:
            logger.error(f"Unknown domain: {domain}")
            return []
    
    def fetch_from_multiple_sources(
        self,
        sources: List[Dict],
        max_reviews_per_source: int = 50
    ) -> List[Dict]:
        """
        Fetch reviews from multiple sources
        
        Args:
            sources: List of dicts with 'source', 'identifier', and optional 'product_name'
            max_reviews_per_source: Max reviews per source
        
        Example:
            sources = [
                {'source': 'amazon', 'identifier': 'https://amazon.in/...'},
                {'source': 'twitter', 'identifier': 'iPhone 15 review', 'product_name': 'iPhone 15'}
            ]
        
        Returns:
            Combined list of reviews from all sources
        """
        all_reviews = []
        
        for source_info in sources:
            source = source_info.get('source')
            identifier = source_info.get('identifier')
            product_name = source_info.get('product_name')
            
            if not source or not identifier:
                logger.warning(f"Skipping invalid source info: {source_info}")
                continue
            
            reviews = self.fetch_reviews(
                source, identifier, max_reviews_per_source, product_name
            )
            all_reviews.extend(reviews)
        
        logger.info(f"Total reviews from all sources: {len(all_reviews)}")
        return all_reviews
    
    def analyze_reviews(self, reviews: List[Dict]) -> Dict:

        if not reviews or not isinstance(reviews, list):
            return {
                'reviews': [],
                'summary': {
                    'total_reviews': 0,
                    'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                    'average_rating': 0.0,
                    'summary_text': 'No reviews available for analysis.'
                }
            }

        try:
        # Step 1: Run sentiment analysis on each review
            analyzed_reviews = self.sentiment_analyzer.analyze_reviews(reviews)

        # Step 2: Compute summary statistics
            summary = self.sentiment_analyzer.generate_summary(analyzed_reviews)

        # Step 3: Attach fallback or confidence fields (optional)
            if 'confidence' not in summary:
                summary['confidence'] = (
                    "High" if summary.get("total_reviews", 0) >= 20 else
                    "Medium" if summary.get("total_reviews", 0) >= 10 else
                    "Low"
                )

            return {
                'reviews': analyzed_reviews,
                'summary': summary
            }

        except Exception as e:
            import logging
            logging.exception(f"Error during review analysis: {e}")
            return {
                'reviews': [],
                'summary': {
                    'total_reviews': 0,
                    'sentiment_distribution': {},
                    'average_rating': 0.0,
                    'summary_text': f'Analysis failed due to error: {str(e)}'
                }
            }

    
    def fetch_and_analyze(
        self,
        source: str,
        identifier: str,
        max_reviews: int = 50,
        product_name: Optional[str] = None
    ) -> Dict:
        """
        Complete pipeline: fetch reviews and analyze sentiment
        
        Args:
            source: Review source
            identifier: URL or search term
            max_reviews: Maximum reviews
            product_name: Product name (for social media)
        
        Returns:
            Complete analysis results
        """
        # Fetch reviews
        reviews = self.fetch_reviews(source, identifier, max_reviews, product_name)
        
        # Analyze sentiment
        results = self.analyze_reviews(reviews)
        
        # Add metadata
        results['metadata'] = {
            'source': source,
            'identifier': identifier,
            'product_name': product_name or reviews[0].get('product_name', 'Unknown') if reviews else 'Unknown',
            'fetched_at': datetime.now().isoformat(),
            'total_fetched': len(reviews)
        }
        
        return results
    
    def fetch_and_analyze_from_url(self, url: str, max_reviews: int = 50) -> Dict:
        """
        Convenience method: fetch and analyze from URL
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if 'flipkart' in domain:
            source = 'flipkart'
        else:
            raise ValueError(f"Unsupported domain: {domain}")
        
        return self.fetch_and_analyze(source, url, max_reviews)
    def analyze_aspects(self, reviews: List[Dict]) -> Dict:
        if not reviews:
            return self.aspect_analyzer._empty_analysis("Unknown Product")
    
        product_name = reviews[0].get('product_name', 'Unknown Product')
        return self.aspect_analyzer.analyze_reviews(product_name, reviews)

    def fetch_and_analyze_aspects(
        self,
        source: str,
        identifier: str,
        max_reviews: int = 50,
        product_name: Optional[str] = None
    ) -> Dict:
        
        try:
            # Fetch reviews
            reviews = self.fetch_reviews(source, identifier, max_reviews, product_name)

            # If no reviews, return empty analysis
            if not reviews:
                results = self.aspect_analyzer._empty_analysis(product_name or "Unknown Product")
                results['metadata'] = {
                    'source': source,
                    'identifier': identifier,
                    'fetched_at': datetime.now().isoformat(),
                    'total_reviews': 0
                }
                return results

            # Analyze aspects
            results = self.analyze_aspects(reviews)

            # Attach metadata
            results['metadata'] = {
                'source': source,
                'identifier': identifier,
                'product_name': product_name or reviews[0].get('product_name', 'Unknown'),
                'fetched_at': datetime.now().isoformat(),
                'total_reviews': len(reviews)
            }
            return results

        except Exception as e:
            logger.exception(f"Error in fetch_and_analyze_aspects: {e}")
            return {
                'analysis': {},
                'metadata': {
                    'source': source,
                    'identifier': identifier,
                    'product_name': product_name or 'Unknown',
                    'fetched_at': datetime.now().isoformat(),
                    'total_reviews': 0,
                    'error': str(e)
                }
            }

 
    # Fetch reviews
        reviews = self.fetch_reviews(source, identifier, max_reviews, product_name)
    
    # Analyze aspects
        results = self.analyze_aspects(reviews)
    
    # Add metadata
        results['metadata'] = {
        'source': source,
        'identifier': identifier,
        'fetched_at': datetime.now().isoformat(),
        'total_reviews': len(reviews)
        }
    
        return results
    def export_to_dataframe(self, results: Dict) -> pd.DataFrame:
        """
        Convert results to pandas DataFrame
        
        Args:
            results: Results from fetch_and_analyze()
        
        Returns:
            DataFrame with review data
        """
        reviews = results.get('reviews', [])
        
        if not reviews:
            return pd.DataFrame()
        
        # Flatten data for DataFrame
        df_data = []
        for review in reviews:
            sentiment = review.get('sentiment_analysis', {})
            
            row = {
                'product_name': review.get('product_name'),
                'review_text': review.get('review_text'),
                'rating': review.get('rating'),
                'reviewer': review.get('reviewer'),
                'review_date': review.get('review_date'),
                'source': review.get('source'),
                'language': review.get('language'),
                'sentiment': sentiment.get('sentiment'),
                'sentiment_score': sentiment.get('score'),
                'sentiment_confidence': sentiment.get('confidence')
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        return df
    
    def export_to_json(self, results: Dict, filepath: str):
        """Save results to JSON file"""
        import json
        
        # Convert date objects to strings
        def date_converter(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return obj
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, default=date_converter, indent=2, ensure_ascii=False)
        
        logger.info(f"Results exported to {filepath}")
    
    def export_to_csv(self, results: Dict, filepath: str):
        """Save results to CSV file"""
        df = self.export_to_dataframe(results)
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Results exported to {filepath}")
    
    def close(self):
        """Clean up resources"""
        logger.info("Resources closed")


# Convenience functions
def quick_analyze_url(url: str, max_reviews: int = 50) -> Dict:
    """
    Quick function to analyze product from URL
    
    Example:
        results = quick_analyze_url('https://www.amazon.in/dp/B08N5WRWNW')
        print(results['summary']['summary_text'])
    """
    fetcher = UnifiedReviewFetcher()
    try:
        results = fetcher.fetch_and_analyze_from_url(url, max_reviews)
        return results
    finally:
        fetcher.close()


def quick_analyze_keyword(
    keyword: str,
    platform: str = "twitter",
    max_reviews: int = 50
) -> Dict:
    """
    Quick function to analyze from social media keyword
    
    Example:
        results = quick_analyze_keyword('iPhone 15 review', 'twitter')
        print(results['summary']['summary_text'])
    """
    fetcher = UnifiedReviewFetcher()
    try:
        results = fetcher.fetch_and_analyze(platform, keyword, max_reviews)
        return results
    finally:
        fetcher.close()


# Example usage
if __name__ == "__main__":
    print("=== Unified Review Fetcher Demo ===\n")
    
    # Initialize fetcher
    fetcher = UnifiedReviewFetcher(
        use_selenium=False,  # Use requests for faster demo
        sentiment_backend="vader",
        use_real_social_apis=False  # Use mock data for demo
    )
    
    # Example 1: Analyze Amazon product
    
    # Example 2: Analyze Twitter mentions
    print("\n\nExample 2: Twitter Analysis")
    print("-" * 50)
    
    results_twitter = fetcher.fetch_and_analyze(
        source="twitter",
        identifier="iPhone 15 review",
        max_reviews=10,
        product_name="iPhone 15"
    )
    
    print(f"Product: {results_twitter['metadata']['product_name']}")
    print(f"Total tweets: {results_twitter['summary']['total_reviews']}")
    print(f"\n{results_twitter['summary']['summary_text']}")
    
    # Example 3: Multi-source analysis
    print("\n\nExample 3: Multi-Source Analysis")
    print("-" * 50)
    
    sources = [
        {'source': 'flipkart', 'identifier': 'https://www.flipkart.com/product/p/itm123'},
        {'source': 'twitter', 'identifier': 'product review', 'product_name': 'Test Product'}
    ]
    
    multi_reviews = fetcher.fetch_from_multiple_sources(sources, max_reviews_per_source=10)
    multi_results = fetcher.analyze_reviews(multi_reviews)
    
    print(f"Total reviews from all sources: {len(multi_reviews)}")
    print(f"\n{multi_results['summary']['summary_text']}")
    
    # Export results
    try:
        fetcher.export_to_csv(multi_results, 'reviews_analysis.csv')
        fetcher.export_to_json(multi_results, 'reviews_analysis.json')
        print("\nResults exported to reviews_analysis.csv and reviews_analysis.json")
    except Exception as e:
        print(f"Export error: {e}")
    
    # Clean up
    fetcher.close()
    print("\n=== Demo Complete ===")
