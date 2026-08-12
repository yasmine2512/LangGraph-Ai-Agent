from langchain_core.tools import tool
from app.database.DbConnection import db
from bson import ObjectId
from datetime import datetime, timezone
from app.utils.dates import parse_date

def customer_tools(organization_id: str):
    
    @tool
    def get_customers(
        name: str | None = None,
        address: str | None = None,
        created_at_from: str | None = None,
        created_at_to: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ):
        """
        Retrieve a small paginated list of customers.
        Use for customer search/listing by:
        name, address, or creation date.

        Use get_customer when a specific customer ID is known.
        Use count_customers for "how many customers" questions.
        Use analyze_customers for spending, rankings, activity,
        repeat customers, or other customer analytics.

        Filters:
        name, address, created_at_from, created_at_to.

        Pagination:
        page (default 1), page_size (default 10, max 10).
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
        page_size = min(max(1, page_size), 10)

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

    @tool
    def count_customers(
        created_at_from: str | None = None,
        created_at_to: str | None = None,
    ):
        """
        Count customers belonging to the organization.

        Use this tool whenever the user asks HOW MANY customers exist
        or match a date-based filter.

        Optional filters:
        - created_at_from: minimum customer creation date, ISO format
        - created_at_to: maximum customer creation date, ISO format

        Use only the filters relevant to the user's request.

        """

        query = {
            "organization": organization_id
        }

        if created_at_from or created_at_to:
            query["createdAt"] = {}

            if created_at_from:
                query["createdAt"]["$gte"] = parse_date(created_at_from)

            if created_at_to:
                query["createdAt"]["$lte"] = parse_date(created_at_to)

        return {
            "count": db.customers.count_documents(query)
        }
    
    return [get_customers, get_customer, count_customers]