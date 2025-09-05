"""
Inventory Intelligence Agent for Warehouse Operations

Provides intelligent inventory management capabilities including stock lookup,
replenishment recommendations, cycle counting assistance, and WMS integration.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
from datetime import datetime, timedelta
import asyncio

from chain_server.services.llm.nim_client import get_nim_client, LLMResponse
from inventory_retriever.hybrid_retriever import get_hybrid_retriever, SearchContext
from inventory_retriever.structured.inventory_queries import InventoryItem
from memory_retriever.memory_manager import get_memory_manager
from .action_tools import get_inventory_action_tools, InventoryActionTools

logger = logging.getLogger(__name__)

@dataclass
class InventoryQuery:
    """Structured inventory query."""
    intent: str  # "stock_lookup", "replenishment", "cycle_count", "location", "low_stock"
    entities: Dict[str, Any]  # Extracted entities like SKU, location, etc.
    context: Dict[str, Any]  # Additional context
    user_query: str  # Original user query

@dataclass
class InventoryResponse:
    """Structured inventory response."""
    response_type: str  # "stock_info", "replenishment_advice", "cycle_count_plan", "location_info"
    data: Dict[str, Any]  # Structured data
    natural_language: str  # Natural language response
    recommendations: List[str]  # Actionable recommendations
    confidence: float  # Confidence score (0.0 to 1.0)
    actions_taken: List[Dict[str, Any]]  # Actions performed by the agent

class InventoryIntelligenceAgent:
    """
    Inventory Intelligence Agent with NVIDIA NIM integration.
    
    Provides comprehensive inventory management capabilities including:
    - Stock lookup and analysis
    - Replenishment recommendations
    - Cycle counting assistance
    - Location-based queries
    - WMS integration support
    """
    
    def __init__(self):
        self.nim_client = None
        self.hybrid_retriever = None
        self.conversation_context = {}  # Maintain conversation context
    
    async def initialize(self) -> None:
        """Initialize the agent with required services."""
        try:
            self.nim_client = await get_nim_client()
            self.hybrid_retriever = await get_hybrid_retriever()
            logger.info("Inventory Intelligence Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Inventory Intelligence Agent: {e}")
            raise
    
    async def process_query(
        self, 
        query: str, 
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> InventoryResponse:
        """
        Process inventory-related queries with full intelligence.
        
        Args:
            query: User's inventory query
            session_id: Session identifier for context
            context: Additional context
            
        Returns:
            InventoryResponse with structured data and natural language
        """
        try:
            # Initialize if needed
            if not self.nim_client or not self.hybrid_retriever:
                await self.initialize()
            
            # Get memory manager for context
            memory_manager = await get_memory_manager()
            
            # Get context from memory manager
            memory_context = await memory_manager.get_context_for_query(
                session_id=session_id,
                user_id=context.get("user_id", "default_user") if context else "default_user",
                query=query
            )
            
            # Step 1: Understand intent and extract entities using LLM
            inventory_query = await self._understand_query(query, session_id, context)
            
            # Step 2: Retrieve relevant data using hybrid retriever
            retrieved_data = await self._retrieve_data(inventory_query)
            
            # Step 3: Generate intelligent response using LLM
            response = await self._generate_response(inventory_query, retrieved_data, session_id, memory_context)
            
            # Step 4: Store conversation in memory
            await memory_manager.store_conversation_turn(
                session_id=session_id,
                user_id=context.get("user_id", "default_user") if context else "default_user",
                user_query=query,
                agent_response=response.natural_language,
                intent=inventory_query.intent,
                entities=inventory_query.entities,
                metadata={
                    "response_type": response.response_type,
                    "confidence": response.confidence,
                    "structured_data": response.data
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process inventory query: {e}")
            return InventoryResponse(
                response_type="error",
                data={"error": str(e)},
                natural_language=f"I encountered an error processing your inventory query: {str(e)}",
                recommendations=[],
                confidence=0.0
            )
    
    async def _understand_query(
        self, 
        query: str, 
        session_id: str, 
        context: Optional[Dict[str, Any]]
    ) -> InventoryQuery:
        """Use LLM to understand query intent and extract entities."""
        try:
            # Build context-aware prompt
            conversation_history = self.conversation_context.get(session_id, {}).get("history", [])
            context_str = self._build_context_string(conversation_history, context)
            
            prompt = f"""
You are an inventory intelligence agent for warehouse operations. Analyze the user query and extract structured information.

User Query: "{query}"

Previous Context: {context_str}

Extract the following information:
1. Intent: One of ["stock_lookup", "replenishment", "cycle_count", "location", "low_stock", "general"]
2. Entities: Extract SKU codes, locations, quantities, time periods, etc.
3. Context: Any additional relevant context

