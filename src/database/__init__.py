"""Módulo de banco de dados e consultas estruturadas."""

from src.database.loader import get_db_connection, init_database
from src.database.queries import (
    get_order_status,
    get_product_by_id,
    list_active_promotions,
    list_categories,
    search_products,
)

__all__ = [
    "get_db_connection",
    "init_database",
    "search_products",
    "get_product_by_id",
    "get_order_status",
    "list_active_promotions",
    "list_categories",
]
