"""
A2A Client

HTTP client for communicating with other A2A-compatible agents.
"""

import httpx
import logging
from typing import Optional, Dict, Any

from common.types import TaskRequest, TaskResponse, TaskStatus, AgentCard


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("A2A_CLIENT")


class A2AClient:
    """
    A2A Protocol Client
    
    Sends tasks to other A2A-compatible agents and handles responses.
    """
    
    def __init__(self, base_url: str, timeout: float = 60.0):
        """
        Initialize the A2A client.
        
        Args:
            base_url: Base URL of the target agent (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_agent_card(self) -> Optional[AgentCard]:
        """
        Fetch the agent card for discovery.
        
        Returns:
            AgentCard if available, None otherwise
        """
        try:
            logger.debug(f"📋 Fetching agent card from {self.base_url}/.well-known/agent.json")
            response = await self.client.get(f"{self.base_url}/.well-known/agent.json")
            response.raise_for_status()
            card = AgentCard(**response.json())
            logger.debug(f"✅ Agent card received: {card.name}")
            return card
        except Exception as e:
            logger.error(f"❌ Failed to fetch agent card from {self.base_url}: {e}")
            return None
    
    async def send_task(self, task: TaskRequest) -> TaskResponse:
        """
        Send a task to the target agent.
        
        Args:
            task: The task request to send
            
        Returns:
            TaskResponse with the result or error
        """
        try:
            logger.info(f"📤 A2A Request → {self.base_url}/tasks")
            logger.info(f"   Task ID: {task.id}")
            logger.info(f"   Task Type: {task.task_type}")
            logger.info(f"   Description: {task.description[:60]}...")
            
            response = await self.client.post(
                f"{self.base_url}/tasks",
                json=task.model_dump(mode='json')
            )
            response.raise_for_status()
            
            task_response = TaskResponse(**response.json())
            
            logger.info(f"📥 A2A Response ← {self.base_url}")
            logger.info(f"   Status: {task_response.status}")
            
            return task_response
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error sending task: {e}")
            return TaskResponse(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=f"HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"❌ Error sending task: {e}")
            return TaskResponse(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
    
    async def send_task_simple(
        self,
        description: str,
        task_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> TaskResponse:
        """
        Simplified method to send a task.
        
        Args:
            description: Task description
            task_type: Type of task
            parameters: Optional task parameters
            
        Returns:
            TaskResponse with the result
        """
        task = TaskRequest(
            description=description,
            task_type=task_type,
            parameters=parameters or {}
        )
        return await self.send_task(task)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
