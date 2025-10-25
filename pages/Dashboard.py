# ==================== pages/Dashboard.py ====================
# User progress and statistics dashboard with direct agent integration

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(
    page_title="Dashboard - unHabit",
    page_icon="📊",
    layout="wide"
)

# Check if agents are initialized
if not st.session_state.get('agents_initialized'):
    st.error("❌ Agents not initialized. Please return to the home page.")
    if st.button("🏠 Go to Home"):
        st.switch_page("Home.py")
    st.stop()

# Get agents from session state
assessment_agent = st.session_state.assessment_agent
USER_ID = st.session_state.user_id

# Page header
st.title("📊 Your Progress Dashboard")
st.caption("Track your journey and celebrate your wins")

# Fetch user stats
with st.spinner("Loading your statistics..."):
    try:
        stats = assessment_agent.get_user_statistics(USER_ID)
    except Exception as e:
        st.error(f"❌ Error loading statistics: {str(e)}")
        stats = None

if stats:
    # Top metrics
    st.subheader("📈 Overview")
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            label="Total Reflections",
            value=stats.get('total_reflections', 0),
            delta="+1 this week" if stats.get('total_reflections', 0) > 0 else None
        )
    
    with metric_col2:
        st.metric(
            label="Goals Created",
            value=stats.get('total_goals', 0),
            delta="+3 this week" if stats.get('total_goals', 0) > 0 else None
        )
    
    with metric_col3:
        st.metric(
            label="Support Searches",
            value=stats.get('total_interactions', 0),
            delta=None
        )
    
    with metric_col4:
        completion_rate = (stats.get('total_goals', 0) * 0.7)  # Mock completion rate
        st.metric(
            label="Goal Completion",
            value=f"{int(completion_rate)}%",
            delta="+5% from last week" if completion_rate > 0 else None
        )
    
    st.divider()
    
    # Current state summary
    st.subheader("🧠 Current State")
    
    current_state = stats.get('current_state')
    if current_state:
        st.info(current_state)
    else:
        st.info("Complete your first reflection to see your mental state analysis.")
    
    st.divider()
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("📅 Activity Over Time")
        
        # Mock data for activity chart
        dates = pd.date_range(end=datetime.now(), periods=14, freq='D')
        reflections_data = [0, 1, 0, 2, 1, 0, 1, 3, 0, 1, 2, 1, 0, stats.get('total_reflections', 1)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=reflections_data,
            mode='lines+markers',
            name='Reflections',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Daily Reflection Activity",
            xaxis_title="Date",
            yaxis_title="Reflections",
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        st.subheader("🎯 Goal Breakdown")
        
        # Mock goal priority data
        total_goals = max(stats.get('total_goals', 0), 1)
        goal_data = {
            'Priority': ['High', 'Medium', 'Low'],
            'Count': [
                int(total_goals * 0.3),
                int(total_goals * 0.5),
                int(total_goals * 0.2)
            ]
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=goal_data['Priority'],
            values=goal_data['Count'],
            marker=dict(colors=['#F44336', '#FF9800', '#2196F3']),
            hole=0.4
        )])
        
        fig.update_layout(
            title="Goals by Priority",
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Emotional trends
    st.subheader("💭 Emotional Patterns")
    
    # Mock emotional tone data
    emotions_data = {
        'Emotion': ['Hopeful', 'Anxious', 'Determined', 'Frustrated', 'Calm'],
        'Frequency': [8, 5, 6, 3, 7]
    }
    
    fig = px.bar(
        emotions_data,
        x='Emotion',
        y='Frequency',
        color='Frequency',
        color_continuous_scale=['#81C784', '#4CAF50', '#2E7D32'],
        title="Most Common Emotional Tones in Reflections"
    )
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Reflection summaries
    st.subheader("📝 Recent Reflections")
    
    # Mock reflection summaries
    mock_reflections = [
        {
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'title': 'Struggling with social media',
            'themes': ['social media', 'productivity', 'self-control'],
            'tone': 'frustrated but motivated'
        },
        {
            'date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'title': 'Making progress on morning routine',
            'themes': ['habits', 'morning routine', 'consistency'],
            'tone': 'hopeful'
        },
        {
            'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            'title': 'Feeling overwhelmed with goals',
            'themes': ['goal-setting', 'anxiety', 'perfectionism'],
            'tone': 'anxious'
        }
    ]
    
    for reflection in mock_reflections:
        with st.expander(f"📅 {reflection['date']} - {reflection['title']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Themes:**")
                for theme in reflection['themes']:
                    st.markdown(f"- {theme}")
            
            with col2:
                st.info(f"**Tone:** {reflection['tone']}")
            
            if st.button(f"View Full Reflection", key=f"view_{reflection['date']}"):
                st.info("Full reflection view coming soon!")
    
    st.divider()
    
    # Achievements section
    st.subheader("🏆 Achievements")
    
    achievement_col1, achievement_col2, achievement_col3 = st.columns(3)
    
    with achievement_col1:
        if stats.get('total_reflections', 0) >= 7:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); border-radius: 15px; color: white;">
                <h1 style="margin: 0;">🔥</h1>
                <h3>7-Day Streak</h3>
                <p>Reflected daily for a week!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: #E0E0E0; border-radius: 15px; color: #666;">
                <h1 style="margin: 0;">🔒</h1>
                <h3>7-Day Streak</h3>
                <p>Locked</p>
            </div>
            """, unsafe_allow_html=True)
    
    with achievement_col2:
        if stats.get('total_goals', 0) >= 10:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%); border-radius: 15px; color: white;">
                <h1 style="margin: 0;">🎯</h1>
                <h3>Goal Setter</h3>
                <p>Created 10 goals</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: #E0E0E0; border-radius: 15px; color: #666;">
                <h1 style="margin: 0;">🔒</h1>
                <h3>Goal Setter</h3>
                <p>Locked</p>
            </div>
            """, unsafe_allow_html=True)
    
    with achievement_col3:
        if stats.get('total_interactions', 0) >= 5:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #2196F3 0%, #64B5F6 100%); border-radius: 15px; color: white;">
                <h1 style="margin: 0;">🤝</h1>
                <h3>Community Seeker</h3>
                <p>Found 5 support groups</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: #E0E0E0; border-radius: 15px; color: #666;">
                <h1 style="margin: 0;">🔒</h1>
                <h3>Community Seeker</h3>
                <p>Locked</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Action buttons
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("💬 Start New Reflection", use_container_width=True):
            st.switch_page("pages/Reflection.py")
    
    with action_col2:
        if st.button("🔍 Find Support", use_container_width=True):
            st.switch_page("pages/Support.py")

else:
    # No data yet
    st.info("🌱 Your journey starts here!")
    
    st.markdown("""
    ### Getting Started
    
    You haven't created any reflections yet. Here's how to begin:
    
    1. **💬 Start a Reflection** - Share your thoughts and feelings
    2. **🎯 Receive Goals** - Get personalized action items
    3. **🔍 Find Support** - Discover communities that understand
    4. **📊 Track Progress** - Watch your growth over time
    """)
    
    if st.button("🚀 Start Your First Reflection", use_container_width=True):
        st.switch_page("pages/Reflection.py")