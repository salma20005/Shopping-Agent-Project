from typing import Optional
import os
import sqlite3
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from reviews_api import get_product_rating, get_ratings_for_products
import json
import base64
load_dotenv()
DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")
llm = ChatGroq(
    model = 'qwen/qwen3.8-27b',temperature=0
)
@tool
def search_products(query:str , max_price : Optional[float] = None,is_organic : Optional[bool] = None) -> str:
    """
    Search for products in the store database based on the given query,
    maximum price, and organic preference.

    Args:
        query (str): The search query.
        max_price (Optional[float]): The maximum price for the product.
        is_organic (Optional[bool]): Whether the product should be organic.

    Returns:
        str: A list of products that match the search criteria.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = "select id , name , category , price , description , is_organic from products where 1=1 "
    params: list = []
    if query:
        sql += "And (name like ? or description like ? or category like ?)"
        like = f"%{query}%"
        params.extend([like, like, like])
    if max_price is not None:
        sql += " and price <= ?"
        params.append(max_price)
    if is_organic is not None:
        sql += " and is_organic = ?"
        params.append(1 if is_organic else 0)
    cursor.execute(sql, params)
    products = cursor.fetchall()
    conn.close()
    products = [
        {
            "id": product[0],
            "name": product[1],
            "category": product[2],
            "price": product[3],
            "description": product[4],
            "is_organic": product[5],
        }
        for product in products
    ]
    return json.dumps(products) 
@tool 
def get_rating(product_id: int) -> str:
     """
     Get the average rating and number of reviews for a product.
     """
     rating = get_product_rating(product_id)
     return json.dumps(rating)
@tool
def checkout(product_id: int) -> str:
    """
    Place an order for a given product ID.
    Saves the order to the database and returns
    a confirmation message.
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, price FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        conn.close()
        return f"Error: Product with ID {product_id} not found."

    name, price = product

    cursor.execute(
        """
        INSERT INTO orders
        (product_id, product_name, price)
        VALUES (?, ?, ?)
        """,
        (product_id, name, price)
    )

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return (
        f"Order #{order_id} placed successfully. "
        f"Product: {name}, Price: {price}. "
        f"Your order will arrive in 3-5 business days. "
        f"Thank you for shopping with us!"
    )
# add image search instead of just writing
@tool
def describe_product_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.
    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{image_data}"},
        },
        {
            "type": "text",
            "text": (
                "Look at this product image and extract its key attributes. "
                "Return ONLY a JSON object with these fields:\n"
                "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                "- search_query: a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                "- is_organic: true if the label says organic, false if not, null if unclear\n"
                "- description: one sentence describing the product"
            ),
        },
    ])
    response = llm.invoke([message])
    return response.content

# Agent
agent = create_agent(
    tools=[search_products, get_rating, checkout, describe_product_image],
    model=llm,
    system_prompt=(
        "You are a helpful shopping assistant. Follow these rules strictly.\n\n"
        "IMAGE SEARCH — when the user provides an image path:\n"
        "1. Call describe_product_image with the path to identify the product.\n"
        "2. Use the returned search_query and is_organic to call search_products.\n"
        "3. Continue with the BROWSING flow from step 2 onwards.\n\n"
        "BROWSING — when the user describes what they want to buy:\n"
        "1. Call search_products to find matching items (apply any price/organic filters given).\n"
        "2. For each candidate, call get_rating to retrieve its average rating.\n"
        "3. Filter by the user's minimum rating if specified.\n"
        "4. Present qualifying products as a numbered list. For each item use this exact format "
        "   (plain text, no backticks, no code blocks, no bold, no italic):\n\n"
        "   #<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>\n\n"
        "   Add a blank line between each product entry for readability. "
        "   Always include (ID:X) so you can reference it later.\n"
        "5. If only one product qualifies, still show it in the list and ask: "
        "   'Would you like to order it? Just say yes or give me the number.'\n"
        "6. Do NOT call checkout at this stage.\n\n"
        "ORDERING — when the user confirms they want to buy (e.g. 'yes', 'sure', 'go ahead', "
        "'order number 2', 'the first one', 'get me #3'):\n"
        "1. Look at your previous message to find the (ID:X) for the chosen product "
        "   (if only one was listed and the user says 'yes', use that product's ID).\n"
        "2. Call checkout with that product_id (the number from (ID:X)).\n"
        "3. Confirm the order to the user in plain text.\n\n"
        "Never place an order unless the user explicitly confirms. "
        "Never guess a product_id — always take it from the (ID:X) in your own previous message."
    ),
)

# if __name__ == "__main__":
#     result = agent.invoke(
#         {
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": (
#                         "I want to buy organic tiger with 4.5+ rating and less than $20 price."
#                     ),
#                 }
#             ]
#         }
#     )
#     print(result["messages"][-1].content)
