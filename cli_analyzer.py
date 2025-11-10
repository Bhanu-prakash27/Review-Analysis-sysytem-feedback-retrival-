"""
cli_analyzer.py

Command-line interface for the review analysis system
Easy-to-use interface for collecting and analyzing reviews
"""

import argparse
import sys
from typing import Optional
import logging

from data_collection.unified_review_fetcher import UnifiedReviewFetcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         📊 Review Analysis & Sentiment System 📊          ║
║                                                           ║
║  Collect reviews from Amazon, Flipkart & Social Media    ║
║  Powered by AI/NLP Sentiment Analysis                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)


def print_results(results: dict):
    """Print analysis results in a formatted way"""
    summary = results.get('summary', {})
    metadata = results.get('metadata', {})
    
    print("\n" + "="*60)
    print("📈 ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\n📦 Product: {metadata.get('product_name', 'Unknown')}")
    print(f"📍 Source: {metadata.get('source', 'Unknown').upper()}")
    print(f"📊 Total Reviews Analyzed: {summary.get('total_reviews', 0)}")
    print(f"⭐ Average Rating: {summary.get('average_rating', 0):.1f}/5.0")
    
    print("\n" + "-"*60)
    print("💭 SENTIMENT DISTRIBUTION")
    print("-"*60)
    
    dist = summary.get('sentiment_distribution', {})
    pos = dist.get('positive', 0)
    neu = dist.get('neutral', 0)
    neg = dist.get('negative', 0)
    
    print(f"✅ Positive: {pos:5.1f}% {'█' * int(pos/2)}")
    print(f"➖ Neutral:  {neu:5.1f}% {'█' * int(neu/2)}")
    print(f"❌ Negative: {neg:5.1f}% {'█' * int(neg/2)}")
    
    print("\n" + "-"*60)
    print("📝 SUMMARY")
    print("-"*60)
    print(f"\n{summary.get('summary_text', 'No summary available.')}")
    
    # Print themes if available
    pos_themes = summary.get('positive_themes', [])
    neg_themes = summary.get('negative_themes', [])
    
    if pos_themes:
        print(f"\n✨ Positive Themes: {', '.join(pos_themes)}")
    
    if neg_themes:
        print(f"⚠️  Negative Themes: {', '.join(neg_themes)}")
    
    print("\n" + "="*60)


def analyze_url(url: str, max_reviews: int, output: Optional[str]):
    """Analyze reviews from a product URL"""
    print(f"\n🔍 Analyzing: {url}")
    print(f"📥 Fetching up to {max_reviews} reviews...\n")
    
    fetcher = UnifiedReviewFetcher(use_selenium=True)
    
    try:
        results = fetcher.fetch_and_analyze_from_url(url, max_reviews)
        
        # Print results
        print_results(results)
        
        # Export if requested
        if output:
            if output.endswith('.csv'):
                fetcher.export_to_csv(results, output)
                print(f"\n✅ Results exported to: {output}")
            elif output.endswith('.json'):
                fetcher.export_to_json(results, output)
                print(f"\n✅ Results exported to: {output}")
            else:
                print(f"\n⚠️  Invalid output format. Use .csv or .json")
        
        # Show sample reviews
        print("\n" + "="*60)
        print("📋 SAMPLE REVIEWS")
        print("="*60)
        
        reviews = results.get('reviews', [])[:5]  # Show first 5
        for i, review in enumerate(reviews, 1):
            sentiment = review.get('sentiment_analysis', {})
            print(f"\n{i}. [{sentiment.get('sentiment', 'N/A').upper()}] "
                  f"Rating: {review.get('rating', 0):.1f}/5")
            print(f"   {review.get('review_text', '')[:150]}...")
        
        if len(results.get('reviews', [])) > 5:
            print(f"\n... and {len(results.get('reviews', [])) - 5} more reviews")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ Error: {e}")
    finally:
        fetcher.close()


def analyze_social(platform: str, keyword: str, max_reviews: int, 
                   product_name: Optional[str], output: Optional[str]):
    """Analyze reviews from social media"""
    print(f"\n🔍 Analyzing {platform.upper()} for: {keyword}")
    print(f"📥 Fetching up to {max_reviews} posts...\n")
    
    fetcher = UnifiedReviewFetcher(
        use_selenium=False,
        use_real_social_apis=True  # Set to False to use mock data
    )
    
    try:
        results = fetcher.fetch_and_analyze(
            source=platform,
            identifier=keyword,
            max_reviews=max_reviews,
            product_name=product_name or keyword
        )
        
        # Print results
        print_results(results)
        
        # Export if requested
        if output:
            if output.endswith('.csv'):
                fetcher.export_to_csv(results, output)
                print(f"\n✅ Results exported to: {output}")
            elif output.endswith('.json'):
                fetcher.export_to_json(results, output)
                print(f"\n✅ Results exported to: {output}")
        
        # Show sample posts
        print("\n" + "="*60)
        print("📋 SAMPLE POSTS")
        print("="*60)
        
        reviews = results.get('reviews', [])[:5]
        for i, review in enumerate(reviews, 1):
            sentiment = review.get('sentiment_analysis', {})
            print(f"\n{i}. [{sentiment.get('sentiment', 'N/A').upper()}] "
                  f"@{review.get('reviewer', 'unknown')}")
            print(f"   {review.get('review_text', '')[:150]}...")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ Error: {e}")
    finally:
        fetcher.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Review Analysis & Sentiment System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze Amazon product
  python cli_analyzer.py --url "https://www.amazon.in/dp/B08N5WRWNW" --max 50
  
  # Analyze Flipkart product and export to CSV
  python cli_analyzer.py --url "https://www.flipkart.com/..." --max 100 --output reviews.csv
  
  # Analyze Twitter mentions
  python cli_analyzer.py --social twitter --keyword "iPhone 15 review" --max 50
  
  # Analyze Instagram hashtag
  python cli_analyzer.py --social instagram --keyword "GalaxyS24" --product "Samsung Galaxy S24"
        """
    )
    
    # Main arguments
    parser.add_argument('--url', type=str, help='Product URL (Amazon or Flipkart)')
    parser.add_argument('--social', type=str, choices=['twitter', 'instagram'],
                       help='Social media platform')
    parser.add_argument('--keyword', type=str, help='Search keyword/hashtag for social media')
    parser.add_argument('--product', type=str, help='Product name (for social media)')
    parser.add_argument('--max', type=int, default=50, 
                       help='Maximum reviews to fetch (default: 50)')
    parser.add_argument('--output', type=str, 
                       help='Output file path (.csv or .json)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress banner and verbose output')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.url and not args.social:
        parser.error("Either --url or --social must be specified")
    
    if args.social and not args.keyword:
        parser.error("--keyword is required when using --social")
    
    if args.url and args.social:
        parser.error("Cannot use both --url and --social simultaneously")
    
    # Print banner
    if not args.quiet:
        print_banner()
    
    # Execute analysis
    if args.url:
        analyze_url(args.url, args.max, args.output)
    elif args.social:
        analyze_social(args.social, args.keyword, args.max, 
                      args.product, args.output)
    
    print("\n✨ Analysis complete!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)