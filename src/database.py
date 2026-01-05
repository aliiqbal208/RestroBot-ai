"""Database connection and queries for RestroBot."""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from contextlib import contextmanager


def get_database_url() -> str:
    """Get database URL from environment variable."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://restrobot:restrobot_pass@localhost:5432/restrobot"
    )


def create_db_engine() -> Engine:
    """Create SQLAlchemy engine for database connection."""
    return create_engine(get_database_url(), pool_pre_ping=True)


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    engine = create_db_engine()
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()
        engine.dispose()


def get_menu_from_db() -> str:
    """Fetch the complete menu from the database and format it as a string.
    
    Returns:
        Formatted menu string with categories, items, modifiers, and specials
    """
    try:
        with get_db_connection() as conn:
            # Get menu items by category
            menu_query = text("""
                SELECT 
                    c.name as category,
                    c.display_order,
                    m.name as item_name,
                    m.description,
                    m.price,
                    m.available
                FROM categories c
                JOIN menu_items m ON c.id = m.category_id
                WHERE m.available = true
                ORDER BY c.display_order, m.name
            """)
            
            menu_items = conn.execute(menu_query).fetchall()
            
            # Get modifiers
            modifiers_query = text("""
                SELECT name, type, description
                FROM modifiers
                ORDER BY type, name
            """)
            
            modifiers = conn.execute(modifiers_query).fetchall()
            
            # Get specials
            specials_query = text("""
                SELECT title, description
                FROM specials
                WHERE active = true
            """)
            
            specials = conn.execute(specials_query).fetchall()
            
            # Get out of stock items
            out_of_stock_query = text("""
                SELECT item_name
                FROM out_of_stock
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            out_of_stock = conn.execute(out_of_stock_query).fetchall()
            
        # Format the menu
        menu_text = "RESTAURANT MENU:\n\n"
        
        # Group items by category
        current_category = None
        for item in menu_items:
            if current_category != item.category:
                current_category = item.category
                menu_text += f"    {current_category}:\n"
            
            # Format item with price if available
            item_line = f"    - {item.item_name}"
            if item.price:
                item_line += f" (${item.price:.2f})"
            if item.description:
                item_line += f" - {item.description}"
            menu_text += item_line + "\n"
        
        # Add modifiers section
        if modifiers:
            menu_text += "\n    Modifiers & Notes:\n"
            
            # Group modifiers by type
            modifier_types = {}
            for mod in modifiers:
                if mod.type not in modifier_types:
                    modifier_types[mod.type] = []
                modifier_types[mod.type].append(mod.name)
            
            # Format each type
            type_labels = {
                'spice_level': 'Spice Level',
                'dietary': 'Dietary Options',
                'addon': 'Add-ons',
                'custom': 'Custom Requests'
            }
            
            for mod_type, items in modifier_types.items():
                label = type_labels.get(mod_type, mod_type.title())
                menu_text += f"    - {label}: {', '.join(items)}\n"
        
        # Add specials
        if specials:
            menu_text += "\n    Specials:\n"
            for special in specials:
                menu_text += f"    - \"{special.title}\""
                if special.description:
                    menu_text += f" - {special.description}"
                menu_text += "\n"
        
        # Add out of stock notice
        if out_of_stock:
            items_list = ', '.join([item.item_name for item in out_of_stock])
            menu_text += f"\n    *Note: Today we are out of stock on {items_list}.\n"
        
        return menu_text
        
    except Exception as e:
        print(f"Error fetching menu from database: {e}")
        # Return a fallback message
        return """
        RESTAURANT MENU:
        
        Unable to load menu from database. Please try again later.
        """


