"""
test_scrapers_fixed.py

Comprehensive test suite to validate Amazon and Flipkart scraper fixes
Run this before deploying to Streamlit
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.optimized_scrapers import AmazonScraper, FlipkartScraper
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_reviews(reviews, source):
    """Validate that reviews are real and diverse"""
    if not reviews:
        return False, "No reviews fetched"
    
    # Check if mock data
    mock_reviewers = ["John D.", "Sarah M.", "Mike R.", "Emma W.", "David L."]
    if reviews[0]['reviewer'] in mock_reviewers:
        return False, "Using mock data (scraping failed)"
    
    # Check rating diversity
    ratings = [r['rating'] for r in reviews if r.get('rating')]
    unique_ratings = len(set(ratings))
    
    if unique_ratings == 1 and ratings[0] == 3.0:
        return False, "All ratings are 3.0 (default fallback)"
    
    # Good diversity threshold: at least 30% unique
    if unique_ratings < len(reviews) * 0.3 and len(reviews) > 5:
        return False, f"Low rating diversity ({unique_ratings}/{len(reviews)})"
    
    return True, "Real reviews with good diversity"


def test_flipkart_detailed():
    """Test Flipkart with multiple products"""
    print("\n" + "="*80)
    print("TESTING FLIPKART SCRAPER")
    print("="*80)
    
    test_products = [
        {
            "url": "https://www.flipkart.com/samsung-galaxy-m34-5g-midnight-blue-128-gb/p/itm6d2b78fa8608c",
            "name": "Samsung Galaxy M34"
        },
        {
            "url": "https://www.flipkart.com/realme-narzo-60-5g-mars-orange-128-gb/p/itm05e65cfbad6af",
            "name": "Realme Narzo 60"
        }
    ]
    
    scraper = FlipkartScraper()
    results = []
    
    for i, product in enumerate(test_products, 1):
        print(f"\n{'─'*80}")
        print(f"TEST {i}/{len(test_products)}: {product['name']}")
        print(f"{'─'*80}")
        
        try:
            reviews = scraper.get_flipkart_reviews(product['url'], max_reviews=10)
            
            is_valid, message = validate_reviews(reviews, "Flipkart")
            
            print(f"\n📊 Results:")
            print(f"   Total reviews: {len(reviews)}")
            print(f"   Status: {'✅ PASS' if is_valid else '❌ FAIL'}")
            print(f"   Message: {message}")
            
            if reviews:
                ratings = [r['rating'] for r in reviews]
                print(f"\n   Rating Analysis:")
                print(f"   - Unique ratings: {len(set(ratings))}")
                print(f"   - Ratings: {ratings}")
                print(f"   - Avg: {sum(ratings)/len(ratings):.2f}")
                
                # Show sample
                print(f"\n   Sample Reviews:")
                for j, review in enumerate(reviews[:3], 1):
                    print(f"\n   [{j}] ⭐ {review['rating']}/5")
                    print(f"       {review['reviewer']}")
                    print(f"       {review['review_text'][:60]}...")
            
            results.append({
                'product': product['name'],
                'valid': is_valid,
                'count': len(reviews)
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'product': product['name'],
                'valid': False,
                'count': 0
            })
    
    # Summary
    print(f"\n{'='*80}")
    print("FLIPKART TEST SUMMARY")
    print(f"{'='*80}")
    passed = sum(1 for r in results if r['valid'])
    print(f"Passed: {passed}/{len(results)}")
    
    for result in results:
        status = "✅" if result['valid'] else "❌"
        print(f"{status} {result['product']}: {result['count']} reviews")
    
    return passed == len(results)


def test_amazon_detailed():
    """Test Amazon with multiple products"""
    print("\n" + "="*80)
    print("TESTING AMAZON SCRAPER")
    print("="*80)
    
    test_products = [
        {
            "url": "https://www.amazon.in/dp/B0CTZG25TF",
            "name": "Product 1"
        },
        {
            "url": "https://www.amazon.in/dp/B0CHWRXH8B",
            "name": "Product 2"
        }
    ]
    
    scraper = AmazonScraper(use_selenium=False)
    results = []
    
    for i, product in enumerate(test_products, 1):
        print(f"\n{'─'*80}")
        print(f"TEST {i}/{len(test_products)}: {product['name']}")
        print(f"URL: {product['url']}")
        print(f"{'─'*80}")
        
        try:
            reviews = scraper.get_amazon_reviews(product['url'], max_reviews=10)
            
            is_valid, message = validate_reviews(reviews, "Amazon")
            
            print(f"\n📊 Results:")
            print(f"   Total reviews: {len(reviews)}")
            print(f"   Status: {'✅ PASS' if is_valid else '❌ FAIL'}")
            print(f"   Message: {message}")
            
            if not is_valid and reviews:
                print(f"\n   ⚠️  Possible causes:")
                print(f"   - Amazon bot detection (CAPTCHA)")
                print(f"   - Product has no reviews")
                print(f"   - Selectors changed (check amazon_debug.html)")
            
            if reviews:
                ratings = [r['rating'] for r in reviews]
                print(f"\n   Rating Analysis:")
                print(f"   - Unique ratings: {len(set(ratings))}")
                print(f"   - Ratings: {ratings}")
                print(f"   - Avg: {sum(ratings)/len(ratings):.2f}")
                
                # Show sample
                print(f"\n   Sample Reviews:")
                for j, review in enumerate(reviews[:3], 1):
                    print(f"\n   [{j}] ⭐ {review['rating']}/5")
                    print(f"       {review['reviewer']}")
                    print(f"       {review['review_text'][:60]}...")
            
            results.append({
                'product': product['name'],
                'valid': is_valid,
                'count': len(reviews)
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'product': product['name'],
                'valid': False,
                'count': 0
            })
    
    scraper.close()
    
    # Summary
    print(f"\n{'='*80}")
    print("AMAZON TEST SUMMARY")
    print(f"{'='*80}")
    passed = sum(1 for r in results if r['valid'])
    print(f"Passed: {passed}/{len(results)}")
    
    for result in results:
        status = "✅" if result['valid'] else "❌"
        print(f"{status} {result['product']}: {result['count']} reviews")
    
    if passed == 0:
        print("\n⚠️  NOTE: Amazon may block requests. Consider:")
        print("   1. Use Selenium mode (slower but more reliable)")
        print("   2. Add proxy support")
        print("   3. Check amazon_debug.html for page structure")
    
    return passed == len(results)


def test_url_validation():
    """Test that invalid URLs are properly rejected"""
    print("\n" + "="*80)
    print("TESTING URL VALIDATION")
    print("="*80)
    
    invalid_urls = [
        ("https://www.amazon.in/s?k=phone", "Amazon", "Search URL"),
        ("https://www.flipkart.com/search?q=phone", "Flipkart", "Search URL"),
    ]
    
    amazon = AmazonScraper(use_selenium=False)
    flipkart = FlipkartScraper()
    
    all_passed = True
    
    for url, platform, desc in invalid_urls:
        print(f"\n{'─'*80}")
        print(f"Testing: {platform} - {desc}")
        print(f"URL: {url}")
        print(f"{'─'*80}")
        
        if platform == "Amazon":
            reviews = amazon.get_amazon_reviews(url, max_reviews=2)
        else:
            reviews = flipkart.get_flipkart_reviews(url, max_reviews=2)
        
        # Should return mock data
        if reviews and reviews[0]['reviewer'] in ["John D.", "Sarah M."]:
            print("✅ Correctly rejected and returned mock data")
        else:
            print("❌ Did not properly handle invalid URL")
            all_passed = False
    
    amazon.close()
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 SCRAPER FIX VALIDATION SUITE")
    print("="*80)
    print("\nThis will test:")
    print("1. URL validation (rejects search URLs)")
    print("2. Amazon review fetching with rating diversity")
    print("3. Flipkart rating extraction per review")
    print("\n" + "="*80 + "\n")
    
    results = {}
    
    try:
        # Test 1: URL validation
        print("\n[1/3] Testing URL validation...")
        results['url_validation'] = test_url_validation()
        
        # Test 2: Amazon
        print("\n[2/3] Testing Amazon scraper...")
        results['amazon'] = test_amazon_detailed()
        
        # Test 3: Flipkart
        print("\n[3/3] Testing Flipkart scraper...")
        results['flipkart'] = test_flipkart_detailed()
        
        # Final summary
        print("\n" + "="*80)
        print("📋 FINAL TEST SUMMARY")
        print("="*80)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name.replace('_', ' ').title()}")
        
        all_passed = all(results.values())
        
        print("\n" + "="*80)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
            print("\n✨ Next steps:")
            print("   1. Replace your optimized_scrapers.py with the fixed version")
            print("   2. Run: streamlit run app.py")
            print("   3. Test with real product URLs")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("\n🔍 Troubleshooting:")
            print("   - Check amazon_debug.html / flipkart_debug.html")
            print("   - Verify product URLs are correct")
            print("   - Consider enabling Selenium for Amazon")
            print("   - Amazon may require CAPTCHA solving")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()