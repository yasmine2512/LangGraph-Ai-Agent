from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from app.tools.customers import customer_tools
from app.tools.orders import order_tools
from app.tools.products import product_tools
from app.tools.analytics.customers_analysis import customer_analysis
from app.tools.analytics.inventory_analysis import inventory_tools
from app.tools.analytics.orders_analysis import order_analysis
from app.tools.analytics.products_analysis import product_analysis
from app.tools.analytics.sales_analysis import sales_tools
from app.tools.analytics.overview_analytics import overview_tools

class RouteDecision(BaseModel):
    routes: list[
        Literal[
            "customer_info",
            "customer_analysis",
            "order_info",
            "order_analysis",
            "product_info",
            "product_analysis",
            "sales",
            "inventory",
            "overview",
            "general",
        ]
    ] = Field(
        description="One or more business domains required to answer the user's question."
    )

ROUTER_PROMPT = """
You are a routing engine for a business management AI assistant.

Your ONLY job is deciding which business domains are required
to answer the user's question.

You NEVER answer the question yourself.

A question may require one OR MORE routes.

CUSTOMER_INFO:
Basic customer records and retrieval.
Can search, list, retrieve, count, and filter customers.
Use when counting/filtering customers themselves.
Does not analyze their orders, spending, or behavior.

CUSTOMER_ANALYSIS:
Customer business performance and behavior.
Use when customers are evaluated based on orders, spending, or activity.
Can calculate customer order counts, total spending, rankings,
repeat customers, active customers, new customers, and lifetime value.

ORDER_INFO:
Actual order records.
Can retrieve, search, count, filter, and inspect individual orders.
Does not perform aggregate analysis.

ORDER_ANALYSIS:
Order statistics.
Can count orders, calculate averages, analyze statuses,
trends, and orders by customer/product.
Do NOT use for simply retrieving or counting orders when no
analysis or aggregation is requested.

PRODUCT_INFO:
Basic product records.
Can search, retrieve, list, count, and filter products.
Use when counting/filtering products themselves.
Does not calculate sales or revenue.


PRODUCT_ANALYSIS:
Product sales performance.
Use when products are evaluated based on orders, units sold, or revenue.
Can calculate units sold and revenue, rank products,
find best sellers, and analyze product/category sales.

INVENTORY:
Current stock and inventory.
Can analyze stock levels, low stock, out-of-stock products,
inventory value, and restocking needs.

SALES:
Overall sales and revenue.
Can calculate total revenue, sales trends, revenue by product,
category, customer, and time period.

OVERVIEW:
High-level business performance.
Use for broad questions about how the business is doing.
Provides a compact overview of revenue, orders, customers,
average order value, and comparisons.

GENERAL:
Questions that don't require business database tools.
Also use for RAG/document knowledge when appropriate.


Examples:

"How many customers do I have?"
→ [customer_info]

"How much did customers spend?"
→ [customer_analysis]

"How many orders did Ahmed make?"
→ [customer_info,customer_analysis]

"How many customers have completed orders?"
→ [customer_analysis]

"How many orders did we receive?"
→ [order_info]

"Show me the orders from Ahmed."
→ [order_info]

"How much revenue did the iPhone generate?"
→ [product_info,product_analysis]

"Show me the iPhone."
→ [product_info]

"Which products sold the most?"
→ [product_analysis]

"How much revenue did we make this month?"
→ [sales]

"How is my business doing?"
→ [overview]

"Which products are low in stock?"
→ [inventory]

COUNTING RULE:
If counting records themselves, use INFO.
If counting entities based on orders, sales, spending, or activity, use ANALYSIS.

IMPORTANT ROUTING RULE:
The current user message may depend on previous messages.
Use the recent conversation to resolve references such as:
"them", "those", "these", "that customer",
"that product", "those orders", "what about them",
"how many of them", etc.
Always determine what entity the user is referring to
before selecting routes.

Example:
User: "How many products do I have?"
Assistant: "You have 23 products."
User: "How many of them are pending?"
"them" refers to PRODUCTS.
→ use product-related routes, NOT order-related routes.

IMPORTANT:
- Do NOT select customer routes merely because the user asks for
  "recommendations".
- Select general for generic advice or recommendations.
- You may select multiple routes when answering the question requires
  information from multiple business domains.
- Only select a business route when the user's question actually
  requires data from that domain.
- Return only the route names.

"""

def create_router(llm: BaseChatModel):
    router_llm = llm.with_structured_output(RouteDecision)

    def route_query(messages) -> list[str]:
        result = router_llm.invoke([
            {
                "role": "system",
                "content": ROUTER_PROMPT
            },
            *messages
        ])

        return result.routes

    return route_query

def build_route_tools(organization_id):
    return {
        "customer_info": customer_tools(organization_id),
        "customer_analysis": customer_analysis(organization_id),

        "order_info": order_tools(organization_id),
        "order_analysis": order_analysis(organization_id),

        "product_info": product_tools(organization_id),
        "product_analysis": product_analysis(organization_id),

        "sales": sales_tools(organization_id),

        "inventory": inventory_tools(organization_id),

        "overview": overview_tools(organization_id),
    }