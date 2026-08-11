from langchain_core.tools import tool
from app.database.DbConnection import db
from bson import ObjectId
from app.utils.dates import parse_date, get_period_dates

def inventory_tools(organization_id):

    @tool
    def analyze_inventory(
        analysis: str = None,
        category: str = None,
        product_id: str = None,
        stock_threshold: int = None,
        limit: int = None
    ):
        """
        Analyze current product inventory and stock levels.

        USE THIS TOOL for questions about inventory, available stock,
        low-stock products, out-of-stock products, inventory value,
        or products that may need restocking.

        Do NOT use this tool for product sales, revenue, or best-selling
        product questions. Use analyze_products for those.

        analysis determines what inventory analysis to perform:

        - stock_levels:
            Return current stock quantities for products.
            Use for:
            "How much stock do I have?"
            "What are my current stock levels?"
            "Show me the stock for my products."

        - low_stock:
            Find products whose stock is below or equal to the
            specified stock_threshold.
            Use for:
            "Which products are low in stock?"
            "What products have less than 10 units?"

        - out_of_stock:
            Find products whose stock quantity is exactly zero.
            Use for:
            "Which products are out of stock?"
            "Do I have any products with no stock?"

        - inventory_value:
            Calculate the current value of inventory using:
            stock quantity × product price.
            Use for:
            "How much is my inventory worth?"
            "What is the total value of my stock?"

        - total_products:
            Count the total number of products in the inventory.
            Use for:
            "How many products do I have?"
            "How many products are in my inventory?"

        - restock_alerts:
            Identify products that need attention because their stock
            is low or zero.
            Use for:
            "What products should I restock?"
            "What are my restock alerts?"

        - stock_by_category:
            Analyze or summarize stock levels grouped by product category.
            Use for:
            "How much stock do I have in each category?"
            "Which category has the most stock?"

        category:
            Use when the user asks about inventory for a specific
            product category.

        product_id:
            Use only when the user asks about inventory for one
            specific product whose ID is already known.

        stock_threshold:
            Use with low_stock or restock_alerts when the user gives
            a specific threshold.
            Example: "Show products with fewer than 5 units."
            If the user does not specify a threshold, use the tool's
            default threshold.

        limit:
            Use when returning a list of products.
            Keep the value small unless the user explicitly asks for more.
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
            "total_products"
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

            return list(db.products.aggregate([
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

        # Individual products
        return list(
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

    return [analyze_inventory]