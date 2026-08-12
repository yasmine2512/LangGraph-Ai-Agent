from langchain_core.tools import tool
from app.database.DbConnection import db
from bson import ObjectId
from app.utils.dates import parse_date, get_period_dates

def sales_tools(organization_id: str):


    @tool
    def analyze_sales(
    period: str | None = None,
    group_by: str | None = None,
    customer_id: str | None = None,
    product_id: str | None = None,
    category: str | None = None
    ):
        """
        Analyze completed sales and revenue.

        Use for:
        - total revenue or sales
        - revenue/sales for a time period
        - revenue trends
        - sales by product, category, or customer
        - customer spending

        Use `period` for time-based questions.
        Use `group_by` for comparisons or breakdowns.
        Use `customer_id`, `product_id`, or `category` to filter results.

        period:
        - today, this_week, this_month
        - last_month, this_year, last_year
        - all_time

        group_by:
        - product, category, customer
        - month, day
        """
        query = {"organization": organization_id,"status": "completed"}
        start, end = get_period_dates(period)
        if start:query["completedAt"] = {
                "$gte": start,
                "$lt": end
            }

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

        pipeline = [
            {"$match": query}
        ]

        # Sales by product/category/customer
        if group_by in ["product", "category", "customer"]:

            pipeline.append({"$unwind": "$products"})

            if product_id:
                pipeline.append({
                    "$match": {
                        "products.product": ObjectId(product_id)
                    }
                })

            if group_by == "product":
                pipeline.extend([
                    {
                        "$group": {
                            "_id": "$products.product",
                            "unitsSold": {
                                "$sum": "$products.quantity"
                            },
                            "revenue": {
                                "$sum": {
                                    "$multiply": [
                                        "$products.quantity",
                                        "$products.priceAtPurchase"
                                    ]
                                }
                            }
                        }
                    },
                    {"$sort": {"revenue": -1}},
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
                            "category": "$product.category",
                            "unitsSold": 1,
                            "revenue": 1
                        }
                    }
                ])

            elif group_by == "category":

                pipeline.extend([
                    {
                        "$lookup": {
                            "from": "products",
                            "localField": "products.product",
                            "foreignField": "_id",
                            "as": "product"
                        }
                    },
                    {"$unwind": "$product"},
                    {
                        "$group": {
                            "_id": "$product.category",
                            "unitsSold": {
                                "$sum": "$products.quantity"
                            },
                            "revenue": {
                                "$sum": {
                                    "$multiply": [
                                        "$products.quantity",
                                        "$products.priceAtPurchase"
                                    ]
                                }
                            }
                        }
                    },
                    {"$sort": {"revenue": -1}},
                    {
                        "$project": {
                            "_id": 0,
                            "category": "$_id",
                            "unitsSold": 1,
                            "revenue": 1
                        }
                    }
                ])

            elif group_by == "customer":

                pipeline.extend([
                    {
                        "$group": {
                            "_id": "$customer",
                            "unitsPurchased": {
                                "$sum": "$products.quantity"
                            },
                            "revenue": {
                                "$sum": {
                                    "$multiply": [
                                        "$products.quantity",
                                        "$products.priceAtPurchase"
                                    ]
                                }
                            }
                        }
                    },
                    {"$sort": {"revenue": -1}},
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
                            "revenue": 1,
                            "unitsPurchased": 1
                        }
                    }
                ])

        elif group_by in ["month", "day"]:

            date_format = "%Y-%m" if group_by == "month" else "%Y-%m-%d"

            pipeline.extend([
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": date_format,
                                "date": "$completedAt"
                            }
                        },
                        "revenue": {
                            "$sum": "$totalPrice"
                        },
                        "orders": {
                            "$sum": 1
                        }
                    }
                },
                {"$sort": {"_id": 1}},
                {
                    "$project": {
                        "_id": 0,
                        "period": "$_id",
                        "revenue": 1,
                        "orders": 1
                    }
                }
            ])

        else:

            result = list(db.orders.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "revenue": {
                            "$sum": "$totalPrice"
                        },
                        "orders": {
                            "$sum": 1
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "revenue": 1,
                        "orders": 1
                    }
                }
            ]))

            return result[0] if result else {
                "revenue": 0,
                "orders": 0
            }

        return list(db.orders.aggregate(pipeline))

    return [analyze_sales]