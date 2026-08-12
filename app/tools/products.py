from langchain_core.tools import tool
from app.database.DbConnection import db
from bson import ObjectId
from app.utils.dates import parse_date

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
        page: int = 1,
        page_size: int = 10,
    ):
        """
        Retrieve a small paginated list of products.

        Use when the user wants to:
        - search or list products
        - find products by name, SKU, category, price, or stock
        - retrieve multiple products without a specific product ID

        If a specific product ID is known, use get_product instead.

        Do NOT use for:
        - counting products → count_products
        - inventory analysis → analyze_inventory
        - sales/revenue analysis → analyze_products

        Filters:
        - name: product name
        - sku: product SKU
        - stock_min / stock_max: stock range
        - category: product category
        - price_min / price_max: price range

        Pagination:
        - page: starts at 1
        - page_size: 1–10, default 10

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

        page = max(1, page)
        page_size = min(max(1, page_size), 10)

        skip = (page - 1) * page_size       

        products = list(
        db.products.find(
            query,
            {"_id": 0,"image": 0}
        )
        .sort("createdAt", -1)
        .skip(skip)
        .limit(page_size)
    )
        return {
            "page": page,
            "page_size": page_size,
            "products": products
        }        



    @tool
    def get_product(product_id: str):
        """
        Get detailed information about a specific product using its product ID.

        Use this tool when you already have a specific product ID and need:
        - product name
        - SKU
        - price
        - stock
        - category
        - description
        - features

        Do NOT use this tool to search for products or retrieve multiple
        products. Use get_products instead.

        Do NOT use this tool to determine which product sells the most,
        generates the most revenue, or other sales analytics. Use
        analyze_orders instead.
        """

        product = db.products.find_one(
            {"organization": organization_id,"_id": ObjectId(product_id)},
            {"_id": 0,"image": 0}
        )

        if not product:
            return {
                "error": f"Product {ObjectId(product_id)} not found"
            }

        return product

    @tool
    def count_products(
        created_at_from: str | None = None,
        created_at_to: str | None = None,
        category: str | None = None,
        stock_min: int | None = None,
        stock_max: int | None = None,
    ):
        """
        Count products belonging to the organization.

        Use this tool whenever the user asks HOW MANY products exist
        or match specific product filters.

        Optional filters:
        - created_at_from: minimum product creation date, ISO format
        - created_at_to: maximum product creation date, ISO format
        - category: filter by product category
        - stock_min: minimum stock quantity
        - stock_max: maximum stock quantity

        Use only the filters relevant to the user's request.
        """

        query = {
            "organization": organization_id
        }

        if created_at_from or created_at_to:
            query["createdAt"] = {}

            if created_at_from:
                query["createdAt"]["$gte"] = parse_date(created_at_from)

            if created_at_to:
                query["createdAt"]["$lte"] = parse_date(created_at_to)

        if category:
            query["category"] = category

        if stock_min is not None or stock_max is not None:
            query["stock"] = {}

            if stock_min is not None:
                query["stock"]["$gte"] = stock_min

            if stock_max is not None:
                query["stock"]["$lte"] = stock_max

        return {
            "count": db.products.count_documents(query)
        }

    return [get_products, get_product, count_products]