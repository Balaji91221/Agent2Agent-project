"""
Itinerary Planner Agent (Host Agent)

A generic orchestrator agent that discovers and communicates with sub-agents
to create complete travel itineraries. Uses Google Gemini for planning and
the A2A Protocol for agent communication.

This agent is GENERIC - it doesn't know the specifics of flight/hotel search.
It discovers available agents, decides which ones to use, and delegates tasks.
"""

import os
import json
import asyncio
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.client import A2AClient
from common.types import TaskRequest, AgentCard

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("HOST_AGENT")
logger.setLevel(logging.DEBUG)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class ItineraryPlannerAgent:
    """
    Generic Host Agent that orchestrates sub-agents via A2A Protocol.
    
    This agent:
    1. Discovers available agents via A2A discovery
    2. Uses LLM to decide which agents to contact based on the user request
    3. Delegates tasks to appropriate agents
    4. Synthesizes results into a final response
    
    The host agent is GENERIC - it doesn't hardcode knowledge about specific agents.
    """
    
    def __init__(self):
        """Initialize the Itinerary Planner Agent."""
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.name = "Itinerary Planner Agent"
        self.description = "Generic orchestrator that discovers and coordinates with specialized agents"
        
        # Registry of known agent URLs (can be discovered dynamically)
        self.agent_registry = [
            os.getenv("FLIGHT_SEARCH_API_URL", "http://localhost:8000"),
            os.getenv("HOTEL_SEARCH_API_URL", "http://localhost:8003"),
        ]
        
        # Cached agent cards
        self.discovered_agents: Dict[str, Dict[str, Any]] = {}
        
        logger.info("=" * 60)
        logger.info(f"🚀 {self.name} initialized")
        logger.info(f"📋 Registered agent URLs: {self.agent_registry}")
        logger.info("=" * 60)
    
    async def discover_agents(self) -> List[Dict[str, Any]]:
        """
        Discover available agents via A2A Protocol.
        
        Fetches agent cards from registered agent URLs to understand
        their capabilities.
        """
        logger.info("")
        logger.info("🔍 STEP 1: AGENT DISCOVERY")
        logger.info("-" * 40)
        
        discovered = []
        
        for agent_url in self.agent_registry:
            try:
                logger.info(f"   📡 Contacting {agent_url}/.well-known/agent.json")
                
                async with A2AClient(agent_url) as client:
                    agent_card = await client.get_agent_card()
                    if agent_card:
                        agent_info = {
                            "url": agent_url,
                            "name": agent_card.name,
                            "description": agent_card.description,
                            "capabilities": [cap.model_dump() for cap in agent_card.capabilities],
                            "supported_task_types": agent_card.supported_task_types
                        }
                        discovered.append(agent_info)
                        self.discovered_agents[agent_url] = agent_info
                        
                        logger.info(f"   ✅ Discovered: {agent_card.name}")
                        logger.info(f"      Description: {agent_card.description}")
                        logger.info(f"      Task Types: {agent_card.supported_task_types}")
                        
            except Exception as e:
                logger.warning(f"   ❌ Failed to discover agent at {agent_url}: {e}")
        
        logger.info(f"   📊 Total agents discovered: {len(discovered)}")
        return discovered
    
    async def decide_agents_to_use(self, request: str, available_agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use LLM to decide which agents are needed for this request.
        
        Args:
            request: The user's natural language request
            available_agents: List of discovered agent capabilities
            
        Returns:
            List of agents to use with tasks to send them
        """
        logger.info("")
        logger.info("🤖 STEP 2: LLM DECISION - Which agents to use?")
        logger.info("-" * 40)
        logger.info(f"   User Request: \"{request}\"")
        
        prompt = f"""
        You are an orchestrator agent. Based on the user's request, decide which agents to contact.
        
        User Request: "{request}"
        
        Available Agents:
        {json.dumps(available_agents, indent=2)}
        
        For each agent you want to use, create a task description in natural language.
        The sub-agent will understand and process the task - you don't need to structure it.
        
        Return ONLY a JSON array (no markdown, no explanation):
        [
            {{
                "agent_url": "<url of the agent to use>",
                "agent_name": "<name of the agent>",
                "task_description": "<natural language description of what you want this agent to do>",
                "task_type": "<one of the supported_task_types from the agent>"
            }}
        ]
        
        Include all agents that might be helpful for this travel request.
        """
        
        logger.info("   🧠 Sending request to Gemini for decision...")
        response = self.model.generate_content(prompt)
        
        try:
            text = response.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            agents_to_use = json.loads(text)
            
            logger.info(f"   ✅ LLM decided to use {len(agents_to_use)} agent(s):")
            for agent in agents_to_use:
                logger.info(f"      • {agent['agent_name']}")
                logger.info(f"        Task: \"{agent['task_description'][:80]}...\"")
            
            return agents_to_use
            
        except json.JSONDecodeError:
            logger.warning("   ⚠️ Failed to parse LLM response, using all agents")
            return [
                {
                    "agent_url": agent["url"],
                    "agent_name": agent["name"],
                    "task_description": f"Help with: {request}",
                    "task_type": agent["supported_task_types"][0] if agent["supported_task_types"] else "generic"
                }
                for agent in available_agents
            ]
    
    async def delegate_task_to_agent(self, agent_url: str, agent_name: str, task_description: str, task_type: str) -> Dict[str, Any]:
        """
        Delegate a task to a specific agent via A2A Protocol.
        
        The host agent sends a natural language task description.
        The sub-agent is responsible for understanding and executing it.
        """
        logger.info("")
        logger.info(f"📤 DELEGATING TASK TO: {agent_name}")
        logger.info("-" * 40)
        logger.info(f"   URL: {agent_url}")
        logger.info(f"   Task Type: {task_type}")
        logger.info(f"   Task Description: \"{task_description}\"")
        
        try:
            async with A2AClient(agent_url) as client:
                task = TaskRequest(
                    description=task_description,
                    task_type=task_type,
                    parameters={}  # Let the sub-agent parse the description itself
                )
                
                logger.info(f"   📨 Sending A2A TaskRequest (ID: {task.id[:8]}...)")
                
                response = await client.send_task(task)
                
                if response.result:
                    logger.info(f"   ✅ Response received from {agent_name}")
                    logger.info(f"      Status: {response.status}")
                    if 'summary' in response.result:
                        logger.info(f"      Summary preview: {response.result['summary'][:100]}...")
                    return {
                        "status": "success",
                        "agent_url": agent_url,
                        "result": response.result
                    }
                else:
                    logger.error(f"   ❌ Error from {agent_name}: {response.error}")
                    return {
                        "status": "error",
                        "agent_url": agent_url,
                        "error": response.error or "Unknown error"
                    }
                    
        except Exception as e:
            logger.error(f"   ❌ Failed to contact {agent_name}: {str(e)}")
            return {
                "status": "error",
                "agent_url": agent_url,
                "error": str(e)
            }
    
    async def synthesize_results(self, request: str, agent_results: List[Dict[str, Any]]) -> str:
        """
        Use LLM to synthesize results from multiple agents into a coherent response.
        """
        logger.info("")
        logger.info("🔄 STEP 4: SYNTHESIZING RESULTS")
        logger.info("-" * 40)
        logger.info(f"   Combining results from {len(agent_results)} agent(s)")
        
        prompt = f"""
        You are a travel planning assistant. Create a comprehensive travel itinerary
        based on the user's request and the information gathered from specialized agents.
        
        Original Request: "{request}"
        
        Information from Agents:
        {json.dumps(agent_results, indent=2)}
        
        Please create a well-formatted travel itinerary that includes:
        1. A summary of the trip
        2. Recommended flight options (if available)
        3. Recommended hotel options (if available)
        4. Total estimated cost
        5. Helpful travel tips for the destination
        
        Format the response in a clear, readable manner with sections and bullet points.
        If any agent failed to respond, mention what information is missing.
        """
        
        logger.info("   🧠 Sending to Gemini for synthesis...")
        response = self.model.generate_content(prompt)
        logger.info("   ✅ Itinerary generated successfully")
        
        return response.text
    
    async def plan_trip(self, request: str) -> Dict[str, Any]:
        """
        Main method to plan a complete trip using agent orchestration.
        """
        logger.info("")
        logger.info("=" * 60)
        logger.info("🌍 NEW TRIP PLANNING REQUEST")
        logger.info("=" * 60)
        logger.info(f"Request: \"{request}\"")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # Step 1: Discover available agents
            available_agents = await self.discover_agents()
            
            if not available_agents:
                logger.error("❌ No agents available for orchestration")
                return {
                    "status": "error",
                    "error": "No agents available for orchestration",
                    "agent": self.name
                }
            
            # Step 2: Use LLM to decide which agents to contact
            agents_to_use = await self.decide_agents_to_use(request, available_agents)
            
            # Step 3: Delegate tasks to agents in parallel
            logger.info("")
            logger.info("⚡ STEP 3: PARALLEL TASK DELEGATION")
            logger.info("-" * 40)
            logger.info(f"   Sending tasks to {len(agents_to_use)} agent(s) in parallel...")
            
            tasks = [
                self.delegate_task_to_agent(
                    agent_info["agent_url"],
                    agent_info["agent_name"],
                    agent_info["task_description"],
                    agent_info["task_type"]
                )
                for agent_info in agents_to_use
            ]
            
            agent_results = await asyncio.gather(*tasks)
            
            # Combine results with agent names for context
            results_with_context = []
            for i, result in enumerate(agent_results):
                result["agent_name"] = agents_to_use[i]["agent_name"]
                results_with_context.append(result)
            
            # Step 4: Synthesize results
            itinerary = await self.synthesize_results(request, results_with_context)
            
            # Extract structured results for UI
            flight_results = {}
            hotel_results = {}
            parsed_params = {}
            
            for result in results_with_context:
                if result["status"] == "success" and "result" in result:
                    agent_result = result["result"]
                    if "Flight" in result.get("agent_name", ""):
                        flight_results = agent_result
                        if "data" in agent_result and "query" in agent_result["data"]:
                            query = agent_result["data"]["query"]
                            parsed_params["origin"] = query.get("origin", "")
                            parsed_params["destination"] = query.get("destination", "")
                            parsed_params["departure_date"] = query.get("date", "")

                    elif "Hotel" in result.get("agent_name", ""):
                        hotel_results = agent_result
                        if "data" in agent_result and "query" in agent_result["data"]:
                            query = agent_result["data"]["query"]
                            parsed_params["destination"] = query.get("location", parsed_params.get("destination", ""))
                            parsed_params["return_date"] = query.get("check_out", "")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ TRIP PLANNING COMPLETE")
            logger.info("=" * 60)
            logger.info(f"   Agents discovered: {[a['name'] for a in available_agents]}")
            logger.info(f"   Agents used: {[a['agent_name'] for a in agents_to_use]}")
            logger.info(f"   Parsed params: {parsed_params}")
            
            results = {
                "status": "success",
                "request": request,
                "parsed_parameters": parsed_params,
                "discovered_agents": [a["name"] for a in available_agents],
                "agents_used": [a["agent_name"] for a in agents_to_use],
                "agent_results": results_with_context,
                "flight_results": flight_results,
                "hotel_results": hotel_results,
                "itinerary": itinerary,
                "agent": self.name
            }
            print(results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during trip planning: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name
            }
    
    def get_agent_card(self) -> Dict[str, Any]:
        """Get the agent card for A2A discovery."""
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "capabilities": [
                {
                    "name": "orchestration",
                    "description": "Discover and coordinate with specialized agents",
                    "task_types": ["trip_planning_v1", "generic_orchestration"]
                }
            ],
            "supported_task_types": ["trip_planning_v1", "generic_orchestration"]
        }


# Create a singleton instance
itinerary_agent = ItineraryPlannerAgent()
