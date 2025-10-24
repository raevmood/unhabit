# ==================== serper_tool.py ====================
"""
Serper API integration for Support Agent
Web search tool for discovering support communities
"""

import requests
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass
class SearchResult:
    """Structured search result"""
    title: str
    snippet: str
    url: str
    position: int
    raw_data: Dict[str, Any]

class SerperTool:
    """
    Serper API wrapper for web search
    Used by Support Agent to find communities
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SERPER_API_KEY')
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found")
        
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search",
        **kwargs
    ) -> List[SearchResult]:
        """
        Perform web search
        
        Args:
            query: Search query
            num_results: Number of results to return
            search_type: "search", "news", "places", "images"
            **kwargs: Additional Serper API parameters
        
        Returns:
            List of SearchResult objects
        """
        payload = {
            "q": query,
            "num": num_results,
            **kwargs
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return self._parse_results(data)
            
        except requests.exceptions.RequestException as e:
            print(f"Serper API error: {e}")
            return []
    
    def search_communities(
        self,
        topic: str,
        addiction_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Specialized search for support communities
        
        Args:
            topic: Main search topic (e.g., "social media addiction")
            addiction_type: Type of addiction/habit
            location: Geographic location for local groups
        """
        # Build enhanced query
        query_parts = [topic]
        
        if addiction_type:
            query_parts.append(addiction_type)
        
        query_parts.extend([
            "support group",
            "online community",
            "recovery",
            "forum"
        ])
        
        if location:
            query_parts.append(location)
        
        query = " ".join(query_parts)
        
        return self.search(query, num_results=15)
    
    def _parse_results(self, data: Dict) -> List[SearchResult]:
        """Parse Serper API response"""
        results = []
        organic = data.get("organic", [])
        
        for i, item in enumerate(organic):
            result = SearchResult(
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("link", ""),
                position=i + 1,
                raw_data=item
            )
            results.append(result)
        
        return results
    
    def filter_by_keywords(
        self,
        results: List[SearchResult],
        required_keywords: List[str] = None,
        excluded_keywords: List[str] = None
    ) -> List[SearchResult]:
        """
        Filter results by keywords
        
        Args:
            results: List of search results
            required_keywords: Must contain at least one of these
            excluded_keywords: Must not contain any of these
        """
        filtered = []
        
        for result in results:
            text = f"{result.title} {result.snippet}".lower()
            
            # Check exclusions
            if excluded_keywords:
                if any(kw.lower() in text for kw in excluded_keywords):
                    continue
            
            # Check requirements
            if required_keywords:
                if any(kw.lower() in text for kw in required_keywords):
                    filtered.append(result)
            else:
                filtered.append(result)
        
        return filtered
    
    def rank_by_relevance(
        self,
        results: List[SearchResult],
        relevance_keywords: List[str]
    ) -> List[SearchResult]:
        """
        Rank results by relevance score
        
        Args:
            results: List of search results
            relevance_keywords: Keywords to score by
        """
        scored_results = []
        
        for result in results:
            text = f"{result.title} {result.snippet}".lower()
            score = sum(1 for kw in relevance_keywords if kw.lower() in text)
            scored_results.append((score, result))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [result for score, result in scored_results]


if __name__ == "__main__":
    try:
        serper = SerperTool()
        results = serper.search("test query", num_results=3)
        print(f"Serper test: Found {len(results)} results")
    except Exception as e:
        print(f"Serper test failed: {e}")