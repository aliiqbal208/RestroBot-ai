"""State definition for RestroBot conversation."""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class OrderState(TypedDict):
    """State representing the customer's order conversation.
    
    Attributes:
        messages: Chat conversation history with add_messages annotation
                 to append new messages instead of replacing them
        order: List of ordered items with their modifiers
        finished: Flag indicating if the order is placed and session should end
    """
    messages: Annotated[list, add_messages]
    order: list[str]
    finished: bool
