"""
Operations Coordination Agent for Warehouse Operations

Provides intelligent workforce scheduling, task management, equipment allocation,
and operational KPI tracking for warehouse operations.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
from datetime import datetime, timedelta
import asyncio

from chain_server.services.llm.nim_client import get_nim_client, LLMResponse
from inventory_retriever.hybrid_retriever import get_hybrid_retriever, SearchContext
from inventory_retriever.structured.task_queries import TaskQueries, Task
from inventory_retriever.structured.telemetry_queries import TelemetryQueries

logger = logging.getLogger(__name__)

@dataclass
class OperationsQuery:
    """Structured operations query."""
    intent: str  # "workforce", "task_management", "equipment", "kpi", "scheduling"
    entities: Dict[str, Any]  # Extracted entities like shift, employee, equipment, etc.
    context: Dict[str, Any]  # Additional context
    user_query: str  # Original user query

@dataclass
class OperationsResponse:
    """Structured operations response."""
    response_type: str  # "workforce_info", "task_assignment", "equipment_status", "kpi_report", "schedule_info"
    data: Dict[str, Any]  # Structured data
    natural_language: str  # Natural language response
    recommendations: List[str]  # Actionable recommendations
    confidence: float  # Confidence score (0.0 to 1.0)

@dataclass
class WorkforceInfo:
    """Workforce information structure."""
    shift: str
    employees: List[Dict[str, Any]]
    total_count: int
    active_tasks: int
    productivity_score: float

@dataclass
class TaskAssignment:
    """Task assignment structure."""
    task_id: int
    assignee: str
    priority: str
    estimated_duration: int
    dependencies: List[str]
    status: str

class OperationsCoordinationAgent:
    """
    Operations Coordination Agent with NVIDIA NIM integration.
    
    Provides comprehensive operations management capabilities including:
    - Workforce scheduling and shift management
    - Task assignment and prioritization
    - Equipment allocation and maintenance
    - KPI tracking and performance analytics
    - Workflow optimization recommendations
    """
    
    def __init__(self):
        self.nim_client = None
        self.hybrid_retriever = None
        self.task_queries = None
        self.telemetry_queries = None
        self.conversation_context = {}  # Maintain conversation context
    
    async def initialize(self) -> None:
        """Initialize the agent with required services."""
        try:
            self.nim_client = await get_nim_client()
            self.hybrid_retriever = await get_hybrid_retriever()
            
            # Initialize task and telemetry queries
            from inventory_retriever.structured.sql_retriever import get_sql_retriever
            sql_retriever = await get_sql_retriever()
            self.task_queries = TaskQueries(sql_retriever)
            self.telemetry_queries = TelemetryQueries(sql_retriever)
            
            logger.info("Operations Coordination Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Operations Coordination Agent: {e}")
            raise
    
    async def process_query(
        self, 
        query: str, 
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> OperationsResponse:
        """
        Process operations-related queries with full intelligence.
        
        Args:
            query: User's operations query
            session_id: Session identifier for context
            context: Additional context
            
        Returns:
            OperationsResponse with structured data and natural language
        """
        try:
            # Initialize if needed
            if not self.nim_client or not self.hybrid_retriever:
                await self.initialize()
            
            # Update conversation context
            if session_id not in self.conversation_context:
                self.conversation_context[session_id] = {
                    "history": [],
                    "current_focus": None,
                    "last_entities": {}
                }
            
            # Step 1: Understand intent and extract entities using LLM
            operations_query = await self._understand_query(query, session_id, context)
            
            # Step 2: Retrieve relevant data using hybrid retriever and task queries
            retrieved_data = await self._retrieve_operations_data(operations_query)
            
            # Step 3: Generate intelligent response using LLM
            response = await self._generate_operations_response(operations_query, retrieved_data, session_id)
            
            # Step 4: Update conversation context
            self._update_context(session_id, operations_query, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process operations query: {e}")
            return OperationsResponse(
                response_type="error",
                data={"error": str(e)},
                natural_language=f"I encountered an error processing your operations query: {str(e)}",
                recommendations=[],
                confidence=0.0
            )
    
    async def _understand_query(
        self, 
        query: str, 
        session_id: str, 
        context: Optional[Dict[str, Any]]
    ) -> OperationsQuery:
        """Use LLM to understand query intent and extract entities."""
        try:
            # Build context-aware prompt
            conversation_history = self.conversation_context.get(session_id, {}).get("history", [])
            context_str = self._build_context_string(conversation_history, context)
            
            prompt = f"""
