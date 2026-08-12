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
        Analyze order activity and statistics.

        Use for:
        - order counts and status breakdowns
        - order trends over time
        - orders grouped by customer or product
        - average order value
        - statistics for a specific customer or product

        Use count_orders for simple "how many orders" queries when no
        analysis or grouping is needed.

        Do not use for:
        - revenue or sales performance → analyze_sales
        - customer spending/rankings → analyze_customers
        - retrieving individual orders → get_orders

        Arguments:
        - period: today, this_week, this_month, last_month, this_year,
        last_year, all_time, or None
        - status: filter by order status
        - group_by: status, customer, product, day, month, or None
        - customer_id: analyze orders for a specific customer
        - product_id: analyze orders containing a specific product

        Average order value is calculated from completed orders by default.
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