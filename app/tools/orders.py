from langchain_core.tools import tool
from app.database.DbConnection import db

def order_tools(organization_id: str):

    @tool
    def get_orders(
        created_at_from: str | None = None,
        created_at_to: str | None = None,
        status: str | None = None,
        customer_id: str | None = None,
        completed_at_from: str | None = None,
        completed_at_to: str | None = None,
        product_id: str | None = None,
    ):
        """
        Get orders belonging to the current organization.

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
            query["customer"] = customer_id

        if created_at_from or created_at_to:
            query["createdAt"] = {}

            if created_at_from:
                query["createdAt"]["$gte"] = created_at_from

            if created_at_to:
                query["createdAt"]["$lte"] = created_at_to

        if completed_at_from or completed_at_to:
            query["completedAt"] = {}

            if completed_at_from:
                query["completedAt"]["$gte"] = completed_at_from

            if completed_at_to:
                query["completedAt"]["$lte"] = completed_at_to

        if product_id:
            query["products"] = {
                "$elemMatch": {
                    "product": product_id
                }
            }

        return list(
            db.orders.find(
                query,
                {"_id": 0}
            ).limit(100)
        )

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
        Count orders belonging to the current organization.

        Use this when the user asks how many orders match certain criteria.
        """

        query = {
            "organization": organization_id
        }

        if status:
            query["status"] = status

        if customer_id:
            query["customer"] = customer_id

        if created_at_from or created_at_to:
            query["createdAt"] = {}

            if created_at_from:
                query["createdAt"]["$gte"] = created_at_from

            if created_at_to:
                query["createdAt"]["$lte"] = created_at_to

        if completed_at_from or completed_at_to:
            query["completedAt"] = {}

            if completed_at_from:
                query["completedAt"]["$gte"] = completed_at_from

            if completed_at_to:
                query["completedAt"]["$lte"] = completed_at_to

        if product_id:
            query["products"] = {
                "$elemMatch": {
                    "product": product_id
                }
            }

        return {
            "count": db.orders.count_documents(query)
        }

    @tool
    def get_order(order_id: str):
        """Get a specific order using its order ID."""

        order = db.orders.find_one(
            {"organization": organization_id,"_id": order_id},
            {"_id": 0}
        )

        if not order:
            return {
                "error": f"Order {order_id} not found"
            }

        return order

    return [get_orders, get_order, count_orders]