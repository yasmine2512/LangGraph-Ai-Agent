from langchain_core.tools import tool
from app.database.DbConnection import db

def product_tools(organization_id: str):

    @tool
    def get_products(
        name: str | None = None,
        sku: str | None = None,
        stock_min: int | None = None,
        stock_max: int | None = None,
        category: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
    ):
        """
        Get products belonging to the current organization.

        Optional filters:
        - name: product name
        - sku: product SKU
        - stock_min: minimum stock
        - stock_max: maximum stock
        - category: product category
        - price_min: minimum price
        - price_max: maximum price

        Use only the filters relevant to the user's request.
        """

        query = {
            "organization": organization_id
        }

        if name:
            query["name"] = {
                "$regex": name,
                "$options": "i"
            }

        if sku:
            query["sku"] = sku

        if stock_min is not None or stock_max is not None:
            query["stock"] = {}

            if stock_min is not None:
                query["stock"]["$gte"] = stock_min

            if stock_max is not None:
                query["stock"]["$lte"] = stock_max

        if category:
            query["category"] = category

        if price_min is not None or price_max is not None:
            query["price"] = {}

            if price_min is not None:
                query["price"]["$gte"] = price_min

            if price_max is not None:
                query["price"]["$lte"] = price_max

        return list(
            db.products.find(
                query,
                {"_id": 0}
            ).limit(100)
        )


    @tool
    def get_product(product_id: str):
        """Get a specific product using its product ID."""

        product = db.products.find_one(
            {"organization": organization_id,"_id": product_id},
            {"_id": 0}
        )

        if not product:
            return {
                "error": f"Product {product_id} not found"
            }

        return product

    return [get_products, get_product]