"""
Flight MCP Server

Mock MCP server that provides flight search functionality.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from datetime import datetime, timedelta
import random


# Create the MCP server
server = Server("flight-search")


# Mock flight data generator
def generate_mock_flights(origin: str, destination: str, date: str, passengers: int = 1):
    """Generate mock flight data."""
    airlines = ["United Airlines", "Delta Air Lines", "American Airlines", "JetBlue", "Southwest"]
    
    flights = []
    base_price = random.randint(200, 800)
    
    for i in range(5):
        airline = airlines[i % len(airlines)]
        departure_hour = random.randint(6, 20)
        duration_hours = random.randint(2, 12)
        
        flight = {
            "flight_id": f"FL{random.randint(1000, 9999)}",
            "airline": airline,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": date,
            "departure_time": f"{departure_hour:02d}:{random.randint(0, 59):02d}",
            "arrival_time": f"{(departure_hour + duration_hours) % 24:02d}:{random.randint(0, 59):02d}",
            "duration": f"{duration_hours}h {random.randint(0, 59)}m",
            "price": base_price + random.randint(-100, 200),
            "currency": "USD",
            "seats_available": random.randint(1, 50),
            "class": "Economy",
            "stops": random.choice([0, 0, 0, 1, 1, 2])
        }
        flights.append(flight)
    
    return sorted(flights, key=lambda x: x["price"])


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="search_flights",
            description="Search for flights between two airports on a specific date",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin airport code (e.g., 'JFK', 'LAX')"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination airport code (e.g., 'CDG', 'LHR')"
                    },
                    "date": {
                        "type": "string",
                        "description": "Travel date in YYYY-MM-DD format"
                    },
                    "passengers": {
                        "type": "integer",
                        "description": "Number of passengers",
                        "default": 1
                    }
                },
                "required": ["origin", "destination", "date"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "search_flights":
        origin = arguments.get("origin", "")
        destination = arguments.get("destination", "")
        date = arguments.get("date", "")
        passengers = arguments.get("passengers", 1)
        
        flights = generate_mock_flights(origin, destination, date, passengers)
        
        result = {
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
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
