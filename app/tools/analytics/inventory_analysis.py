from langchain_core.tools import tool
from app.database.DbConnection import get_db
from bson import ObjectId
from app.utils.dates import parse_date, get_period_dates

def inventory_tools(organization_id):
    db = get_db()
    @tool
    def analyze_inventory(
        analysis: str | None = None,
        category: str | None = None,
        product_id: str | None = None,
        stock_threshold: int | None = None,
        limit: int | None = None
    ):
        """
        Analyze current product inventory and stock levels.

        Use for:
        - current stock levels
        - low-stock or out-of-stock products
        - inventory value
        - restock alerts
        - stock by category

        Do not use for product sales, revenue, or best-selling products
        → analyze_products.

        analysis:
        - stock_levels: current stock quantities
        - low_stock: products below the stock threshold
        - out_of_stock: products with zero stock
        - inventory_value: total stock × product price
        - restock_alerts: products needing restocking
        - stock_by_category: stock grouped by category

        Arguments:
        - category: filter by product category
        - product_id: inventory for a specific product ID
        - stock_threshold: threshold for low_stock/restock_alerts
        - limit: maximum products returned

        Use the default threshold when none is specified.
        Keep limit small unless the user requests more.
        """

        if limit is None:
            limit = 10

        if stock_threshold is None:
            stock_threshold = 10

        query = {
            "organization": organization_id
        }

        if category:
            query["category"] = category

        if product_id:
            try:
                query["_id"] = ObjectId(product_id)
            except Exception:
                return {"error": "Invalid product ID"}

        # Total products / inventory value / stock summary
        if analysis in [
            "stock_levels",
            "inventory_value",
        ]:

            result = list(db.products.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "totalProducts": {"$sum": 1},
                        "totalStock": {"$sum": "$stock"},
                        "inventoryValue": {
                            "$sum": {
                                "$multiply": [
                                    "$stock",
                                    "$price"
                                ]
                            }
                        },
                        "lowStock": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {
                                                "$gt": [
                                                    "$stock",
                                                    0
                                                ]
                                            },
                                            {
                                                "$lte": [
                                                    "$stock",
                                                    stock_threshold
                                                ]
                                            }
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        },
                        "outOfStock": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$eq": [
                                            "$stock",
                                            0
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "totalProducts": 1,
                        "totalStock": 1,
                        "inventoryValue": 1,
                        "lowStock": 1,
                        "outOfStock": 1
                    }
                }
            ]))

            return result[0] if result else {
                "totalProducts": 0,
                "totalStock": 0,
                "inventoryValue": 0,
                "lowStock": 0,
                "outOfStock": 0
            }

        # Low stock
        if analysis in [
            "low_stock",
            "restock_alerts"
        ]:

            query["stock"] = {
                "$gt": 0,
                "$lte": stock_threshold
            }

        # Out of stock
        elif analysis == "out_of_stock":

            query["stock"] = 0

        # Stock by category
        if analysis == "stock_by_category":

            result = list(db.products.aggregate([
                {"$match": query},
                {
                    "$group": {
                        "_id": "$category",
                        "products": {"$sum": 1},
                        "totalStock": {"$sum": "$stock"},
                        "inventoryValue": {
                            "$sum": {
                                "$multiply": [
                                    "$stock",
                                    "$price"
                                ]
                            }
                        }
                    }
                },
                {"$sort": {"inventoryValue": -1}},
                {
                    "$project": {
                        "_id": 0,
                        "category": "$_id",
                        "products": 1,
                        "totalStock": 1,
                        "inventoryValue": 1
                    }
                }
            ]))
            if not result:
                return {
                    "results": [],
                    "message": "No matching results were found."
                }
            return result

        # Individual products
        result = list(
            db.products.find(
                query,
                {
                    "_id": 1,
                    "name": 1,
                    "sku": 1,
                    "category": 1,
                    "stock": 1,
                    "price": 1
                }
            ).limit(limit)
        )
        if not result:
            return {
                "results": [],
                "message": "No matching results were found."
            }
        return result

    return [analyze_inventory]