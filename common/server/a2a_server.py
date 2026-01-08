"""
A2A Server

FastAPI-based server for handling A2A protocol requests.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Awaitable, Optional
import logging
import uvicorn

from common.types import TaskRequest, TaskResponse, TaskStatus, AgentCard


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("A2A_SERVER")


class A2AServer:
    """
    A2A Protocol Server
    
    Wraps a FastAPI application to expose A2A-compatible endpoints.
    """
    
    def __init__(
        self,
        agent_card: AgentCard,
        task_handler: Callable[[TaskRequest], Awaitable[TaskResponse]]
    ):
        """
        Initialize the A2A server.
        
        Args:
            agent_card: The agent's metadata card
            task_handler: Async function to handle incoming tasks
        """
        self.agent_card = agent_card
        self.task_handler = task_handler
        self.app = self._create_app()
        
        logger.info(f"🖥️  A2A Server configured for: {agent_card.name}")
    
    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title=self.agent_card.name,
            description=self.agent_card.description,
            version=self.agent_card.version
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app: FastAPI):
        """Register A2A protocol routes."""
        
        @app.get("/.well-known/agent.json")
        async def get_agent_card():
            """Agent discovery endpoint."""
            logger.info(f"📋 Agent card requested for: {self.agent_card.name}")
            return self.agent_card.model_dump()
        
        @app.post("/tasks", response_model=TaskResponse)
        async def handle_task(task: TaskRequest):
            """
            Handle incoming task requests.
            
            This is the main endpoint for A2A communication.
            """
            logger.info("")
            logger.info(f"📥 INCOMING A2A TASK")
            logger.info(f"   Agent: {self.agent_card.name}")
            logger.info(f"   Task ID: {task.id}")
            logger.info(f"   Task Type: {task.task_type}")
            logger.info(f"   Description: {task.description[:80]}...")
            
            try:
                response = await self.task_handler(task)
                
                logger.info(f"📤 TASK RESPONSE")
                logger.info(f"   Status: {response.status}")
                
                return response
            except Exception as e:
                logger.error(f"❌ Error handling task {task.id}: {e}")
                return TaskResponse(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error=str(e)
                )
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "agent": self.agent_card.name}
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        logger.info(f"🚀 Starting {self.agent_card.name} on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application for ASGI servers."""
        return self.app
