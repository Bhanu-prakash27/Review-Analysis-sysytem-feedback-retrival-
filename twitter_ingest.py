import os, time, logging
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import tweepy
from database.connection import get_mysql_conn

load_dotenv()

# v2 credentials (Bearer token required!)
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

keywords = [k.strip() for k in os.getenv("TWEET_KEYWORDS", "Amazon,Flipkart").split(",")]
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("twitter_ingest")

def get_client():
    return tweepy.Client(bearer_token=BEARER_TOKEN, wait_on_rate_limit=True)

def get_source_id(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM data_sources WHERE name=%s", ("Twitter",))
    row = cur.fetchone()
    if row:
        return int(row['id'])
    cur.execute("INSERT INTO data_sources (name) VALUES (%s)", ("Twitter",))
    conn.commit()
    return cur.lastrowid

def main():
    client = get_client()
    analyzer = SentimentIntensityAnalyzer()
    conn = get_mysql_conn()
    cur = conn.cursor(dictionary=True)
    source_id = get_source_id(conn)

    last_seen = {}

    logger.info(f"Monitoring keywords {keywords}")

    try:
        while True:
            for kw in keywords:
                try:
                    query = f"{kw} lang:en -is:retweet"
                    since_id = last_seen.get(kw)

                    tweets = client.search_recent_tweets(
                        query=query,
                        since_id=since_id,
                        max_results=20,
                        tweet_fields=["id", "text", "lang", "created_at"]
                    )

                    if not tweets.data:
                        continue

                    max_id = since_id
                    for t in reversed(tweets.data):
                        tweet_id = str(t.id)
                        tweet_text = t.text
                        tweet_date = t.created_at
                        lang = t.lang or "en"

                        # insert raw review
                        cur.execute("""
                            INSERT INTO raw_reviews (external_id, review_text, review_date, language, source_id, collected_at)
                            VALUES (%s, %s, %s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE collected_at=NOW()
                        """, (tweet_id, tweet_text, tweet_date, lang, source_id))
                        conn.commit()

                        # fetch id for analysis
                        cur.execute("SELECT id FROM raw_reviews WHERE external_id=%s AND source_id=%s", (tweet_id, source_id))
                        review_id = cur.fetchone()['id']

                        # sentiment
                        vs = analyzer.polarity_scores(tweet_text)
                        score = vs['compound']
                        label = "positive" if score >= 0.05 else "negative" if score <= -0.05 else "neutral"

                        cur.execute("SELECT id FROM analysis_results WHERE review_id=%s", (review_id,))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO analysis_results (review_id, sentiment, sentiment_score, positive_words, negative_words)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (review_id, label, score, '', ''))
                            conn.commit()

                        if max_id is None or int(tweet_id) > int(max_id):
                            max_id = tweet_id

                    last_seen[kw] = max_id

                except Exception as e:
                    logger.exception("Error fetching tweets for %s: %s", kw, e)

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Stopped")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
