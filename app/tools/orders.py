from langchain_core.tools import tool
from app.database.DbConnection import get_db
from bson import ObjectId
from datetime import datetime, timezone
from app.utils.dates import parse_date

def order_tools(organization_id: str):
    db = get_db()
    @tool
    def get_orders(
        created_at_from: str | None = None,
        created_at_to: str | None = None,
        status: str | None = None,
        customer_id: str | None = None,
        completed_at_from: str | None = None,
        completed_at_to: str | None = None,
        product_id: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ):
        """
        Retrieve a small paginated list of orders.

        Use for searching/listing specific orders or filtering orders by:
        customer, status, product, or date.

        Use get_order when a specific order ID is known.
        Use count_orders for "how many orders" questions.
        Use analyze_orders for order statistics, averages, trends,
        comparisons, or other order analytics.

        Filters:
        created_at_from, created_at_to,
        status, customer_id,
        completed_at_from, completed_at_to,
        product_id.

        Pagination:
        page (default 1), page_size (default 10, max 10).

        Use only the filters relevant to the user's request.
        """

        query = {
            "organization": organization_id
        }

        if status:
            query["status"] = status

        if customer_id:
            query["customer"] = ObjectId(customer_id)

        if created_at_from or created_at_to:
            query["createdAt"] = {}

            if created_at_from:
                query["createdAt"]["$gte"] = parse_date(created_at_from)

            if created_at_to:
                query["createdAt"]["$lte"] = parse_date(created_at_to)

        if completed_at_from or completed_at_to:
            query["completedAt"] = {}

            if completed_at_from:
                query["completedAt"]["$gte"] = parse_date(completed_at_from)

            if completed_at_to:
                query["completedAt"]["$lte"] = parse_date(completed_at_to)

        if product_id:
            query["products"] = {
                "$elemMatch": {
                    "product": ObjectId(product_id)
                }
            }

        page = max(1, page)
        page_size = min(max(1, page_size), 10)
        
        skip = (page - 1) * page_size       

        orders = list(
        db.orders.find(
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
            "orders": orders
        }    


    @tool
    def count_orders(
        created_at_from: str | None = None,
        created_at_to: str | None = None,
        status: str | None = None,
        customer_id: str | None = None,
        completed_at_from: str | None = None,
        completed_at_to: str | None = None,
        product_id: str | None = None,
    ):
        """
        Count orders. Use this tool whenever the user asks HOW MANY
        orders exist or match specific filters.

        Use this when the user asks how many orders match certain criteria.

        Optional filters:
                - created_at_from: minimum order creation date, ISO format
                - created_at_to: maximum order creation date, ISO format
                - status: order status such as pending, completed, shipped, cancelled
                - customer_id: filter by customer ID
                - completed_at_from: minimum completion date, ISO format
                - completed_at_to: maximum completion date, ISO format
                - product_id: filter orders containing this product
        
                Use only the filters relevant to the user's request.
        """

        query = {
            "organization": organization_id
        }

        if status:
            query["status"] = status

        if customer_id:
            query["customer"] = ObjectId(customer_id)

        if created_at_from or created_at_to:
            query["createdAt"] = {}

            if created_at_from:
                query["createdAt"]["$gte"] = parse_date(created_at_from)

            if created_at_to:
                query["createdAt"]["$lte"] = parse_date(created_at_to)

        if completed_at_from or completed_at_to:
            query["completedAt"] = {}

            if completed_at_from:
                query["completedAt"]["$gte"] = parse_date(completed_at_from)

            if completed_at_to:
                query["completedAt"]["$lte"] = parse_date(completed_at_to)

        if product_id:
            query["products"] = {
                "$elemMatch": {
                    "product": ObjectId(product_id)
                }
            }

        return {
            "count": db.orders.count_documents(query)
        }

    @tool
    def get_order(order_id: str):
        """
        Get detailed information about a specific order using its order ID.

        Use this tool when you already have an order ID and need:
        - the order status
        - the products purchased in that order
        - the quantity purchased for each product
        - the customer ID associated with the order
        - the order creation date
        - the completion date, if the order is completed

        Do NOT use this tool to search for multiple orders or perform
        order analytics. Use get_orders or analyze_orders instead.
        """

        order = db.orders.find_one(
            {"organization": organization_id,"_id": ObjectId(order_id)},
            {"_id": 0}
        )

        if not order:
            return {
                "error": f"Order {ObjectId(order_id)} not found"
            }

        return order

    return [get_orders, get_order, count_orders]