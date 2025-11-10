# dashboard/user_dashboard.py - Complete User Dashboard
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from database.connection import get_database_connection


def load_review_data(sources, date_range, product_filter=None, product_url=None):
    """Load review data with optional product filter"""
    conn = get_database_connection()
    if not conn:
        st.error("Database connection failed")
        return pd.DataFrame()
    
    try:
        query = """
        SELECT r.id, r.product_name, r.product_url, r.review_text, r.rating, 
               r.review_date, r.language,
               a.sentiment, a.sentiment_score, 
               a.positive_words, a.negative_words,
               ds.name as source
        FROM raw_reviews r
        LEFT JOIN analysis_results a ON r.id = a.review_id
        JOIN data_sources ds ON r.source_id = ds.id
        WHERE r.review_date BETWEEN %s AND %s
        """
        
        params = [date_range[0], date_range[1]]
        
        # CRITICAL FIX: Filter by product URL if provided
        if product_url and product_url.strip():
            query += " AND r.product_url = %s"
            params.append(product_url.strip())
        
        # Add product name filter if provided
        if product_filter and product_filter.strip():
            query += " AND r.product_name LIKE %s"
            params.append(f"%{product_filter}%")
        
        if sources and len(sources) > 0:
            placeholders = ','.join(['%s'] * len(sources))
            query += f" AND ds.name IN ({placeholders})"
            params.extend(sources)
        
        query += " ORDER BY r.review_date DESC"
        
        df = pd.read_sql(query, conn, params=params)
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()


def extract_key_themes(df, sentiment_type='positive', top_n=5):
    """Extract key themes from reviews for a specific sentiment"""
    if df.empty:
        return []
    
    filtered_df = df[df['sentiment'] == sentiment_type]
    
    if sentiment_type == 'positive':
        words_col = 'positive_words'
    else:
        words_col = 'negative_words'
    
    all_words = filtered_df[words_col].dropna()
    
    if all_words.empty:
        return []
    
    # Split and count words
    word_list = []
    for words in all_words:
        word_list.extend([w.strip() for w in str(words).split(',') if w.strip()])
    
    if not word_list:
        return []
    
    word_freq = pd.Series(word_list).value_counts().head(top_n)
    return word_freq.index.tolist()


