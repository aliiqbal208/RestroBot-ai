"""FastAPI backend for multi-user RestroBot - AI."""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

import sys
sys.path.append('/app')
from src.state import OrderState
from src.tools import get_menu, add_to_order, confirm_order, get_order, clear_order, place_order
from src.config import LLM_MODEL, LLM_TEMPERATURE, RESTROBOT_SYSINT, WELCOME_MSG
from src.database import test_db_connection


# Session storage (in production, use Redis or similar)
sessions: Dict[str, Dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("🚀 Starting RestroBot API...")
    
    # Test database connection
    if test_db_connection():
        print("✓ Database connected")
    else:
        print("✗ Database connection failed")
    
    yield
    
    print("Shutting down RestroBot - AI API...")


app = FastAPI(
    title="RestroBot - AI",
    description="AI-Powered Restaurant Ordering System",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class SessionCreate(BaseModel):
    """Create a new chat session."""
    customer_name: Optional[str] = None
    table_number: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message from user."""
    message: str
    session_id: str


class ChatResponse(BaseModel):
    """Response from bot."""
    message: str
    session_id: str
    order_items: List[str] = []
    finished: bool = False


class OrderPlacement(BaseModel):
    """Place order request."""
    session_id: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    order_type: str = "dine-in"
    table_number: Optional[str] = None


# Initialize LLM and tools
llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
auto_tools = [get_menu]
order_tools = [add_to_order, confirm_order, get_order, clear_order, place_order]
all_tools = auto_tools + order_tools
tool_node = ToolNode(all_tools)
llm_with_tools = llm.bind_tools(all_tools)


def create_session_graph():
    """Create a simplified graph for API usage."""
    from src.nodes import chatbot_with_tools
    from src.config import RESTROBOT_SYSINT
    
    def chatbot_node(state: OrderState) -> OrderState:
        """Chatbot node for API - processes messages with tools."""
        defaults = {"order": [], "finished": False}
        
        if state["messages"]:
            new_output = llm_with_tools.invoke([RESTROBOT_SYSINT] + state["messages"])
        else:
            new_output = AIMessage(content=WELCOME_MSG)
        
        return defaults | state | {"messages": [new_output]}
    
    def should_continue(state: OrderState) -> str:
        """Determine if we should continue to tools or end."""
        messages = state.get("messages", [])
        if not messages:
            return END
        
        last_message = messages[-1]
        
        # If the last message has tool calls, route to tools
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            return "tools"
        
        # Otherwise, we're done with this turn
        return END
    
    graph_builder = StateGraph(OrderState)
    graph_builder.add_node("chatbot", chatbot_node)
    graph_builder.add_node("tools", tool_node)
    
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", should_continue)
    graph_builder.add_edge("tools", "chatbot")
    
    return graph_builder.compile()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RestroBot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/session/create", response_model=Dict)
async def create_session(session_data: SessionCreate):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "customer_name": session_data.customer_name,
        "table_number": session_data.table_number,
        "messages": [],
        "order": [],
        "finished": False,
        "graph": create_session_graph()
    }
    
    return {
        "session_id": session_id,
        "welcome_message": WELCOME_MSG,
        "created_at": sessions[session_id]["created_at"]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(chat_msg: ChatMessage):
    """Send a message and get bot response."""
    session_id = chat_msg.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Add user message
    session["messages"].append(HumanMessage(content=chat_msg.message))
    
    # Run the graph
    state = {
        "messages": session["messages"],
        "order": session["order"],
        "finished": session["finished"]
    }
    
    try:
        # Invoke graph
        result = session["graph"].invoke(state)
        
        # Update session
        session["messages"] = result["messages"]
        session["order"] = result.get("order", [])
        session["finished"] = result.get("finished", False)
        
        # Get bot's last message
        last_message = result["messages"][-1]
        bot_response = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        return ChatResponse(
            message=bot_response,
            session_id=session_id,
            order_items=session["order"],
            finished=session["finished"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.get("/session/{session_id}/order")
async def get_session_order(session_id: str):
    """Get current order for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return {
        "session_id": session_id,
        "order": session["order"],
        "item_count": len(session["order"])
    }


@app.post("/order/place")
async def place_order_endpoint(order_data: OrderPlacement):
    """Place an order from a session."""
    session_id = order_data.session_id
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if not session["order"]:
        raise HTTPException(status_code=400, detail="No items in order")
    
    try:
        # Call the place_order tool directly
        result = place_order.invoke({
            "customer_name": order_data.customer_name or session.get("customer_name"),
            "customer_phone": order_data.customer_phone,
            "order_type": order_data.order_type,
            "table_number": order_data.table_number or session.get("table_number")
        })
        
        # Mark session as finished
        session["finished"] = True
        
        return {
            "success": True,
            "message": result,
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error placing order: {str(e)}")


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    
    return {"message": "Session deleted", "session_id": session_id}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = test_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/menu")
async def get_menu_endpoint():
    """Get the restaurant menu."""
    try:
        menu = get_menu.invoke({})
        return {
            "menu": menu,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching menu: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
