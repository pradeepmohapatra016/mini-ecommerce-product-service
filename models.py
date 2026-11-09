
def product_to_dict(product):
    return {
        "id": product["id"],
        "name": product["name"],
        "description": product["description"],
        "price": product["price"],
        "stock": product["stock"]
    }
