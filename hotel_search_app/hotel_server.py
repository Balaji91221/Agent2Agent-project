"""
Hotel Search A2A Server

Exposes the Hotel Search Agent as an A2A-compatible endpoint.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.server import A2AServer
from common.types import TaskRequest, TaskResponse, TaskStatus, AgentCard, AgentCapability
from hotel_search_app.hotel_agent import hotel_agent


# Define the agent card
agent_card = AgentCard(
    name="Hotel Search Agent",
    description="Searches for hotels based on location and travel dates. Uses OpenAI GPT-4o for intelligent query processing.",
    version="1.0.0",
    url="http://localhost:8003",
    capabilities=[
        AgentCapability(
            name="hotel_search",
            description="Search for hotels in a location",
            task_types=["hotel_search_v1"]
        )
    ],
    supported_task_types=["hotel_search_v1"]
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
        result = await hotel_agent.process_request(
            task_description=task.description,
            parameters=task.parameters
        )
        
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
    
    server.run(host="0.0.0.0", port=8003)
