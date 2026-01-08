"""
A2A Protocol Types

This module defines the core types used in the Agent-to-Agent (A2A) protocol
for communication between agents.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    """Status of a task in the A2A protocol"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRequest(BaseModel):
    """
    A2A Task Request
    
    Represents a request to perform a task, sent from one agent to another.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = Field(..., description="Description of the task to perform")
    task_type: str = Field(..., description="Type of task (e.g., 'flight_search', 'hotel_search')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskResponse(BaseModel):
    """
    A2A Task Response
    
    Represents the response from an agent after processing a task.
    """
    task_id: str = Field(..., description="ID of the original task")
    status: TaskStatus = Field(..., description="Current status of the task")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task result data")
    error: Optional[str] = Field(default=None, description="Error message if task failed")
    completed_at: Optional[datetime] = Field(default=None)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AgentCapability(BaseModel):
    """Describes a capability of an agent"""
    name: str
    description: str
    task_types: List[str] = Field(default_factory=list)


class AgentCard(BaseModel):
    """
    Agent Card - Agent Discovery Metadata
    
    This is exposed at /.well-known/agent.json for agent discovery.
    """
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of what the agent does")
    version: str = Field(default="1.0.0")
    url: str = Field(..., description="Base URL of the agent")
    capabilities: List[AgentCapability] = Field(default_factory=list)
    supported_task_types: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Flight Search Agent",
                "description": "Searches for flights based on origin, destination, and dates",
                "version": "1.0.0",
                "url": "http://localhost:8000",
                "capabilities": [
                    {
                        "name": "flight_search",
                        "description": "Search for flights",
                        "task_types": ["flight_search_v1"]
                    }
                ],
                "supported_task_types": ["flight_search_v1"]
            }
        }
