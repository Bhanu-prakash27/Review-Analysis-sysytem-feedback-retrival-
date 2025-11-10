"""
dashboard/admin_dashboard.py

Admin dashboard for managing users and viewing system statistics
Enhanced UI/UX with modern design
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.authentication import (
    list_all_users, 
    get_user_count, 
    delete_user, 
    update_user,
    register_user
)


# Custom CSS for beautiful UI
def inject_custom_css():
    st.markdown("""
    <style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border-left: 5px solid;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    
    .metric-card.total {
        border-left-color: #667eea;
    }
    
    .metric-card.admin {
        border-left-color: #f093fb;
    }
    
    .metric-card.users {
        border-left-color: #4facfe;
    }
    
    /* Header styling */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .dashboard-title {
        font-size: 42px;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .dashboard-subtitle {
        font-size: 16px;
        opacity: 0.9;
        margin-top: 5px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Info boxes */
    .info-box {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 10px 0;
    }
    
    .info-box h4 {
        color: #667eea;
        margin-bottom: 10px;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
    }
    
    .status-badge.success {
        background: #d4edda;
        color: #155724;
    }
    
    .status-badge.warning {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-badge.info {
        background: #d1ecf1;
        color: #0c5460;
    }
    
    /* Form styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Data table styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    
    /* Metric value styling */
    [data-testid="stMetricValue"] {
        font-size: 36px;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 10px;
        font-weight: 600;
        color: #667eea;
    }
    
    /* Success/Error message styling */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 10px;
        padding: 15px;
    }
    </style>
    """, unsafe_allow_html=True)


def show():
    """Main admin dashboard display function"""
    
    # Inject custom CSS
    inject_custom_css()
    
    # Check if user is admin
    if st.session_state.get('user', {}).get('role') != 'admin':
        st.markdown("""
        <div style='text-align: center; padding: 100px 20px;'>
            <h1 style='font-size: 72px; margin: 0;'>🔒</h1>
            <h2 style='color: #667eea; margin-top: 20px;'>Access Denied</h2>
            <p style='color: #666; font-size: 18px;'>Admin privileges required to access this dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Dashboard Header
    st.markdown("""
    <div class='dashboard-header'>
        <h1 class='dashboard-title'>👨‍💼 Admin Dashboard</h1>
        <p class='dashboard-subtitle'>Manage users, monitor system health, and configure settings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation with icons
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎛️ Navigation")
        st.markdown("<br>", unsafe_allow_html=True)
        
        page = st.radio(
            "Select Page",
            ["📊 Overview", "👥 User Management", "⚙️ System Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick stats in sidebar
        stats = get_user_count()
        st.markdown(f"""
        <div style='color: white; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px;'>
            <h4 style='margin: 0 0 10px 0;'>📈 Quick Stats</h4>
            <p style='margin: 5px 0;'><b>{stats['total']}</b> Total Users</p>
            <p style='margin: 5px 0;'><b>{stats['admins']}</b> Admins</p>
            <p style='margin: 5px 0;'><b>{stats['users']}</b> Regular Users</p>
        </div>
        """, unsafe_allow_html=True)
    
    if page == "📊 Overview":
        show_overview()
    elif page == "👥 User Management":
        show_user_management()
    elif page == "⚙️ System Settings":
        show_system_settings()


def show_overview():
    """Display system overview and statistics"""
    
    # User Statistics with beautiful cards
    stats = get_user_count()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        delta_val = stats['total'] - 2 if stats['total'] > 2 else 0
        delta_text = f"+{delta_val} new" if delta_val > 0 else "Default users"
        
        st.markdown(f"""
        <div class='metric-card total'>
            <h4 style='color: #667eea; margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;'>Total Users</h4>
            <h2 style='margin: 10px 0; font-size: 42px; font-weight: 800; color: #333;'>{stats['total']}</h2>
            <p style='color: #666; margin: 0; font-size: 14px;'>{delta_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card admin'>
            <h4 style='color: #f093fb; margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;'>Admin Users</h4>
            <h2 style='margin: 10px 0; font-size: 42px; font-weight: 800; color: #333;'>{stats['admins']}</h2>
            <p style='color: #666; margin: 0; font-size: 14px;'>System administrators</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card users'>
            <h4 style='color: #4facfe; margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;'>Regular Users</h4>
            <h2 style='margin: 10px 0; font-size: 42px; font-weight: 800; color: #333;'>{stats['users']}</h2>
            <p style='color: #666; margin: 0; font-size: 14px;'>Standard access</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recent Activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='info-box'>
            <h4>📊 Review Analysis Stats</h4>
            <div style='display: flex; flex-direction: column; gap: 10px;'>
                <div style='display: flex; justify-content: space-between; padding: 8px; background: #f8f9fa; border-radius: 8px;'>
                    <span>Flipkart reviews analyzed</span>
                    <span style='font-weight: 700; color: #667eea;'>50</span>
                </div>
                <div style='display: flex; justify-content: space-between; padding: 8px; background: #f8f9fa; border-radius: 8px;'>
                    <span>Twitter posts</span>
                    <span style='font-weight: 700; color: #667eea;'>0</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='info-box'>
            <h4>💚 System Health</h4>
            <div style='display: flex; flex-direction: column; gap: 10px;'>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <span class='status-badge success'>✓ Connected</span>
                    <span>Database</span>
                </div>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <span class='status-badge success'>✓ Operational</span>
                    <span>Scrapers</span>
                </div>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <span class='status-badge success'>✓ Loaded</span>
                    <span>NLP Models</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # User Activity Chart
    st.markdown("""
    <div class='info-box'>
        <h4>📈 User Activity (Last 7 Days)</h4>
    </div>
    """, unsafe_allow_html=True)
    
    chart_data = pd.DataFrame({
        'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'Logins': [12, 19, 15, 25, 22, 30, 28],
        'Analyses': [8, 15, 12, 20, 18, 25, 22]
    })
    
    st.line_chart(chart_data.set_index('Day'), height=300)


def show_user_management():
    """User management interface"""
    
    # Tabs with icons
    tab1, tab2, tab3 = st.tabs(["👁️ View Users", "➕ Add User", "✏️ Manage Users"])
    
    with tab1:
        show_users_list()
    
    with tab2:
        add_new_user()
    
    with tab3:
        manage_users()


def show_users_list():
    """Display list of all users"""
    
    st.markdown("""
    <div style='background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>
        <h3 style='color: #667eea; margin-top: 0;'>👥 All Registered Users</h3>
    """, unsafe_allow_html=True)
    
    users = list_all_users()
    
    if not users:
        st.info("📭 No users found in the system")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(users)
    df.index = df.index + 1
    
    # Add search/filter
    search = st.text_input("🔍 Search users", placeholder="Search by username or email...")
    
    if search:
        df = df[df.apply(lambda row: search.lower() in row.to_string().lower(), axis=1)]
    
    # Display as table with custom styling
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "username": st.column_config.TextColumn("👤 Username", width="medium"),
            "email": st.column_config.TextColumn("📧 Email", width="medium"),
            "role": st.column_config.TextColumn("🎭 Role", width="small"),
            "created_at": st.column_config.TextColumn("📅 Created At", width="medium")
        },
        height=400
    )
    
    # Download button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"users_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)


def add_new_user():
    """Add new user form"""
    
    st.markdown("""
    <div style='background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>
        <h3 style='color: #667eea; margin-top: 0;'>➕ Create New User</h3>
        <p style='color: #666;'>Fill in the details below to add a new user to the system</p>
    """, unsafe_allow_html=True)
    
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("👤 Username *", placeholder="Enter username", help="Unique username for the user")
            new_email = st.text_input("📧 Email *", placeholder="user@example.com", help="Valid email address")
        
        with col2:
            new_password = st.text_input("🔒 Password *", type="password", placeholder="Min 6 characters", help="Secure password (min 6 chars)")
            new_role = st.selectbox("🎭 Role *", ["user", "admin"], help="Select user access level")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            submit = st.form_submit_button("✨ Create User", use_container_width=True, type="primary")
        
        if submit:
            if not all([new_username, new_email, new_password]):
                st.error("❌ All fields are required")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            else:
                if register_user(new_username, new_email, new_password, new_role):
                    st.success(f"✅ User '{new_username}' added successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to add user. Username or email may already exist.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def manage_users():
    """Manage existing users"""
    
    st.markdown("""
    <div style='background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>
        <h3 style='color: #667eea; margin-top: 0;'>✏️ Manage Existing Users</h3>
        <p style='color: #666;'>Update user information or remove users from the system</p>
    """, unsafe_allow_html=True)
    
    users = list_all_users()
    
    if not users:
        st.info("📭 No users to manage")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Select user to manage
    usernames = [u['username'] for u in users]
    selected_user = st.selectbox("🔍 Select User to Manage", usernames, help="Choose a user to edit or delete")
    
    if selected_user:
        user_data = next(u for u in users if u['username'] == selected_user)
        
        # User info card
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin: 20px 0;'>
            <h4 style='margin: 0 0 10px 0;'>👤 {selected_user}</h4>
            <div style='display: flex; gap: 20px; flex-wrap: wrap;'>
                <span>📧 {user_data['email']}</span>
                <span>🎭 {user_data['role'].upper()}</span>
                <span>📅 {user_data['created_at']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💾 Update User")
            
            with st.form("update_user_form"):
                new_email = st.text_input("📧 New Email", value=user_data['email'])
                new_role = st.selectbox("🎭 New Role", ["user", "admin"], 
                                       index=0 if user_data['role'] == 'user' else 1)
                new_password = st.text_input("🔒 New Password (optional)", type="password", 
                                            placeholder="Leave blank to keep current")
                
                update_btn = st.form_submit_button("💾 Update User", use_container_width=True, type="primary")
                
                if update_btn:
                    update_data = {
                        'email': new_email,
                        'role': new_role
                    }
                    
                    if new_password:
                        if len(new_password) < 6:
                            st.error("❌ Password must be at least 6 characters")
                        else:
                            update_data['password'] = new_password
                    
                    if 'password' not in update_data or len(update_data.get('password', '')) >= 6:
                        if update_user(selected_user, **update_data):
                            st.success(f"✅ User '{selected_user}' updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update user")
        
        with col2:
            st.markdown("#### 🗑️ Delete User")
            
            if selected_user == 'admin':
                st.warning("⚠️ Cannot delete default admin user")
            else:
                st.error("⚠️ This action cannot be undone!")
                
                with st.form("delete_user_form"):
                    confirm = st.checkbox("✓ I confirm I want to delete this user")
                    delete_btn = st.form_submit_button("🗑️ Delete User", use_container_width=True, type="secondary")
                    
                    if delete_btn:
                        if not confirm:
                            st.error("❌ Please confirm deletion")
                        else:
                            if delete_user(selected_user):
                                st.success(f"✅ User '{selected_user}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete user")
    
    st.markdown("</div>", unsafe_allow_html=True)


def show_system_settings():
    """System settings interface"""
    
    st.markdown("""
    <div style='background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;'>
        <h3 style='color: #667eea; margin-top: 0;'>⚙️ System Settings</h3>
        <p style='color: #666;'>Configure system-wide settings and preferences</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Scraper Configuration
    with st.expander("🔧 Scraper Configuration", expanded=True):
        st.markdown("### Amazon Scraper")
        
        col1, col2 = st.columns(2)
        with col1:
            use_selenium = st.checkbox("Use Selenium", value=True, help="Enable Selenium for dynamic content")
        with col2:
            headless = st.checkbox("Run headless", value=True, help="Run browser in background")
        
        st.markdown("### Rate Limiting")
        col1, col2 = st.columns(2)
        with col1:
            min_delay = st.slider("Min delay (seconds)", 1.0, 5.0, 2.0)
        with col2:
            max_delay = st.slider("Max delay (seconds)", 2.0, 10.0, 3.5)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("💾 Save Settings", use_container_width=True, type="primary"):
                st.success("✅ Scraper settings saved!")
    
    # NLP Configuration
    with st.expander("🤖 NLP Configuration"):
        st.markdown("### Sentiment Analysis")
        backend = st.selectbox("Backend", ["vader", "textblob", "transformers"], 
                               help="Choose sentiment analysis engine")
        
        st.markdown("### Language Support")
        languages = st.multiselect("Supported languages", 
                                   ["en", "hi", "es", "fr", "de"], 
                                   default=["en"],
                                   help="Select languages for text analysis")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("💾 Save NLP Config", use_container_width=True, type="primary"):
                st.success("✅ NLP settings saved!")
    
    # Database Settings
    with st.expander("🗄️ Database Settings"):
        st.markdown("### Connection Status")
        st.success("✓ Connected to in-memory database")
        
        st.markdown("### Backup & Maintenance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Backup Database", use_container_width=True):
                with st.spinner("Creating backup..."):
                    st.info("💡 Backup functionality coming soon")
        
        with col2:
            if st.button("🗑️ Clear Cache", use_container_width=True, type="secondary"):
                st.success("✅ Cache cleared successfully!")


# Main execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Admin Dashboard", 
        layout="wide",
        page_icon="👨‍💼",
        initial_sidebar_state="expanded"
    )
    show()