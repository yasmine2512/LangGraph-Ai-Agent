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
        page: int = 1,
        page_size: int = 20,
    ):
        """
        Retrieve ORDER information.

        Use this tool when the user wants:
        - specific orders
        - orders belonging to a customer
        - orders with a particular status
        - order details

        DO NOT use this tool to retrieve customer or product information.

        Optional filters:
        - created_at_from: minimum order creation date, ISO format
        - created_at_to: maximum order creation date, ISO format
        - status: order status such as pending, completed, shipped, cancelled
        - customer_id: filter by customer ID
        - completed_at_from: minimum completion date, ISO format
        - completed_at_to: maximum completion date, ISO format
        - product_id: filter orders containing this product

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
        page_size = min(max(1, page_size), 20)
        
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
        Count orders belonging to the current organization.

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

    # @tool
    # def analyze_orders(
    #     group_by: str | None = None,
    #     operation: str = "count",
    #     sort: str = "desc",
    #     limit: int = 10
    # ):
    #     """
    #     Analyze order data using database aggregation.

    #     group_by:
    #     - customer
    #     - product
    #     - status

    #     operation:
    #     - count
    #     - sum_quantity
    #     - sum_revenue

    #     Use this tool instead of get_orders when the user asks
    #     for calculations, rankings, comparisons, trends, totals,
    #     or summaries involving multiple orders.

    #     Do NOT retrieve all orders with get_orders() for analytical
    #     questions.
    #     """

    #     match_stage = {
    #         "$match": {
    #             "organization": organization_id
    #         }
    #     }

    #     if group_by == "customer":
    #         group_field = "$customer"

    #     elif group_by == "product":
    #         group_field = "$products.product"

    #     elif group_by == "status":
    #         group_field = "$status"

    #     else:
    #         return {"error": "Invalid group_by"}

    #     if operation == "count":
    #         group_stage = {
    #             "$group": {
    #                 "_id": group_field,
    #                 "count": {"$sum": 1}
    #             }
    #         }

    #     elif operation == "sum_quantity":
    #         group_stage = {
    #             "$group": {
    #                 "_id": group_field,
    #                 "quantity": {
    #                     "$sum": "$products.quantity"
    #                 }
    #             }
    #         }

    #     else:
    #         return {"error": "Unsupported operation"}

    #     pipeline = [
    #         match_stage,
    #         group_stage,
    #         {
    #             "$sort": {
    #                 "count" if operation == "count" else "quantity": -1
    #             }
    #         },
    #         {
    #             "$limit": limit
    #         }
    #     ]

    #     return list(db.orders.aggregate(pipeline))

    return [get_orders, get_order, count_orders]