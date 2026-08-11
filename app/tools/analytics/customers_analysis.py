from langchain_core.tools import tool
from app.database.DbConnection import db
from bson import ObjectId
from app.utils.dates import parse_date, get_period_dates

def customer_analysis(organization_id: str):

    @tool
    def analyze_customers(
        period: str = None,
        analysis: str = None,
        customer_id: str = None,
        limit: int = None
    ):
        """
         Analyze customer behavior and customer performance.

        USE THIS TOOL when the user asks about customers as a group,
        customer rankings, customer activity, repeat customers,
        new customers, customer spending, or customer lifetime value.

        Do NOT use this tool to retrieve basic customer information such as
        name, email, phone, or address. Use get_customer/get_customers for that.

        analysis determines what customer analysis to perform:

        - top_customers:
            Find customers ranked by overall customer value or performance.
            Use for questions like:
            "Who are my top customers?"
            "Which customers are the most valuable?"

        - most_orders:
            Find customers with the highest number of orders.
            Use for:
            "Who orders the most?"
            "Which customer has placed the most orders?"
            "Who are my most frequent customers?"

        - highest_spending:
            Find customers who spent the most money on completed orders.
            Use for:
            "Who spent the most?"
            "Which customers generated the most revenue?"
            "Who are my biggest spenders?"

        - new_customers:
            Count or identify customers created during a specified period.
            Use for:
            "How many new customers did I get this month?"
            "How many customers joined last month?"

        - repeat_customers:
            Find customers who have placed more than one order.
            Use for:
            "Do I have repeat customers?"
            "How many returning customers do I have?"
            "Which customers ordered more than once?"

        - active_customers:
            Find customers who placed orders during the specified period.
            Use for:
            "How many active customers do I have this month?"
            "How many customers bought something this week?"

        - average_clv:
            Calculate the average customer lifetime value based on
            completed-order spending.
            Use for:
            "What is my average customer lifetime value?"
            "What is the average amount customers spend?"

        - spending_distribution:
            Group customers into spending ranges based on completed orders.
            Use for:
            "How are my customers distributed by spending?"
            "How many customers spent under 100?"
            "How many customers spent more than 1000?"

        period specifies the time period when relevant:
        - today
        - this_week
        - this_month
        - last_month
        - this_year
        - last_year
        - all_time
        - None = all available data

        customer_id:
            Use only when the user is asking for analysis about one
            specific customer whose ID is already known.

        limit:
            Use when returning a ranking or list of customers.
            Keep the value small unless the user explicitly requests more.
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

            return list(db.orders.aggregate(pipeline))

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