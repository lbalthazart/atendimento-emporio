import json
import sqlite3
from typing import Any, Dict, List, Optional

from src.database.loader import get_db_connection

def list_categories() -> List[Dict[str, Any]]:
    """Retorna todas as categorias disponíveis no catálogo."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT category_id, name, description FROM categories ORDER BY category_id;")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    in_stock_only: bool = True,
    sort_by: str = "price_asc",
    limit: int = 6
) -> List[Dict[str, Any]]:
    """
    Busca produtos no catálogo da loja aplicando filtros estruturados.
    Calcula automaticamente descontos promocionais ativos.
    """
    conn = get_db_connection()
    try:
        sql = """
            SELECT 
                p.product_id,
                p.name,
                p.price_brl,
                c.name AS category_name,
                p.description,
                p.stock_quantity,
                p.status,
                p.specs,
                pr.discount_percent,
                pr.description AS promo_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
            WHERE p.status = 'active'
        """
        params: List[Any] = []

        if in_stock_only:
            sql += " AND p.stock_quantity > 0"

        if max_price is not None:
            sql += " AND p.price_brl <= ?"
            params.append(float(max_price))

        if min_price is not None:
            sql += " AND p.price_brl >= ?"
            params.append(float(min_price))

        if category:
            sql += " AND (LOWER(c.name) LIKE ? OR LOWER(p.name) LIKE ?)"
            params.extend([f"%{category.lower()}%", f"%{category.lower()}%"])

        if query:
            # Busca por termo tanto no nome quanto na descrição do produto
            keywords = [k.strip().lower() for k in query.split() if k.strip()]
            for kw in keywords:
                sql += " AND (LOWER(p.name) LIKE ? OR LOWER(p.description) LIKE ? OR LOWER(c.name) LIKE ?)"
                params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])

        if sort_by == "price_desc":
            sql += " ORDER BY p.price_brl DESC LIMIT ?;"
        elif sort_by == "name_asc":
            sql += " ORDER BY p.name ASC LIMIT ?;"
        else:
            sql += " ORDER BY p.price_brl ASC LIMIT ?;"
        params.append(limit)

        cursor = conn.execute(sql, params)
        results = []
        for row in cursor.fetchall():
            item = dict(row)
            price = float(item["price_brl"])
            discount = float(item["discount_percent"]) if item.get("discount_percent") else 0.0

            if discount > 0:
                final_price = round(price * (1.0 - (discount / 100.0)), 2)
                item["final_price_brl"] = final_price
                item["has_discount"] = True
            else:
                item["final_price_brl"] = price
                item["has_discount"] = False

            # Cálculo de pagamento à vista no PIX (5% de desconto de tabela para produtos sem promoção)
            if not item["has_discount"]:
                item["pix_price_brl"] = round(price * 0.95, 2)
            else:
                item["pix_price_brl"] = item["final_price_brl"]

            # Parse de specs JSON se existir
            if item.get("specs"):
                try:
                    item["specs"] = json.loads(item["specs"])
                except Exception:
                    pass

            results.append(item)

        return results
    finally:
        conn.close()

def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Retorna detalhes completos de um produto específico pelo seu ID."""
    conn = get_db_connection()
    try:
        sql = """
            SELECT 
                p.product_id,
                p.name,
                p.price_brl,
                c.name AS category_name,
                p.description,
                p.stock_quantity,
                p.status,
                p.specs,
                pr.discount_percent,
                pr.description AS promo_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN promotions pr ON p.product_id = pr.product_id AND pr.is_active = 1
            WHERE p.product_id = ?;
        """
        cursor = conn.execute(sql, (product_id,))
        row = cursor.fetchone()
        if not row:
            return None

        item = dict(row)
        price = float(item["price_brl"])
        discount = float(item["discount_percent"]) if item.get("discount_percent") else 0.0

        if discount > 0:
            item["final_price_brl"] = round(price * (1.0 - (discount / 100.0)), 2)
            item["has_discount"] = True
        else:
            item["final_price_brl"] = price
            item["has_discount"] = False

        if not item["has_discount"]:
            item["pix_price_brl"] = round(price * 0.95, 2)
        else:
            item["pix_price_brl"] = item["final_price_brl"]

        if item.get("specs"):
            try:
                item["specs"] = json.loads(item["specs"])
            except Exception:
                pass

        return item
    finally:
        conn.close()

