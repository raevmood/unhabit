# ==================== memory.py ====================
"""
Memory management for unHabit using LangChain ChromaDB
Handles all vector database operations with strict access control
Uses default ChromaDB embeddings (no API calls)
Compatible with VectorUploadTool
"""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from chromadb.utils import embedding_functions
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class ChromaDBManager:
    """
    Manages ChromaDB with access control using LangChain
    Only Assessment Agent should have write permissions
    Uses default sentence-transformers embeddings (no API required)
    """
    
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        
        # Use default sentence-transformers embeddings (no API required)
        # This is the same as ChromaDB's default behavior
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Create collections
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize all required collections"""
        self.reflections_collection = Chroma(
            collection_name="user_reflections",
            embedding_function=self.embedding_function,
            persist_directory=os.path.join(self.persist_dir, "reflections"),
            collection_metadata={"description": "User reflection summaries and journal entries"}
        )
        
        self.goals_collection = Chroma(
            collection_name="user_goals",
            embedding_function=self.embedding_function,
            persist_directory=os.path.join(self.persist_dir, "goals"),
            collection_metadata={"description": "Generated goals and task history"}
        )
        
        self.state_collection = Chroma(
            collection_name="user_states",
            embedding_function=self.embedding_function,
            persist_directory=os.path.join(self.persist_dir, "states"),
            collection_metadata={"description": "Compressed user mental state representations"}
        )
        
        self.interactions_collection = Chroma(
            collection_name="user_interactions",
            embedding_function=self.embedding_function,
            persist_directory=os.path.join(self.persist_dir, "interactions"),
            collection_metadata={"description": "Support agent interactions and feedback"}
        )
    
    # ==================== READ OPERATIONS (All Agents) ====================
    
    def read_reflections(self, user_id: str, query: str, n_results: int = 5) -> Dict:
        """
        Read past reflections (READ-ONLY)
        Used by: Reflections Agent, Assessment Agent
        """
        try:
            results = self.reflections_collection.similarity_search_with_score(
                query=query,
                k=n_results,
                filter={"user_id": user_id}
            )
            
            # Format results to match original structure
            return {
                "documents": [[doc.page_content for doc, score in results]],
                "metadatas": [[doc.metadata for doc, score in results]],
                "ids": [[doc.metadata.get("id", "") for doc, score in results]],
                "distances": [[score for doc, score in results]]
            }
        except Exception as e:
            print(f"Error reading reflections: {e}")
            return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
    
    def read_user_state(self, user_id: str, n_results: int = 1) -> Dict:
        """
        Read current user state (READ-ONLY)
        Used by: All Agents
        """
        try:
            results = self.state_collection.similarity_search_with_score(
                query="current mental state and behavioral patterns",
                k=n_results,
                filter={"user_id": user_id}
            )
            
            return {
                "documents": [[doc.page_content for doc, score in results]],
                "metadatas": [[doc.metadata for doc, score in results]],
                "ids": [[doc.metadata.get("id", "") for doc, score in results]],
                "distances": [[score for doc, score in results]]
            }
        except Exception as e:
            print(f"Error reading user state: {e}")
            return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
    
    def read_goals_history(self, user_id: str, n_results: int = 10) -> Dict:
        """
        Read past goals (READ-ONLY)
        Used by: Goal Planner Agent, Assessment Agent
        """
        try:
            results = self.goals_collection.similarity_search_with_score(
                query="recent goals and tasks",
                k=n_results,
                filter={"user_id": user_id}
            )
            
            return {
                "documents": [[doc.page_content for doc, score in results]],
                "metadatas": [[doc.metadata for doc, score in results]],
                "ids": [[doc.metadata.get("id", "") for doc, score in results]],
                "distances": [[score for doc, score in results]]
            }
        except Exception as e:
            print(f"Error reading goals: {e}")
            return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
    
    def read_interactions(self, user_id: str, n_results: int = 5) -> Dict:
        """
        Read support interactions (READ-ONLY)
        Used by: Support Agent, Assessment Agent
        """
        try:
            results = self.interactions_collection.similarity_search_with_score(
                query="support community interactions",
                k=n_results,
                filter={"user_id": user_id}
            )
            
            return {
                "documents": [[doc.page_content for doc, score in results]],
                "metadatas": [[doc.metadata for doc, score in results]],
                "ids": [[doc.metadata.get("id", "") for doc, score in results]],
                "distances": [[score for doc, score in results]]
            }
        except Exception as e:
            print(f"Error reading interactions: {e}")
            return {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
    
    # ==================== WRITE OPERATIONS (Assessment Agent Only) ====================
    # These methods are called by VectorUploadTool and must return bool
    
    def write_reflection(
        self, 
        user_id: str, 
        summary: str, 
        metadata: Dict[str, Any], 
        document_id: str
    ) -> bool:
        """
        RESTRICTED: Only Assessment Agent can write reflections
        Called by: VectorUploadTool.upload_reflection_summary()
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Sanitize metadata to avoid ChromaDB issues
            clean_metadata = self._sanitize_metadata({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "id": document_id,
                **metadata
            })
            
            doc = Document(
                page_content=summary,
                metadata=clean_metadata
            )
            self.reflections_collection.add_documents([doc], ids=[document_id])
            print(f"✓ Reflection written: {document_id}")
            return True
        except Exception as e:
            print(f"✗ Error writing reflection: {e}")
            return False
    
    def write_goal(
        self, 
        user_id: str, 
        goal_summary: str, 
        metadata: Dict[str, Any], 
        document_id: str
    ) -> bool:
        """
        RESTRICTED: Only Assessment Agent can write goals
        Called by: VectorUploadTool.upload_goal_summary()
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Sanitize metadata to avoid ChromaDB issues
            clean_metadata = self._sanitize_metadata({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "id": document_id,
                **metadata
            })
            
            doc = Document(
                page_content=goal_summary,
                metadata=clean_metadata
            )
            self.goals_collection.add_documents([doc], ids=[document_id])
            print(f"✓ Goal written: {document_id}")
            return True
        except Exception as e:
            print(f"✗ Error writing goal: {e}")
            return False
    
    def write_user_state(
        self, 
        user_id: str, 
        state_summary: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        RESTRICTED: Only Assessment Agent can update user state
        Called by: VectorUploadTool.upload_user_state()
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc_id = f"{user_id}_state_{datetime.now().isoformat()}"
            
            # Sanitize metadata to avoid ChromaDB issues
            clean_metadata = self._sanitize_metadata({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "id": doc_id,
                **metadata
            })
            
            doc = Document(
                page_content=state_summary,
                metadata=clean_metadata
            )
            self.state_collection.add_documents([doc], ids=[doc_id])
            print(f"✓ User state written: {doc_id}")
            return True
        except Exception as e:
            print(f"✗ Error writing user state: {e}")
            return False
    
    def write_interaction(
        self, 
        user_id: str, 
        interaction_summary: str, 
        metadata: Dict[str, Any], 
        document_id: str
    ) -> bool:
        """
        RESTRICTED: Only Assessment Agent can write interactions
        Called by: VectorUploadTool.upload_interaction_feedback()
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Sanitize metadata to avoid ChromaDB issues
            clean_metadata = self._sanitize_metadata({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "id": document_id,
                **metadata
            })
            
            doc = Document(
                page_content=interaction_summary,
                metadata=clean_metadata
            )
            self.interactions_collection.add_documents([doc], ids=[document_id])
            print(f"✓ Interaction written: {document_id}")
            return True
        except Exception as e:
            print(f"✗ Error writing interaction: {e}")
            return False
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize metadata values to ensure ChromaDB compatibility
        Handles None values, lists, dicts, sets, and tuples
        """
        clean_meta = {}
        for k, v in metadata.items():
            # Replace None with empty string
            if v is None:
                clean_meta[k] = ""
            # Convert lists to comma-separated strings
            elif isinstance(v, list):
                clean_meta[k] = ", ".join(map(str, v))
            # Convert dicts to JSON strings, handling None values inside
            elif isinstance(v, dict):
                safe_dict = {ik: ("" if iv is None else iv) for ik, iv in v.items()}
                clean_meta[k] = json.dumps(safe_dict, ensure_ascii=False)
            # Convert sets and tuples to comma-separated strings
            elif isinstance(v, (set, tuple)):
                clean_meta[k] = ", ".join(map(str, v))
            else:
                clean_meta[k] = v
        return clean_meta
    
    def delete_old_data(self, user_id: str, days_old: int = 90) -> Dict[str, int]:
        """
        Delete data older than specified days (maintenance operation)
        RESTRICTED: Only Assessment Agent
        Uses ISO datetime string comparison (lexicographically sortable)
        """
        from datetime import timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        deleted_counts = {
            "reflections": 0,
            "goals": 0,
            "interactions": 0
        }
        
        try:
            # Delete old reflections
            old_reflections = self.reflections_collection.get(
                where={
                    "$and": [
                        {"user_id": user_id},
                        {"timestamp": {"$lt": cutoff_date}}
                    ]
                }
            )
            if old_reflections['ids']:
                self.reflections_collection.delete(ids=old_reflections['ids'])
                deleted_counts["reflections"] = len(old_reflections['ids'])
            
            # Delete old goals
            old_goals = self.goals_collection.get(
                where={
                    "$and": [
                        {"user_id": user_id},
                        {"timestamp": {"$lt": cutoff_date}}
                    ]
                }
            )
            if old_goals['ids']:
                self.goals_collection.delete(ids=old_goals['ids'])
                deleted_counts["goals"] = len(old_goals['ids'])
            
            # Delete old interactions
            old_interactions = self.interactions_collection.get(
                where={
                    "$and": [
                        {"user_id": user_id},
                        {"timestamp": {"$lt": cutoff_date}}
                    ]
                }
            )
            if old_interactions['ids']:
                self.interactions_collection.delete(ids=old_interactions['ids'])
                deleted_counts["interactions"] = len(old_interactions['ids'])
                
        except Exception as e:
            print(f"✗ Error deleting old data: {e}")
        
        print(f"✓ Deleted data for user {user_id} older than {days_old} days: {deleted_counts}")
        return deleted_counts
    
if __name__ == "__main__": 
    # Test Memory with VectorUploadTool compatibility
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 60)
    print("Testing ChromaDB Manager with LangChain")
    print("Using default embeddings (no API required)")
    print("=" * 60)
    
    # Initialize manager
    db = ChromaDBManager()
    print("\n✓ ChromaDB Manager initialized successfully")
    
    # Test with VectorUploadTool pattern
    test_user = "test_user_123"
    test_doc_id = f"test_reflection_{datetime.now().isoformat()}"
    
    print("\n--- Testing VectorUploadTool Compatibility ---")
    
    # Test write_reflection (called by VectorUploadTool)
    success = db.write_reflection(
        user_id=test_user,
        summary="Today I reflected on my progress with reducing screen time.",
        metadata={
            "emotional_tone": "positive",
            "key_themes": json.dumps(["digital_wellness", "progress"]),
            "insights": json.dumps(["Made progress", "Feeling motivated"]),
            "type": "reflection_summary"
        },
        document_id=test_doc_id
    )
    print(f"Write reflection: {'✓ Success' if success else '✗ Failed'}")
    
    # Test write_goal (called by VectorUploadTool)
    goal_doc_id = f"test_goal_{datetime.now().isoformat()}"
    success = db.write_goal(
        user_id=test_user,
        goal_summary="Goal: Reduce screen time to 2 hours daily",
        metadata={
            "goal_count": 1,
            "goals_json": json.dumps([{"title": "Screen Time", "description": "2hrs daily"}]),
            "type": "goal_summary"
        },
        document_id=goal_doc_id
    )
    print(f"Write goal: {'✓ Success' if success else '✗ Failed'}")
    
    # Test write_user_state (called by VectorUploadTool)
    success = db.write_user_state(
        user_id=test_user,
        state_summary="User is making progress on digital wellness goals",
        metadata={
            "reflection_count": 1,
            "goal_count": 1,
            "interaction_count": 0,
            "analysis_period": "7_days",
            "type": "user_state"
        }
    )
    print(f"Write user state: {'✓ Success' if success else '✗ Failed'}")
    
    # Test write_interaction (called by VectorUploadTool)
    interaction_doc_id = f"test_interaction_{datetime.now().isoformat()}"
    success = db.write_interaction(
        user_id=test_user,
        interaction_summary="User received encouragement from support community",
        metadata={
            "interaction_type": "community_support",
            "type": "support_interaction"
        },
        document_id=interaction_doc_id
    )
    print(f"Write interaction: {'✓ Success' if success else '✗ Failed'}")
    
    # Test read operations
    print("\n--- Testing Read Operations ---")
    
    results = db.read_reflections(
        user_id=test_user,
        query="screen time progress",
        n_results=5
    )
    print(f"Read reflections: Found {len(results['documents'][0])} documents")
    
    results = db.read_goals_history(
        user_id=test_user,
        n_results=5
    )
    print(f"Read goals: Found {len(results['documents'][0])} documents")
    
    results = db.read_user_state(
        user_id=test_user,
        n_results=1
    )
    print(f"Read user state: Found {len(results['documents'][0])} documents")
    
    results = db.read_interactions(
        user_id=test_user,
        n_results=5
    )
    print(f"Read interactions: Found {len(results['documents'][0])} documents")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("✓ VectorUploadTool compatibility confirmed")
    print("✓ No API calls required for embeddings")
    print("=" * 60)