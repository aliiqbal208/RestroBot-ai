"""Graph builder for RestroBot conversation flow."""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from .state import OrderState
from .tools import get_menu, add_to_order, confirm_order, get_order, clear_order, place_order
from .nodes import (
    chatbot_with_tools,
    human_node,
    order_node,
    maybe_route_to_tools,
    maybe_exit_human_node
)
from .config import LLM_MODEL, LLM_TEMPERATURE


def build_graph():
    """Build and compile the RestroBot conversation graph.
    
    Returns:
        Compiled LangGraph ready for execution
    """
    # Initialize the LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    # Auto-tools will be invoked automatically by the ToolNode
    auto_tools = [get_menu]
    tool_node = ToolNode(auto_tools)

    # Order-tools will be handled by the order node
    order_tools = [add_to_order, confirm_order, get_order, clear_order, place_order]

    # Bind all tools to the LLM
    llm_with_tools = llm.bind_tools(auto_tools + order_tools)

    # Create wrapper function with llm_with_tools
    def chatbot_node(state: OrderState) -> OrderState:
        return chatbot_with_tools(state, llm_with_tools)

    # Create routing function with tool_node tools
    def route_to_tools(state: OrderState) -> str:
        return maybe_route_to_tools(state, tool_node.tools_by_name)

    # Build the graph
    graph_builder = StateGraph(OrderState)

    # Add nodes
    graph_builder.add_node("chatbot", chatbot_node)
    graph_builder.add_node("human", human_node)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_node("ordering", order_node)

    # Define edges
    # Chatbot -> {ordering, tools, human, END}
    graph_builder.add_conditional_edges("chatbot", route_to_tools)
    # Human -> {chatbot, END}
    graph_builder.add_conditional_edges("human", maybe_exit_human_node)

    # Tools always route back to chatbot
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge("ordering", "chatbot")

    # Start at chatbot
    graph_builder.add_edge(START, "chatbot")

    return graph_builder.compile()
