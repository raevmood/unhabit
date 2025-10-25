# ==================== pages/Support.py ====================
# Support community search page with direct agent integration

import streamlit as st
from datetime import datetime
from utils.agents import UserFeedback

st.set_page_config(
    page_title="Find Support - unHabit",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for community cards
st.markdown("""
<style>
    .community-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }
    
    .community-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        transition: all 0.3s;
    }
    
    .community-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
    
    .badge-reddit { background: #FF4500; color: white; }
    .badge-discord { background: #5865F2; color: white; }
    .badge-forum { background: #4CAF50; color: white; }
    .badge-facebook_group { background: #1877F2; color: white; }
    .badge-online_community { background: #9C27B0; color: white; }
    .badge-meetup { background: #ED1C40; color: white; }
    .badge-12_step_program { background: #00897B; color: white; }
</style>
""", unsafe_allow_html=True)

# Check if agents are initialized
if not st.session_state.get('agents_initialized'):
    st.error("❌ Agents not initialized. Please return to the home page.")
    if st.button("🏠 Go to Home"):
        st.switch_page("Home.py")
    st.stop()

# Get agents from session state
support_agent = st.session_state.support_agent
assessment_agent = st.session_state.assessment_agent
USER_ID = st.session_state.user_id

# Initialize session state for search
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# Helper function to submit feedback
def submit_feedback(community, reaction):
    """Submit user feedback on a community"""
    try:
        feedback = UserFeedback(
            user_id=USER_ID,
            recommendation_id=community.url,
            reaction=reaction,
            notes=f"Feedback on: {community.title}",
            timestamp=datetime.now()
        )
        
        # Record feedback with Support Agent
        support_agent.record_feedback(feedback)
        
        # Immediately collect and send to Assessment Agent
        feedback_list = support_agent.get_feedback_for_assessment(USER_ID)
        if feedback_list:
            assessment_agent.collect_support_feedback(feedback_list)
            # Process and update memory
            assessment_agent.process_and_update_memory(USER_ID)
        
        st.toast(f"✅ Feedback recorded: {reaction}", icon="✅")
        
    except Exception as e:
        st.error(f"❌ Error submitting feedback: {str(e)}")

# Page header
st.title("🔍 Find Your Support Community")
st.caption("Discover communities that understand your journey")

# Search interface
st.divider()

col1, col2 = st.columns([3, 1])

with col1:
    search_query = st.text_input(
        "What kind of support are you looking for?",
        placeholder="e.g., social media addiction, procrastination recovery, mindful eating",
        key="support_search_query"
    )

with col2:
    addiction_type = st.selectbox(
        "Category",
        ["Any", "Social Media", "Procrastination", "Overeating", "Eating Disorder", "Other"],
        key="addiction_type_select"
    )

search_button = st.button("🔍 Search Communities", use_container_width=True)

# Sidebar with filters and history
with st.sidebar:
    st.subheader("Filters")
    
    community_types = st.multiselect(
        "Community Type",
        ["Reddit", "Discord", "Forum", "Facebook Group", "Online Community"],
        default=[]
    )
    
    st.divider()
    
    st.subheader("Search History")
    if st.session_state.search_history:
        for idx, search in enumerate(st.session_state.search_history[-5:]):
            if st.button(f"🔄 {search[:30]}...", key=f"history_{idx}", use_container_width=True):
                st.session_state.search_query = search
                st.rerun()
    else:
        st.caption("No search history yet")

# Perform search
if search_button and search_query:
    with st.spinner("🔍 Searching for communities..."):
        try:
            # Prepare filters
            filters = {
                'community_types': [ct.lower().replace(' ', '_') for ct in community_types] if community_types else None
            }
            
            # Call Support Agent
            recommendations = support_agent.search_communities(
                user_id=USER_ID,
                query=search_query,
                addiction_type=addiction_type if addiction_type != "Any" else None,
                filters=filters
            )
            
            # Store results
            st.session_state.search_results = {
                'recommendations': recommendations,
                'count': len(recommendations)
            }
            
            # Add to search history
            if search_query not in st.session_state.search_history:
                st.session_state.search_history.append(search_query)
            
            st.success(f"✅ Found {len(recommendations)} communities!")
            
        except Exception as e:
            st.error(f"❌ Search failed: {str(e)}")

# Display results
st.divider()

if st.session_state.search_results:
    recommendations = st.session_state.search_results.get('recommendations', [])
    
    if recommendations:
        st.subheader(f"Found {len(recommendations)} Communities")
        
        # Display as cards
        for idx, community in enumerate(recommendations):
            # Get badge class based on community type
            comm_type = community.community_type
            badge_class = f"badge-{comm_type}"
            
            # Relevance score as percentage
            relevance = int(community.relevance_score * 100)
            
            st.markdown(f"""
            <div class="community-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="margin: 0 0 0.5rem 0;">{community.title}</h3>
                        <span class="community-badge {badge_class}">{comm_type.replace('_', ' ').title()}</span>
                        <span class="community-badge" style="background: #E0E0E0; color: #333;">
                            {relevance}% match
                        </span>
                    </div>
                </div>
                <p style="margin: 1rem 0;">{community.description}</p>
                <a href="{community.url}" target="_blank" style="color: #4CAF50; text-decoration: none; font-weight: bold;">
                    Visit Community →
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            # Feedback buttons
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col2:
                if st.button("✅ Helpful", key=f"helpful_{idx}"):
                    submit_feedback(community, "accepted")
            with col3:
                if st.button("⭐ Interested", key=f"interested_{idx}"):
                    submit_feedback(community, "interested")
            with col4:
                if st.button("❌ Not Relevant", key=f"not_relevant_{idx}"):
                    submit_feedback(community, "rejected")
            
            st.divider()
    
    else:
        st.info("No communities found. Try different search terms or broaden your filters.")

else:
    # Show example searches
    st.info("👆 Enter your search above to find support communities")
    
    st.subheader("💡 Try searching for:")
    
    example_col1, example_col2 = st.columns(2)
    
    with example_col1:
        st.markdown("""
        - Social media addiction support
        - Procrastination recovery
        - Mindful eating communities
        - Digital minimalism groups
        """)
    
    with example_col2:
        st.markdown("""
        - Reddit communities for habit change
        - Discord servers for accountability
        - Online support groups for recovery
        - Forums for behavioral change
        """)