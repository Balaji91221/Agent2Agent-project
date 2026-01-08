"""
Hotel MCP Server

Mock MCP server that provides hotel search functionality.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import random


# Create the MCP server
server = Server("hotel-search")


# Mock hotel data generator
def generate_mock_hotels(location: str, check_in: str, check_out: str, guests: int = 2):
    """Generate mock hotel data."""
    hotel_names = [
        "Grand Palace Hotel",
        "The Ritz Carlton",
        "Marriott Luxury Suites",
        "Hilton Downtown",
        "Four Seasons Resort",
        "Hyatt Regency",
        "InterContinental",
        "Sheraton Premium"
    ]
    
    amenities_pool = [
        "Free WiFi", "Pool", "Spa", "Gym", "Restaurant",
        "Room Service", "Bar", "Business Center", "Parking",
        "Airport Shuttle", "Concierge", "Pet Friendly"
    ]
    
    hotels = []
    
    for i in range(6):
        base_price = random.randint(100, 500)
        hotel = {
            "hotel_id": f"HTL{random.randint(10000, 99999)}",
            "name": hotel_names[i % len(hotel_names)],
            "location": location,
            "address": f"{random.randint(100, 999)} Main Street, {location}",
            "star_rating": random.choice([3, 4, 4, 5, 5]),
            "user_rating": round(random.uniform(3.5, 5.0), 1),
            "review_count": random.randint(100, 5000),
            "check_in": check_in,
            "check_out": check_out,
            "price_per_night": base_price,
            "total_price": base_price * 3,  # Assuming 3 nights
            "currency": "USD",
            "room_type": random.choice(["Standard Room", "Deluxe Room", "Suite", "Junior Suite"]),
            "amenities": random.sample(amenities_pool, random.randint(4, 8)),
            "cancellation_policy": random.choice(["Free cancellation", "Non-refundable", "Flexible"]),
            "breakfast_included": random.choice([True, False])
        }
        hotels.append(hotel)
    
    return sorted(hotels, key=lambda x: x["price_per_night"])


@server.list_tools()
async def list_tools():
    """List available tools."""
    return [
        Tool(
            name="search_hotels",
            description="Search for hotels in a specific location for given dates",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or location to search for hotels (e.g., 'Paris', 'New York')"
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date in YYYY-MM-DD format"
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date in YYYY-MM-DD format"
                    },
                    "guests": {
                        "type": "integer",
                        "description": "Number of guests",
                        "default": 2
                    }
                },
                "required": ["location", "check_in", "check_out"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name == "search_hotels":
        location = arguments.get("location", "")
        check_in = arguments.get("check_in", "")
        check_out = arguments.get("check_out", "")
        guests = arguments.get("guests", 2)
        
        hotels = generate_mock_hotels(location, check_in, check_out, guests)
        
        result = {
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
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
