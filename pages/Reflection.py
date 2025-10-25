# ==================== pages/Reflection.py ====================
# Reflection chat interface with direct agent integration

import streamlit as st
from datetime import datetime
from utils.agents import ReflectionSummary

st.set_page_config(
    page_title="Reflection - unHabit",
    page_icon="💬",
    layout="wide"
)

# Apply same CSS
st.markdown("""
<style>
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        margin-left: 20%;
        text-align: right;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        margin-right: 20%;
    }
    
    .message-time {
        font-size: 0.8rem;
        opacity: 0.7;
        margin-top: 0.5rem;
    }
    
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
</style>
""", unsafe_allow_html=True)

# Check if agents are initialized
if not st.session_state.get('agents_initialized'):
    st.error("❌ Agents not initialized. Please return to the home page.")
    if st.button("🏠 Go to Home"):
        st.switch_page("Home.py")
    st.stop()

# Get agents from session state
reflections_agent = st.session_state.reflections_agent
goal_planner_agent = st.session_state.goal_planner_agent
assessment_agent = st.session_state.assessment_agent
USER_ID = st.session_state.user_id

# Initialize session state for conversation
if 'conversation' not in st.session_state:
    st.session_state.conversation = []

if 'session_started' not in st.session_state:
    st.session_state.session_started = False

if 'session_ended' not in st.session_state:
    st.session_state.session_ended = False

if 'goals_generated' not in st.session_state:
    st.session_state.goals_generated = None

# Page header
st.title("💬 Reflection Space")
st.caption("A safe space to explore your thoughts and patterns")

# Sidebar controls
with st.sidebar:
    st.subheader("Session Controls")
    
    if not st.session_state.session_started:
        if st.button("🟢 Start New Session", use_container_width=True):
            st.session_state.session_started = True
            st.session_state.conversation = []
            st.session_state.session_ended = False
            st.rerun()
    else:
        if st.button("⏸️ Pause Session", use_container_width=True):
            st.session_state.session_started = False
            st.success("Session paused. Click 'Resume' to continue.")
        
        if st.button("🔴 End Session & Generate Goals", use_container_width=True):
            with st.spinner("Generating summary and goals..."):
                try:
                    # Step 1: End reflection and get summary
                    summary = reflections_agent.end_session_and_summarize(USER_ID)
                    
                    # Step 2: Collect summary for Assessment Agent
                    assessment_agent.collect_reflection_summary(summary)
                    
                    # Step 3: Generate goals
                    task_payload = goal_planner_agent.process_reflection_summary(summary)
                    
                    # Step 4: Collect goals for Assessment Agent
                    assessment_agent.collect_goal_summary(task_payload)
                    
                    # Step 5: Process and update memory (Assessment Agent)
                    assessment_result = assessment_agent.process_and_update_memory(USER_ID)
                    
                    # Step 6: Send to n8n for calendar sync
                    calendar_sync = goal_planner_agent.send_to_n8n(task_payload)
                    
                    # Store results
                    st.session_state.goals_generated = {
                        'summary': summary.dict(),
                        'goals': [goal.dict() for goal in task_payload.goals],
                        'calendar_sync': calendar_sync,
                        'assessment_result': assessment_result
                    }
                    st.session_state.session_ended = True
                    st.session_state.session_started = False
                    
                    st.success("✅ Session ended! Scroll down to see your goals.")
                    
                except Exception as e:
                    st.error(f"❌ Error ending session: {str(e)}")
                    
            st.rerun()
    
    if not st.session_state.session_started and st.session_state.conversation:
        if st.button("▶️ Resume Session", use_container_width=True):
            st.session_state.session_started = True
            st.rerun()
    
    st.divider()
    
    # Session info
    st.subheader("Session Info")
    st.metric("Messages", len(st.session_state.conversation))
    if st.session_state.conversation:
        st.caption(f"Started: {st.session_state.conversation[0].get('time', 'Unknown')}")

