"""
dashboard/complete_enhanced_dashboard.py

Complete user dashboard for review analysis - ENHANCED UI VERSION
"""
from data_collection.aspect_analyzer import FlipkartReviewAnalyzer
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import logging
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.unified_review_fetcher import UnifiedReviewFetcher

# Enhanced CSS Styling
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Title Styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        padding: 1rem 0;
    }
    
    h2 {
        color: #1f2937;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #374151;
        font-weight: 600;
    }
    
    /* Card Containers */
    .analysis-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }
    
    .analysis-card:hover {
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
        transform: translateY(-2px);
    }
    
    /* Metrics */
    .stMetric {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .stMetric label {
        font-weight: 600;
        color: #6b7280;
        font-size: 0.9rem;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1f2937;
    }
    
    /* Form Styling */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Selectbox */
    .stSelectbox>div>div {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
    }
    
    /* Slider */
    .stSlider>div>div>div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Radio Buttons */
    .stRadio>div {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        border: 2px solid #e5e7eb;
    }
    
    .stRadio>div>label>div[data-testid="stMarkdownContainer"] {
        font-weight: 600;
        color: #374151;
    }
    
    /* Checkbox */
    .stCheckbox {
        background: white;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton>button[kind="primary"],
    .stButton>button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
        border-radius: 10px;
        font-weight: 600;
        padding: 1rem;
        border: 1px solid #e5e7eb;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%);
        border-color: #667eea;
    }
    
    /* Info/Warning/Success/Error Messages */
    .stAlert {
        border-radius: 12px;
        border: none;
        padding: 1rem 1.5rem;
        font-weight: 500;
    }
    
    div[data-baseweb="notification"] {
        border-radius: 12px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f9fafb;
        border-radius: 12px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Dataframe */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    /* Sidebar Enhancements */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f9fafb 0%, #f3f4f6 100%);
    }
    
    [data-testid="stSidebar"] .stRadio>div {
        background: white;
    }
    
    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem 0;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    
    .section-header h2 {
        margin: 0;
    }
    
    /* Icon Badges */
    .icon-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.2rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Sentiment Badges */
    .sentiment-positive {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .sentiment-negative {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .sentiment-neutral {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    /* Loading Spinner */
    .stSpinner>div {
        border-color: #667eea !important;
    }
    
    /* Download Buttons */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: 600;
    }
    
    /* Caption Styling */
    .stCaption {
        color: #6b7280;
        font-size: 0.9rem;
    }
    
    /* Review Card Styling */
    .review-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }
    
    .review-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
        margin: 2rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def show_complete_dashboard():
    """Main dashboard for users with enhanced UI"""
    
    # Beautiful Header
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📊 Review & Sentiment Analysis Dashboard</h1>
            <p style='color: #6b7280; font-size: 1.1rem;'>Analyze reviews from Flipkart, Twitter, and more</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar options with enhanced styling
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding: 1rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 12px; margin-bottom: 1.5rem;'>
                <h3 style='color: white; margin: 0;'>⚙️ Analysis Options</h3>
            </div>
        """, unsafe_allow_html=True)
        
        analysis_type = st.radio(
            "Select Analysis Type",
            ["🔗 URL Analysis", "🔍 Keyword Analysis", "🌐 Multi-Source Analysis"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        st.markdown("### 🛠️ Settings")
        
        use_selenium = st.checkbox("⚡ Use Selenium (slower but more reliable)", value=False)
        max_reviews = st.slider("📊 Max Reviews to Fetch", 10, 200, 50)
        sentiment_backend = st.selectbox("🧠 Sentiment Engine", ["vader", "textblob"])
        show_aspect_analysis = st.checkbox("🎯 Show Aspect Analysis", value=True)
        
        # Info box
        st.markdown("""
            <div style='background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%); 
                        padding: 1rem; border-radius: 10px; margin-top: 1rem;'>
                <p style='margin: 0; font-size: 0.85rem; color: #4c1d95;'>
                    <strong>💡 Tip:</strong> Increase max reviews for more comprehensive analysis
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # Route to appropriate analysis page
    if "URL Analysis" in analysis_type:
        url_analysis_page(use_selenium, max_reviews, sentiment_backend)
    elif "Keyword Analysis" in analysis_type:
        keyword_analysis_page(use_selenium, max_reviews, sentiment_backend)
    elif "Multi-Source Analysis" in analysis_type:
        multi_source_page(use_selenium, max_reviews, sentiment_backend)


def url_analysis_page(use_selenium, max_reviews, sentiment_backend):
    """Analyze reviews from a product URL with enhanced UI"""
    
    st.markdown('<div class="section-header"><span class="icon-badge">🔗</span><h2>URL Analysis</h2></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%); 
                    padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;'>
            <p style='margin: 0; color: #075985;'>
                📝 Enter a Flipkart product URL to analyze customer reviews and sentiment
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Input form
    with st.form("url_form"):
        url = st.text_input(
            "🌐 Product URL",
            placeholder="https://www.flipkart.com/product-name/p/...",
            help="Paste the complete Flipkart product URL"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            submit = st.form_submit_button("🚀 Analyze Reviews", use_container_width=True, type="primary")
        with col2:
            clear = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    if clear:
        for key in ['analysis_results', 'current_product_url']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    if submit:
        if not url:
            st.warning("⚠️ Please enter a valid URL")
            return
        
        st.session_state.analysis_results = None
        st.session_state.current_product_url = url
        
        with st.spinner("🔄 Fetching and analyzing reviews... This may take a moment."):
            try:
                fetcher = UnifiedReviewFetcher(
                    use_selenium=use_selenium,
                    headless=True,
                    sentiment_backend=sentiment_backend,
                    use_real_social_apis=False
                )
                
                results = fetcher.fetch_and_analyze_from_url(url, max_reviews)
                results['metadata']['product_url'] = url
                
                st.session_state.analysis_results = results
                fetcher.close()
                
                st.success("✅ Analysis complete! Scroll down to view results.")
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                with st.expander("🔍 View Error Details"):
                    import traceback
                    st.code(traceback.format_exc())
                return
    
    if st.session_state.get('analysis_results'):
        current_url = st.session_state.get('current_product_url', 'Unknown')
        st.info(f"📊 Currently viewing: {current_url}")
        display_results(st.session_state.analysis_results)


def display_aspect_analysis(reviews, product_name):
    """Display aspect-based analysis in dashboard with enhanced UI"""
    if not reviews:
        st.warning("⚠️ No reviews available for aspect analysis")
        return
    
    analyzer = FlipkartReviewAnalyzer()
    
    with st.spinner("🔍 Performing aspect-based analysis..."):
        analysis_result = analyzer.analyze_reviews(product_name, reviews)
    
    st.markdown("---")
    st.markdown('<div class="section-header"><span class="icon-badge">🎯</span><h2>Aspect-Based Analysis</h2></div>', unsafe_allow_html=True)
    
    # Product info with enhanced cards
    st.subheader("🛍️ Product Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📦 Product", product_name or "Unknown")
    
    with col2:
        category = analysis_result.get("category", "Unknown")
        st.metric("📂 Category", category.title())
    
    with col3:
        confidence = analysis_result.get("analysis_confidence", "Medium")
        confidence_emoji = "🟢" if confidence == "High" else "🟡" if confidence == "Medium" else "🔴"
        st.metric(f"{confidence_emoji} Confidence", confidence)
    
    # Overall feedback
    st.subheader("📝 Overall Feedback")
    overall = analysis_result.get("overall_feedback", "No feedback available")
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 100%); 
                    padding: 1.5rem; border-radius: 12px; border-left: 4px solid #667eea;'>
            <p style='margin: 0; color: #1e3a8a; font-size: 1rem;'>{overall}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Aspects
    st.subheader("🔍 Detected Aspects")
    aspects = analysis_result.get("aspects", {})
    
    if aspects:
        aspect_df = []
        for aspect, data in aspects.items():
            sentiment = data.get('sentiment', 'neutral').title()
            aspect_df.append({
                'Aspect': aspect.title(),
                'Sentiment': sentiment,
                'Mentions': data.get('count', 0),
                'Reason': data.get('reason', 'N/A')
            })
        
        df = pd.DataFrame(aspect_df)
        
        # Display as styled table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Aspect": st.column_config.TextColumn("Aspect", width="medium"),
                "Sentiment": st.column_config.TextColumn("Sentiment", width="small"),
                "Mentions": st.column_config.NumberColumn("Mentions", width="small"),
                "Reason": st.column_config.TextColumn("Reason", width="large")
            }
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sentiment distribution chart with enhanced styling
        sentiment_counts = df['Sentiment'].value_counts()
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Aspect Sentiment Distribution",
            color_discrete_map={
                'Positive': '#10b981',
                'Neutral': '#f59e0b',
                'Negative': '#ef4444'
            },
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            font=dict(size=14, family="Inter"),
            showlegend=True,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No aspects detected")
    
    # Key themes with enhanced styling
    key_themes = analysis_result.get("key_themes", [])
    if key_themes:
        st.subheader("💡 Key Themes")
        
        for theme in key_themes:
            sentiment = theme.get('sentiment', 'neutral')
            theme_name = theme.get('theme', 'Unknown')
            reason = theme.get('reason', '')
            
            if sentiment == 'positive':
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                                padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 4px solid #10b981;'>
                        <strong style='color: #065f46;'>✅ {theme_name}</strong>
                        <p style='margin: 0.5rem 0 0 0; color: #047857;'>{reason}</p>
                    </div>
                """, unsafe_allow_html=True)
            elif sentiment == 'negative':
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                                padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 4px solid #ef4444;'>
                        <strong style='color: #7f1d1d;'>❌ {theme_name}</strong>
                        <p style='margin: 0.5rem 0 0 0; color: #991b1b;'>{reason}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                                padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; border-left: 4px solid #f59e0b;'>
                        <strong style='color: #78350f;'>ℹ️ {theme_name}</strong>
                        <p style='margin: 0.5rem 0 0 0; color: #92400e;'>{reason}</p>
                    </div>
                """, unsafe_allow_html=True)
    
    # Competitor recommendations
    competitors = analysis_result.get("recommended_products", [])
    if competitors:
        st.subheader("🏆 Recommended Alternatives")
        
        for comp in competitors[:4]:
            with st.expander(f"📦 {comp.get('name', 'Unknown Product')}"):
                st.markdown(f"""
                    <div style='padding: 0.5rem;'>
                        <p style='color: #374151;'>{comp.get('reason', 'No reason provided')}</p>
                    </div>
                """, unsafe_allow_html=True)

            
def keyword_analysis_page(use_selenium, max_reviews, sentiment_backend):
    """Analyze social media posts by keyword with enhanced UI"""
    
    st.markdown('<div class="section-header"><span class="icon-badge">🔍</span><h2>Keyword Analysis</h2></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                    padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;'>
            <p style='margin: 0; color: #78350f;'>
                🐦 Search Twitter or Instagram for product mentions and analyze sentiment
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("keyword_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            keyword = st.text_input(
                "🔎 Search Keyword",
                placeholder="e.g., iPhone 15 review, #GalaxyS24",
                help="Enter keywords or hashtags to search"
            )
        
        with col2:
            platform = st.selectbox("📱 Platform", ["Twitter", "Instagram"])
        
        product_name = st.text_input(
            "📦 Product Name (optional)",
            placeholder="e.g., iPhone 15",
            help="Optional: Specify product name for better analysis"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            submit = st.form_submit_button("🚀 Analyze", use_container_width=True, type="primary")
        with col2:
            clear = st.form_submit_button("🗑️ Clear", use_container_width=True)
    
    if clear:
        for key in ['analysis_results', 'current_keyword']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    if submit:
        if not keyword:
            st.warning("⚠️ Please enter a search keyword")
            return
        
        st.session_state.analysis_results = None
        st.session_state.current_keyword = keyword
        
        with st.spinner(f"🔄 Fetching posts from {platform}... This may take a moment."):
            try:
                fetcher = UnifiedReviewFetcher(
                    use_selenium=use_selenium,
                    headless=True,
                    sentiment_backend=sentiment_backend,
                    use_real_social_apis=False
                )
                
                source = "twitter" if platform == "Twitter" else "instagram"
                results = fetcher.fetch_and_analyze(
                    source=source,
                    identifier=keyword,
                    max_reviews=max_reviews,
                    product_name=product_name or keyword
                )
                
                st.session_state.analysis_results = results
                fetcher.close()
                
                st.success("✅ Analysis complete! Scroll down to view results.")
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                with st.expander("🔍 View Error Details"):
                    import traceback
                    st.code(traceback.format_exc())
                return
    
    if st.session_state.get('analysis_results'):
        current_keyword = st.session_state.get('current_keyword', 'Unknown')
        st.info(f"📊 Currently viewing: {current_keyword}")
        display_results(st.session_state.analysis_results)


def multi_source_page(use_selenium, max_reviews, sentiment_backend):
    """Analyze reviews from multiple sources with enhanced UI"""
    
    st.markdown('<div class="section-header"><span class="icon-badge">🌐</span><h2>Multi-Source Analysis</h2></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%); 
                    padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;'>
            <p style='margin: 0; color: #4c1d95;'>
                📊 Compare reviews across multiple platforms for comprehensive insights
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize sources in session state
    if 'sources' not in st.session_state:
        st.session_state.sources = []
    
    # Add source form
    with st.expander("➕ Add New Source", expanded=len(st.session_state.sources) == 0):
        with st.form("add_source_form"):
            source_type = st.selectbox(
                "📍 Source Type",
                ["Flipkart", "Twitter", "Instagram"]
            )
            
            if source_type in ["Flipkart"]:
                identifier = st.text_input("🔗 Product URL", placeholder="https://www.flipkart.com/...")
                product_name = ""
            else:
                identifier = st.text_input("🔎 Search Keyword/Hashtag", placeholder="e.g., #ProductName")
                product_name = st.text_input("📦 Product Name", placeholder="Optional")
            
            add_source = st.form_submit_button("✅ Add Source", use_container_width=True, type="primary")
            
            if add_source and identifier:
                st.session_state.sources.append({
                    'source': source_type.lower(),
                    'identifier': identifier,
                    'product_name': product_name
                })
                st.success(f"✅ Added {source_type} source")
                st.rerun()
    
    # Display current sources with enhanced styling
    if st.session_state.sources:
        st.subheader("📋 Selected Sources")
        
        for i, src in enumerate(st.session_state.sources):
            col1, col2 = st.columns([5, 1])
            with col1:
                icon = "🛍️" if src['source'] == 'flipkart' else "🐦" if src['source'] == 'twitter' else "📸"
                st.markdown(f"""
                    <div style='background: white; padding: 1rem; border-radius: 10px; 
                                border: 2px solid #e5e7eb; margin-bottom: 0.5rem;'>
                        <strong style='color: #1f2937;'>{icon} {src['source'].upper()}</strong>
                        <p style='margin: 0.5rem 0 0 0; color: #6b7280;'>{src['identifier']}</p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"remove_{i}", use_container_width=True):
                    st.session_state.sources.pop(i)
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Analyze button
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🚀 Analyze All Sources", use_container_width=True, type="primary"):
                analyze_multiple_sources(
                    st.session_state.sources,
                    use_selenium,
                    max_reviews,
                    sentiment_backend
                )
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.sources = []
                if 'analysis_results' in st.session_state:
                    del st.session_state.analysis_results
                st.rerun()
    else:
        st.info("👆 Click 'Add New Source' to begin adding sources for analysis")
    
    # Display results
    if st.session_state.get('analysis_results'):
        display_results(st.session_state.analysis_results)


def analyze_multiple_sources(sources, use_selenium, max_reviews, sentiment_backend):
    """Analyze multiple sources"""
    st.session_state.analysis_results = None
    
    with st.spinner("🔄 Fetching and analyzing from multiple sources... This may take a while."):
        try:
            fetcher = UnifiedReviewFetcher(
                use_selenium=use_selenium,
                headless=True,
                sentiment_backend=sentiment_backend,
                use_real_social_apis=False
            )
            
            all_reviews = fetcher.fetch_from_multiple_sources(
                sources,
                max_reviews_per_source=max_reviews
            )
            
            results = fetcher.analyze_reviews(all_reviews)
            
            # Add metadata
            results['metadata'] = {
                'source': 'Multiple Sources',
                'identifier': f"{len(sources)} sources",
                'product_name': 'Multi-Source Analysis',
                'fetched_at': datetime.now().isoformat(),
                'total_fetched': len(all_reviews),
                'sources': sources
            }
            
            st.session_state.analysis_results = results
            fetcher.close()
            
            st.success(f"✅ Analysis complete! Analyzed {len(all_reviews)} total reviews from {len(sources)} sources")
            
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            with st.expander("🔍 View Error Details"):
                import traceback
                st.code(traceback.format_exc())


def display_results(results):
    """Display analysis results with enhanced visualizations"""
    
    st.markdown("---")
    st.markdown('<div class="section-header"><span class="icon-badge">📊</span><h2>Analysis Results</h2></div>', unsafe_allow_html=True)
    
    summary = results.get('summary', {})
    reviews = results.get('reviews', [])
    metadata = results.get('metadata', {})
    
    # Product info with enhanced header
    product_name = metadata.get('product_name', 'Unknown')
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 16px; margin-bottom: 1.5rem;'>
            <h3 style='color: white; margin: 0; font-size: 1.8rem;'>🛍️ {product_name}</h3>
            <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>
                📍 Source: {metadata.get('source', 'Unknown').upper()} | 
                🕒 Analyzed: {metadata.get('fetched_at', 'N/A')[:10]}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Show product URL if available
    product_url = metadata.get('product_url')
    if product_url:
        st.caption(f"🔗 URL: {product_url}")
    
    # Key Metrics with enhanced cards
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 Total Reviews",
            summary.get('total_reviews', 0),
            help="Total number of reviews analyzed"
        )
    
    with col2:
        avg_rating = summary.get('average_rating', 0)
        st.metric(
            "⭐ Avg Rating",
            f"{avg_rating:.1f}/5.0",
            help="Average product rating"
        )
    
    with col3:
        sentiment_dist = summary.get('sentiment_distribution', {})
        positive_pct = sentiment_dist.get('positive', 0)
        delta_color = "normal" if positive_pct >= 50 else "inverse"
        st.metric(
            "✅ Positive",
            f"{positive_pct:.1f}%",
            help="Percentage of positive reviews"
        )
    
    with col4:
        negative_pct = sentiment_dist.get('negative', 0)
        st.metric(
            "❌ Negative",
            f"{negative_pct:.1f}%",
            help="Percentage of negative reviews"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Aspect Analysis
    if reviews:
        product_name = results.get('metadata', {}).get('product_name', 'Unknown')
        try:
            display_aspect_analysis(reviews, product_name)
        except Exception as e:
            st.error(f"❌ Aspect analysis failed: {str(e)}")
            logger.exception("Aspect analysis error")
    
    st.markdown("---")
    
    # Visualizations
    st.subheader("📊 Visual Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Sentiment Distribution")
        if sentiment_dist:
            fig = go.Figure(data=[go.Pie(
                labels=['Positive 😊', 'Neutral 😐', 'Negative 😞'],
                values=[
                    sentiment_dist.get('positive', 0),
                    sentiment_dist.get('neutral', 0),
                    sentiment_dist.get('negative', 0)
                ],
                hole=0.4,
                marker_colors=['#10b981', '#f59e0b', '#ef4444'],
                textinfo='label+percent',
                textposition='inside'
            )])
            fig.update_layout(
                height=350,
                font=dict(size=13, family="Inter"),
                showlegend=True,
                margin=dict(t=30, b=30, l=30, r=30)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### ⭐ Rating Distribution")
        if reviews:
            ratings = [r.get('rating', 0) for r in reviews if r.get('rating')]
            if ratings:
                rating_counts = pd.Series(ratings).value_counts().sort_index()
                
                fig = go.Figure(data=[go.Bar(
                    x=[f"{int(r)} ⭐" for r in rating_counts.index],
                    y=rating_counts.values,
                    marker=dict(
                        color=rating_counts.values,
                        colorscale='Viridis',
                        showscale=False
                    ),
                    text=rating_counts.values,
                    textposition='auto'
                )])
                fig.update_layout(
                    xaxis_title="Rating",
                    yaxis_title="Number of Reviews",
                    height=350,
                    font=dict(size=13, family="Inter"),
                    margin=dict(t=30, b=30, l=30, r=30)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ No rating data available")
    
    # Key Themes with enhanced styling
    if summary.get('positive_themes') or summary.get('negative_themes'):
        st.markdown("---")
        st.subheader("💡 Key Themes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ✅ Positive Themes")
            pos_themes = summary.get('positive_themes', [])
            if pos_themes:
                for theme in pos_themes:
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                                    padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.5rem;
                                    border-left: 3px solid #10b981;'>
                            <span style='color: #065f46; font-weight: 600;'>• {theme}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ No significant themes found")
        
        with col2:
            st.markdown("### ❌ Negative Themes")
            neg_themes = summary.get('negative_themes', [])
            if neg_themes:
                for theme in neg_themes:
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                                    padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.5rem;
                                    border-left: 3px solid #ef4444;'>
                            <span style='color: #7f1d1d; font-weight: 600;'>• {theme}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ No significant themes found")
    
    # Individual Reviews Section
    st.markdown("---")
    st.markdown('<div class="section-header"><span class="icon-badge">💬</span><h2>Individual Reviews</h2></div>', unsafe_allow_html=True)
    
    # Filter options with enhanced UI
    with st.expander("🔧 Filter Options", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sentiment_filter = st.selectbox(
                "😊 Filter by Sentiment",
                ["All", "Positive", "Negative", "Neutral"]
            )
        
        with col2:
            min_rating = st.slider("⭐ Min Rating", 1, 5, 1)
        
        with col3:
            sort_by = st.selectbox("🔄 Sort by", ["Date", "Rating", "Sentiment Score"])
    
    # Filter reviews
    filtered_reviews = reviews
    
    if sentiment_filter != "All":
        filtered_reviews = [
            r for r in filtered_reviews
            if r.get('sentiment_analysis', {}).get('sentiment', '').lower() == sentiment_filter.lower()
        ]
    
    filtered_reviews = [r for r in filtered_reviews if r.get('rating', 0) >= min_rating]
    
    # Sort reviews
    if sort_by == "Rating":
        filtered_reviews.sort(key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_by == "Sentiment Score":
        filtered_reviews.sort(
            key=lambda x: x.get('sentiment_analysis', {}).get('score', 0),
            reverse=True
        )
    
    # Display count with styling
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); 
                    padding: 0.75rem; border-radius: 8px; margin: 1rem 0;'>
            <span style='color: #374151; font-weight: 600;'>
                📊 Showing {len(filtered_reviews)} of {len(reviews)} reviews
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    # Display reviews with enhanced cards
    for i, review in enumerate(filtered_reviews[:20], 1):
        sentiment_data = review.get('sentiment_analysis', {})
        sentiment = sentiment_data.get('sentiment', 'neutral')
        score = sentiment_data.get('score', 0)
        
        # Sentiment styling
        if sentiment == 'positive':
            sentiment_badge = '<span class="sentiment-positive">😊 Positive</span>'
            border_color = '#10b981'
        elif sentiment == 'negative':
            sentiment_badge = '<span class="sentiment-negative">😞 Negative</span>'
            border_color = '#ef4444'
        else:
            sentiment_badge = '<span class="sentiment-neutral">😐 Neutral</span>'
            border_color = '#f59e0b'
        
        # Star rating
        rating = review.get('rating', 0)
        stars = "⭐" * int(rating) if rating else "N/A"
        
        with st.expander(f"Review #{i} - {review.get('reviewer', 'Anonymous')} - {stars}"):
            st.markdown(f"""
                <div style='border-left: 4px solid {border_color}; padding-left: 1rem;'>
                    <p style='color: #1f2937; font-size: 1rem; line-height: 1.6;'>
                        {review.get('review_text', 'No text')}
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Sentiment:** {sentiment_badge}", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Score:** `{score:.2f}`")
            with col3:
                st.markdown(f"**Date:** {review.get('review_date', 'N/A')}")
    
    if len(filtered_reviews) > 20:
        st.info(f"ℹ️ Showing first 20 reviews. Total filtered reviews: {len(filtered_reviews)}")
    
    # Export Options with enhanced styling
    st.markdown("---")
    st.markdown('<div class="section-header"><span class="icon-badge">📥</span><h2>Export Results</h2></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV Export
        if reviews:
            df = pd.DataFrame([{
                'Product': r.get('product_name'),
                'Review': r.get('review_text'),
                'Rating': r.get('rating'),
                'Reviewer': r.get('reviewer'),
                'Date': r.get('review_date'),
                'Source': r.get('source'),
                'Sentiment': r.get('sentiment_analysis', {}).get('sentiment'),
                'Score': r.get('sentiment_analysis', {}).get('score')
            } for r in reviews])
            
            csv = df.to_csv(index=False)
            st.download_button(
                "📊 Download as CSV",
                data=csv,
                file_name=f"reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        # JSON Export
        import json
        
        def date_converter(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return obj
        
        json_data = json.dumps(results, default=date_converter, indent=2)
        st.download_button(
            "📄 Download as JSON",
            data=json_data,
            file_name=f"reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        # Summary Report
        summary_text = f"""
        REVIEW ANALYSIS SUMMARY
        =======================
        
        Product: {product_name}
        Source: {metadata.get('source', 'Unknown').upper()}
        Analysis Date: {metadata.get('fetched_at', 'N/A')[:10]}
        
        METRICS
        -------
        Total Reviews: {summary.get('total_reviews', 0)}
        Average Rating: {summary.get('average_rating', 0):.1f}/5.0
        
        SENTIMENT DISTRIBUTION
        ----------------------
        Positive: {sentiment_dist.get('positive', 0):.1f}%
        Neutral: {sentiment_dist.get('neutral', 0):.1f}%
        Negative: {sentiment_dist.get('negative', 0):.1f}%
        """
        
        st.download_button(
            "📝 Download Summary",
            data=summary_text,
            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )


# Main execution
if __name__ == "__main__":
    st.set_page_config(page_title="Review Analysis", layout="wide")
    show_complete_dashboard()