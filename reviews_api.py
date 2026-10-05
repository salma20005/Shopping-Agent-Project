"""
Reviews API
Reads product reviews from store.db
and returns aggregated rating information.
"""

import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")


def get_product_rating(product_id: int) -> dict:
    """
    Return the average rating and number of reviews for one product.
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                AVG(rating),
                COUNT(rating)
            FROM reviews
            WHERE product_id = ?
            """,
            (product_id,),
        )

        rating, count = cursor.fetchone()

    return {
        "product_id": product_id,
        "rating": round(rating, 2) if rating is not None else None,
        "count": count,
    }


def get_ratings_for_products(product_ids: list[int]) -> list[dict]:
    """
    Return average rating and number of reviews
    for multiple products.
    """

    if not product_ids:
        return []

    placeholders = ", ".join(["?"] * len(product_ids))

    query = f"""
        SELECT
            product_id,
            AVG(rating),
            COUNT(rating)
        FROM reviews
        WHERE product_id IN ({placeholders})
        GROUP BY product_id
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, product_ids)

        rows = cursor.fetchall()

    return [
        {
            "product_id": product_id,
            "rating": round(rating, 2) if rating is not None else None,
            "count": count,
        }
        for product_id, rating, count in rows
    ]
# main to test
if __name__ == "__main__":
    print(get_product_rating(1))
    print(get_ratings_for_products([1, 2, 3]))