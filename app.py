"""
app.py - Complete Application Entry Point (ENHANCED UI VERSION)
Review & Sentiment Analysis Platform - Main Application
Integrates all features: Authentication, Dashboards, NLP, Data Collection
"""
import streamlit as st
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.authentication import login_user, register_user
from dashboard import admin_dashboard
from dashboard.complete_enhanced_dashboard import show_complete_dashboard

# Page Configuration
st.set_page_config(
    page_title="Review Analysis Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS with Modern Design
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Hero Section */
    .hero-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 24px;
        padding: 3rem 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(10px);
        margin-bottom: 2rem;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .hero-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        animation: slideInDown 0.8s ease-out;
    }
    
    .hero-subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1.2rem;
        font-weight: 400;
        margin-top: 0;
    }
    
    /* Auth Container */
    .auth-container {
        background: white;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        animation: fadeIn 0.8s ease-out;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.2em;
        font-weight: 600;
        font-size: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Form Inputs */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
        background-color: transparent;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Feature Cards */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 2rem 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        height: 100%;
        border: 2px solid transparent;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
        border-color: #667eea;
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .feature-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
    }
    
    .feature-text {
        color: #6b7280;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Info Box */
    .stAlert {
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, #e0e7ff 0%, #ede9fe 100%);
        padding: 1rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    .user-profile-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 2px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .user-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        margin: 0 auto 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Metrics */
    .stMetric {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #667eea;
    }
    
    /* Select Box */
    .stSelectbox>div>div {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
    }
    
    /* Success/Error Messages */
    .stSuccess, .stError, .stWarning {
        border-radius: 12px;
        padding: 1rem;
        animation: fadeInUp 0.4s ease-out;
    }
    
    /* Form Labels */
    .stTextInput>label, .stSelectbox>label {
        font-weight: 600;
        color: #374151;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 2rem 0;
    }
    
    /* Demo Badge */
    .demo-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None


def show_login_page():
    """Display enhanced login and registration page"""
    
    # Hero Section
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">📊 Review Analysis Platform</h1>
            <p class="hero-subtitle">AI-Powered Sentiment Analysis & Insights</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Login/Register Section
    col1, col2, col3 = st.columns([1, 2.5, 1])
    
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.markdown("### Welcome Back!")
            st.markdown("Login to access your analytics dashboard")
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    submit = st.form_submit_button("🚀 Login", use_container_width=True)
                
                if submit:
                    if username and password:
                        user = login_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
                    else:
                        st.warning("⚠️ Please enter both username and password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Demo credentials with better styling
            st.info("""
                **🎯 Demo Accounts Available:**
                
                **Admin Access:**  
                Username: `admin` | Password: `admin123`
                
                **User Access:**  
                Username: `user` | Password: `user123`
            """)
        
        with tab2:
            st.markdown("### Create Your Account")
            st.markdown("Join us and start analyzing reviews today")
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.form("register_form"):
                new_username = st.text_input("👤 Username", placeholder="Choose a unique username", key="reg_user")
                new_email = st.text_input("📧 Email", placeholder="your.email@example.com", key="reg_email")
                new_password = st.text_input("🔒 Password", type="password", placeholder="Create a strong password", key="reg_pass")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
                role = st.selectbox("👔 Account Type", ["user", "admin"], help="Choose your account type")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                register = st.form_submit_button("✨ Create Account", use_container_width=True)
                
                if register:
                    if not all([new_username, new_email, new_password, confirm_password]):
                        st.warning("⚠️ Please fill all fields")
                    elif new_password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(new_password) < 6:
                        st.warning("⚠️ Password must be at least 6 characters")
                    else:
                        if register_user(new_username, new_email, new_password, role):
                            st.success("✅ Account created successfully! Please login.")
                        else:
                            st.error("❌ Registration failed. Username or email might already exist.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Features Section
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h2 style='color: white; font-size: 2.5rem; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>
                ✨ Platform Features
            </h2>
            <p style='color: rgba(255, 255, 255, 0.9); font-size: 1.1rem;'>
                Powerful tools to analyze and understand customer feedback
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    features = [
        {
            "icon": "🛍️",
            "title": "Multi-Platform Analysis",
            "items": ["Flipkart", "Twitter", "Real-time data collection"]
        },
        {
            "icon": "🤖",
            "title": "Advanced AI/NLP",
            "items": ["Sentiment Analysis", "Aspect-Based Analysis"]
        },
        {
            "icon": "🌍",
            "title": "Global Insights",
            "items": ["Multi-language support",  "Competitor comparison"]
        },
        {
            "icon": "⚡",
            "title": "Smart Features",
            "items": ["Manage users", "Pie-charts"]
        }
    ]
    
    for col, feature in zip([col1, col2, col3, col4], features):
        with col:
            st.markdown(f"""
                <div class="feature-card">
                    <span class="feature-icon">{feature['icon']}</span>
                    <div class="feature-title">{feature['title']}</div>
                    <div class="feature-text">
                        {'<br>'.join([f"✓ {item}" for item in feature['items']])}
                    </div>
                </div>
            """, unsafe_allow_html=True)


def show_main_dashboard():
    """Main application dashboard after login with enhanced UI"""
    
    # Enhanced Sidebar user profile
    with st.sidebar:
        # Get user initials for avatar
        initials = ''.join([word[0].upper() for word in st.session_state.user['username'].split()[:2]])
        if len(initials) == 0:
            initials = st.session_state.user['username'][0].upper()
        
        st.markdown(f"""
            <div class="user-profile-card">
                <div class="user-avatar">{initials}</div>
                <h3 style='margin: 0; text-align: center; font-size: 1.3rem; font-weight: 700;'>
                    {st.session_state.user['username']}
                </h3>
                <p style='margin: 0.5rem 0 0 0; text-align: center; font-size: 0.9rem; opacity: 0.9;'>
                    🎯 {st.session_state.user['role'].upper()}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Route to appropriate dashboard based on role
    if st.session_state.user['role'] == 'admin':
        # Admin gets access to both dashboards
        dashboard_choice = st.sidebar.radio(
            "📍 Navigate",
            ["📊 User Dashboard", "👨‍💼 Admin Dashboard"],
            label_visibility="visible"
        )
        
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        st.sidebar.markdown("""
            <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px;'>
                <p style='margin: 0; font-size: 0.85rem; opacity: 0.9;'>
                    💡 <strong>Admin Tip:</strong><br>
                    Switch between dashboards to access different features and analytics.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if dashboard_choice == "👨‍💼 Admin Dashboard":
            admin_dashboard.show()
        else:
            show_complete_dashboard()
    else:
        # Regular users see the complete enhanced dashboard
        st.sidebar.markdown("""
            <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px;'>
                <p style='margin: 0; font-size: 0.85rem; opacity: 0.9;'>
                    📊 <strong>Dashboard Active</strong><br>
                    Explore your review analytics and insights.
                </p>
            </div>
        """, unsafe_allow_html=True)
        show_complete_dashboard()


def main():
    """Main application entry point"""
    
    # Check login status and route accordingly
    if st.session_state.logged_in:
        show_main_dashboard()
    else:
        show_login_page()


if __name__ == "__main__":
    main()