def get_order_status(
    order_id: int,
    customer_identifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Localiza o pedido pelo ID obrigatório e retorna detalhes, status, rastreamento e itens.
    Para segurança contra vazamento de dados (LGPD), a consulta exige estritamente o número do pedido.
    Se fornecido, valida se o identificador do cliente confere com o titular.
    """
    if not order_id or int(order_id) <= 0:
        return {
            "found": False,
            "message": "O número do pedido (ID) é obrigatório para localização. Não realizamos busca avulsa por nome para prevenir vazamento de dados (LGPD)."
        }

    conn = get_db_connection()
    try:
        order_sql = """
            SELECT 
                o.order_id,
                o.customer_id,
                c.name AS customer_name,
                c.phone AS customer_phone,
                c.email AS customer_email,
                c.city AS customer_city,
                o.order_date,
                o.status,
                o.total_brl,
                o.payment_method,
                o.tracking_code,
                o.estimated_delivery,
                o.notes
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = ?;
        """
        cursor = conn.execute(order_sql, (int(order_id),))
        row = cursor.fetchone()
        if not row:
            return {"found": False, "message": f"Pedido #{order_id} não foi encontrado no sistema."}
        order = dict(row)

        # Validação opcional de segurança
        if customer_identifier:
            ident = customer_identifier.strip().lower()
            name_match = ident in (order["customer_name"] or "").lower()
            email_match = ident in (order["customer_email"] or "").lower()
            phone_clean_ident = "".join(filter(str.isdigit, ident))
            phone_clean_order = "".join(filter(str.isdigit, order["customer_phone"] or ""))
            phone_match = bool(phone_clean_ident and phone_clean_ident in phone_clean_order)

            if not (name_match or email_match or phone_match):
                return {
                    "found": True,
                    "authenticated": False,
                    "message": f"Pedido #{order_id} encontrado, mas os dados do cliente informado não conferem com o titular."
                }

        # Busca os itens do pedido
        items_sql = """
            SELECT 
                oi.quantity,
                p.product_id,
                p.name AS product_name,
                p.price_brl
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?;
        """
        items_cursor = conn.execute(items_sql, (order_id,))
        items = [dict(r) for r in items_cursor.fetchall()]

        return {
            "found": True,
            "authenticated": True,
            "order_id": order["order_id"],
            "customer_name": order["customer_name"],
            "order_date": order["order_date"],
            "status": order["status"],
            "total_brl": order["total_brl"],
            "payment_method": order["payment_method"],
            "tracking_code": order["tracking_code"],
            "estimated_delivery": order["estimated_delivery"],
            "items": items,
            "notes": order["notes"]
        }
    finally:
        conn.close()

def list_active_promotions() -> List[Dict[str, Any]]:
    """Lista todos os produtos atualmente em promoção ativa."""
    conn = get_db_connection()
    try:
        sql = """
            SELECT 
                pr.promotion_id,
                pr.description AS promo_description,
                pr.discount_percent,
                p.product_id,
                p.name AS product_name,
                p.price_brl,
                ROUND(p.price_brl * (1.0 - (pr.discount_percent / 100.0)), 2) AS discounted_price,
                p.stock_quantity
            FROM promotions pr
            JOIN products p ON pr.product_id = p.product_id
            WHERE pr.is_active = 1
            ORDER BY pr.discount_percent DESC;
        """
        cursor = conn.execute(sql)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()
