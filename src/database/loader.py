import csv
import sqlite3
from pathlib import Path
from typing import Optional

from src.config import DATA_DIR, settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    city TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    price_brl REAL NOT NULL,
    name TEXT NOT NULL,
    category_id INTEGER,
    description TEXT,
    stock_quantity INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    specs TEXT,
    created_at TEXT,
    FOREIGN KEY(category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date TEXT,
    status TEXT,
    total_brl REAL,
    payment_method TEXT,
    tracking_code TEXT,
    estimated_delivery TEXT,
    notes TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    quantity INTEGER DEFAULT 1,
    product_id INTEGER,
    FOREIGN KEY(order_id) REFERENCES orders(order_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS promotions (
    promotion_id INTEGER PRIMARY KEY,
    product_id INTEGER,
    discount_percent REAL,
    description TEXT,
    is_active INTEGER DEFAULT 0,
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price_brl);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_tracking ON orders(tracking_code);
CREATE INDEX IF NOT EXISTS idx_promotions_active ON promotions(is_active);
"""

def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Retorna uma conexão configurada com o SQLite."""
    path = db_path or settings.DATABASE_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def _find_csv(prefix: str, data_dir: Path) -> Optional[Path]:
    """Localiza o arquivo CSV correspondente, aceitando prefixos flexíveis."""
    for p in data_dir.glob("*.csv"):
        if prefix.lower() in p.name.lower():
            return p
    return None

def init_database(db_path: Optional[Path] = None, data_dir: Optional[Path] = None) -> None:
    """Inicializa as tabelas e popula com os dados dos arquivos CSV da loja."""
    path = db_path or settings.DATABASE_PATH
    source_dir = data_dir or DATA_DIR

    conn = get_db_connection(path)
    with conn:
        conn.executescript(SCHEMA_SQL)

        # Ingestão de Categorias
        cat_file = _find_csv("categories", source_dir)
        if cat_file and conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
            with open(cat_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [(int(r["category_id"]), r["name"].strip(), r.get("description", "").strip()) for r in reader]
                conn.executemany("INSERT INTO categories (category_id, name, description) VALUES (?, ?, ?);", rows)

        # Ingestão de Clientes
        cust_file = _find_csv("customers", source_dir)
        if cust_file and conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            with open(cust_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [(int(r["customer_id"]), r["name"].strip(), r.get("phone", "").strip(), r.get("email", "").strip(), r.get("city", "").strip()) for r in reader]
                conn.executemany("INSERT INTO customers (customer_id, name, phone, email, city) VALUES (?, ?, ?, ?, ?);", rows)

        # Ingestão de Produtos
        prod_file = _find_csv("products", source_dir)
        if prod_file and conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            with open(prod_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [
                    (
                        int(r["product_id"]),
                        float(r["price_brl"]),
                        r["name"].strip(),
                        int(r["category_id"]) if r.get("category_id") else None,
                        r.get("description", "").strip(),
                        int(r.get("stock_quantity", 0)),
                        r.get("status", "active").strip(),
                        r.get("specs", "").strip(),
                        r.get("created_at", "").strip()
                    )
                    for r in reader
                ]
                conn.executemany(
                    """INSERT INTO products 
                       (product_id, price_brl, name, category_id, description, stock_quantity, status, specs, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    rows
                )

        # Ingestão de Pedidos
        orders_file = _find_csv("orders.csv", source_dir)
        if orders_file and conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            with open(orders_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [
                    (
                        int(r["order_id"]),
                        int(r["customer_id"]) if r.get("customer_id") else None,
                        r.get("order_date", "").strip(),
                        r.get("status", "").strip(),
                        float(r["total_brl"]) if r.get("total_brl") else 0.0,
                        r.get("payment_method", "").strip(),
                        r.get("tracking_code", "").strip(),
                        r.get("estimated_delivery", "").strip(),
                        r.get("notes", "").strip()
                    )
                    for r in reader
                ]
                conn.executemany(
                    """INSERT INTO orders 
                       (order_id, customer_id, order_date, status, total_brl, payment_method, tracking_code, estimated_delivery, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    rows
                )

        # Ingestão de Itens dos Pedidos
        items_file = _find_csv("order_items", source_dir)
        if items_file and conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 0:
            with open(items_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [
                    (
                        int(r["order_id"]),
                        int(r.get("quantity", 1)),
                        int(r["product_id"])
                    )
                    for r in reader
                ]
                conn.executemany(
                    "INSERT INTO order_items (order_id, quantity, product_id) VALUES (?, ?, ?);",
                    rows
                )

        # Ingestão de Promoções
        promos_file = _find_csv("promotions", source_dir)
        if promos_file and conn.execute("SELECT COUNT(*) FROM promotions").fetchone()[0] == 0:
            with open(promos_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [
                    (
                        int(r["promotion_id"]),
                        int(r["product_id"]),
                        float(r.get("discount_percent", 0.0)),
                        r.get("description", "").strip(),
                        1 if str(r.get("is_active", "0")).lower() in ("1", "true") else 0
                    )
                    for r in reader
                ]
                conn.executemany(
                    """INSERT INTO promotions (promotion_id, product_id, discount_percent, description, is_active)
                       VALUES (?, ?, ?, ?, ?);""",
                    rows
                )

    conn.close()
