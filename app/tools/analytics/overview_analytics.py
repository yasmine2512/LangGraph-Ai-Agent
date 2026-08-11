from langchain_core.tools import tool
from app.database.DbConnection import db
from app.utils.dates import get_period_dates


def overview_tools(organization_id):

    @tool
    def analyze_business(period: str = "this_month"):
        """
        Give a high-level overview of business performance.

        Use this tool for broad questions such as:
        - how is my business doing?
        - how is my business going lately?
        - how are my sales doing?
        - is my business performing well?
        - give me a business overview
        - give me a business performance summary

        Returns a compact summary of revenue, orders, customers,
        average order value, and comparison with the previous period.

        period:
        - this_week
        - this_month
        - last_month
        - this_year
        """
        
        start_date, end_date = get_period_dates(period)

        # Calculate previous period with the same duration
        duration = end_date - start_date
        previous_end = start_date
        previous_start = start_date - duration

        pipeline = [
            {
                "$match": {
                    "organization": organization_id
                }
            },
            {
                "$facet": {
                    "current": [
                        {
                            "$match": {
                                "createdAt": {
                                    "$gte": start_date,
                                    "$lt": end_date
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "orders": {"$sum": 1},
                                "revenue": {
                                    "$sum": {
                                        "$cond": [
                                            {"$eq": ["$status", "completed"]},
                                            "$totalPrice",
                                            0
                                        ]
                                    }
                                },
                                "customers": {
                                    "$addToSet": "$customer"
                                },
                                "completedOrders": {
                                    "$sum": {
                                        "$cond": [
                                            {"$eq": ["$status", "completed"]},
                                            1,
                                            0
                                        ]
                                    }
                                }
                            }
                        }
                    ],
                    "previous": [
                        {
                            "$match": {
                                "createdAt": {
                                    "$gte": previous_start,
                                    "$lt": previous_end
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "orders": {"$sum": 1},
                                "revenue": {
                                    "$sum": {
                                        "$cond": [
                                            {"$eq": ["$status", "completed"]},
                                            "$totalPrice",
                                            0
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        ]

        result = list(db.orders.aggregate(pipeline))

        if not result:
            return {
                "period": period,
                "orders": 0,
                "revenue": 0,
                "customers": 0,
                "completed_orders": 0
            }

        data = result[0]

        current = data["current"][0] if data["current"] else {
            "orders": 0,
            "revenue": 0,
            "customers": [],
            "completedOrders": 0
        }

        previous = data["previous"][0] if data["previous"] else {
            "orders": 0,
            "revenue": 0
        }

        current_orders = current["orders"]
        current_revenue = current["revenue"]
        current_customers = len(current["customers"])
        completed_orders = current["completedOrders"]

        previous_orders = previous["orders"]
        previous_revenue = previous["revenue"]

        average_order_value = (
            current_revenue / completed_orders
            if completed_orders > 0
            else 0
        )

        revenue_growth = (
            ((current_revenue - previous_revenue) / previous_revenue) * 100
            if previous_revenue > 0
            else None
        )

        orders_growth = (
            ((current_orders - previous_orders) / previous_orders) * 100
            if previous_orders > 0
            else None
        )

        return {
            "period": period,
            "revenue": round(current_revenue, 2),
            "orders": current_orders,
            "completed_orders": completed_orders,
            "customers": current_customers,
            "average_order_value": round(average_order_value, 2),
            "previous_revenue": round(previous_revenue, 2),
            "revenue_growth_percent": (
                round(revenue_growth, 2)
                if revenue_growth is not None
                else None
            ),
            "previous_orders": previous_orders,
            "orders_growth_percent": (
                round(orders_growth, 2)
                if orders_growth is not None
                else None
            )
        }

    return [analyze_business]