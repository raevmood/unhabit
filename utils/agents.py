# ==================== agents.py ====================
"""
Agent implementations for unHabit
All four agents: Reflections, Goal Planner, Support, Assessment
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import uuid
import requests
from pydantic import BaseModel, Field

# Import our modules
from utils.llm_provider import LLMManager
from tools.memory import ChromaDBManager
from tools.vector_tool import VectorUploadTool
from tools.serper_tool import SerperTool
from utils.prompts import (
    ReflectionPrompts,
    GoalPlannerPrompts,
    AssessmentPrompts,
    SupportPrompts
)

# ==================== Data Models ====================

class ReflectionSummary(BaseModel):
    user_id: str
    summary: str
    emotional_tone: str
    key_themes: List[str]
    insights: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

class Goal(BaseModel):
    title: str
    description: str
    priority: str  # high, medium, low
    duration_minutes: int
    recurrence: Optional[str] = None  # daily, weekly, monthly

class TaskPayload(BaseModel):
    user_id: str
    goals: List[Goal]
    source_summary: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SupportRecommendation(BaseModel):
    title: str
    description: str
    url: str
    relevance_score: float
    community_type: str
    source_position: int

class UserFeedback(BaseModel):
    user_id: str
    recommendation_id: str
    reaction: str  # accepted, rejected, interested
    timestamp: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None


# ==================== Agent 1: Reflections Agent ====================

class ReflectionsAgent:
    """
    Primary conversational interface for user reflections
    - Conducts empathetic conversations
    - READ-ONLY access to ChromaDB
    - Generates summaries at end of sessions
    """
    
    def __init__(self, llm_manager: LLMManager, db_manager: ChromaDBManager):
        self.llm = llm_manager
        self.db = db_manager
        self.conversation_buffer = {}  # In-memory session storage
    
    def start_reflection_session(self, user_id: str, initial_message: str) -> str:
        """
        Begin a new reflective conversation
        
        Args:
            user_id: User identifier
            initial_message: User's opening message
        
        Returns:
            Agent's empathetic response
        """
        # Retrieve relevant past reflections
        past_context = self.db.read_reflections(user_id, initial_message, n_results=3)
        user_state = self.db.read_user_state(user_id)
        
        # Build context string
        context = self._build_context(past_context, user_state)
        
        # Generate response using prompt template
        prompt = ReflectionPrompts.INITIAL_RESPONSE.format(
            context=context,
            user_message=initial_message
        )
        
        response = self.llm.invoke(prompt)
        
        # Initialize or reset conversation buffer
        self.conversation_buffer[user_id] = [
            {"role": "user", "content": initial_message, "timestamp": datetime.now()},
            {"role": "assistant", "content": response, "timestamp": datetime.now()}
        ]
        
        return response
    
    def continue_reflection(self, user_id: str, message: str) -> str:
        """
        Continue an ongoing reflection conversation
        
        Args:
            user_id: User identifier
            message: User's message
        
        Returns:
            Agent's response
        """
        conversation = self.conversation_buffer.get(user_id, [])
        
        if not conversation:
            # No active session, start new one
            return self.start_reflection_session(user_id, message)
        
        # Build conversation history (last 6 messages = 3 exchanges)
        recent_conversation = conversation[-6:]
        history = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in recent_conversation
        ])
        
        prompt = ReflectionPrompts.CONTINUE_CONVERSATION.format(
            conversation_history=history,
            user_message=message
        )
        
        response = self.llm.invoke(prompt)
        
        # Update conversation buffer
        self.conversation_buffer[user_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        })
        self.conversation_buffer[user_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })
        
        return response
    
    def end_session_and_summarize(self, user_id: str) -> ReflectionSummary:
        """
        Generate structured summary at end of conversation
        This summary is sent to Goal Planner Agent
        
        Args:
            user_id: User identifier
        
        Returns:
            ReflectionSummary object
        """
        conversation = self.conversation_buffer.get(user_id, [])
        
        if not conversation:
            raise ValueError(f"No active conversation found for user {user_id}")
        
        # Build full conversation text
        full_conversation = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in conversation
        ])
        
        prompt = ReflectionPrompts.SUMMARIZE_SESSION.format(
            full_conversation=full_conversation
        )
        
        response = self.llm.invoke(prompt)
        
        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_text = response[json_start:json_end]
                summary_data = json.loads(json_text)
            else:
                summary_data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: create basic summary
            summary_data = {
                "summary": response[:300] if len(response) > 300 else response,
                "emotional_tone": "reflective",
                "key_themes": ["self-reflection"],
                "insights": []
            }
        
        summary = ReflectionSummary(
            user_id=user_id,
            summary=summary_data.get("summary", ""),
            emotional_tone=summary_data.get("emotional_tone", "neutral"),
            key_themes=summary_data.get("key_themes", []),
            insights=summary_data.get("insights", []),
            timestamp=datetime.now()
        )
        
        # Clear conversation buffer
        del self.conversation_buffer[user_id]
        
        return summary
    
    def _build_context(self, past_context: Dict, user_state: Dict) -> str:
        """Build context string from past reflections and user state"""
        context_parts = []
        
        # Add recent reflections
        if past_context and past_context.get('documents') and past_context['documents'][0]:
            context_parts.append("Recent reflections:")
            for doc in past_context['documents'][0][:2]:
                context_parts.append(f"- {doc[:150]}...")
        
        # Add current user state
        if user_state and user_state.get('documents') and user_state['documents'][0]:
            state_text = user_state['documents'][0][0]
            context_parts.append(f"\nCurrent state: {state_text[:200]}...")
        
        return "\n".join(context_parts) if context_parts else "No prior context available."


# ==================== Agent 2: Goal Planner Agent ====================

class GoalPlannerAgent:
    """
    Converts reflection summaries into actionable goals
    - Receives summaries from Reflections Agent
    - Generates structured goals
    - Sends tasks to n8n for Google Calendar integration
    - NO direct ChromaDB access
    """
    
    def __init__(self, llm_manager: LLMManager, n8n_webhook_url: str = None):
        self.llm = llm_manager
        self.n8n_webhook_url = n8n_webhook_url
        self.pending_tasks = {}  # Temporary storage
    
    def process_reflection_summary(self, summary: ReflectionSummary) -> TaskPayload:
        """
        Convert reflection summary to structured, actionable goals
        
        Args:
            summary: ReflectionSummary from Reflections Agent
        
        Returns:
            TaskPayload with generated goals
        """
        prompt = GoalPlannerPrompts.GENERATE_GOALS.format(
            summary=summary.summary,
            emotional_tone=summary.emotional_tone,
            key_themes=', '.join(summary.key_themes),
            insights=', '.join(summary.insights) if summary.insights else 'None identified'
        )
        
        response = self.llm.invoke(prompt)
        
        # Parse goals from response
        goals = self._parse_goals(response)
        
        # Create task payload
        task_payload = TaskPayload(
            user_id=summary.user_id,
            goals=goals,
            source_summary=summary.summary,
            timestamp=datetime.now()
        )
        
        # Store temporarily
        self.pending_tasks[summary.user_id] = task_payload
        
        return task_payload
    
    def _parse_goals(self, response: str) -> List[Goal]:
        """Parse goals from LLM response"""
        try:
            # Try to extract JSON array
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_text = response[json_start:json_end]
                goals_data = json.loads(json_text)
            else:
                goals_data = json.loads(response)
            
            # Ensure it's a list
            if not isinstance(goals_data, list):
                goals_data = [goals_data]
            
            # Validate and create Goal objects
            goals = []
            for goal_dict in goals_data:
                try:
                    goal = Goal(**goal_dict)
                    goals.append(goal)
                except Exception as e:
                    print(f"Error parsing goal: {e}")
                    continue
            
            return goals if goals else self._create_fallback_goal()
            
        except Exception as e:
            print(f"Error parsing goals JSON: {e}")
            return self._create_fallback_goal()
    
    def _create_fallback_goal(self) -> List[Goal]:
        """Create a default goal if parsing fails"""
        return [Goal(
            title="Daily Reflection Check-in",
            description="Take 10 minutes to reflect on today's progress and emotions",
            priority="medium",
            duration_minutes=10,
            recurrence="daily"
        )]
    
    def send_to_n8n(self, task_payload: TaskPayload) -> Dict[str, Any]:
        """
        Send goals to n8n webhook for Google Calendar integration
        
        Args:
            task_payload: TaskPayload with goals
        
        Returns:
            Response status and data
        """
        if not self.n8n_webhook_url:
            return {
                "status": "error",
                "message": "n8n webhook URL not configured"
            }
        
        # Convert to n8n-compatible format
        n8n_payload = {
            "user_id": task_payload.user_id,
            "timestamp": task_payload.timestamp.isoformat(),
            "source": "unhabit_goal_planner",
            "tasks": []
        }
        
        for goal in task_payload.goals:
            task = {
                "summary": goal.title,
                "description": goal.description,
                "duration": goal.duration_minutes,
                "priority": goal.priority,
                "recurrence": goal.recurrence
            }
            n8n_payload["tasks"].append(task)
        
        try:
            response = requests.post(
                self.n8n_webhook_url,
                json=n8n_payload,
                timeout=15
            )
            response.raise_for_status()
            
            return {
                "status": "success",
                "data": response.json() if response.text else {},
                "tasks_sent": len(task_payload.goals)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e),
                "tasks_sent": 0
            }
    
    def get_pending_tasks(self, user_id: str) -> Optional[TaskPayload]:
        """Retrieve pending tasks for a user"""
        return self.pending_tasks.get(user_id)


# ==================== Agent 3: Support Agent ====================

class SupportAgent:
    """
    Discovers online communities and support resources
    - Uses Serper API for web search
    - Filters and ranks results
    - Records user feedback
    - NO direct ChromaDB access
    """
    
    def __init__(self, llm_manager: LLMManager, serper_tool: SerperTool):
        self.llm = llm_manager
        self.serper = serper_tool
        self.feedback_buffer = {}  # Store feedback for Assessment Agent
    
    def search_communities(
        self,
        user_id: str,
        query: str,
        addiction_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SupportRecommendation]:
        """
        Search for relevant support communities
        
        Args:
            user_id: User identifier
            query: Search query
            addiction_type: Type of addiction/habit
            filters: Additional filters
        
        Returns:
            List of SupportRecommendation objects
        """
        # Use Serper to search
        search_results = self.serper.search_communities(
            topic=query,
            addiction_type=addiction_type
        )
        
        if not search_results:
            return []
        
        # Filter and rank results
        recommendations = self._filter_and_rank(search_results, query, filters)
        
        return recommendations[:5]  # Top 5 results
    
    def _filter_and_rank(
        self,
        results: List,
        query: str,
        filters: Optional[Dict[str, Any]]
    ) -> List[SupportRecommendation]:
        """
        Filter and rank search results for relevance
        
        Args:
            results: Raw search results from Serper
            query: Original query
            filters: Additional filtering criteria
        
        Returns:
            Ranked list of recommendations
        """
        # Keywords indicating legitimate support communities
        community_keywords = [
            "support", "community", "group", "forum", "recovery",
            "addiction", "help", "peer", "online", "reddit", "discord",
            "therapy", "counseling", "anonymous", "meeting"
        ]
        
        # Keywords to avoid
        excluded_keywords = filters.get('excluded_keywords', []) if filters else []
        excluded_keywords.extend([
            "buy", "purchase", "sale", "shop", "product",
            "advertisement", "sponsored"
        ])
        
        recommendations = []
        
        for result in results:
            title = result.title.lower()
            snippet = result.snippet.lower()
            combined_text = f"{title} {snippet}"
            
            # Skip if contains excluded keywords
            if any(kw.lower() in combined_text for kw in excluded_keywords):
                continue
            
            # Calculate relevance score
            relevance_score = sum(
                1 for kw in community_keywords if kw in combined_text
            ) / len(community_keywords)
            
            # Boost score if query terms are in title
            query_terms = query.lower().split()
            if any(term in title for term in query_terms):
                relevance_score *= 1.5
            
            # Only include if minimum relevance
            if relevance_score > 0.1:
                recommendation = SupportRecommendation(
                    title=result.title,
                    description=result.snippet[:250],
                    url=result.url,
                    relevance_score=min(relevance_score, 1.0),
                    community_type=self._classify_community_type(combined_text),
                    source_position=result.position
                )
                recommendations.append(recommendation)
        
        # Sort by relevance score
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return recommendations
    
    def _classify_community_type(self, text: str) -> str:
        """Classify the type of community from text"""
        text = text.lower()
        
        if "reddit" in text:
            return "reddit"
        elif "discord" in text:
            return "discord"
        elif "forum" in text:
            return "forum"
        elif "facebook" in text:
            return "facebook_group"
        elif "meetup" in text:
            return "meetup"
        elif "12" in text and "step" in text:
            return "12_step_program"
        else:
            return "online_community"
    
    def record_feedback(self, feedback: UserFeedback) -> None:
        """
        Record user feedback on recommendations
        Stored for Assessment Agent to process
        
        Args:
            feedback: UserFeedback object
        """
        user_id = feedback.user_id
        if user_id not in self.feedback_buffer:
            self.feedback_buffer[user_id] = []
        
        self.feedback_buffer[user_id].append(feedback)
    
    def get_feedback_for_assessment(self, user_id: str) -> List[UserFeedback]:
        """Retrieve feedback for Assessment Agent"""
        feedback = self.feedback_buffer.get(user_id, [])
        # Clear after retrieval
        if user_id in self.feedback_buffer:
            del self.feedback_buffer[user_id]
        return feedback


# ==================== Agent 4: Assessment Agent ====================

class AssessmentAgent:
    """
    Central analytic and supervisory agent
    - EXCLUSIVE write access to ChromaDB
    - Collects data from all other agents
    - Generates comprehensive user state analysis
    - Updates vector database with compressed summaries
    """
    
    def __init__(
        self,
        llm_manager: LLMManager,
        db_manager: ChromaDBManager,
        vector_tool: VectorUploadTool
    ):
        self.llm = llm_manager
        self.db = db_manager
        self.vector_tool = vector_tool
        self.pending_data = {}  # Accumulate data before processing
    
    def collect_reflection_summary(self, summary: ReflectionSummary) -> None:
        """
        Collect reflection summary from Reflections Agent
        
        Args:
            summary: ReflectionSummary object
        """
        user_id = summary.user_id
        self._ensure_user_data(user_id)
        self.pending_data[user_id]["reflections"].append(summary)
    
    def collect_goal_summary(self, task_payload: TaskPayload) -> None:
        """
        Collect goal summary from Goal Planner Agent
        
        Args:
            task_payload: TaskPayload object
        """
        user_id = task_payload.user_id
        self._ensure_user_data(user_id)
        self.pending_data[user_id]["goals"].append(task_payload)
    
    def collect_support_feedback(self, feedback_list: List[UserFeedback]) -> None:
        """
        Collect support feedback from Support Agent
        
        Args:
            feedback_list: List of UserFeedback objects
        """
        if not feedback_list:
            return
        
        user_id = feedback_list[0].user_id
        self._ensure_user_data(user_id)
        self.pending_data[user_id]["feedback"].extend(feedback_list)
    
    def process_and_update_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Main processing function: Aggregate all data and update ChromaDB
        This is where all memory updates happen
        
        Args:
            user_id: User identifier
        
        Returns:
            Processing results and statistics
        """
        user_data = self.pending_data.get(user_id)
        if not user_data:
            return {"status": "no_data", "message": "No pending data to process"}
        
        results = {
            "reflections_processed": 0,
            "goals_processed": 0,
            "feedback_processed": 0,
            "state_updated": False
        }
        
        # 1. Upload reflection summaries to ChromaDB
        for reflection in user_data["reflections"]:
            upload_result = self.vector_tool.upload_reflection_summary(
                user_id=user_id,
                summary=reflection.summary,
                emotional_tone=reflection.emotional_tone,
                key_themes=reflection.key_themes,
                insights=reflection.insights
            )
            if upload_result["success"]:
                results["reflections_processed"] += 1
        
        # 2. Upload goal summaries to ChromaDB
        for task_payload in user_data["goals"]:
            goals_dict = [goal.dict() for goal in task_payload.goals]
            upload_result = self.vector_tool.upload_goal_summary(
                user_id=user_id,
                goals=goals_dict,
                source_summary=task_payload.source_summary
            )
            if upload_result["success"]:
                results["goals_processed"] += 1
        
        # 3. Upload support feedback to ChromaDB
        for feedback in user_data["feedback"]:
            upload_result = self.vector_tool.upload_interaction_feedback(
                user_id=user_id,
                interaction_type="support_recommendation",
                feedback_summary=f"{feedback.reaction}: {feedback.notes or 'No notes'}",
                metadata={
                    "recommendation_id": feedback.recommendation_id,
                    "reaction": feedback.reaction
                }
            )
            if upload_result["success"]:
                results["feedback_processed"] += 1
        
        # 4. Generate comprehensive user state analysis
        state_analysis = self._generate_state_analysis(user_data)
        
        # 5. Upload user state to ChromaDB
        aggregated_data = {
            "reflection_count": len(user_data["reflections"]),
            "goal_count": sum(len(tp.goals) for tp in user_data["goals"]),
            "interaction_count": len(user_data["feedback"]),
            "period": "recent_session"
        }
        
        state_result = self.vector_tool.upload_user_state(
            user_id=user_id,
            state_analysis=state_analysis,
            aggregated_data=aggregated_data
        )
        results["state_updated"] = state_result["success"]
        
        # 6. Clear processed data
        self._clear_user_data(user_id)
        
        return results
    
    def _generate_state_analysis(self, user_data: Dict) -> str:
        """
        Generate comprehensive state analysis from all collected data
        
        Args:
            user_data: Dictionary with reflections, goals, and feedback
        
        Returns:
            Comprehensive state analysis text
        """
        # Build text summaries
        reflections_text = "\n".join([
            f"- {r.summary} (tone: {r.emotional_tone}, themes: {', '.join(r.key_themes[:2])})"
            for r in user_data["reflections"]
        ]) or "None"
        
        goals_text = "\n".join([
            f"- {len(tp.goals)} goals created: {', '.join([g.title for g in tp.goals[:3]])}"
            for tp in user_data["goals"]
        ]) or "None"
        
        feedback_text = "\n".join([
            f"- {f.reaction} reaction to support recommendation"
            for f in user_data["feedback"]
        ]) or "None"
        
        time_period = "current session"
        
        prompt = AssessmentPrompts.ANALYZE_USER_STATE.format(
            reflections_text=reflections_text,
            goals_text=goals_text,
            feedback_text=feedback_text,
            time_period=time_period
        )
        
        analysis = self.llm.invoke(prompt)
        return analysis
    
    def _ensure_user_data(self, user_id: str) -> None:
        """Ensure user data structure exists"""
        if user_id not in self.pending_data:
            self.pending_data[user_id] = {
                "reflections": [],
                "goals": [],
                "feedback": []
            }
    
    def _clear_user_data(self, user_id: str) -> None:
        """Clear processed user data"""
        if user_id in self.pending_data:
            self.pending_data[user_id] = {
                "reflections": [],
                "goals": [],
                "feedback": []
            }
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user statistics from ChromaDB
        
        Args:
            user_id: User identifier
        
        Returns:
            Statistics dictionary
        """
        # Read from ChromaDB
        reflections = self.db.read_reflections(user_id, "all reflections", n_results=100)
        goals = self.db.read_goals_history(user_id, n_results=100)
        interactions = self.db.read_interactions(user_id, n_results=100)
        state = self.db.read_user_state(user_id)
        
        stats = {
            "user_id": user_id,
            "total_reflections": len(reflections.get("ids", [[]])[0]),
            "total_goals": len(goals.get("ids", [[]])[0]),
            "total_interactions": len(interactions.get("ids", [[]])[0]),
            "current_state": state.get("documents", [[""]])[0][0] if state.get("documents") else None,
            "timestamp": datetime.now().isoformat()
        }
        
        return stats


# ==================== Agent Initialization Factory ====================

class AgentFactory:
    """
    Factory for initializing all agents with proper dependencies
    """
    
    @staticmethod
    def create_all_agents(
        n8n_webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create and initialize all four agents
        
        Args:
            n8n_webhook_url: URL for n8n webhook (optional)
        
        Returns:
            Dictionary with all initialized agents and managers
        """
        # Initialize core managers
        llm_manager = LLMManager()
        db_manager = ChromaDBManager()
        vector_tool = VectorUploadTool(db_manager)
        serper_tool = SerperTool()
        
        # Initialize agents
        reflections_agent = ReflectionsAgent(llm_manager, db_manager)
        goal_planner_agent = GoalPlannerAgent(llm_manager, n8n_webhook_url)
        support_agent = SupportAgent(llm_manager, serper_tool)
        assessment_agent = AssessmentAgent(llm_manager, db_manager, vector_tool)
        
        return {
            "llm_manager": llm_manager,
            "db_manager": db_manager,
            "vector_tool": vector_tool,
            "serper_tool": serper_tool,
            "reflections_agent": reflections_agent,
            "goal_planner_agent": goal_planner_agent,
            "support_agent": support_agent,
            "assessment_agent": assessment_agent
        }


if __name__ == "__main__":
    # Test agent initialization
    agents = AgentFactory.create_all_agents()
    print("All agents initialized successfully!")
    print(f"Available agents: {[k for k in agents.keys() if 'agent' in k]}")