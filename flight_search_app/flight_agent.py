"""
Flight Search Agent

ADK-based agent that uses MCP to search for flights.
Uses Google's Gemini model for reasoning.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("FLIGHT_AGENT")
logger.setLevel(logging.DEBUG)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class FlightSearchAgent:
    """
    Flight Search Agent using Google Gemini.
    
    This agent processes flight search requests and uses the Flight MCP Server
    to fetch flight data.
    """
    
    def __init__(self):
        """Initialize the Flight Search Agent."""
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.name = "Flight Search Agent"
        self.description = "Searches for flights based on origin, destination, and dates"
        
        logger.info("=" * 50)
        logger.info(f"✈️  {self.name} initialized")
        logger.info("=" * 50)
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        date: str,
        passengers: int = 1
    ) -> Dict[str, Any]:
        """
        Search for flights using mock data.
        
        In production, this would connect to an actual MCP server or API.
        """
        logger.info(f"   🔍 Calling MCP Server: search_flights({origin}, {destination}, {date})")
        
        # Generate mock flight data (simulating MCP server response)
        from mcp_servers.flight_mcp_server import generate_mock_flights
        
        flights = generate_mock_flights(origin, destination, date, passengers)
        
        logger.info(f"   📊 MCP Server returned {len(flights)} flights")
        
        return {
            "status": "success",
            "query": {
                "origin": origin,
                "destination": destination,
                "date": date,
                "passengers": passengers
            },
            "results_count": len(flights),
            "flights": flights
        }
    
    async def process_request(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a flight search request.
        
        Args:
            task_description: Description of the search request
            parameters: Search parameters (origin, destination, date, etc.)
            
        Returns:
            Search results with flight options
        """
        logger.info("")
        logger.info("=" * 50)
        logger.info("✈️  FLIGHT SEARCH REQUEST RECEIVED")
        logger.info("=" * 50)
        logger.info(f"   Task Description: \"{task_description}\"")
        logger.info(f"   Received Parameters: {parameters}")
        
        try:
            # Extract parameters
            origin = parameters.get("origin", "")
            destination = parameters.get("destination", "")
            date = parameters.get("date", "")
            passengers = parameters.get("passengers", 1)
            
            # If parameters are missing, use Gemini to extract them from description
            if not origin or not destination or not date:
                logger.info("")
                logger.info("   🤖 PARSING TASK DESCRIPTION WITH GEMINI")
                logger.info("   -" * 20)
                logger.info("   ⚠️ Parameters missing, extracting from description...")
                
                extraction_prompt = f"""
                Extract flight search parameters from this request:
                "{task_description}"
                
                Today is {datetime.now().strftime('%Y-%m-%d')}.
                
                Return a JSON object with:
                - origin: 3-letter airport code (convert city names to airport codes)
                - destination: 3-letter airport code (convert city names to airport codes)
                - date: date in YYYY-MM-DD format
                - passengers: number of passengers (default 1)
                
                Only return the JSON, no other text.
                """
                
                logger.info("   📤 Sending extraction request to Gemini...")
                response = self.model.generate_content(extraction_prompt)
                
                try:
                    extracted = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
                    origin = extracted.get("origin", origin)
                    destination = extracted.get("destination", destination)
                    date = extracted.get("date", date)
                    passengers = extracted.get("passengers", passengers)
                    
                    logger.info(f"   ✅ Gemini extracted parameters:")
                    logger.info(f"      Origin: {origin}")
                    logger.info(f"      Destination: {destination}")
                    logger.info(f"      Date: {date}")
                    logger.info(f"      Passengers: {passengers}")
                    
                except json.JSONDecodeError:
                    logger.warning("   ⚠️ Failed to parse Gemini response")
            
            # Search for flights
            logger.info("")
            logger.info("   🔍 CALLING MCP SERVER")
            logger.info("   -" * 20)
            
            search_results = await self.search_flights(origin, destination, date, passengers)
            
            # Log flight results
            logger.info(f"   📋 Search Results:")
            for i, flight in enumerate(search_results['flights'][:3]):
                logger.info(f"      {i+1}. {flight['airline']} - ${flight['price']} - {flight['departure_time']}")
            
            # Use Gemini to format a nice response
            logger.info("")
            logger.info("   🤖 FORMATTING RESPONSE WITH GEMINI")
            logger.info("   -" * 20)
            
            format_prompt = f"""
            Format these flight search results into a helpful summary:
            
            Query: Flights from {origin} to {destination} on {date}
            
            Results:
            {json.dumps(search_results['flights'][:3], indent=2)}
            
            Provide a brief, friendly summary of the top 3 options with prices.
            """
            
            response = self.model.generate_content(format_prompt)
            summary = response.text
            
            logger.info("   ✅ Response formatted successfully")
            logger.info("")
            logger.info("=" * 50)
            logger.info("✅ FLIGHT SEARCH COMPLETE")
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
                    "name": "flight_search",
                    "description": "Search for flights between airports",
                    "task_types": ["flight_search_v1"]
                }
            ],
            "supported_task_types": ["flight_search_v1"]
        }


# Create a singleton instance
flight_agent = FlightSearchAgent()