You are an operations coordination agent for warehouse operations. Analyze the user query and extract structured information.

User Query: "{query}"

Previous Context: {context_str}

Extract the following information:
1. Intent: One of ["workforce", "task_management", "equipment", "kpi", "scheduling", "general"]
2. Entities: Extract shift times, employee names, task types, equipment IDs, time periods, etc.
3. Context: Any additional relevant context

Respond in JSON format:
{{
    "intent": "workforce",
    "entities": {{
        "shift": "morning",
        "employee": "John Doe",
        "task_type": "picking",
        "equipment": "Forklift-001"
    }},
    "context": {{
        "time_period": "today",
        "urgency": "high"
    }}
}}
"""
            
            messages = [
                {"role": "system", "content": "You are an expert operations coordinator. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.nim_client.generate_response(messages, temperature=0.1)
            
            # Parse LLM response
            try:
                parsed_response = json.loads(response.content)
                return OperationsQuery(
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
    
    def _fallback_intent_detection(self, query: str) -> OperationsQuery:
        """Fallback intent detection using keyword matching."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["shift", "workforce", "employee", "staff", "team"]):
            intent = "workforce"
        elif any(word in query_lower for word in ["task", "assignment", "work", "job", "pick", "pack"]):
            intent = "task_management"
        elif any(word in query_lower for word in ["equipment", "forklift", "conveyor", "machine"]):
            intent = "equipment"
        elif any(word in query_lower for word in ["kpi", "performance", "metrics", "productivity"]):
            intent = "kpi"
        elif any(word in query_lower for word in ["schedule", "planning", "roster"]):
            intent = "scheduling"
        else:
            intent = "general"
        
        return OperationsQuery(
            intent=intent,
            entities={},
            context={},
            user_query=query
        )
    
    async def _retrieve_operations_data(self, operations_query: OperationsQuery) -> Dict[str, Any]:
        """Retrieve relevant operations data."""
        try:
            data = {}
            
            # Get task summary
            if self.task_queries:
                task_summary = await self.task_queries.get_task_summary()
                data["task_summary"] = task_summary
            
            # Get tasks by status
            if operations_query.intent == "task_management":
                pending_tasks = await self.task_queries.get_tasks_by_status("pending", limit=20)
                in_progress_tasks = await self.task_queries.get_tasks_by_status("in_progress", limit=20)
                data["pending_tasks"] = [asdict(task) for task in pending_tasks]
                data["in_progress_tasks"] = [asdict(task) for task in in_progress_tasks]
            
            # Get equipment health status
            if operations_query.intent == "equipment":
                equipment_health = await self.telemetry_queries.get_equipment_health_status()
                data["equipment_health"] = equipment_health
            
            # Get workforce simulation data (since we don't have real workforce data yet)
            if operations_query.intent == "workforce":
                data["workforce_info"] = self._simulate_workforce_data()
            
            return data
            
        except Exception as e:
            logger.error(f"Operations data retrieval failed: {e}")
            return {"error": str(e)}
    
    def _simulate_workforce_data(self) -> Dict[str, Any]:
        """Simulate workforce data for demonstration."""
        return {
            "shifts": {
                "morning": {
                    "start_time": "06:00",
                    "end_time": "14:00",
                    "employees": [
                        {"name": "John Smith", "role": "Picker", "status": "active"},
                        {"name": "Sarah Johnson", "role": "Packer", "status": "active"},
                        {"name": "Mike Wilson", "role": "Forklift Operator", "status": "active"}
                    ],
                    "total_count": 3,
                    "active_tasks": 8
                },
                "afternoon": {
                    "start_time": "14:00",
                    "end_time": "22:00",
                    "employees": [
                        {"name": "Lisa Brown", "role": "Picker", "status": "active"},
                        {"name": "David Lee", "role": "Packer", "status": "active"},
                        {"name": "Amy Chen", "role": "Supervisor", "status": "active"}
                    ],
                    "total_count": 3,
                    "active_tasks": 6
                }
            },
            "productivity_metrics": {
                "picks_per_hour": 45.2,
                "packages_per_hour": 38.7,
                "accuracy_rate": 98.5
            }
        }
    
    async def _generate_operations_response(
        self, 
        operations_query: OperationsQuery, 
        retrieved_data: Dict[str, Any],
        session_id: str
    ) -> OperationsResponse:
        """Generate intelligent response using LLM with retrieved context."""
        try:
            # Build context for LLM
            context_str = self._build_retrieved_context(retrieved_data)
            conversation_history = self.conversation_context.get(session_id, {}).get("history", [])
            
            prompt = f"""
You are an operations coordination agent. Generate a comprehensive response based on the user query and retrieved data.

User Query: "{operations_query.user_query}"
Intent: {operations_query.intent}
Entities: {operations_query.entities}

Retrieved Data:
{context_str}

Conversation History: {conversation_history[-3:] if conversation_history else "None"}

Generate a response that includes:
1. Natural language answer to the user's question
2. Structured data in JSON format
3. Actionable recommendations for operations improvement
4. Confidence score (0.0 to 1.0)

Respond in JSON format:
{{
    "response_type": "workforce_info",
    "data": {{
        "shifts": {{...}},
        "metrics": {{...}}
    }},
    "natural_language": "Based on your query, here's the current workforce status...",
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],
    "confidence": 0.95
}}
"""
            
            messages = [
                {"role": "system", "content": "You are an expert operations coordinator. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.nim_client.generate_response(messages, temperature=0.2)
            
            # Parse LLM response
            try:
                parsed_response = json.loads(response.content)
                return OperationsResponse(
                    response_type=parsed_response.get("response_type", "general"),
                    data=parsed_response.get("data", {}),
                    natural_language=parsed_response.get("natural_language", "I processed your operations query."),
                    recommendations=parsed_response.get("recommendations", []),
                    confidence=parsed_response.get("confidence", 0.8)
                )
            except json.JSONDecodeError:
                # Fallback response
                return self._generate_fallback_response(operations_query, retrieved_data)
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._generate_fallback_response(operations_query, retrieved_data)
    
    def _generate_fallback_response(
        self, 
        operations_query: OperationsQuery, 
        retrieved_data: Dict[str, Any]
    ) -> OperationsResponse:
        """Generate fallback response when LLM fails."""
        try:
            intent = operations_query.intent
            data = retrieved_data
            
            if intent == "workforce":
                natural_language = "Here's the current workforce information for your warehouse operations."
                recommendations = ["Consider cross-training employees", "Monitor shift productivity metrics"]
            elif intent == "task_management":
                natural_language = "Here's the current task status and assignments."
                recommendations = ["Prioritize urgent tasks", "Balance workload across team members"]
            elif intent == "equipment":
                natural_language = "Here's the current equipment status and health information."
                recommendations = ["Schedule preventive maintenance", "Monitor equipment performance"]
            elif intent == "kpi":
                natural_language = "Here are the current operational KPIs and performance metrics."
                recommendations = ["Focus on accuracy improvements", "Optimize workflow efficiency"]
            else:
                natural_language = "I processed your operations query and retrieved relevant information."
                recommendations = ["Review operational procedures", "Monitor performance metrics"]
            
            return OperationsResponse(
                response_type="fallback",
                data=data,
                natural_language=natural_language,
                recommendations=recommendations,
                confidence=0.6
            )
            
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return OperationsResponse(
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
            
            # Add task summary
            if "task_summary" in retrieved_data:
                task_summary = retrieved_data["task_summary"]
                context_parts.append(f"Task Summary: {task_summary}")
            
            # Add workforce info
            if "workforce_info" in retrieved_data:
                workforce_info = retrieved_data["workforce_info"]
                context_parts.append(f"Workforce Info: {workforce_info}")
            
            # Add equipment health
            if "equipment_health" in retrieved_data:
                equipment_health = retrieved_data["equipment_health"]
                context_parts.append(f"Equipment Health: {equipment_health}")
            
            return "\n".join(context_parts) if context_parts else "No relevant data found"
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return "Error building context"
    
    def _update_context(
        self, 
        session_id: str, 
        operations_query: OperationsQuery, 
        response: OperationsResponse
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
                "query": operations_query.user_query,
                "intent": operations_query.intent,
                "response_type": response.response_type,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update current focus
            if operations_query.intent != "general":
                self.conversation_context[session_id]["current_focus"] = operations_query.intent
            
            # Update last entities
            if operations_query.entities:
                self.conversation_context[session_id]["last_entities"] = operations_query.entities
            
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

# Global operations agent instance
_operations_agent: Optional[OperationsCoordinationAgent] = None

async def get_operations_agent() -> OperationsCoordinationAgent:
    """Get or create the global operations agent instance."""
    global _operations_agent
    if _operations_agent is None:
        _operations_agent = OperationsCoordinationAgent()
        await _operations_agent.initialize()
    return _operations_agent
