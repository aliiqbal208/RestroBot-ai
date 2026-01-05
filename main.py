#!/usr/bin/env python3
"""
RestroBot - AI: An interactive restaurant ordering system using LangGraph and OpenAI.

This is the main entry point for the CLI application.
"""

from src import check_api_key, check_database, build_graph, RECURSION_LIMIT


def main():
    """Run the RestroBot - AI ordering system."""
    # Check API key before starting
    check_api_key()
    
    # Check database connection
    check_database()
    
    print("=" * 70)
    print("RestroBot - AI | Restaurant Ordering System")
    print("=" * 70)
    print("=" * 70)
    print()
    
    # Build the conversation graph
    graph = build_graph()
    
    # Configuration for graph execution
    config = {"recursion_limit": RECURSION_LIMIT}
    
    try:
        # Run the conversation
        state = graph.invoke({"messages": []}, config)
        
        # Display results
        print("\n" + "=" * 70)
        print("Session Complete!")
        print("=" * 70)
        
        if state.get("order"):
            print("\nFinal Order:")
            for item in state["order"]:
                print(f"  - {item}")
                
    except KeyboardInterrupt:
        print("\n\nSession interrupted. Goodbye!")
        
    except Exception as e:
        print(f"\nError occurred: {e}")
        raise


if __name__ == "__main__":
    main()
