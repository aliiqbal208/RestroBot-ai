"""Menu and ordering tools for RestroBot."""

from collections.abc import Iterable
from typing import Dict, List, Optional
from langchain_core.tools import tool
from .database import (
    get_menu_from_db,
    create_order,
    add_order_item,
    get_order_summary,
    update_order_status
)

# In-memory order state for the current conversation
current_order: Dict = {
    "order_id": None,
    "items": [],  # List of dicts: {"name": str, "quantity": int, "modifiers": list, "notes": str}
    "customer_info": {}
}


@tool
def get_menu() -> str:
    """Provide the latest up-to-date restaurant menu from the database."""
    return get_menu_from_db()


@tool
def add_to_order(item: str, modifiers: Iterable[str] = None, quantity: int = 1, special_instructions: str = None) -> str:
    """Adds a menu item to the customer's order with optional modifiers.
    
    Args:
        item: The name of the menu item (e.g., "Margherita Pizza", "Caesar Salad", "Iced Tea")
        modifiers: List of modifications like spice level, dietary options, or custom requests
                  Examples: ["extra cheese", "medium spicy", "no onions", "vegan"]
        quantity: Number of this item (default: 1)
        special_instructions: Any special instructions for this item
    
    Returns:
        The updated order in progress showing all items.
    
    Examples:
        - add_to_order("Margherita Pizza", ["extra cheese", "extra crispy"], 2)
        - add_to_order("Caesar Salad", ["no croutons"])
        - add_to_order("Iced Tea", ["peach", "less sugar"], 1, "Extra ice")
    """
    global current_order
    
    modifiers_list = list(modifiers) if modifiers else []
    
    # Add to in-memory order
    current_order["items"].append({
        "name": item,
        "quantity": quantity,
        "modifiers": modifiers_list,
        "special_instructions": special_instructions
    })
    
    # Return current order state
    order_text = "Current order:\n"
    for idx, order_item in enumerate(current_order["items"], 1):
        order_text += f"{idx}. {order_item['quantity']}x {order_item['name']}"
        if order_item['modifiers']:
            order_text += f" ({', '.join(order_item['modifiers'])})"
        if order_item['special_instructions']:
            order_text += f" - Note: {order_item['special_instructions']}"
        order_text += "\n"
    
    return order_text


@tool
def confirm_order() -> str:
    """Asks the customer if the order is correct.

    Returns:
      The user's free-text response.
    """
    return "Is this order correct? You can say 'yes' to confirm, or let me know if you'd like to make any changes."


@tool
def get_order() -> str:
    """Returns the users order so far. One item per line."""
    global current_order
    
    if not current_order["items"]:
        return "Your order is currently empty."
    
    order_text = "Your current order:\n"
    for idx, item in enumerate(current_order["items"], 1):
        order_text += f"{idx}. {item['quantity']}x {item['name']}"
        if item['modifiers']:
            order_text += f" ({', '.join(item['modifiers'])})"
        if item['special_instructions']:
            order_text += f" - Note: {item['special_instructions']}"
        order_text += "\n"
    
    return order_text


@tool
def clear_order():
    """Removes all items from the user's order."""
    global current_order
    current_order = {
        "order_id": None,
        "items": [],
        "customer_info": {}
    }
    return "Your order has been cleared."


@tool
def place_order(customer_name: str = None, customer_phone: str = None, 
                order_type: str = "dine-in", table_number: str = None) -> str:
    """Sends the order to the kitchen for preparation and saves it to the database.
    
    Args:
        customer_name: Customer's name (optional)
        customer_phone: Customer's phone number (optional)
        order_type: Type of order - "dine-in", "takeaway", or "delivery" (default: "dine-in")
        table_number: Table number for dine-in orders (optional)

    Returns:
        Order confirmation with order number and estimated time.
    """
    global current_order
    
    if not current_order["items"]:
        return "Cannot place order - your order is empty. Please add some items first."
    
    # Create order in database
    order_id = create_order(
        customer_name=customer_name,
        customer_phone=customer_phone,
        order_type=order_type,
        table_number=table_number,
        notes=None
    )
    
    if not order_id:
        return "Sorry, there was an error creating your order. Please try again."
    
    # Add all items to the order
    success_count = 0
    for item in current_order["items"]:
        if add_order_item(
            order_id=order_id,
            item_name=item["name"],
            quantity=item["quantity"],
            modifiers=item["modifiers"],
            special_instructions=item["special_instructions"]
        ):
            success_count += 1
    
    if success_count == 0:
        return "Sorry, none of the items could be added to your order. Please check the menu and try again."
    
    # Update order status to confirmed
    update_order_status(order_id, "confirmed")
    
    # Get order summary
    summary = get_order_summary(order_id)
    
    # Store order ID and clear current order
    current_order["order_id"] = order_id
    current_order["items"] = []
    
    # Calculate estimated time (5-10 minutes per item, max 45 minutes)
    estimated_minutes = min(success_count * 7 + 10, 45)
    
    result = summary + f"\n✓ Your order has been sent to the kitchen!\n"
    result += f"Estimated preparation time: {estimated_minutes} minutes\n"
    result += "\nThank you for your order! 🍽️"
    
    return result

