#!/usr/bin/env python3
"""Script to view orders from the database."""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection
from sqlalchemy import text


def view_recent_orders(days: int = 1):
    """View recent orders from the database.
    
    Args:
        days: Number of days to look back (default: 1)
    """
    print(f"\n{'='*70}")
    print(f"RECENT ORDERS (Last {days} day(s))")
    print(f"{'='*70}\n")
    
    try:
        with get_db_connection() as conn:
            query = text("""
                SELECT 
                    o.id,
                    o.order_number,
                    o.customer_name,
                    o.order_type,
                    o.table_number,
                    o.status,
                    o.total_amount,
                    o.created_at,
                    COUNT(oi.id) as item_count
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.created_at >= CURRENT_DATE - INTERVAL :days DAY
                GROUP BY o.id, o.order_number, o.customer_name, o.order_type, 
                         o.table_number, o.status, o.total_amount, o.created_at
                ORDER BY o.created_at DESC
            """)
            
            orders = conn.execute(query, {"days": str(days)}).fetchall()
            
            if not orders:
                print(f"No orders found in the last {days} day(s).")
                return
            
            for order in orders:
                print(f"Order #{order.id} - {order.order_number}")
                print(f"  Customer: {order.customer_name or 'N/A'}")
                print(f"  Type: {order.order_type.upper()}", end="")
                if order.table_number:
                    print(f" | Table: {order.table_number}", end="")
                print()
                print(f"  Status: {order.status.upper()}")
                print(f"  Items: {order.item_count}")
                print(f"  Total: ${order.total_amount:.2f}")
                print(f"  Time: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'-'*70}")
            
            print(f"\nTotal orders: {len(orders)}")
            
    except Exception as e:
        print(f"Error fetching orders: {e}")


def view_order_details(order_id: int):
    """View detailed information about a specific order.
    
    Args:
        order_id: ID of the order to view
    """
    print(f"\n{'='*70}")
    print(f"ORDER DETAILS - ID: {order_id}")
    print(f"{'='*70}\n")
    
    try:
        with get_db_connection() as conn:
            # Get order info
            order_query = text("""
                SELECT 
                    order_number, customer_name, customer_phone,
                    order_type, table_number, status, total_amount,
                    notes, created_at, updated_at, completed_at
                FROM orders
                WHERE id = :order_id
            """)
            
            order = conn.execute(order_query, {"order_id": order_id}).fetchone()
            
            if not order:
                print(f"Order #{order_id} not found.")
                return
            
            # Print order info
            print(f"Order Number: {order.order_number}")
            print(f"Customer: {order.customer_name or 'N/A'}")
            if order.customer_phone:
                print(f"Phone: {order.customer_phone}")
            print(f"Type: {order.order_type.upper()}")
            if order.table_number:
                print(f"Table: {order.table_number}")
            print(f"Status: {order.status.upper()}")
            print(f"Created: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if order.completed_at:
                print(f"Completed: {order.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if order.notes:
                print(f"Notes: {order.notes}")
            
            print(f"\n{'-'*70}")
            print("ORDER ITEMS:")
            print(f"{'-'*70}\n")
            
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
            
            for item in items:
                print(f"{item.quantity}x {item.item_name}")
                print(f"   Price: ${item.unit_price:.2f} each")
                print(f"   Subtotal: ${item.subtotal:.2f}")
                if item.modifiers:
                    print(f"   Modifiers: {item.modifiers}")
                if item.special_instructions:
                    print(f"   Instructions: {item.special_instructions}")
                print()
            
            print(f"{'-'*70}")
            print(f"TOTAL: ${order.total_amount:.2f}")
            print(f"{'='*70}\n")
            
    except Exception as e:
        print(f"Error fetching order details: {e}")


def view_sales_summary(days: int = 1):
    """View sales summary for the specified period.
    
    Args:
        days: Number of days to look back (default: 1)
    """
    print(f"\n{'='*70}")
    print(f"SALES SUMMARY (Last {days} day(s))")
    print(f"{'='*70}\n")
    
    try:
        with get_db_connection() as conn:
            query = text("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_sales,
                    AVG(total_amount) as average_order,
                    MIN(total_amount) as min_order,
                    MAX(total_amount) as max_order
                FROM orders
                WHERE created_at >= CURRENT_DATE - INTERVAL :days DAY
                AND status != 'cancelled'
            """)
            
            result = conn.execute(query, {"days": str(days)}).fetchone()
            
            print(f"Total Orders: {result.total_orders or 0}")
            print(f"Total Sales: ${result.total_sales or 0:.2f}")
            print(f"Average Order: ${result.average_order or 0:.2f}")
            print(f"Smallest Order: ${result.min_order or 0:.2f}")
            print(f"Largest Order: ${result.max_order or 0:.2f}")
            
            # Popular items
            print(f"\n{'-'*70}")
            print("TOP SELLING ITEMS:")
            print(f"{'-'*70}\n")
            
            popular_query = text("""
                SELECT 
                    oi.item_name,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.subtotal) as total_revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.created_at >= CURRENT_DATE - INTERVAL :days DAY
                AND o.status != 'cancelled'
                GROUP BY oi.item_name
                ORDER BY total_quantity DESC
                LIMIT 10
            """)
            
            popular = conn.execute(popular_query, {"days": str(days)}).fetchall()
            
            for idx, item in enumerate(popular, 1):
                print(f"{idx}. {item.item_name}")
                print(f"   Sold: {item.total_quantity} units")
                print(f"   Revenue: ${item.total_revenue:.2f}")
                print()
            
    except Exception as e:
        print(f"Error fetching sales summary: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View orders from RestroBot database")
    parser.add_argument("--days", type=int, default=1, help="Number of days to look back (default: 1)")
    parser.add_argument("--order-id", type=int, help="View specific order details")
    parser.add_argument("--summary", action="store_true", help="Show sales summary")
    
    args = parser.parse_args()
    
    if args.order_id:
        view_order_details(args.order_id)
    elif args.summary:
        view_sales_summary(args.days)
    else:
        view_recent_orders(args.days)
