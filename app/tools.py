from langchain_core.tools import tool


products = [
        {
            "product_id": "PROD_001",
            "name": "Wireless Mouse",
            "price": 25.99,
            "stock": 120
        },
        {
            "product_id": "PROD_002",
            "name": "Mechanical Keyboard",
            "price": 79.99,
            "stock": 5
        },
        {
            "product_id": "PROD_003",
            "name": "27-inch Monitor",
            "price": 249.99,
            "stock": 2
        }
    ]

orders = [
        {
            "order_id": "ORD-001",
            "customer": "CUS-003",
            "product_id": "PROD_001",
            "quantity": 2,
            "status": "completed"
        },
        {
            "order_id": "ORD-002",
            "customer": "CUS-003",
            "product_id": "PROD_002",
            "quantity": 1,
            "status": "pending"
        },
        {
            "order_id": "ORD-003",
            "customer": "CUS-002",
            "product_id": "PROD_003",
            "quantity": 1,
            "status": "shipped"
        }
    ]


customers =  [
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

@tool
def get_products():
    """Get the list of available products."""
    
    return products

@tool
def get_orders():
    """Get information about recent customer orders."""

    return orders

@tool
def get_customers():
    """Get information about customers."""

    return customers

@tool
def get_customer(customer_id: str):
    """Get the name and email of a specific customer using their customer ID."""
    for customer in customers:
        if customer["id"] == customer_id:
            return customer

    return {
        "error": f"Customer {customer_id} not found"
    }

@tool
def get_order(order_id: str):
    """Get the information of a specific order using its order ID."""
    for order in orders:
        if order["order_id"] == order_id:
            return order

    return {
        "error": f"Order {order_id} not found"
    }

@tool
def get_product(product_id: str):
    """Get the information of a specific product using their product ID."""
    for product in products:
        if product["product_id"] == product_id:
            return product

    return {
        "error": f"Product {product_id} not found"
    }