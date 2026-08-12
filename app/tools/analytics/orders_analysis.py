from langchain_core.tools import tool
from app.database.DbConnection import db
from bson import ObjectId
from app.utils.dates import parse_date, get_period_dates

def order_analysis(organization_id: str):


    @tool
    def analyze_orders(
        period: str | None = None,
        status: str | None = None,
        group_by: str | None = None,
        customer_id: str | None = None,
        product_id: str | None = None
    ):
        """
        Analyze order activity and order statistics.

        USE THIS TOOL when the user asks about orders themselves:
        order counts, order statuses, order trends, orders from a customer,
        orders containing a product, or average order value.

        Do NOT use this tool for general revenue or sales-performance
        questions such as total sales revenue, revenue trends, sales by
        category, or product revenue. Use analyze_sales for those.

        Do NOT use get_orders() to retrieve many orders when the user
        is asking for a count, total, ranking, comparison, trend,
        or other calculation. Use this analytical tool instead.

        period specifies the time period:
        - today
        - this_week
        - this_month
        - last_month
        - this_year
        - last_year
        - all_time
        - None = all available data

        status filters orders by their status.
        Use when the user specifically mentions a status such as:
        - pending
        - completed
        - canceled

        group_by determines how orders should be grouped:

        - status:
            Count or summarize orders by their status.
            Use for:
            "Give me my order status breakdown."
            "How many orders are pending, completed, and canceled?"

        - customer:
            Group orders by customer.
            Use for:
            "How many orders did each customer make?"
            "Which customers have the most orders?"

        - product:
            Group orders by product.
            Use for:
            "How many orders contained each product?"

        - day:
            Group orders by day.
            Use for:
            "How many orders did I receive each day this week?"

        - month:
            Group orders by month.
            Use for:
            "Show my order trend by month."

        - None:
            Return an overall order statistic rather than a grouped result.

        customer_id:
            Use when the user asks about orders belonging to one
            specific customer whose ID is already known.

        product_id:
            Use when the user asks about orders containing one
            specific product whose ID is already known.

        average order value:
            Use this tool when the user asks for the average value
            of an order. Calculate this from completed orders unless
            the user explicitly specifies another status.

        IMPORTANT:
        If the user asks "Who is my biggest customer?" or
        "Who spent the most?", this is a CUSTOMER analysis and
        analyze_customers should be used instead.

        If the user asks "What is my total revenue?" or
        "How is my revenue trending?", this is a SALES analysis and
        analyze_sales should be used instead.
        """

        query = {
            "organization": organization_id
        }

        start, end = get_period_dates(period)

        if start:
            query["createdAt"] = {
                "$gte": start,
                "$lt": end
            }

        if status:
            query["status"] = status

        if customer_id:
            try:
                query["customer"] = ObjectId(customer_id)
            except Exception:
                return {"error": "Invalid customer ID"}

        if product_id:
            try:
                query["products.product"] = ObjectId(product_id)
            except Exception:
                return {"error": "Invalid product ID"}

        # Status breakdown
        if group_by == "status":
            return list(db.orders.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "status": "$_id",
                        "count": 1
                    }
                },
                {"$sort": {"count": -1}}
            ]))

        # Orders by customer
        if group_by == "customer":
            return list(db.orders.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": "$customer",
                        "orderCount": {"$sum": 1}
                    }
                },
                {"$sort": {"orderCount": -1}},
                {"$limit": 10},
                {
                    "$lookup": {
                        "from": "customers",
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "customer"
                    }
                },
                {"$unwind": "$customer"},
                {
                    "$project": {
                        "_id": 0,
                        "customerId": "$customer._id",
                        "name": "$customer.name",
                        "orderCount": 1
                    }
                }
            ]))

        # Orders by day/month
        if group_by in ["day", "month"]:

            date_format = (
                "%Y-%m-%d"
                if group_by == "day"
                else "%Y-%m"
            )

            return list(db.orders.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": date_format,
                                "date": "$createdAt"
                            }
                        },
                        "orders": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}},
                {
                    "$project": {
                        "_id": 0,
                        "period": "$_id",
                        "orders": 1
                    }
                }
            ]))

        # Orders by product
        if group_by == "product":
            return list(db.orders.aggregate([
                {"$match": query},
                {"$unwind": "$products"},
                {
                    "$group": {
                        "_id": "$products.product",
                        "orders": {"$sum": 1},
                        "quantity": {
                            "$sum": "$products.quantity"
                        }
                    }
                },
                {"$sort": {"quantity": -1}},
                {"$limit": 10},
                {
                    "$lookup": {
                        "from": "products",
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "product"
                    }
                },
                {"$unwind": "$product"},
                {
                    "$project": {
                        "_id": 0,
                        "productId": "$product._id",
                        "name": "$product.name",
                        "orders": 1,
                        "quantity": 1
                    }
                }
            ]))

        # Average order value
        if group_by == "average_value":

            result = list(db.orders.aggregate([
                {
                    "$match": {
                        **query,
                        "status": "completed"
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "orders": {"$sum": 1},
                        "revenue": {
                            "$sum": "$totalPrice"
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "orders": 1,
                        "revenue": 1,
                        "averageOrderValue": {
                            "$cond": [
                                {"$eq": ["$orders", 0]},
                                0,
                                {
                                    "$divide": [
                                        "$revenue",
                                        "$orders"
                                    ]
                                }
                            ]
                        }
                    }
                }
            ]))

            return result[0] if result else {
                "orders": 0,
                "revenue": 0,
                "averageOrderValue": 0
            }

        # Simple order count
        return {
            "orderCount": db.orders.count_documents(query)
        }
    
    return [analyze_orders]