from langchain_core.tools import tool
from app.database.DbConnection import db

def customer_tools(organization_id: str):
    
    @tool
    def get_customers(
        name: str | None = None,
        address: str | None = None,
        created_at_from: str | None = None,
        created_at_to: str | None = None,
    ):
        """
        Get customers belonging to the current organization.

        Optional filters:
        - name: customer name
        - address: customer address
        - created_at_from: minimum creation date, ISO format
        - created_at_to: maximum creation date, ISO format

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
                query["createdAt"]["$gte"] = created_at_from

            if created_at_to:
                query["createdAt"]["$lte"] = created_at_to

        return list(
            db.customers.find(
                query,
                {"_id": 0}
            ).limit(100)
        )


    @tool
    def get_customer(customer_id: str):
        """Get a specific customer using their customer ID."""

        customer = db.customers.find_one(
            {"organization": organization_id,"_id": customer_id},
            {"_id": 0}
        )

        if not customer:
            return {
                "error": f"Customer {customer_id} not found"
            }

        return customer
    
    return [get_customers, get_customer]