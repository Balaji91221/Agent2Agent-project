"""
Itinerary Planner A2A Server

Exposes the Itinerary Planner Agent as an A2A-compatible endpoint.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.server import A2AServer
from common.types import TaskRequest, TaskResponse, TaskStatus, AgentCard, AgentCapability
from itinerary_planner.itinerary_agent import itinerary_agent


# Define the agent card
agent_card = AgentCard(
    name="Itinerary Planner Agent",
    description="Creates complete travel itineraries by orchestrating flight and hotel searches. Uses Google Gemini for intelligent planning and synthesis.",
    version="1.0.0",
    url="http://localhost:8005",
    capabilities=[
        AgentCapability(
            name="trip_planning",
            description="Plan complete travel itineraries with flights and hotels",
            task_types=["trip_planning_v1"]
        )
    ],
    supported_task_types=["trip_planning_v1"]
)


async def handle_task(task: TaskRequest) -> TaskResponse:
    """
    Handle incoming A2A task requests.
    
    Args:
        task: The incoming task request
        
    Returns:
        TaskResponse with the result
    """
    try:
        result = await itinerary_agent.plan_trip(task.description)
        
        return TaskResponse(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            result=result,
            completed_at=datetime.now()
        )
        
    except Exception as e:
        return TaskResponse(
            task_id=task.id,
            status=TaskStatus.FAILED,
            error=str(e)
        )


# Create the A2A server
server = A2AServer(agent_card=agent_card, task_handler=handle_task)
app = server.get_app()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    server.run(host="0.0.0.0", port=8005)
