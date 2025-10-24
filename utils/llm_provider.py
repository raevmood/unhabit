# ==================== llm_provider.py ====================
"""
LLM providers for unHabit
Gemini 2.5 Flash as primary, Groq as backup
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class LLMManager:
    def __init__(self):
        """Initialize both LLM providers"""
        gemini_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not gemini_key:
            raise ValueError("GOOGLE_API_KEY or GOOGLE_API_KEY environment variable not set")
        
        self.primary_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_key,
            temperature=0.7,
            max_tokens=2048
        )
        
        # Backup: Groq
        groq_key = os.getenv('GROQ_API_KEY')
        if not groq_key:
            print("Warning: GROQ_API_KEY not set, backup unavailable")
            self.backup_llm = None
        else:
            self.backup_llm = ChatGroq(
                model="mixtral-8x7b-32768",
                groq_api_key=groq_key,
                temperature=0.7,
                max_tokens=2048
            )
    
    def get_response(self, messages: List[BaseMessage]) -> str:
        """Get response with fallback logic"""
        try:
            response = self.primary_llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"Gemini error: {e}")
            
            if self.backup_llm:
                try:
                    response = self.backup_llm.invoke(messages)
                    return response.content
                except Exception as e:
                    print(f"Groq error: {e}")
            
            return "I'm having trouble processing your request. Please try again."
    
    def invoke(self, prompt: str) -> str:
        """Simple invoke interface"""
        from langchain_core.messages import HumanMessage
        return self.get_response([HumanMessage(content=prompt)])
    
    def stream_response(self, messages: List[BaseMessage]):
        """Stream response with fallback"""
        try:
            return self.primary_llm.stream(messages)
        except Exception as e:
            print(f"Gemini streaming error: {e}")
            if self.backup_llm:
                return self.backup_llm.stream(messages)
            return iter(["Error: Unable to stream response"])

if __name__ == "__main__":
    # Test LLM Manager
    from langchain_core.messages import HumanMessage
    
    llm_manager = LLMManager()
    test_messages = [HumanMessage(content="Hello, how are you?")]
    response = llm_manager.get_response(test_messages)
    print(f"LLM Response: {response}")