# Main chat interface
if st.session_state.session_ended and st.session_state.goals_generated:
    # Show goals after session ends
    st.success("🎉 Reflection session completed!")
    
    result = st.session_state.goals_generated
    summary = result.get('summary', {})
    
    # Display summary
    st.subheader("📝 Session Summary")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(summary.get('summary', 'No summary available'))
    with col2:
        st.info(f"**Emotional Tone**: {summary.get('emotional_tone', 'N/A')}")
    
    # Display themes
    if summary.get('key_themes'):
        st.write("**Key Themes:**")
        for theme in summary['key_themes']:
            st.markdown(f"- {theme}")
    
    # Display insights
    if summary.get('insights'):
        st.write("**Insights:**")
        for insight in summary['insights']:
            st.markdown(f"- {insight}")
    
    st.divider()
    
    # Display goals
    st.subheader("🎯 Your Personalized Goals")
    
    goals = result.get('goals', [])
    if goals:
        for i, goal in enumerate(goals, 1):
            priority = goal.get('priority', 'medium')
            card_class = f"goal-card goal-card-{priority}"
            
            st.markdown(f"""
            <div class="{card_class}">
                <h4>{i}. {goal['title']}</h4>
                <p>{goal['description']}</p>
                <div style="display: flex; justify-content: space-between; margin-top: 1rem;">
                    <span>⏱️ {goal['duration_minutes']} min</span>
                    <span>🔥 {priority.upper()}</span>
                    <span>🔄 {goal.get('recurrence', 'One-time')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Calendar sync status
    calendar_sync = result.get('calendar_sync', {})
    if calendar_sync.get('status') == 'success':
        st.success(f"✅ Goals synced to your Google Calendar! ({calendar_sync.get('tasks_sent', 0)} tasks)")
    elif calendar_sync.get('status') == 'error':
        st.warning(f"⚠️ Calendar sync issue: {calendar_sync.get('message', 'Unknown error')}")
    
    # Assessment result
    assessment_result = result.get('assessment_result', {})
    if assessment_result:
        with st.expander("📊 Processing Details"):
            st.write(f"✅ Reflections processed: {assessment_result.get('reflections_processed', 0)}")
            st.write(f"✅ Goals processed: {assessment_result.get('goals_processed', 0)}")
            st.write(f"✅ Memory updated: {assessment_result.get('state_updated', False)}")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start New Reflection", use_container_width=True):
            st.session_state.conversation = []
            st.session_state.session_started = True
            st.session_state.session_ended = False
            st.session_state.goals_generated = None
            st.rerun()
    with col2:
        if st.button("📊 View Dashboard", use_container_width=True):
            st.switch_page("pages/Dashboard.py")

else:
    # Active chat interface
    
    # Display conversation history
    if st.session_state.conversation:
        st.subheader("Conversation")
        
        for msg in st.session_state.conversation:
            # Escape HTML in content to prevent rendering issues
            import html
            safe_content = html.escape(msg['content'])
            
            if msg['role'] == 'user':
                st.markdown(f"""
                <div class="user-message">
                    {safe_content}
                    <div class="message-time">{msg.get('time', '')}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    {safe_content}
                    <div class="message-time">{msg.get('time', '')}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("👋 Start a new session to begin reflecting. I'm here to listen and help you explore your thoughts.")
    
    # Input area
    st.divider()
    
    if st.session_state.session_started:
        # Text input
        user_input = st.text_area(
            "Share your thoughts...",
            placeholder="What's on your mind today?",
            height=100,
            key="reflection_input"
        )
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            send_button = st.button("📤 Send", use_container_width=True)
        
        with col2:
            # Voice input placeholder (requires additional setup)
            voice_button = st.button("🎤 Voice", use_container_width=True, disabled=True)
            if voice_button:
                st.info("Voice input coming soon! For now, please type your message.")
        
        with col3:
            clear_button = st.button("🗑️ Clear", use_container_width=True)
        
        if send_button and user_input:
            # Add user message
            user_msg = {
                'role': 'user',
                'content': user_input,
                'time': datetime.now().strftime('%H:%M')
            }
            st.session_state.conversation.append(user_msg)
            
            # Get AI response
            with st.spinner("Thinking..."):
                try:
                    if len(st.session_state.conversation) == 1:
                        # First message - start session
                        response = reflections_agent.start_reflection_session(USER_ID, user_input)
                    else:
                        # Continue session
                        response = reflections_agent.continue_reflection(USER_ID, user_input)
                    
                    assistant_msg = {
                        'role': 'assistant',
                        'content': response,
                        'time': datetime.now().strftime('%H:%M')
                    }
                    st.session_state.conversation.append(assistant_msg)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    # Remove the user message if there was an error
                    st.session_state.conversation.pop()
            
            st.rerun()
        
        if clear_button:
            st.session_state.conversation = []
            st.rerun()
    
    else:
        st.warning("⏸️ Session paused. Click 'Resume Session' in the sidebar or start a new session.")