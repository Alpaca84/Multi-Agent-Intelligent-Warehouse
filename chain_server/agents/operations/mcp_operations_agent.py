"""
MCP-Enabled Operations Coordination Agent

This agent integrates with the Model Context Protocol (MCP) system to provide
dynamic tool discovery and execution for operations coordination.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
from datetime import datetime, timedelta
import asyncio

from chain_server.services.llm.nim_client import get_nim_client, LLMResponse
from inventory_retriever.hybrid_retriever import get_hybrid_retriever, SearchContext
from memory_retriever.memory_manager import get_memory_manager
from chain_server.services.mcp.tool_discovery import ToolDiscoveryService, DiscoveredTool, ToolCategory
from chain_server.services.mcp.tool_binding import ToolBindingService, BindingStrategy, ExecutionMode
from chain_server.services.mcp.tool_routing import ToolRoutingService, RoutingStrategy, QueryComplexity
from chain_server.services.mcp.tool_validation import ToolValidationService, ErrorHandlingService
from .action_tools import get_operations_action_tools, OperationsActionTools

logger = logging.getLogger(__name__)

@dataclass
class MCPOperationsQuery:
    """MCP-enabled operations query."""
    intent: str
    entities: Dict[str, Any]
    context: Dict[str, Any]
    user_query: str
    mcp_tools: List[str] = None
    tool_execution_plan: List[Dict[str, Any]] = None

@dataclass
class MCPOperationsResponse:
    """MCP-enabled operations response."""
    response_type: str
    data: Dict[str, Any]
    natural_language: str
    recommendations: List[str]
    confidence: float
    actions_taken: List[Dict[str, Any]]
    mcp_tools_used: List[str] = None
    tool_execution_results: Dict[str, Any] = None

class MCPOperationsCoordinationAgent:
    """
    MCP-enabled Operations Coordination Agent.
    
    This agent integrates with the Model Context Protocol (MCP) system to provide:
    - Dynamic tool discovery and execution for operations coordination
    - MCP-based tool binding and routing
    - Enhanced tool selection and validation
    - Comprehensive error handling and fallback mechanisms
    """
    
    def __init__(self):
        self.nim_client = None
        self.hybrid_retriever = None
        self.operations_tools = None
        self.tool_discovery = None
        self.tool_binding = None
        self.tool_routing = None
        self.tool_validation = None
        self.error_handling = None
        self.conversation_context = {}
        self.mcp_tools_cache = {}
        self.tool_execution_history = []
    
    async def initialize(self) -> None:
        """Initialize the agent with required services including MCP."""
        try:
            self.nim_client = await get_nim_client()
            self.hybrid_retriever = await get_hybrid_retriever()
            self.operations_tools = await get_operations_action_tools()
            
            # Initialize MCP components
            self.tool_discovery = ToolDiscoveryService()
            self.tool_binding = ToolBindingService(self.tool_discovery)
            self.tool_routing = ToolRoutingService(self.tool_discovery, self.tool_binding)
            self.tool_validation = ToolValidationService(self.tool_discovery)
            self.error_handling = ErrorHandlingService(self.tool_discovery)
            
            # Start tool discovery
            await self.tool_discovery.start_discovery()
            
            # Register MCP sources
            await self._register_mcp_sources()
            
            logger.info("MCP-enabled Operations Coordination Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Operations Coordination Agent: {e}")
            raise
    
    async def _register_mcp_sources(self) -> None:
        """Register MCP sources for tool discovery."""
        try:
            # Register the operations tools as an MCP source
            if self.operations_tools:
                await self.tool_discovery.register_discovery_source(
                    "operations_action_tools",
                    self.operations_tools,
                    "mcp_adapter"
                )
            
            logger.info("MCP sources registered successfully")
        except Exception as e:
            logger.error(f"Failed to register MCP sources: {e}")
    
    async def process_query(
        self,
        query: str,
        session_id: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> MCPOperationsResponse:
        """
        Process an operations coordination query with MCP integration.
        
        Args:
            query: User's operations query
            session_id: Session identifier for context
            context: Additional context
            
        Returns:
            MCPOperationsResponse with MCP tool execution results
        """
        try:
            # Initialize if needed
            if not self.nim_client or not self.tool_discovery:
                await self.initialize()
            
            # Update conversation context
            if session_id not in self.conversation_context:
                self.conversation_context[session_id] = {
                    "queries": [],
                    "responses": [],
                    "context": {}
                }
            
            # Parse query and identify intent
            parsed_query = await self._parse_operations_query(query, context)
            
            # Create routing context
            routing_context = await self._create_routing_context(parsed_query, session_id)
            
            # Route tools using MCP routing service
            routing_decision = await self.tool_routing.route_tools(
                routing_context,
                strategy=RoutingStrategy.BALANCED,
                max_tools=5
            )
            
            # Bind tools to agent
            bindings = await self.tool_binding.bind_tools(
                agent_id="operations_agent",
                query=query,
                intent=parsed_query.intent,
                entities=parsed_query.entities,
                context=parsed_query.context,
                strategy=BindingStrategy.SEMANTIC_MATCH,
                max_tools=5
            )
            
            # Create execution plan
            execution_plan = await self.tool_binding.create_execution_plan(
                routing_context,
                bindings,
                routing_decision.execution_mode
            )
            
            # Execute tools and gather results
            tool_results = await self._execute_tool_plan(execution_plan)
            
            # Generate response using LLM with tool results
            response = await self._generate_response_with_tools(parsed_query, tool_results)
            
            # Update conversation context
            self.conversation_context[session_id]["queries"].append(parsed_query)
            self.conversation_context[session_id]["responses"].append(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing operations query: {e}")
            return MCPOperationsResponse(
                response_type="error",
                data={"error": str(e)},
                natural_language=f"I encountered an error processing your request: {str(e)}",
                recommendations=["Please try rephrasing your question or contact support if the issue persists."],
                confidence=0.0,
                actions_taken=[],
                mcp_tools_used=[],
                tool_execution_results={}
            )
    
    async def _parse_operations_query(self, query: str, context: Optional[Dict[str, Any]]) -> MCPOperationsQuery:
        """Parse operations query and extract intent and entities."""
        try:
            # Use LLM to parse the query
            parse_prompt = f"""
            Parse this operations coordination query and extract:
            1. Intent (task_assignment, workforce_scheduling, pick_wave_generation, path_optimization, dock_scheduling, equipment_dispatch, kpi_publishing)
            2. Entities (worker_id, task_id, zone, priority, equipment_type, etc.)
            3. Context (urgency, constraints, requirements)
            
            Query: "{query}"
            Context: {context or {}}
            
            Return JSON format:
            {{
                "intent": "task_assignment",
                "entities": {{"worker_id": "W001", "zone": "A"}},
                "context": {{"priority": "high", "urgency": "immediate"}}
            }}
            """
            
            response = await self.nim_client.generate_response(parse_prompt)
            
            # Parse JSON response
            try:
                parsed_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback parsing
                parsed_data = {
                    "intent": "task_assignment",
                    "entities": {},
                    "context": {}
                }
            
            return MCPOperationsQuery(
                intent=parsed_data.get("intent", "task_assignment"),
                entities=parsed_data.get("entities", {}),
                context=parsed_data.get("context", {}),
                user_query=query
            )
            
        except Exception as e:
            logger.error(f"Error parsing operations query: {e}")
            return MCPOperationsQuery(
                intent="task_assignment",
                entities={},
                context={},
                user_query=query
            )
    
    async def _create_routing_context(self, query: MCPOperationsQuery, session_id: str) -> Any:
        """Create routing context for tool routing."""
        from chain_server.services.mcp.tool_routing import RoutingContext, QueryComplexity
        
        # Analyze query complexity
        complexity = QueryComplexity.MODERATE
        if len(query.user_query.split()) > 15:
            complexity = QueryComplexity.COMPLEX
        elif len(query.user_query.split()) < 5:
            complexity = QueryComplexity.SIMPLE
        
        return RoutingContext(
            query=query.user_query,
            intent=query.intent,
            entities=query.entities,
            user_context=query.context,
            session_id=session_id,
            agent_id="operations_agent",
            priority=query.context.get("priority", 1),
            complexity=complexity,
            required_capabilities=["task_management", "workforce_coordination", "operations_planning"]
        )
    
    async def _execute_tool_plan(self, execution_plan: Any) -> Dict[str, Any]:
        """Execute the tool execution plan."""
        try:
            results = await self.tool_binding.execute_plan(execution_plan)
            
            # Convert to dictionary format
            tool_results = {}
            for result in results:
                tool_results[result.tool_id] = {
                    "tool_name": result.tool_name,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "metadata": result.metadata
                }
            
            return tool_results
            
        except Exception as e:
            logger.error(f"Error executing tool plan: {e}")
            return {}
    
    async def _generate_response_with_tools(
        self, 
        query: MCPOperationsQuery, 
        tool_results: Dict[str, Any]
    ) -> MCPOperationsResponse:
        """Generate response using LLM with tool execution results."""
        try:
            # Prepare context for LLM
            successful_results = {k: v for k, v in tool_results.items() if v.get("success", False)}
            failed_results = {k: v for k, v in tool_results.items() if not v.get("success", False)}
            
            # Create response prompt
            response_prompt = f"""
            You are an Operations Coordination Agent. Generate a comprehensive response based on the user query and tool execution results.
            
            User Query: "{query.user_query}"
            Intent: {query.intent}
            Entities: {query.entities}
            Context: {query.context}
            
            Tool Execution Results:
            {json.dumps(successful_results, indent=2)}
            
            Failed Tool Executions:
            {json.dumps(failed_results, indent=2)}
            
            Generate a response that includes:
            1. Natural language explanation of the results
            2. Structured data summary
            3. Actionable recommendations for operations coordination
            4. Confidence assessment
            
            Return JSON format:
            {{
                "response_type": "operations_coordination",
                "data": {{"tasks": [], "workforce": [], "schedules": []}},
                "natural_language": "Based on the tool results...",
                "recommendations": ["Recommendation 1", "Recommendation 2"],
                "confidence": 0.85,
                "actions_taken": [{{"action": "tool_execution", "tool": "assign_tasks"}}]
            }}
            """
            
            response = await self.nim_client.generate_response(response_prompt)
            
            # Parse JSON response
            try:
                response_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback response
                response_data = {
                    "response_type": "operations_coordination",
                    "data": {"results": successful_results},
                    "natural_language": f"Based on the available data, here's what I found regarding your operations query: {query.user_query}",
                    "recommendations": ["Please review the operations status and take appropriate action if needed."],
                    "confidence": 0.7,
                    "actions_taken": [{"action": "mcp_tool_execution", "tools_used": len(successful_results)}]
                }
            
            return MCPOperationsResponse(
                response_type=response_data.get("response_type", "operations_coordination"),
                data=response_data.get("data", {}),
                natural_language=response_data.get("natural_language", ""),
                recommendations=response_data.get("recommendations", []),
                confidence=response_data.get("confidence", 0.7),
                actions_taken=response_data.get("actions_taken", []),
                mcp_tools_used=list(successful_results.keys()),
                tool_execution_results=tool_results
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return MCPOperationsResponse(
                response_type="error",
                data={"error": str(e)},
                natural_language=f"I encountered an error generating a response: {str(e)}",
                recommendations=["Please try again or contact support."],
                confidence=0.0,
                actions_taken=[],
                mcp_tools_used=[],
                tool_execution_results=tool_results
            )
    
    async def get_available_tools(self) -> List[DiscoveredTool]:
        """Get all available MCP tools."""
        if not self.tool_discovery:
            return []
        
        return list(self.tool_discovery.discovered_tools.values())
    
    async def get_tools_by_category(self, category: ToolCategory) -> List[DiscoveredTool]:
        """Get tools by category."""
        if not self.tool_discovery:
            return []
        
        return await self.tool_discovery.get_tools_by_category(category)
    
    async def search_tools(self, query: str) -> List[DiscoveredTool]:
        """Search for tools by query."""
        if not self.tool_discovery:
            return []
        
        return await self.tool_discovery.search_tools(query)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics."""
        return {
            "initialized": self.tool_discovery is not None,
            "available_tools": len(self.tool_discovery.discovered_tools) if self.tool_discovery else 0,
            "tool_execution_history": len(self.tool_execution_history),
            "conversation_contexts": len(self.conversation_context),
            "mcp_discovery_status": self.tool_discovery.get_discovery_status() if self.tool_discovery else None
        }
