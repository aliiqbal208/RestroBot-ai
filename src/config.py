"""Configuration and environment setup for RestroBot - AI."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def check_api_key():
    """Check if OPENAI_API_KEY is set and exit if not."""
    if not os.getenv("OPENAI_API_KEY"):
        print("=" * 70)
        print("ERROR: OPENAI_API_KEY not found!")
        print("=" * 70)
        print("Please create a .env file in the project root with:")
        print("OPENAI_API_KEY=your-api-key-here")
        print()
        print("Or set it as an environment variable:")
        print("export OPENAI_API_KEY='your-key-here'")
        print("=" * 70)
        exit(1)


def check_database():
    """Check if database connection is working."""
    from .database import test_db_connection
    
    if not test_db_connection():
        print("=" * 70)
        print("WARNING: Database connection failed!")
        print("=" * 70)
        print("Make sure PostgreSQL is running and DATABASE_URL is set correctly.")
        print("Using Docker: docker-compose up -d db")
        print("=" * 70)
        # Don't exit, allow app to continue with degraded functionality


# System instruction for the bot
RESTROBOT_SYSINT = (
    "system",
    "You are RestroBot - AI, an intelligent restaurant ordering assistant. A human will talk to you about the "
    "available products you have and you will answer any questions about menu items (and only about "
    "menu items - no off-topic discussion, but you can chat about the products and their history). "
    "The customer will place an order for 1 or more items from the menu, which you will structure "
    "and send to the ordering system after confirming the order with the human. "
    "\n\n"
    "Add items to the customer's order with add_to_order, and reset the order with clear_order. "
    "To see the contents of the order so far, call get_order (this is shown to you, not the user) "
    "Always confirm_order with the user (double-check) before calling place_order. Calling confirm_order will "
    "display the order items to the user and returns their response to seeing the list. Their response may contain modifications. "
    "Always verify and respond with item and modifier names from the MENU before adding them to the order. "
    "If you are unsure an item or modifier matches those on the MENU, ask a question to clarify or redirect. "
    "You only have the modifiers listed on the menu. "
    "Once the customer has finished ordering items, Call confirm_order to ensure it is correct then make "
    "any necessary updates and then call place_order. Once place_order has returned, thank the user and "
    "say goodbye!"
    "\n\n"
    "If any of the tools are unavailable, you can break the fourth wall and tell the user that "
    "they have not implemented them yet and should keep reading to do so.",
)

# Welcome message
WELCOME_MSG = "Welcome to RestroBot - AI. Type `q` to quit. How may I serve you today?"

# LLM Configuration
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7
RECURSION_LIMIT = 100
