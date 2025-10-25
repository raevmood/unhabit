# ==================== Home.py ====================
# Main entry point - place this in your project root
# Run with: streamlit run Home.py

import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from utils.agents import AgentFactory

# Page config
st.set_page_config(
    page_title="unHabit - Behavioral Recovery",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for calming green theme with dark mode
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-green: #4CAF50;
        --light-green: #81C784;
        --dark-green: #2E7D32;
        --bg-light: #F1F8F4;
        --text-dark: #1B5E20;
    }
    
    /* Dark mode */
    [data-theme="dark"] {
        --primary-green: #66BB6A;
        --light-green: #4CAF50;
        --dark-green: #81C784;
        --bg-dark: #1E1E1E;
        --text-light: #E8F5E9;
    }
    
    /* Chat messages */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 80%;
    }
    
    /* Goal cards */
    .goal-card {
        background: white;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .goal-card-high {
        border-left-color: #F44336;
    }
    
    .goal-card-medium {
        border-left-color: #FF9800;
    }
    
    .goal-card-low {
        border-left-color: #2196F3;
    }
    
    /* Community cards */
    .community-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        transition: transform 0.2s;
    }
    
    .community-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: bold;
        margin: 0;
    }
    
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for user ID
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# Initialize agents (only once)
if 'agents_initialized' not in st.session_state:
    try:
        with st.spinner("🚀 Initializing AI agents..."):
            # Get configuration from secrets
            n8n_webhook_url = st.secrets.get("N8N_WEBHOOK_URL", None)
            
            # Initialize all agents
            agents = AgentFactory.create_all_agents(n8n_webhook_url=n8n_webhook_url)
            
            # Store in session state
            st.session_state.reflections_agent = agents['reflections_agent']
            st.session_state.goal_planner_agent = agents['goal_planner_agent']
            st.session_state.support_agent = agents['support_agent']
            st.session_state.assessment_agent = agents['assessment_agent']
            st.session_state.agents_initialized = True
            
            st.success("✅ AI agents initialized successfully!")
            
    except Exception as e:
        st.error(f"❌ Failed to initialize AI agents: {str(e)}")
        st.error("Please check your .streamlit/secrets.toml file and ensure all required API keys are present:")
        st.code("""
# Required in .streamlit/secrets.toml:
GEMINI_API_KEY = "your-gemini-api-key"
SERPER_API_KEY = "your-serper-api-key"
N8N_WEBHOOK_URL = "your-n8n-webhook-url"  # Optional
        """)
        st.stop()

# Sidebar
with st.sidebar:
    st.title("🧠 unHabit")
    st.caption("AI-Powered Behavioral Recovery")
    
    st.divider()
    
    # User ID display
    st.text_input("Your ID", value=st.session_state.user_id, disabled=True, key="user_id_display")
    
    # Theme toggle
    theme_col1, theme_col2 = st.columns(2)
    with theme_col1:
        if st.button("☀️ Light"):
            st.session_state.theme = 'light'
    with theme_col2:
        if st.button("🌙 Dark"):
            st.session_state.theme = 'dark'
    
    st.divider()
    
    # System Status
    st.subheader("System Status")
    if st.session_state.get('agents_initialized'):
        st.success("✅ All Agents Ready")
        st.caption("• Reflections Agent: Active")
        st.caption("• Goal Planner: Active")
        st.caption("• Support Agent: Active")
        st.caption("• Assessment Agent: Active")
    else:
        st.error("❌ Agents Not Initialized")
    
    st.divider()
    
    # Navigation info
    st.info("""
    **📍 Navigation**
    - 💬 Home: Chat & Reflections
    - 🔍 Support: Find Communities  
    - 📊 Dashboard: Your Progress
    """)
    
    st.divider()
    st.caption("Built with ❤️ for recovery")

# Main content
st.title("🏠 Welcome to unHabit")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### Your Journey to Better Habits Starts Here
    
    unHabit uses AI to help you:
    - 🧠 **Reflect** on your patterns and triggers
    - 🎯 **Set goals** that actually work for you
    - 🤝 **Find support** from communities that understand
    - 📈 **Track progress** and celebrate wins
    
    **Ready to start?** Choose an option below or navigate using the sidebar.
    """)

with col2:
    st.image("https://via.placeholder.com/300x200/4CAF50/FFFFFF?text=unHabit", use_container_width=True)

# Quick actions
st.divider()
st.subheader("Quick Actions")

action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    if st.button("💬 Start Reflection", use_container_width=True):
        st.switch_page("pages/Reflection.py")

with action_col2:
    if st.button("🔍 Find Support", use_container_width=True):
        st.switch_page("pages/Support.py")

with action_col3:
    if st.button("📊 View Progress", use_container_width=True):
        st.switch_page("pages/Dashboard.py")

# Recent activity preview
st.divider()
st.subheader("Recent Activity")

with st.spinner("Loading your stats..."):
    try:
        assessment_agent = st.session_state.assessment_agent
        stats = assessment_agent.get_user_statistics(st.session_state.user_id)
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{stats.get('total_reflections', 0)}</p>
                <p class="stat-label">Reflections</p>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col2:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{stats.get('total_goals', 0)}</p>
                <p class="stat-label">Goals Created</p>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col3:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{stats.get('total_interactions', 0)}</p>
                <p class="stat-label">Support Interactions</p>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")
        st.info("Start your first reflection to see your stats!")

# Tips section
st.divider()
with st.expander("💡 Tips for Effective Reflection"):
    st.markdown("""
    - **Be honest**: The AI is here to help, not judge
    - **Take your time**: Meaningful reflection can't be rushed
    - **Be specific**: Instead of "I feel bad," try "I feel anxious when..."
    - **Notice patterns**: Pay attention to recurring themes
    - **Celebrate small wins**: Progress isn't always linear
    """)