def test_db_connection() -> bool:
    """Test if database connection is working.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            return result is not None
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False


def get_menu_item_by_name(item_name: str) -> Optional[Dict]:
    """Get a specific menu item by name.
    
    Args:
        item_name: Name of the menu item
        
    Returns:
        Dictionary with item details or None if not found
    """
    try:
        with get_db_connection() as conn:
            query = text("""
                SELECT 
                    m.id, m.name, m.description, m.price, m.available,
                    c.name as category
                FROM menu_items m
                JOIN categories c ON m.category_id = c.id
                WHERE LOWER(m.name) = LOWER(:item_name)
                AND m.available = true
            """)
            
            result = conn.execute(query, {"item_name": item_name}).fetchone()
            
            if result:
                return {
                    "id": result.id,
                    "name": result.name,
                    "description": result.description,
                    "price": float(result.price) if result.price else None,
                    "category": result.category,
                    "available": result.available
                }
            return None
            
    except Exception as e:
        print(f"Error fetching menu item: {e}")
        return None


def generate_order_number() -> str:
    """Generate a unique order number.
    
    Returns:
        Order number in format ORD-YYYYMMDD-XXXX
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"ORD-{timestamp}"


def create_order(
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    order_type: str = "dine-in",
    table_number: Optional[str] = None,
    notes: Optional[str] = None
) -> Optional[int]:
    """Create a new order in the database.
    
    Args:
        customer_name: Customer's name
        customer_phone: Customer's phone number
        order_type: Type of order (dine-in, takeaway, delivery)
        table_number: Table number for dine-in orders
        notes: Additional notes for the order
        
    Returns:
        Order ID if successful, None otherwise
    """
    try:
        with get_db_connection() as conn:
            order_number = generate_order_number()
            
            query = text("""
                INSERT INTO orders (
                    order_number, customer_name, customer_phone,
                    order_type, table_number, notes, status
                )
                VALUES (
                    :order_number, :customer_name, :customer_phone,
                    :order_type, :table_number, :notes, 'pending'
                )
                RETURNING id
            """)
            
            result = conn.execute(query, {
                "order_number": order_number,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "order_type": order_type,
                "table_number": table_number,
                "notes": notes
            })
            
            conn.commit()
            order_id = result.fetchone()[0]
            print(f"✓ Order created: {order_number} (ID: {order_id})")
            return order_id
            
    except Exception as e:
        print(f"Error creating order: {e}")
        return None