def show_user_dashboard():
    """Display comprehensive user dashboard"""
    st.title("Review Analysis Dashboard")
    st.markdown("### Analyze customer feedback across multiple platforms")
    
    # Sidebar filters
    with st.sidebar:
        st.subheader("Filters")
        
        # CRITICAL FIX: Product URL filter
        st.write("**Product URL Filter**")
        product_url_filter = st.text_input(
            "Filter by specific product URL",
            placeholder="https://www.amazon.in/dp/...",
            key="product_url_filter",
            help="Enter the exact product URL to see reviews only for that product"
        )
        
        if product_url_filter:
            st.info(f"Filtering by: {product_url_filter[:50]}...")
        
        st.divider()
        
        # Date range filter
        st.write("**Date Range**")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "From",
                value=datetime.now() - timedelta(days=30),
                key="start_date"
            )
        with col2:
            end_date = st.date_input(
                "To",
                value=datetime.now(),
                key="end_date"
            )
        
        # Source filter
        st.write("**Data Sources**")
        all_sources = ['Amazon', 'Flipkart', 'Twitter', 'Instagram']
        selected_sources = st.multiselect(
            "Select sources",
            all_sources,
            default=all_sources,
            key="source_filter"
        )

        # Product name filter
        st.write("**Product Name Search**")
        product_search = st.text_input(
            "Search by product name",
            placeholder="e.g., iPhone, Samsung, Galaxy",
            key="product_search"
        )
        
        st.divider()
        
        # Data collection section
        st.subheader("Data Collection")
        
        with st.expander("Twitter Integration"):
            st.info("Twitter API configured")
            search_query = st.text_input("Search query", value="product review")
            tweet_count = st.number_input("Number of tweets", min_value=5, max_value=100, value=10)
            
            if st.button("Fetch Tweets", use_container_width=True):
                with st.spinner("Fetching tweets..."):
                    try:
                        from data_collection.social_media import SocialMediaCollector
                        collector = SocialMediaCollector()
                        tweets = collector.collect_tweets(search_query, tweet_count)
                        
                        if tweets:
                            st.success(f"Fetched {len(tweets)} tweets!")
                        else:
                            st.warning("No tweets found or API limit reached")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with st.expander("Instagram Integration"):
            st.warning("Instagram integration coming soon")
            st.info("Will use Instaloader or Selenium for public posts")
        
        st.divider()
        st.subheader("Scrape New Reviews")

        with st.form("scrape_form"):
            scrape_source = st.selectbox(
                "Platform",
                ["Amazon", "Flipkart"],
                key="scrape_source"
            )
            
            product_url = st.text_input(
                "Product URL",
                placeholder="Paste product URL here...",
                key="product_url"
            )
            
            max_reviews = st.slider(
                "Max reviews to scrape",
                min_value=10,
                max_value=100,
                value=30,
                step=10
            )
            
            scrape_button = st.form_submit_button("Start Scraping", use_container_width=True)
            
            if scrape_button:
                if not product_url:
                    st.error("Please enter a product URL")
                else:
                    with st.spinner(f"Scraping {scrape_source} reviews..."):
                        try:
                            from data_collection.scraper_integration import ReviewCollector
                            
                            collector = ReviewCollector()
                            result = collector.collect_and_store(
                                product_url, 
                                scrape_source, 
                                max_reviews
                            )
                            
                            if 'error' in result:
                                st.error(f"Error: {result['error']}")
                            else:
                                st.success(f"Successfully scraped and stored {result['success_count']} reviews!")
                                st.info(f"Total scraped: {result['total_scraped']}, Failed: {result['failed_count']}")
                                
                                # Auto-set the URL filter
                                st.session_state.product_url_filter = product_url
                                
                                # Refresh the page
                                if st.button("Refresh Dashboard"):
                                    st.rerun()
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    
    # CRITICAL FIX: Load data with product URL filter
    df = load_review_data(
        selected_sources, 
        (start_date, end_date),
        product_filter=product_search if product_search else None,
        product_url=product_url_filter if product_url_filter else None
    )
    
    if df.empty:
        st.warning("No reviews found for the selected filters.")
        st.info("Try adjusting your filters or collect new data using the sidebar tools.")
        
        # Show what filters are active
        if product_url_filter:
            st.info(f"Active filter: Product URL = {product_url_filter}")
        if product_search:
            st.info(f"Active filter: Product Name contains '{product_search}'")
        
        return
    
    # Display active product info
    if product_url_filter or product_search:
        st.info(f"Showing reviews for: {df['product_name'].iloc[0] if not df.empty else 'Unknown'}")
    
    # Key Metrics Row
    st.subheader("Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Reviews", len(df))
    
    with col2:
        if 'rating' in df.columns and not df['rating'].isna().all():
            avg_rating = df['rating'].mean()
            st.metric("Avg Rating", f"{avg_rating:.2f}")
        else:
            st.metric("Avg Rating", "N/A")
    
    with col3:
        positive_count = len(df[df['sentiment'] == 'positive'])
        positive_pct = (positive_count / len(df) * 100) if len(df) > 0 else 0
        st.metric("Positive", f"{positive_count} ({positive_pct:.1f}%)")
    
    with col4:
        negative_count = len(df[df['sentiment'] == 'negative'])
        negative_pct = (negative_count / len(df) * 100) if len(df) > 0 else 0
        st.metric("Negative", f"{negative_count} ({negative_pct:.1f}%)")
    
    with col5:
        neutral_count = len(df[df['sentiment'] == 'neutral'])
        st.metric("Neutral", neutral_count)
    
    st.divider()
    
    # Visualization Section
    st.subheader("Analytics & Visualizations")
    
    # Row 1: Sentiment Distribution and Trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Sentiment Distribution**")
        sentiment_counts = df['sentiment'].value_counts()
        
        colors = {'positive': '#28a745', 'neutral': '#ffc107', 'negative': '#dc3545'}
        fig_pie = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            color=sentiment_counts.index,
            color_discrete_map=colors,
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.write("**Sentiment Trends Over Time**")
        
        df['review_date'] = pd.to_datetime(df['review_date'])
        daily_sentiment = df.groupby([df['review_date'].dt.date, 'sentiment']).size().unstack(fill_value=0)
        
        fig_line = go.Figure()
        
        for sentiment in ['positive', 'neutral', 'negative']:
            if sentiment in daily_sentiment.columns:
                fig_line.add_trace(go.Scatter(
                    x=daily_sentiment.index,
                    y=daily_sentiment[sentiment],
                    mode='lines+markers',
                    name=sentiment.capitalize(),
                    line=dict(color=colors.get(sentiment, '#666'), width=2),
                    marker=dict(size=6)
                ))
        
        fig_line.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Reviews",
            hovermode='x unified',
            height=350
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    
    st.divider()
    
    # Row 2: Source Distribution and Rating Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Reviews by Source**")
        source_counts = df['source'].value_counts()
        
        fig_bar = px.bar(
            x=source_counts.index,
            y=source_counts.values,
            labels={'x': 'Source', 'y': 'Count'},
            color=source_counts.values,
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.write("**Rating Distribution**")
        if 'rating' in df.columns and not df['rating'].isna().all():
            rating_counts = df['rating'].value_counts().sort_index()
            
            fig_rating = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                labels={'x': 'Rating', 'y': 'Count'},
                color=rating_counts.index,
                color_continuous_scale='RdYlGn'
            )
            fig_rating.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_rating, use_container_width=True)
        else:
            st.info("No rating data available")
    
    st.divider()
    
    # CRITICAL FIX: Key Themes Section - Per Product
    st.subheader("Key Themes for This Product")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Positive Keywords**")
        positive_themes = extract_key_themes(df, 'positive', top_n=10)
        
        if positive_themes:
            for theme in positive_themes:
                st.success(f"• {theme}")
        else:
            st.info("No positive keywords available")
    
    with col2:
        st.write("**Negative Keywords**")
        negative_themes = extract_key_themes(df, 'negative', top_n=10)
        
        if negative_themes:
            for theme in negative_themes:
                st.error(f"• {theme}")
        else:
            st.info("No negative keywords available")
    
    st.divider()
    
    # Recent Reviews Table
    st.subheader("Recent Reviews")
    
    # Add filter options for the table
    col1, col2, col3 = st.columns(3)
    with col1:
        sentiment_filter = st.selectbox(
            "Filter by sentiment",
            ["All", "positive", "negative", "neutral"],
            key="table_sentiment_filter"
        )
    with col2:
        source_filter = st.selectbox(
            "Filter by source",
            ["All"] + list(df['source'].unique()),
            key="table_source_filter"
        )
    with col3:
        num_reviews = st.number_input(
            "Number of reviews to display",
            min_value=5,
            max_value=100,
            value=10,
            step=5
        )
    
    # Apply filters
    filtered_df = df.copy()
    if sentiment_filter != "All":
        filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter]
    if source_filter != "All":
        filtered_df = filtered_df[filtered_df['source'] == source_filter]
    
    # Display table
    if not filtered_df.empty:
        display_df = filtered_df[['review_text', 'rating', 'sentiment', 'sentiment_score', 
                                   'source', 'review_date']].head(num_reviews).copy()
        
        # Format sentiment score
        display_df['sentiment_score'] = display_df['sentiment_score'].round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={  
                "review_text": st.column_config.TextColumn("Review", width="large"),
                "rating": st.column_config.NumberColumn("Rating", format="%.1f"),
                "sentiment": st.column_config.TextColumn("Sentiment"),
                "sentiment_score": st.column_config.NumberColumn("Score", format="%.2f"),
                "source": st.column_config.TextColumn("Source"),
                "review_date": st.column_config.DateColumn("Date")
            },
            hide_index=True
        )
        
        # Export option
        if st.button("Export Filtered Data to CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"reviews_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No reviews match the selected filters")


# Legacy function for backward compatibility
def show():
    """Wrapper function for legacy code"""
    show_user_dashboard()


if __name__ == "__main__":
    st.set_page_config(page_title="Review Analysis Dashboard", layout="wide")
    show_user_dashboard()