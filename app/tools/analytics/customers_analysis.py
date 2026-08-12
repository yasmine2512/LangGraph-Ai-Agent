from langchain_core.tools import tool
from app.database.DbConnection import get_db
from bson import ObjectId
from app.utils.dates import parse_date, get_period_dates

def customer_analysis(organization_id: str):
    db = get_db()
    @tool
    def analyze_customers(
        period: str | None = None,
        analysis: str | None = None,
        customer_id: str | None = None,
        limit: int | None = None
    ):
        """
        Analyze customer behavior and performance.

        Use for customer rankings, spending, order activity, repeat/new
        customers, customer value, and customer statistics.

        Use get_customers/get_customer for basic customer information.
        Use count_customers for simple customer counts.

        analysis:
        - top_customers: rank customers by overall value/performance
        - most_orders: customers with the most orders
        - highest_spending: customers with the highest completed-order spending
        - new_customers: customers created during a period
        - repeat_customers: customers with multiple orders
        - active_customers: customers who ordered during a period
        - average_clv: average customer lifetime value
        - spending_distribution: customers grouped by spending ranges

        period:
        today, this_week, this_month, last_month, this_year,
        last_year, all_time

        Arguments:
        - customer_id: analyze one specific customer ID
        - limit: maximum customers returned in rankings/lists

        Keep limit small unless the user requests more.
        """

        if limit is None:
            limit = 5

        # Specific customer spending
        if customer_id:

            try:
                customer_oid = ObjectId(customer_id)
            except Exception:
                return {"error": "Invalid customer ID"}

            start, end = get_period_dates(period)

            query = {
                "organization": organization_id,
                "customer": customer_oid,
                "status": "completed"
            }

            if start:
                query["completedAt"] = {
                    "$gte": start,
                    "$lt": end
                }

            result = list(db.orders.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": "$customer",
                        "orders": {"$sum": 1},
                        "totalSpent": {
                            "$sum": "$totalPrice"
                        }
                    }
                },
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
                        "email": "$customer.email",
                        "orders": 1,
                        "totalSpent": 1
                    }
                }
            ]))

            return result[0] if result else {
                "error": "Customer has no completed orders"
            }

        # New customers
        if analysis == "new_customers":

            start, end = get_period_dates(period)

            query = {
                "organization": organization_id
            }

            if start:
                query["createdAt"] = {
                    "$gte": start,
                    "$lt": end
                }

            return {
                "newCustomers": db.customers.count_documents(query)
            }

        # Active customers
        if analysis == "active_customers":

            start, end = get_period_dates(period)

            query = {
                "organization": organization_id,
                "status": {"$ne": "canceled"}
            }

            if start:
                query["createdAt"] = {
                    "$gte": start,
                    "$lt": end
                }

            result = list(db.orders.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": "$customer"
                    }
                },
                {
                    "$count": "activeCustomers"
                }
            ]))

            return result[0] if result else {
                "activeCustomers": 0
            }

        # Top / highest spending / most orders
        if analysis in [
            "top_customers",
            "most_orders",
            "highest_spending",
            "repeat_customers"
        ]:

            start, end = get_period_dates(period)

            query = {
                "organization": organization_id,
                "status": "completed"
            }

            if start:
                query["completedAt"] = {
                    "$gte": start,
                    "$lt": end
                }

            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": "$customer",
                        "orderCount": {"$sum": 1},
                        "totalSpent": {
                            "$sum": "$totalPrice"
                        }
                    }
                }
            ]

            if analysis == "repeat_customers":
                pipeline.append({
                    "$match": {
                        "orderCount": {"$gte": 2}
                    }
                })

            pipeline.extend([
                {
                    "$sort": {
                        "totalSpent": -1,
                        "orderCount": -1,
                        "_id": 1
                    }
                },
                {"$limit": limit},
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
                        "email": "$customer.email",
                        "orderCount": 1,
                        "totalSpent": 1
                    }
                }
            ])

            result = list(db.orders.aggregate(pipeline))
            if not result:
                return {
                "results": [],
                "message": "No matching results were found."
                }
            return result

        # Average CLV
        if analysis == "average_clv":

            result = list(db.orders.aggregate([
                {
                    "$match": {
                        "organization": organization_id,
                        "status": "completed"
                    }
                },
                {
                    "$group": {
                        "_id": "$customer",
                        "totalSpent": {
                            "$sum": "$totalPrice"
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "averageCLV": {
                            "$avg": "$totalSpent"
                        },
                        "customers": {
                            "$sum": 1
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "averageCLV": 1,
                        "customers": 1
                    }
                }
            ]))

            return result[0] if result else {
                "averageCLV": 0,
                "customers": 0
            }

        return {
            "error": "Unsupported customer analysis"
        }

    return [analyze_customers]