def add_order_item(
    order_id: int,
    item_name: str,
    quantity: int = 1,
    modifiers: Optional[List[str]] = None,
    special_instructions: Optional[str] = None
) -> bool:
    """Add an item to an order.
    
    Args:
        order_id: ID of the order
        item_name: Name of the menu item
        quantity: Quantity of the item
        modifiers: List of modifiers (e.g., ["Medium Spicy", "No Onions"])
        special_instructions: Special instructions for this item
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            # First, get the menu item details
            item_query = text("""
                SELECT id, name, price
                FROM menu_items
                WHERE LOWER(name) = LOWER(:item_name)
                AND available = true
            """)
            
            item_result = conn.execute(item_query, {"item_name": item_name}).fetchone()
            
            if not item_result:
                print(f"✗ Item '{item_name}' not found or unavailable")
                return False
            
            menu_item_id = item_result.id
            item_name_db = item_result.name
            unit_price = float(item_result.price) if item_result.price else 0.00
            subtotal = unit_price * quantity
            
            # Convert modifiers list to JSON string
            modifiers_json = json.dumps(modifiers) if modifiers else None
            
            # Insert order item
            insert_query = text("""
                INSERT INTO order_items (
                    order_id, menu_item_id, item_name, quantity,
                    unit_price, subtotal, modifiers, special_instructions
                )
                VALUES (
                    :order_id, :menu_item_id, :item_name, :quantity,
                    :unit_price, :subtotal, :modifiers, :special_instructions
                )
            """)
            
            conn.execute(insert_query, {
                "order_id": order_id,
                "menu_item_id": menu_item_id,
                "item_name": item_name_db,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "modifiers": modifiers_json,
                "special_instructions": special_instructions
            })
            
            conn.commit()
            print(f"✓ Added {quantity}x {item_name_db} @ ${unit_price:.2f} = ${subtotal:.2f}")
            return True
            
    except Exception as e:
        print(f"Error adding order item: {e}")
        return False


def get_order_details(order_id: int) -> Optional[Dict]:
    """Get complete order details including items.
    
    Args:
        order_id: ID of the order
        
    Returns:
        Dictionary with order details or None if not found
    """
    try:
        with get_db_connection() as conn:
            # Get order info
            order_query = text("""
                SELECT 
                    id, order_number, customer_name, customer_phone,
                    order_type, table_number, status, total_amount,
                    notes, created_at
                FROM orders
                WHERE id = :order_id
            """)
            
            order = conn.execute(order_query, {"order_id": order_id}).fetchone()
            
            if not order:
                return None
            
            # Get order items
            items_query = text("""
                SELECT 
                    item_name, quantity, unit_price, subtotal,
                    modifiers, special_instructions
                FROM order_items
                WHERE order_id = :order_id
                ORDER BY id
            """)
            
            items = conn.execute(items_query, {"order_id": order_id}).fetchall()
            
            # Format the response
            order_details = {
                "order_id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "order_type": order.order_type,
                "table_number": order.table_number,
                "status": order.status,
                "total_amount": float(order.total_amount),
                "notes": order.notes,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "items": []
            }
            
            for item in items:
                modifiers_list = json.loads(item.modifiers) if item.modifiers else []
                order_details["items"].append({
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "subtotal": float(item.subtotal),
                    "modifiers": modifiers_list,
                    "special_instructions": item.special_instructions
                })
            
            return order_details
            
    except Exception as e:
        print(f"Error fetching order details: {e}")
        return None


def get_order_summary(order_id: int) -> str:
    """Get a formatted summary of an order.
    
    Args:
        order_id: ID of the order
        
    Returns:
        Formatted order summary string
    """
    order = get_order_details(order_id)
    
    if not order:
        return "Order not found."
    
    summary = f"\n{'='*50}\n"
    summary += f"ORDER CONFIRMATION\n"
    summary += f"{'='*50}\n\n"
    summary += f"Order Number: {order['order_number']}\n"
    
    if order['customer_name']:
        summary += f"Customer: {order['customer_name']}\n"
    
    if order['customer_phone']:
        summary += f"Phone: {order['customer_phone']}\n"
    
    summary += f"Type: {order['order_type'].title()}\n"
    
    if order['table_number']:
        summary += f"Table: {order['table_number']}\n"
    
    summary += f"Status: {order['status'].upper()}\n"
    summary += f"\n{'='*50}\n"
    summary += "ITEMS:\n"
    summary += f"{'='*50}\n\n"
    
    for item in order['items']:
        summary += f"{item['quantity']}x {item['item_name']}"
        summary += f" @ ${item['unit_price']:.2f} = ${item['subtotal']:.2f}\n"
        
        if item['modifiers']:
            summary += f"   Modifiers: {', '.join(item['modifiers'])}\n"
        
        if item['special_instructions']:
            summary += f"   Note: {item['special_instructions']}\n"
        
        summary += "\n"
    
    summary += f"{'='*50}\n"
    summary += f"TOTAL: ${order['total_amount']:.2f}\n"
    summary += f"{'='*50}\n"
    
    if order['notes']:
        summary += f"\nOrder Notes: {order['notes']}\n"
    
    return summary


def update_order_status(order_id: int, status: str) -> bool:
    """Update the status of an order.
    
    Args:
        order_id: ID of the order
        status: New status (pending, confirmed, preparing, ready, completed, cancelled)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            query = text("""
                UPDATE orders
                SET status = :status,
                    completed_at = CASE WHEN :status = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE id = :order_id
            """)
            
            conn.execute(query, {"order_id": order_id, "status": status})
            conn.commit()
            print(f"✓ Order #{order_id} status updated to: {status}")
            return True
            
    except Exception as e:
        print(f"Error updating order status: {e}")
        return False

