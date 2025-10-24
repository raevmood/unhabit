# ==================== main.py ====================
"""
FastAPI application for unHabit
API endpoints for all agent interactions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Import our modules
from utils.agents import (
    AgentFactory,
    ReflectionSummary,
    Goal,
    TaskPayload,
    SupportRecommendation,
    UserFeedback
)

load_dotenv()

# ==================== Request/Response Models ====================

class ReflectionInput(BaseModel):
    """Input for reflection conversation"""
    user_id: str
    content: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class ReflectionResponse(BaseModel):
    """Response from reflection agent"""
    response: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SessionEndResponse(BaseModel):
    """Response when ending reflection session"""
    summary: Dict[str, Any]
    goals: List[Dict[str, Any]]
    calendar_sync: Dict[str, Any]
    assessment_results: Dict[str, Any]

class SupportSearchRequest(BaseModel):
    """Request to search for support communities"""
    user_id: str
    query: str
    addiction_type: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class SupportSearchResponse(BaseModel):
    """Response with support recommendations"""
    recommendations: List[Dict[str, Any]]
    count: int
    timestamp: datetime = Field(default_factory=datetime.now)

class FeedbackSubmission(BaseModel):
    """Submit user feedback on support recommendation"""
    user_id: str
    recommendation_id: str
    reaction: str  # accepted, rejected, interested
    notes: Optional[str] = None

class UserStatsResponse(BaseModel):
    """User statistics response"""
    user_id: str
    total_reflections: int
    total_goals: int
    total_interactions: int
    current_state: Optional[str]
    timestamp: str

# ==================== Initialize FastAPI App ====================

app = FastAPI(
    title="unHabit API",
    description="AI-driven behavioral recovery platform",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Initialize Agents ====================

# Get n8n webhook URL from environment
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# Initialize all agents
agents = AgentFactory.create_all_agents(n8n_webhook_url=N8N_WEBHOOK_URL)

reflections_agent = agents["reflections_agent"]
goal_planner_agent = agents["goal_planner_agent"]
support_agent = agents["support_agent"]
assessment_agent = agents["assessment_agent"]


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "unHabit API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/api/health",
            "reflection": "/api/reflection/*",
            "support": "/api/support/*",
            "stats": "/api/stats/{user_id}"
        }
    }

@app.get("/api/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "reflections": "operational",
            "goal_planner": "operational",
            "support": "operational",
            "assessment": "operational"
        },
        "n8n_configured": N8N_WEBHOOK_URL is not None
    }


# ==================== Reflection Endpoints ====================

@app.post("/api/reflection/start", response_model=ReflectionResponse)
async def start_reflection(input_data: ReflectionInput):
    """
    Start a new reflection session
    
    This initiates a conversation with the Reflections Agent,
    which retrieves past context and provides an empathetic response.
    """
    try:
        response = reflections_agent.start_reflection_session(
            user_id=input_data.user_id,
            initial_message=input_data.content
        )
        
        return ReflectionResponse(
            response=response,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error continuing reflection: {str(e)}"
        )


@app.post("/api/reflection/end", response_model=SessionEndResponse)
async def end_reflection(
    user_id: str,
    background_tasks: BackgroundTasks
):
    """
    End reflection session and trigger full processing pipeline
    
    This endpoint:
    1. Generates reflection summary
    2. Creates goals from the summary
    3. Sends goals to n8n for calendar integration
    4. Collects all data in Assessment Agent
    5. Updates vector database with new insights
    """
    try:
        # Step 1: Generate reflection summary
        summary = reflections_agent.end_session_and_summarize(user_id)
        
        # Step 2: Send summary to Assessment Agent
        assessment_agent.collect_reflection_summary(summary)
        
        # Step 3: Generate goals from summary
        task_payload = goal_planner_agent.process_reflection_summary(summary)
        
        # Step 4: Send goals to n8n for calendar sync
        n8n_result = goal_planner_agent.send_to_n8n(task_payload)
        
        # Step 5: Collect goals in Assessment Agent
        assessment_agent.collect_goal_summary(task_payload)
        
        # Step 6: Collect any pending support feedback
        feedback_list = support_agent.get_feedback_for_assessment(user_id)
        if feedback_list:
            assessment_agent.collect_support_feedback(feedback_list)
        
        # Step 7: Process all data and update memory (in background)
        # This prevents blocking the response
        background_tasks.add_task(
            assessment_agent.process_and_update_memory,
            user_id
        )
        
        # Return immediate response
        return SessionEndResponse(
            summary=summary.dict(),
            goals=[goal.dict() for goal in task_payload.goals],
            calendar_sync=n8n_result,
            assessment_results={"status": "processing_in_background"}
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid session: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ending reflection: {str(e)}"
        )


# ==================== Support Endpoints ====================

@app.post("/api/support/search", response_model=SupportSearchResponse)
async def search_support(request: SupportSearchRequest):
    """
    Search for support communities and resources
    
    Uses Serper API to find relevant online communities,
    filters results, and returns ranked recommendations.
    """
    try:
        recommendations = support_agent.search_communities(
            user_id=request.user_id,
            query=request.query,
            addiction_type=request.addiction_type,
            filters=request.filters
        )
        
        return SupportSearchResponse(
            recommendations=[rec.dict() for rec in recommendations],
            count=len(recommendations),
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching communities: {str(e)}"
        )


@app.post("/api/support/feedback")
async def submit_feedback(feedback: FeedbackSubmission):
    """
    Submit user feedback on support recommendations
    
    Records user engagement with support resources.
    This data is collected by Assessment Agent for learning.
    """
    try:
        user_feedback = UserFeedback(
            user_id=feedback.user_id,
            recommendation_id=feedback.recommendation_id,
            reaction=feedback.reaction,
            notes=feedback.notes,
            timestamp=datetime.now()
        )
        
        support_agent.record_feedback(user_feedback)
        
        return {
            "status": "success",
            "message": "Feedback recorded",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


# ==================== Assessment & Stats Endpoints ====================

@app.get("/api/stats/{user_id}", response_model=UserStatsResponse)
async def get_user_stats(user_id: str):
    """
    Get comprehensive user statistics
    
    Retrieves aggregated data about user's journey:
    - Total reflections
    - Total goals created
    - Support interactions
    - Current mental state summary
    """
    try:
        stats = assessment_agent.get_user_statistics(user_id)
        
        return UserStatsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving stats: {str(e)}"
        )


@app.post("/api/assessment/process/{user_id}")
async def trigger_assessment(user_id: str):
    """
    Manually trigger assessment and memory update
    
    Usually this happens automatically after reflection sessions,
    but this endpoint allows manual triggering for maintenance.
    """
    try:
        results = assessment_agent.process_and_update_memory(user_id)
        
        return {
            "status": "success",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing assessment: {str(e)}"
        )


# ==================== Goal Management Endpoints ====================

@app.get("/api/goals/pending/{user_id}")
async def get_pending_goals(user_id: str):
    """
    Get pending goals for a user
    
    Returns goals that have been created but may not yet
    be synced to calendar.
    """
    try:
        task_payload = goal_planner_agent.get_pending_tasks(user_id)
        
        if not task_payload:
            return {
                "status": "no_pending_goals",
                "goals": [],
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "goals": [goal.dict() for goal in task_payload.goals],
            "source_summary": task_payload.source_summary,
            "timestamp": task_payload.timestamp.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving pending goals: {str(e)}"
        )


@app.post("/api/goals/resync/{user_id}")
async def resync_goals(user_id: str):
    """
    Resync pending goals to n8n/Calendar
    
    Useful if initial sync failed or needs to be retried.
    """
    try:
        task_payload = goal_planner_agent.get_pending_tasks(user_id)
        
        if not task_payload:
            raise HTTPException(
                status_code=404,
                detail="No pending goals found for this user"
            )
        
        result = goal_planner_agent.send_to_n8n(task_payload)
        
        return {
            "status": "success",
            "sync_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resyncing goals: {str(e)}"
        )


# ==================== Admin/Debug Endpoints ====================

@app.get("/api/debug/agents")
async def debug_agents():
    """
    Debug endpoint to check agent status
    (Remove in production)
    """
    return {
        "reflections_agent": {
            "active_sessions": len(reflections_agent.conversation_buffer)
        },
        "goal_planner_agent": {
            "pending_tasks": len(goal_planner_agent.pending_tasks)
        },
        "support_agent": {
            "pending_feedback": len(support_agent.feedback_buffer)
        },
        "assessment_agent": {
            "pending_users": len(assessment_agent.pending_data)
        }
    }


@app.delete("/api/debug/clear/{user_id}")
async def clear_user_session(user_id: str):
    """
    Clear user session data
    (Use with caution - for debugging only)
    """
    try:
        # Clear conversation buffer
        if user_id in reflections_agent.conversation_buffer:
            del reflections_agent.conversation_buffer[user_id]
        
        # Clear pending tasks
        if user_id in goal_planner_agent.pending_tasks:
            del goal_planner_agent.pending_tasks[user_id]
        
        # Clear feedback
        if user_id in support_agent.feedback_buffer:
            del support_agent.feedback_buffer[user_id]
        
        # Clear pending assessment data
        if user_id in assessment_agent.pending_data:
            del assessment_agent.pending_data[user_id]
        
        return {
            "status": "cleared",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )


# ==================== Error Handlers ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return {
        "error": "Not Found",
        "message": "The requested endpoint does not exist",
        "path": str(request.url)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("=" * 50)
    print("🚀 unHabit API Starting...")
    print("=" * 50)
    print(f"✓ Reflections Agent: Ready")
    print(f"✓ Goal Planner Agent: Ready")
    print(f"✓ Support Agent: Ready")
    print(f"✓ Assessment Agent: Ready")
    print(f"✓ Vector Database: Connected")
    print(f"✓ n8n Webhook: {'Configured' if N8N_WEBHOOK_URL else 'Not configured'}")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("=" * 50)
    print("🛑 unHabit API Shutting Down...")
    print("=" * 50)


# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\nStarting unHabit API on {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Alternative docs: http://{host}:{port}/redoc\n")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Set to False in production
        log_level="info"
    )


# ==================== Support Endpoints ====================

@app.post("/api/support/search", response_model=SupportSearchResponse)
async def search_support(request: SupportSearchRequest):
    """
    Search for support communities and resources
    
    Uses Serper API to find relevant online communities,
    filters results, and returns ranked recommendations.
    """
    try:
        recommendations = support_agent.search_communities(
            user_id=request.user_id,
            query=request.query,
            addiction_type=request.addiction_type,
            filters=request.filters
        )
        
        return SupportSearchResponse(
            recommendations=[rec.dict() for rec in recommendations],
            count=len(recommendations),
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching communities: {str(e)}"
        )


@app.post("/api/support/feedback")
async def submit_feedback(feedback: FeedbackSubmission):
    """
    Submit user feedback on support recommendations
    
    Records user engagement with support resources.
    This data is collected by Assessment Agent for learning.
    """
    try:
        user_feedback = UserFeedback(
            user_id=feedback.user_id,
            recommendation_id=feedback.recommendation_id,
            reaction=feedback.reaction,
            notes=feedback.notes,
            timestamp=datetime.now()
        )
        
        support_agent.record_feedback(user_feedback)
        
        return {
            "status": "success",
            "message": "Feedback recorded",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


# ==================== Assessment & Stats Endpoints ====================

@app.get("/api/stats/{user_id}", response_model=UserStatsResponse)
async def get_user_stats(user_id: str):
    """
    Get comprehensive user statistics
    
    Retrieves aggregated data about user's journey:
    - Total reflections
    - Total goals created
    - Support interactions
    - Current mental state summary
    """
    try:
        stats = assessment_agent.get_user_statistics(user_id)
        
        return UserStatsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving stats: {str(e)}"
        )


@app.post("/api/assessment/process/{user_id}")
async def trigger_assessment(user_id: str):
    """
    Manually trigger assessment and memory update
    
    Usually this happens automatically after reflection sessions,
    but this endpoint allows manual triggering for maintenance.
    """
    try:
        results = assessment_agent.process_and_update_memory(user_id)
        
        return {
            "status": "success",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing assessment: {str(e)}"
        )


# ==================== Goal Management Endpoints ====================

@app.get("/api/goals/pending/{user_id}")
async def get_pending_goals(user_id: str):
    """
    Get pending goals for a user
    
    Returns goals that have been created but may not yet
    be synced to calendar.
    """
    try:
        task_payload = goal_planner_agent.get_pending_tasks(user_id)
        
        if not task_payload:
            return {
                "status": "no_pending_goals",
                "goals": [],
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "goals": [goal.dict() for goal in task_payload.goals],
            "source_summary": task_payload.source_summary,
            "timestamp": task_payload.timestamp.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving pending goals: {str(e)}"
        )


@app.post("/api/goals/resync/{user_id}")
async def resync_goals(user_id: str):
    """
    Resync pending goals to n8n/Calendar
    
    Useful if initial sync failed or needs to be retried.
    """
    try:
        task_payload = goal_planner_agent.get_pending_tasks(user_id)
        
        if not task_payload:
            raise HTTPException(
                status_code=404,
                detail="No pending goals found for this user"
            )
        
        result = goal_planner_agent.send_to_n8n(task_payload)
        
        return {
            "status": "success",
            "sync_result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resyncing goals: {str(e)}"
        )


# ==================== Admin/Debug Endpoints ====================

@app.get("/api/debug/agents")
async def debug_agents():
    """
    Debug endpoint to check agent status
    (Remove in production)
    """
    return {
        "reflections_agent": {
            "active_sessions": len(reflections_agent.conversation_buffer)
        },
        "goal_planner_agent": {
            "pending_tasks": len(goal_planner_agent.pending_tasks)
        },
        "support_agent": {
            "pending_feedback": len(support_agent.feedback_buffer)
        },
        "assessment_agent": {
            "pending_users": len(assessment_agent.pending_data)
        }
    }


@app.delete("/api/debug/clear/{user_id}")
async def clear_user_session(user_id: str):
    """
    Clear user session data
    (Use with caution - for debugging only)
    """
    try:
        # Clear conversation buffer
        if user_id in reflections_agent.conversation_buffer:
            del reflections_agent.conversation_buffer[user_id]
        
        # Clear pending tasks
        if user_id in goal_planner_agent.pending_tasks:
            del goal_planner_agent.pending_tasks[user_id]
        
        # Clear feedback
        if user_id in support_agent.feedback_buffer:
            del support_agent.feedback_buffer[user_id]
        
        # Clear pending assessment data
        if user_id in assessment_agent.pending_data:
            del assessment_agent.pending_data[user_id]
        
        return {
            "status": "cleared",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )


# ==================== Error Handlers ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return {
        "error": "Not Found",
        "message": "The requested endpoint does not exist",
        "path": str(request.url)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("=" * 50)
    print("🚀 unHabit API Starting...")
    print("=" * 50)
    print(f"✓ Reflections Agent: Ready")
    print(f"✓ Goal Planner Agent: Ready")
    print(f"✓ Support Agent: Ready")
    print(f"✓ Assessment Agent: Ready")
    print(f"✓ Vector Database: Connected")
    print(f"✓ n8n Webhook: {'Configured' if N8N_WEBHOOK_URL else 'Not configured'}")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("=" * 50)
    print("🛑 unHabit API Shutting Down...")
    print("=" * 50)


# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\nStarting unHabit API on {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Alternative docs: http://{host}:{port}/redoc\n")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Set to False in production
        log_level="info"
    )
    Exception(
            status_code=500,
            detail=f"Error starting reflection: {str(Exception)}"
        )


@app.post("/api/reflection/continue", response_model=ReflectionResponse)
async def continue_reflection(input_data: ReflectionInput):
    """
    Continue an ongoing reflection session
    
    Maintains conversation context and provides supportive responses.
    """
    try:
        response = reflections_agent.continue_reflection(
            user_id=input_data.user_id,
            message=input_data.content
        )
        
        return ReflectionResponse(
            response=response,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error continuing reflection: {str(e)}"
        )
  
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

