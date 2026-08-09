from langchain_core.tools import tool


@tool
def get_products():
    """Get the list of available products."""
    
    return [
        {
            "name": "Wireless Mouse",
            "price": 25.99,
            "stock": 120
        },
        {
            "name": "Mechanical Keyboard",
            "price": 79.99,
            "stock": 5
        },
        {
            "name": "27-inch Monitor",
            "price": 249.99,
            "stock": 2
        }
    ]

@tool
def get_orders():
    """Get information about recent customer orders."""

    return [
        {
            "order_id": "ORD-001",
            "customer": "CUS-003",
            "product": "Wireless Mouse",
            "quantity": 2,
            "status": "completed"
        },
        {
            "order_id": "ORD-002",
            "customer": "CUS-003",
            "product": "Mechanical Keyboard",
            "quantity": 1,
            "status": "pending"
        },
        {
            "order_id": "ORD-003",
            "customer": "CUS-002",
            "product": "27-inch Monitor",
            "quantity": 1,
            "status": "shipped"
        }
    ]

@tool
def get_customers():
    """Get information about customers."""

    return [
        {
            "id": "CUS-001",
            "name": "Alice",
            "email": "alice@example.com"
        },
        {
            "id": "CUS-002",
            "name": "Bob",
            "email": "bob@example.com"
        },
        {
            "id": "CUS-003",
            "name": "Charlie",
            "email": "charlie@example.com"
        }
    ]