Respond in JSON format:
{{
    "intent": "stock_lookup",
    "entities": {{
        "sku": "SKU123",
        "location": "Aisle A3",
        "quantity": 10
    }},
    "context": {{
        "time_period": "last_week",
        "urgency": "high"
    }}
}}
"""
            
            messages = [
                {"role": "system", "content": "You are an expert inventory analyst. Respond ONLY with valid JSON, no markdown formatting or additional text."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.nim_client.generate_response(messages, temperature=0.1)
            
            # Parse LLM response
            try:
                parsed_response = json.loads(response.content)
                return InventoryQuery(
                    intent=parsed_response.get("intent", "general"),
                    entities=parsed_response.get("entities", {}),
                    context=parsed_response.get("context", {}),
                    user_query=query
                )
            except json.JSONDecodeError:
                # Fallback to simple intent detection
                return self._fallback_intent_detection(query)
                
        except Exception as e:
            logger.error(f"Query understanding failed: {e}")
            return self._fallback_intent_detection(query)
    
    def _fallback_intent_detection(self, query: str) -> InventoryQuery:
        """Fallback intent detection using keyword matching."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["stock", "quantity", "level", "sku"]):
            intent = "stock_lookup"
        elif any(word in query_lower for word in ["reorder", "replenish", "low stock"]):
            intent = "replenishment"
        elif any(word in query_lower for word in ["cycle count", "count", "audit"]):
            intent = "cycle_count"
        elif any(word in query_lower for word in ["location", "where", "aisle"]):
            intent = "location"
        else:
            intent = "general"
        
        return InventoryQuery(
            intent=intent,
            entities={},
            context={},
            user_query=query
        )
    
    async def _retrieve_data(self, inventory_query: InventoryQuery) -> Dict[str, Any]:
        """Retrieve relevant data using hybrid retriever."""
        try:
            # Create search context
            search_context = SearchContext(
                query=inventory_query.user_query,
                search_type="inventory",
                filters=inventory_query.entities,
                limit=20
            )
            
            # Perform hybrid search
            search_results = await self.hybrid_retriever.search(search_context)
            
            # Get inventory summary for context
            inventory_summary = await self.hybrid_retriever.get_inventory_summary()
            
            return {
                "search_results": search_results,
                "inventory_summary": inventory_summary,
                "query_entities": inventory_query.entities
            }
            
        except Exception as e:
            logger.error(f"Data retrieval failed: {e}")
            return {"error": str(e)}
    
    async def _generate_response(
        self, 
        inventory_query: InventoryQuery, 
        retrieved_data: Dict[str, Any],
        session_id: str,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> InventoryResponse:
        """Generate intelligent response using LLM with retrieved context."""
        try:
            # Build context for LLM
            context_str = self._build_retrieved_context(retrieved_data)
            conversation_history = self.conversation_context.get(session_id, {}).get("history", [])
            
            prompt = f"""
You are an inventory intelligence agent. Generate a comprehensive response based on the user query and retrieved data.

User Query: "{inventory_query.user_query}"
Intent: {inventory_query.intent}
Entities: {inventory_query.entities}

Retrieved Data:
{context_str}

Conversation History: {conversation_history[-3:] if conversation_history else "None"}

Generate a response that includes:
1. Natural language answer to the user's question
2. Structured data in JSON format
3. Actionable recommendations
4. Confidence score (0.0 to 1.0)

Respond in JSON format:
{{
    "response_type": "stock_info",
    "data": {{
        "items": [...],
        "summary": {{...}}
    }},
    "natural_language": "Based on your query, here's what I found...",
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],
    "confidence": 0.95
}}
"""
            
            messages = [
                {"role": "system", "content": "You are an expert inventory analyst. Respond ONLY with valid JSON, no markdown formatting or additional text."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.nim_client.generate_response(messages, temperature=0.2, max_retries=2)
            
            # Parse LLM response
            try:
                # Extract JSON from response (handle markdown code blocks)
                content = response.content.strip()
                if "```json" in content:
                    # Extract JSON from markdown code block
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    if end != -1:
                        content = content[start:end].strip()
                elif "```" in content:
                    # Extract JSON from generic code block
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    if end != -1:
                        content = content[start:end].strip()
                
                parsed_response = json.loads(content)
                return InventoryResponse(
                    response_type=parsed_response.get("response_type", "general"),
                    data=parsed_response.get("data", {}),
                    natural_language=parsed_response.get("natural_language", "I processed your inventory query."),
                    recommendations=parsed_response.get("recommendations", []),
                    confidence=parsed_response.get("confidence", 0.8)
                )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                logger.warning(f"Raw response: {response.content}")
                # Fallback response
                return self._generate_fallback_response(inventory_query, retrieved_data)
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._generate_fallback_response(inventory_query, retrieved_data)
    
    def _generate_fallback_response(
        self, 
        inventory_query: InventoryQuery, 
        retrieved_data: Dict[str, Any]
    ) -> InventoryResponse:
        """Generate intelligent fallback response when LLM fails."""
        try:
            search_results = retrieved_data.get("search_results")
            items = []
            
            if search_results and hasattr(search_results, 'structured_results') and search_results.structured_results:
                items = search_results.structured_results
                
                # Generate more intelligent response based on query intent
                if inventory_query.intent == "stock_lookup":
                    if len(items) == 1:
                        item = items[0]
                        natural_language = f"Found {item.name} (SKU: {item.sku}) with {item.quantity} units in stock at {item.location}. "
                        if item.quantity <= item.reorder_point:
                            natural_language += f"⚠️ This item is at or below reorder point ({item.reorder_point} units)."
                        else:
                            natural_language += f"Stock level is healthy (reorder point: {item.reorder_point} units)."
                    else:
                        natural_language = f"I found {len(items)} inventory items matching your query."
                else:
                    natural_language = f"I found {len(items)} inventory items matching your query."
                
                recommendations = ["Consider reviewing stock levels", "Check reorder points"]
                confidence = 0.8 if items else 0.6
            else:
                natural_language = "I couldn't find specific inventory data for your query."
                recommendations = ["Try rephrasing your question", "Check if the SKU exists"]
                confidence = 0.3
            
            return InventoryResponse(
                response_type="fallback",
                data={"items": [asdict(item) for item in items] if items else []},
                natural_language=natural_language,
                recommendations=recommendations,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return InventoryResponse(
                response_type="error",
                data={"error": str(e)},
                natural_language="I encountered an error processing your request.",
                recommendations=[],
                confidence=0.0
            )
    
    def _build_context_string(
        self, 
        conversation_history: List[Dict], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build context string from conversation history."""
        if not conversation_history and not context:
            return "No previous context"
        
        context_parts = []
        
        if conversation_history:
            recent_history = conversation_history[-3:]  # Last 3 exchanges
            context_parts.append(f"Recent conversation: {recent_history}")
        
        if context:
            context_parts.append(f"Additional context: {context}")
        
        return "; ".join(context_parts)
    
    def _build_retrieved_context(self, retrieved_data: Dict[str, Any]) -> str:
        """Build context string from retrieved data."""
        try:
            context_parts = []
            
            # Add inventory summary
            inventory_summary = retrieved_data.get("inventory_summary", {})
            if inventory_summary:
                context_parts.append(f"Inventory Summary: {inventory_summary}")
            
            # Add search results
            search_results = retrieved_data.get("search_results")
            if search_results:
                if search_results.structured_results:
                    items = search_results.structured_results
                    context_parts.append(f"Found {len(items)} inventory items")
                    for item in items[:5]:  # Show first 5 items
                        context_parts.append(f"- {item.sku}: {item.name} (Qty: {item.quantity}, Location: {item.location})")
                
                if search_results.vector_results:
                    docs = search_results.vector_results
                    context_parts.append(f"Found {len(docs)} relevant documents")
            
            return "\n".join(context_parts) if context_parts else "No relevant data found"
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return "Error building context"
    
    def _update_context(
        self, 
        session_id: str, 
        inventory_query: InventoryQuery, 
        response: InventoryResponse
    ) -> None:
        """Update conversation context."""
        try:
            if session_id not in self.conversation_context:
                self.conversation_context[session_id] = {
                    "history": [],
                    "current_focus": None,
                    "last_entities": {}
                }
            
            # Add to history
            self.conversation_context[session_id]["history"].append({
                "query": inventory_query.user_query,
                "intent": inventory_query.intent,
                "response_type": response.response_type,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update current focus
            if inventory_query.intent != "general":
                self.conversation_context[session_id]["current_focus"] = inventory_query.intent
            
            # Update last entities
            if inventory_query.entities:
                self.conversation_context[session_id]["last_entities"] = inventory_query.entities
            
            # Keep history manageable
            if len(self.conversation_context[session_id]["history"]) > 10:
                self.conversation_context[session_id]["history"] = \
                    self.conversation_context[session_id]["history"][-10:]
                    
        except Exception as e:
            logger.error(f"Context update failed: {e}")
    
    async def get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get conversation context for a session."""
        return self.conversation_context.get(session_id, {
            "history": [],
            "current_focus": None,
            "last_entities": {}
        })
    
    async def clear_conversation_context(self, session_id: str) -> None:
        """Clear conversation context for a session."""
        if session_id in self.conversation_context:
            del self.conversation_context[session_id]

# Global inventory agent instance
_inventory_agent: Optional[InventoryIntelligenceAgent] = None

async def get_inventory_agent() -> InventoryIntelligenceAgent:
    """Get or create the global inventory agent instance."""
    global _inventory_agent
    if _inventory_agent is None:
        _inventory_agent = InventoryIntelligenceAgent()
        await _inventory_agent.initialize()
    return _inventory_agent
