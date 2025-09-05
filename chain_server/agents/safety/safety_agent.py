"""
Safety & Compliance Agent for Warehouse Operations

Provides intelligent safety incident management, compliance monitoring,
policy lookup, and safety checklist management for warehouse operations.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
from datetime import datetime, timedelta
import asyncio

from chain_server.services.llm.nim_client import get_nim_client, LLMResponse
from inventory_retriever.hybrid_retriever import get_hybrid_retriever, SearchContext
from inventory_retriever.structured.sql_retriever import get_sql_retriever

logger = logging.getLogger(__name__)

@dataclass
class SafetyQuery:
    """Structured safety query."""
    intent: str  # "incident_report", "policy_lookup", "compliance_check", "safety_audit", "training"
    entities: Dict[str, Any]  # Extracted entities like incident_type, severity, location, etc.
    context: Dict[str, Any]  # Additional context
    user_query: str  # Original user query

@dataclass
class SafetyResponse:
    """Structured safety response."""
    response_type: str  # "incident_logged", "policy_info", "compliance_status", "audit_report", "training_info"
    data: Dict[str, Any]  # Structured data
    natural_language: str  # Natural language response
    recommendations: List[str]  # Actionable recommendations
    confidence: float  # Confidence score (0.0 to 1.0)

@dataclass
class SafetyIncident:
    """Safety incident structure."""
    id: int
    severity: str
    description: str
    reported_by: str
    occurred_at: datetime
    location: str
    incident_type: str
    status: str

class SafetyComplianceAgent:
    """
    Safety & Compliance Agent with NVIDIA NIM integration.
    
    Provides comprehensive safety and compliance capabilities including:
    - Incident logging and reporting
    - Safety policy lookup and enforcement
    - Compliance checklist management
    - Hazard identification and alerts
    - Training record tracking
    """
    
    def __init__(self):
        self.nim_client = None
        self.hybrid_retriever = None
        self.sql_retriever = None
        self.conversation_context = {}  # Maintain conversation context
    
    async def initialize(self) -> None:
        """Initialize the agent with required services."""
        try:
            self.nim_client = await get_nim_client()
            self.hybrid_retriever = await get_hybrid_retriever()
            self.sql_retriever = await get_sql_retriever()
            
            logger.info("Safety & Compliance Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Safety & Compliance Agent: {e}")
            raise
    
    async def process_query(
        self, 
        query: str, 
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> SafetyResponse:
        """
        Process safety and compliance queries with full intelligence.
        
        Args:
            query: User's safety/compliance query
            session_id: Session identifier for context
            context: Additional context
            
        Returns:
            SafetyResponse with structured data and natural language
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
            safety_query = await self._understand_query(query, session_id, context)
            
            # Step 2: Retrieve relevant data using hybrid retriever and safety queries
            retrieved_data = await self._retrieve_safety_data(safety_query)
            
            # Step 3: Generate intelligent response using LLM
            response = await self._generate_safety_response(safety_query, retrieved_data, session_id)
            
            # Step 4: Update conversation context
            self._update_context(session_id, safety_query, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process safety query: {e}")
            return SafetyResponse(
                response_type="error",
                data={"error": str(e)},
                natural_language=f"I encountered an error processing your safety query: {str(e)}",
                recommendations=[],
                confidence=0.0
            )
    
    async def _understand_query(
        self, 
        query: str, 
        session_id: str, 
        context: Optional[Dict[str, Any]]
    ) -> SafetyQuery:
        """Use LLM to understand query intent and extract entities."""
        try:
            # Build context-aware prompt
            conversation_history = self.conversation_context.get(session_id, {}).get("history", [])
            context_str = self._build_context_string(conversation_history, context)
            
            prompt = f"""
You are a safety and compliance agent for warehouse operations. Analyze the user query and extract structured information.

User Query: "{query}"

Previous Context: {context_str}

Extract the following information:
1. Intent: One of ["incident_report", "policy_lookup", "compliance_check", "safety_audit", "training", "general"]
2. Entities: Extract incident types, severity levels, locations, policy names, compliance requirements, etc.
3. Context: Any additional relevant context

Respond in JSON format:
{{
    "intent": "incident_report",
    "entities": {{
        "incident_type": "slip_and_fall",
        "severity": "minor",
        "location": "Aisle A3",
        "reported_by": "John Smith"
    }},
    "context": {{
        "urgency": "high",
        "requires_immediate_action": true
    }}
}}
"""
            
            messages = [
                {"role": "system", "content": "You are an expert safety and compliance officer. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.nim_client.generate_response(messages, temperature=0.1)
            
            # Parse LLM response
            try:
                parsed_response = json.loads(response.content)
                return SafetyQuery(
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
    
    def _fallback_intent_detection(self, query: str) -> SafetyQuery:
        """Fallback intent detection using keyword matching."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["incident", "accident", "injury", "hazard", "report"]):
            intent = "incident_report"
        elif any(word in query_lower for word in ["policy", "procedure", "guideline", "rule"]):
            intent = "policy_lookup"
        elif any(word in query_lower for word in ["compliance", "audit", "check", "inspection"]):
            intent = "compliance_check"
        elif any(word in query_lower for word in ["training", "certification", "safety course"]):
            intent = "training"
        else:
            intent = "general"
        
        return SafetyQuery(
            intent=intent,
            entities={},
            context={},
            user_query=query
        )
    
    async def _retrieve_safety_data(self, safety_query: SafetyQuery) -> Dict[str, Any]:
        """Retrieve relevant safety data."""
        try:
            data = {}
            
            # Get safety incidents
            if safety_query.intent == "incident_report":
                incidents = await self._get_safety_incidents()
                data["incidents"] = incidents
            
            # Get safety policies (simulated for now)
            if safety_query.intent == "policy_lookup":
                policies = self._get_safety_policies()
                data["policies"] = policies
            
            # Get compliance status
            if safety_query.intent == "compliance_check":
                compliance_status = self._get_compliance_status()
                data["compliance"] = compliance_status
            
            # Get training records (simulated)
            if safety_query.intent == "training":
                training_records = self._get_training_records()
                data["training"] = training_records
            
            return data
            
        except Exception as e:
            logger.error(f"Safety data retrieval failed: {e}")
            return {"error": str(e)}
    
    async def _get_safety_incidents(self) -> List[Dict[str, Any]]:
        """Get safety incidents from database."""
        try:
            query = """
            SELECT id, severity, description, reported_by, occurred_at
            FROM safety_incidents 
            ORDER BY occurred_at DESC
            LIMIT 10
            """
            results = await self.sql_retriever.execute_query(query)
            return results
        except Exception as e:
            logger.error(f"Failed to get safety incidents: {e}")
            return []
    
    def _get_safety_policies(self) -> Dict[str, Any]:
        """Get safety policies (simulated for demonstration)."""
        return {
            "policies": [
                {
                    "id": "POL-001",
                    "name": "Personal Protective Equipment (PPE) Policy",
                    "category": "Safety Equipment",
                    "last_updated": "2024-01-15",
                    "status": "Active",
                    "summary": "All personnel must wear appropriate PPE in designated areas"
                },
                {
                    "id": "POL-002", 
                    "name": "Forklift Operation Safety Guidelines",
                    "category": "Equipment Safety",
                    "last_updated": "2024-01-10",
                    "status": "Active",
                    "summary": "Comprehensive guidelines for safe forklift operation"
                },
                {
                    "id": "POL-003",
                    "name": "Emergency Evacuation Procedures",
                    "category": "Emergency Response",
                    "last_updated": "2024-01-05",
                    "status": "Active",
                    "summary": "Step-by-step emergency evacuation procedures"
                }
            ],
            "total_count": 3
        }
    
    def _get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status (simulated for demonstration)."""
        return {
            "overall_status": "Compliant",
            "compliance_score": 95.5,
            "areas": [
                {
                    "area": "Safety Equipment",
                    "status": "Compliant",
                    "score": 98.0,
                    "last_audit": "2024-01-20"
                },
                {
                    "area": "Training Records",
                    "status": "Compliant", 
                    "score": 92.0,
                    "last_audit": "2024-01-18"
                },
                {
                    "area": "Incident Reporting",
                    "status": "Minor Issues",
                    "score": 88.0,
                    "last_audit": "2024-01-15"
                }
            ],
            "next_audit": "2024-02-15"
        }
    
    def _get_training_records(self) -> Dict[str, Any]:
        """Get training records (simulated for demonstration)."""
        return {
            "employees": [
                {
                    "name": "John Smith",
                    "role": "Picker",
                    "certifications": [
                        {"name": "Forklift Safety", "expires": "2024-06-15", "status": "Valid"},
                        {"name": "PPE Training", "expires": "2024-08-20", "status": "Valid"}
                    ]
                },
                {
                    "name": "Sarah Johnson",
                    "role": "Packer",
                    "certifications": [
                        {"name": "Safety Awareness", "expires": "2024-05-10", "status": "Valid"},
                        {"name": "Emergency Response", "expires": "2024-07-25", "status": "Valid"}
                    ]
                }
            ],
            "upcoming_expirations": [
                {"employee": "Mike Wilson", "certification": "Forklift Safety", "expires": "2024-02-28"},
                {"employee": "Lisa Brown", "certification": "PPE Training", "expires": "2024-03-05"}
            ]
        }
    
    async def _generate_safety_response(
        self, 
        safety_query: SafetyQuery, 
        retrieved_data: Dict[str, Any],
        session_id: str
    ) -> SafetyResponse:
        """Generate intelligent response using LLM with retrieved context."""
        try:
            # Build context for LLM
            context_str = self._build_retrieved_context(retrieved_data)
            conversation_history = self.conversation_context.get(session_id, {}).get("history", [])
            
            prompt = f"""
You are a safety and compliance agent. Generate a comprehensive response based on the user query and retrieved data.

User Query: "{safety_query.user_query}"
Intent: {safety_query.intent}
Entities: {safety_query.entities}

Retrieved Data:
{context_str}

Conversation History: {conversation_history[-3:] if conversation_history else "None"}

Generate a response that includes:
1. Natural language answer to the user's question
2. Structured data in JSON format
3. Actionable recommendations for safety improvement
4. Confidence score (0.0 to 1.0)

Respond in JSON format:
{{
    "response_type": "incident_logged",
    "data": {{
        "incidents": [...],
        "policies": [...]
    }},
    "natural_language": "Based on your query, here's the safety information...",
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],
    "confidence": 0.95
}}
"""
            
            messages = [
                {"role": "system", "content": "You are an expert safety and compliance officer. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.nim_client.generate_response(messages, temperature=0.2)
            
            # Parse LLM response
            try:
                parsed_response = json.loads(response.content)
                return SafetyResponse(
                    response_type=parsed_response.get("response_type", "general"),
                    data=parsed_response.get("data", {}),
                    natural_language=parsed_response.get("natural_language", "I processed your safety query."),
                    recommendations=parsed_response.get("recommendations", []),
                    confidence=parsed_response.get("confidence", 0.8)
                )
            except json.JSONDecodeError:
                # Fallback response
                return self._generate_fallback_response(safety_query, retrieved_data)
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._generate_fallback_response(safety_query, retrieved_data)
    
    def _generate_fallback_response(
        self, 
        safety_query: SafetyQuery, 
        retrieved_data: Dict[str, Any]
    ) -> SafetyResponse:
        """Generate fallback response when LLM fails."""
        try:
            intent = safety_query.intent
            data = retrieved_data
            
            if intent == "incident_report":
                natural_language = "Here's the current safety incident information and reporting status."
                recommendations = ["Report incidents immediately", "Follow up on open incidents"]
            elif intent == "policy_lookup":
                natural_language = "Here are the relevant safety policies and procedures."
                recommendations = ["Review policy updates", "Ensure team compliance"]
            elif intent == "compliance_check":
                natural_language = "Here's the current compliance status and audit information."
                recommendations = ["Address compliance gaps", "Schedule regular audits"]
            elif intent == "training":
                natural_language = "Here are the training records and certification status."
                recommendations = ["Schedule upcoming training", "Track certification expirations"]
            else:
                natural_language = "I processed your safety query and retrieved relevant information."
                recommendations = ["Maintain safety standards", "Regular safety reviews"]
            
            return SafetyResponse(
                response_type="fallback",
                data=data,
                natural_language=natural_language,
                recommendations=recommendations,
                confidence=0.6
            )
            
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return SafetyResponse(
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
            
            # Add incidents
            if "incidents" in retrieved_data:
                incidents = retrieved_data["incidents"]
                context_parts.append(f"Recent Incidents: {len(incidents)} incidents found")
            
            # Add policies
            if "policies" in retrieved_data:
                policies = retrieved_data["policies"]
                context_parts.append(f"Safety Policies: {policies.get('total_count', 0)} policies available")
            
            # Add compliance
            if "compliance" in retrieved_data:
                compliance = retrieved_data["compliance"]
                context_parts.append(f"Compliance Status: {compliance.get('overall_status', 'Unknown')}")
            
            # Add training
            if "training" in retrieved_data:
                training = retrieved_data["training"]
                context_parts.append(f"Training Records: {len(training.get('employees', []))} employees tracked")
            
            return "\n".join(context_parts) if context_parts else "No relevant data found"
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return "Error building context"
    
    def _update_context(
        self, 
        session_id: str, 
        safety_query: SafetyQuery, 
        response: SafetyResponse
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
                "query": safety_query.user_query,
                "intent": safety_query.intent,
                "response_type": response.response_type,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update current focus
            if safety_query.intent != "general":
                self.conversation_context[session_id]["current_focus"] = safety_query.intent
            
            # Update last entities
            if safety_query.entities:
                self.conversation_context[session_id]["last_entities"] = safety_query.entities
            
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

# Global safety agent instance
_safety_agent: Optional[SafetyComplianceAgent] = None

async def get_safety_agent() -> SafetyComplianceAgent:
    """Get or create the global safety agent instance."""
    global _safety_agent
    if _safety_agent is None:
        _safety_agent = SafetyComplianceAgent()
        await _safety_agent.initialize()
    return _safety_agent
