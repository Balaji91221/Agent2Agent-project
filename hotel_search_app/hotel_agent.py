"""
Hotel Search Agent

LangChain-based agent that uses MCP to search for hotels.
Uses OpenAI GPT-4o for reasoning.
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("HOTEL_AGENT")
logger.setLevel(logging.DEBUG)


class HotelSearchAgent:
    """
    Hotel Search Agent using LangChain and OpenAI.
    
    This agent processes hotel search requests and uses the Hotel MCP Server
    to fetch hotel data.
    """
    
    def __init__(self):
        """Initialize the Hotel Search Agent."""
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7
        )
        self.name = "Hotel Search Agent"
        self.description = "Searches for hotels based on location and dates"
        
        logger.info("=" * 50)
        logger.info(f"🏨 {self.name} initialized")
        logger.info("=" * 50)
    
    async def search_hotels(
        self,
        location: str,
        check_in: str,
        check_out: str,
        guests: int = 2
    ) -> Dict[str, Any]:
        """
        Search for hotels using mock data.
        
        In production, this would connect to an actual MCP server or API.
        """
        logger.info(f"   🔍 Calling MCP Server: search_hotels({location}, {check_in}, {check_out})")
        
        # Generate mock hotel data (simulating MCP server response)
        from mcp_servers.hotel_mcp_server import generate_mock_hotels
        
        hotels = generate_mock_hotels(location, check_in, check_out, guests)
        
        logger.info(f"   📊 MCP Server returned {len(hotels)} hotels")
        
        return {
            "status": "success",
            "query": {
                "location": location,
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests
            },
            "results_count": len(hotels),
            "hotels": hotels
        }
    
    async def process_request(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a hotel search request.
        
        Args:
            task_description: Description of the search request
            parameters: Search parameters (location, check_in, check_out, etc.)
            
        Returns:
            Search results with hotel options
        """
        logger.info("")
        logger.info("=" * 50)
        logger.info("🏨 HOTEL SEARCH REQUEST RECEIVED")
        logger.info("=" * 50)
        logger.info(f"   Task Description: \"{task_description}\"")
        logger.info(f"   Received Parameters: {parameters}")
        
        try:
            # Extract parameters
            location = parameters.get("location", "")
            check_in = parameters.get("check_in", "")
            check_out = parameters.get("check_out", "")
            guests = parameters.get("guests", 2)
            
            # If parameters are missing, use LLM to extract them from description
            if not location or not check_in or not check_out:
                logger.info("")
                logger.info("   🤖 PARSING TASK DESCRIPTION WITH GPT-4o")
                logger.info("   -" * 20)
                logger.info("   ⚠️ Parameters missing, extracting from description...")
                
                extraction_prompt = f"""
                Extract hotel search parameters from this request:
                "{task_description}"
                
                Today is {datetime.now().strftime('%Y-%m-%d')}.
                
                Return ONLY a JSON object (no markdown, no explanation) with:
                - location: city name
                - check_in: date in YYYY-MM-DD format
                - check_out: date in YYYY-MM-DD format
                - guests: number of guests (default 2)
                """
                
                messages = [
                    SystemMessage(content="You are a helpful assistant that extracts structured data from text. Return only valid JSON."),
                    HumanMessage(content=extraction_prompt)
                ]
                
                logger.info("   📤 Sending extraction request to GPT-4o...")
                response = self.llm.invoke(messages)
                
                try:
                    extracted = json.loads(response.content.strip().replace("```json", "").replace("```", ""))
                    location = extracted.get("location", location)
                    check_in = extracted.get("check_in", check_in)
                    check_out = extracted.get("check_out", check_out)
                    guests = extracted.get("guests", guests)
                    
                    logger.info(f"   ✅ GPT-4o extracted parameters:")
                    logger.info(f"      Location: {location}")
                    logger.info(f"      Check-in: {check_in}")
                    logger.info(f"      Check-out: {check_out}")
                    logger.info(f"      Guests: {guests}")
                    
                except json.JSONDecodeError:
                    logger.warning("   ⚠️ Failed to parse GPT-4o response")
            
            # Search for hotels
            logger.info("")
            logger.info("   🔍 CALLING MCP SERVER")
            logger.info("   -" * 20)
            
            search_results = await self.search_hotels(location, check_in, check_out, guests)
            
            # Log hotel results
            logger.info(f"   📋 Search Results:")
            for i, hotel in enumerate(search_results['hotels'][:3]):
                logger.info(f"      {i+1}. {hotel['name']} - ${hotel['price_per_night']}/night - {'⭐' * hotel['star_rating']}")
            
            # Use LLM to format a nice response
            logger.info("")
            logger.info("   🤖 FORMATTING RESPONSE WITH GPT-4o")
            logger.info("   -" * 20)
            
            format_prompt = f"""
            Format these hotel search results into a helpful summary:
            
            Query: Hotels in {location} from {check_in} to {check_out}
            
            Results:
            {json.dumps(search_results['hotels'][:3], indent=2)}
            
            Provide a brief, friendly summary of the top 3 options with prices and star ratings.
            """
            
            messages = [
                SystemMessage(content="You are a helpful travel assistant that summarizes hotel options."),
                HumanMessage(content=format_prompt)
            ]
            
            response = self.llm.invoke(messages)
            summary = response.content
            
            logger.info("   ✅ Response formatted successfully")
            logger.info("")
            logger.info("=" * 50)
            logger.info("✅ HOTEL SEARCH COMPLETE")
            logger.info("=" * 50)
            
            return {
                "status": "success",
                "summary": summary,
                "data": search_results,
                "agent": self.name
            }
            
        except Exception as e:
            logger.error(f"   ❌ Error processing request: {str(e)}")
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
                    "name": "hotel_search",
                    "description": "Search for hotels in a location",
                    "task_types": ["hotel_search_v1"]
                }
            ],
            "supported_task_types": ["hotel_search_v1"]
        }


# Create a singleton instance
hotel_agent = HotelSearchAgent()
