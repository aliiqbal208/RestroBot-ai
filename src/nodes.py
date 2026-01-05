"""Graph nodes for RestroBot conversation flow."""

from random import randint
from typing import Literal

from langchain_core.messages.ai import AIMessage
from langchain_core.messages.tool import ToolMessage
from langgraph.graph import END

from .state import OrderState
from .config import WELCOME_MSG
from . import tools  # Import tools module


def human_node(state: OrderState) -> OrderState:
    """Display the last model message to the user, and receive the user's input.
    
    Args:
        state: Current conversation state
        
    Returns:
        Updated state with user's input message
    """
    last_msg = state["messages"][-1]
    print("Model:", last_msg.content)

    user_input = input("User: ")

    # If it looks like the user is trying to quit, flag the conversation as over
    if user_input in {"q", "quit", "exit", "goodbye"}:
        state["finished"] = True

    return state | {"messages": [("user", user_input)]}


def order_node(state: OrderState) -> OrderState:
    """Handle order management operations.
    
    This node processes all order-related tool calls by invoking the actual tool functions.
    
    Args:
        state: Current conversation state
        
    Returns:
        Updated state with order modifications and tool responses
    """
    tool_msg = state.get("messages", [])[-1]
    order = state.get("order", [])
    outbound_msgs = []
    order_placed = False

    for tool_call in tool_msg.tool_calls:
        try:
            if tool_call["name"] == "add_to_order":
                # Call the actual add_to_order tool
                response = tools.add_to_order.invoke(tool_call["args"])

            elif tool_call["name"] == "confirm_order":
                # Call the actual confirm_order tool
                response = tools.confirm_order.invoke(tool_call["args"])

            elif tool_call["name"] == "get_order":
                # Call the actual get_order tool
                response = tools.get_order.invoke(tool_call["args"])

            elif tool_call["name"] == "clear_order":
                # Call the actual clear_order tool
                response = tools.clear_order.invoke(tool_call["args"])

            elif tool_call["name"] == "place_order":
                # Call the actual place_order tool
                response = tools.place_order.invoke(tool_call["args"])
                order_placed = True

            else:
                raise NotImplementedError(f'Unknown tool call: {tool_call["name"]}')

            # Record the tool results as tool messages
            outbound_msgs.append(
                ToolMessage(
                    content=str(response) if response is not None else "",
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"Error executing {tool_call['name']}: {str(e)}"
            print(f"Tool execution error: {error_msg}")
            outbound_msgs.append(
                ToolMessage(
                    content=error_msg,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

    return {"messages": outbound_msgs, "order": order, "finished": order_placed}


def chatbot_with_tools(state: OrderState, llm_with_tools) -> OrderState:
    """Execute the chatbot with tool-calling capabilities.
    
    Args:
        state: Current conversation state
        llm_with_tools: LLM instance with tools bound
        
    Returns:
        Updated state with chatbot's response
    """
    from .config import RESTROBOT_SYSINT
    
    defaults = {"order": [], "finished": False}

    if state["messages"]:
        new_output = llm_with_tools.invoke([RESTROBOT_SYSINT] + state["messages"])
    else:
        new_output = AIMessage(content=WELCOME_MSG)

    return defaults | state | {"messages": [new_output]}


def maybe_route_to_tools(state: OrderState, tool_node_tools: dict) -> str:
    """Route between chat and tool nodes based on the last message.
    
    Args:
        state: Current conversation state
        tool_node_tools: Dictionary of available auto-tools
        
    Returns:
        Name of the next node to execute: "tools", "ordering", "human", or END
    """
    if not (msgs := state.get("messages", [])):
        raise ValueError(f"No messages found when parsing state: {state}")

    msg = msgs[-1]

    if state.get("finished", False):
        return END

    elif hasattr(msg, "tool_calls") and len(msg.tool_calls) > 0:
        # Route to appropriate tool handler
        if any(tool["name"] in tool_node_tools for tool in msg.tool_calls):
            return "tools"
        else:
            return "ordering"

    else:
        return "human"


def maybe_exit_human_node(state: OrderState) -> Literal["chatbot", "__end__"]:
    """Determine if conversation should continue or end.
    
    Args:
        state: Current conversation state
        
    Returns:
        "chatbot" to continue, END to finish
    """
    if state.get("finished", False):
        return END
    else:
        return "chatbot"
