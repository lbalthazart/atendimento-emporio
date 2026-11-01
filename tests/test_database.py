from src.database.queries import (
    get_order_status,
    get_product_by_id,
    list_active_promotions,
    list_categories,
    search_products,
)

def test_list_categories():
    categories = list_categories()
    assert len(categories) == 9
    cat_names = [c["name"] for c in categories]
    assert "Violões" in cat_names
    assert "Guitarras" in cat_names

def test_search_violao_under_1000():
    results = search_products(query="violão", max_price=1000.0)
    assert len(results) > 0
    for r in results:
        assert r["price_brl"] <= 1000.0
        assert "violão" in r["name"].lower() or "violão" in r["description"].lower() or r["category_name"] == "Violões"

def test_search_takamine_gd20():
    results = search_products(query="Takamine GD20")
    assert len(results) >= 1
    gd20 = results[0]
    assert "GD20" in gd20["name"]
    assert gd20["price_brl"] == 2199.0
    assert gd20["stock_quantity"] == 5
    assert gd20["pix_price_brl"] == round(2199.0 * 0.95, 2)

def test_get_product_by_id():
    prod = get_product_by_id(81)
    assert prod is not None
    assert prod["name"] == "Yamaha C40 Nylon Natural"
    assert prod["stock_quantity"] == 12

def test_order_status():
    status = get_order_status(1)
    assert status["found"] is True
    assert status["order_id"] == 1
    assert status["status"] == "delivered"
    assert len(status["items"]) > 0

def test_active_promotions():
    promos = list_active_promotions()
    assert len(promos) == 4
    for p in promos:
        assert p["discount_percent"] > 0
        assert p["discounted_price"] < p["price_brl"]

def test_order_status_requires_order_id():
    status = get_order_status(0)
    assert status["found"] is False
    assert "obrigatório" in status["message"]