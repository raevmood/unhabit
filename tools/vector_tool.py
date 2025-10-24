# ==================== vector_tool.py ====================
"""
Vector database upload tool for Assessment Agent
Provides structured interface for memory operations
"""

from typing import Dict, Any, List
from datetime import datetime
import uuid
import json

class VectorUploadTool:
    """
    Tool for Assessment Agent to upload data to vector database
    Encapsulates all write operations with proper validation
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def upload_reflection_summary(
        self,
        user_id: str,
        summary: str,
        emotional_tone: str,
        key_themes: List[str],
        insights: List[str],
        session_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Upload a reflection summary to vector database
        
        Returns:
            Dict with status and document_id
        """
        document_id = f"{user_id}_reflection_{uuid.uuid4()}"
        
        metadata = {
            "emotional_tone": emotional_tone,
            "key_themes": json.dumps(key_themes),
            "insights": json.dumps(insights),
            "type": "reflection_summary"
        }
        
        if session_metadata:
            metadata.update(session_metadata)
        
        success = self.db.write_reflection(
            user_id=user_id,
            summary=summary,
            metadata=metadata,
            document_id=document_id
        )
        
        return {
            "success": success,
            "document_id": document_id if success else None,
            "timestamp": datetime.now().isoformat()
        }
    
    def upload_goal_summary(
        self,
        user_id: str,
        goals: List[Dict[str, Any]],
        source_summary: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Upload goal planning summary to vector database
        """
        document_id = f"{user_id}_goals_{uuid.uuid4()}"
        
        # Create text summary of goals
        goal_text = f"Goals created from reflection: {source_summary}\n\nGoals:\n"
        for i, goal in enumerate(goals, 1):
            goal_text += f"{i}. {goal.get('title', 'Untitled')}: {goal.get('description', '')}\n"
        
        goal_metadata = {
            "goal_count": len(goals),
            "goals_json": json.dumps(goals),
            "type": "goal_summary"
        }
        
        if metadata:
            goal_metadata.update(metadata)
        
        success = self.db.write_goal(
            user_id=user_id,
            goal_summary=goal_text,
            metadata=goal_metadata,
            document_id=document_id
        )
        
        return {
            "success": success,
            "document_id": document_id if success else None,
            "goal_count": len(goals),
            "timestamp": datetime.now().isoformat()
        }
    
    def upload_user_state(
        self,
        user_id: str,
        state_analysis: str,
        aggregated_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upload comprehensive user state analysis
        """
        metadata = {
            "reflection_count": aggregated_data.get("reflection_count", 0),
            "goal_count": aggregated_data.get("goal_count", 0),
            "interaction_count": aggregated_data.get("interaction_count", 0),
            "analysis_period": aggregated_data.get("period", "unknown"),
            "type": "user_state"
        }
        
        success = self.db.write_user_state(
            user_id=user_id,
            state_summary=state_analysis,
            metadata=metadata
        )
        
        return {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
    
    def upload_interaction_feedback(
        self,
        user_id: str,
        interaction_type: str,
        feedback_summary: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Upload support interaction feedback
        """
        document_id = f"{user_id}_interaction_{uuid.uuid4()}"
        
        interaction_metadata = {
            "interaction_type": interaction_type,
            "type": "support_interaction"
        }
        
        if metadata:
            interaction_metadata.update(metadata)
        
        success = self.db.write_interaction(
            user_id=user_id,
            interaction_summary=feedback_summary,
            metadata=interaction_metadata,
            document_id=document_id
        )
        
        return {
            "success": success,
            "document_id": document_id if success else None,
            "timestamp": datetime.now().isoformat()
        }
    
    def batch_upload(
        self,
        user_id: str,
        reflections: List[Dict] = None,
        goals: List[Dict] = None,
        interactions: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Batch upload multiple items at once
        More efficient for Assessment Agent periodic updates
        """
        results = {
            "reflections": [],
            "goals": [],
            "interactions": [],
            "total_success": 0,
            "total_failed": 0
        }
        
        if reflections:
            for ref in reflections:
                result = self.upload_reflection_summary(user_id=user_id, **ref)
                results["reflections"].append(result)
                if result["success"]:
                    results["total_success"] += 1
                else:
                    results["total_failed"] += 1
        
        if goals:
            for goal in goals:
                result = self.upload_goal_summary(user_id=user_id, **goal)
                results["goals"].append(result)
                if result["success"]:
                    results["total_success"] += 1
                else:
                    results["total_failed"] += 1
        
        if interactions:
            for interaction in interactions:
                result = self.upload_interaction_feedback(user_id=user_id, **interaction)
                results["interactions"].append(result)
                if result["success"]:
                    results["total_success"] += 1
                else:
                    results["total_failed"] += 1
        
        return results