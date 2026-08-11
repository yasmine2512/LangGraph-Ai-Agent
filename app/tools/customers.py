from langchain_core.tools import tool
from app.database.DbConnection import db
from bson import ObjectId
from datetime import datetime, timezone

def parse_date(date_string):
    if not date_string:
        return None

    return datetime.fromisoformat(
        date_string.replace("Z", "+00:00")
    )

def customer_tools(organization_id: str):
    
    @tool
    def get_customers(
        name: str | None = None,
        address: str | None = None,
        created_at_from: str | None = None,
        created_at_to: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        """
        Get information about customers.

        Use this tool when you need to:
        - search for customers
        - retrieve multiple customers
        - filter customers by name, address, or creation date
        - find customer information when you do not already have a specific
        customer ID

        If you already have a specific customer ID and only need that
        customer's information, use get_customer instead.

        Do NOT use this tool to determine which customer has the most orders,
        highest revenue, or other order-based metrics. Use analyze_orders instead.

        Optional filters:
        - name: customer name
        - address: customer address
        - created_at_from: minimum creation date, ISO format
        - created_at_to: maximum creation date, ISO format

         Pagination:
        - page starts at 1
        - page_size controls the number of customers returned
        - default page_size is 20
        - maximum page_size is 20

        Use only the filters relevant to the user's request.
        """

        query = {
            "organization": organization_id
        }

        if name:
            query["name"] = {
                "$regex": name,
                "$options": "i"
            }

        if address:
            query["address"] = {
                "$regex": address,
                "$options": "i"
            }

        if created_at_from or created_at_to:
            query["createdAt"] = {}

            if created_at_from:
                query["createdAt"]["$gte"] = parse_date(created_at_from)

            if created_at_to:
                query["createdAt"]["$lte"] = parse_date(created_at_to)

        page = max(1, page)
        page_size = min(max(1, page_size), 20)

        skip = (page - 1) * page_size       

        customers = list(
        db.customers.find(
            query,
            {"_id": 0}
        )
        .sort("createdAt", -1)
        .skip(skip)
        .limit(page_size)
    )
        return {
            "page": page,
            "page_size": page_size,
            "customers": customers
        }


    @tool
    def get_customer(customer_id: str):
        """Get CUSTOMER INFORMATION for a specific customer.
        
        Use this tool when you already have a customer ID and need:
        - customer name
        - customer email
        - customer phone
        - customer address
        - customer details
        """

        customer = db.customers.find_one(
            {"organization": organization_id,"_id": ObjectId(customer_id)},
            {"_id": 0}
        )

        if not customer:
            return {
                "error": f"Customer {ObjectId(customer_id)} not found"
            }

        return customer
    
    return [get_customers, get_customer]