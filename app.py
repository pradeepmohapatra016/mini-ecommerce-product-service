
from flask import Flask, request, jsonify
from database import get_db_connection, initialize_database
from models import product_to_dict

app = Flask(__name__)
initialize_database()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "product-service"})


@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object required"}), 400

    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")
    description = data.get("description", "")

    if (not isinstance(name, str) or not name.strip()
            or isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price < 0
            or type(stock) is not int
            or stock < 0
            or not isinstance(description, str)):
        return jsonify({"error": "Invalid product details"}), 400

    connection = get_db_connection()
    cursor = connection.execute(
        "INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
        (name.strip(), description, price, stock)
    )
    connection.commit()
    product_id = cursor.lastrowid
    connection.close()

    return jsonify({
        "message": "Product created successfully",
        "product_id": product_id
    }), 201


@app.route("/products", methods=["GET"])
def get_products():
    connection = get_db_connection()
    products = connection.execute("SELECT * FROM products").fetchall()
    connection.close()

    return jsonify([product_to_dict(p) for p in products])


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    connection = get_db_connection()
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    connection.close()

    if product is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product_to_dict(product))


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object required"}), 400

    connection = get_db_connection()
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()

    if product is None:
        connection.close()
        return jsonify({"error": "Product not found"}), 404

    name = data.get("name", product["name"])
    description = data.get("description", product["description"])
    price = data.get("price", product["price"])
    stock = data.get("stock", product["stock"])

    if (not isinstance(name, str) or not name.strip()
            or not isinstance(description, str)
            or isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price < 0
            or type(stock) is not int
            or stock < 0):
        connection.close()
        return jsonify({"error": "Invalid product details"}), 400

    connection.execute(
        """UPDATE products
           SET name = ?, description = ?, price = ?, stock = ?
           WHERE id = ?""",
        (name.strip(), description, price, stock, product_id)
    )
    connection.commit()
    connection.close()

    return jsonify({"message": "Product updated successfully"})


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    connection = get_db_connection()
    cursor = connection.execute(
        "DELETE FROM products WHERE id = ?", (product_id,)
    )
    connection.commit()
    connection.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({"message": "Product deleted successfully"})


@app.route("/products/<int:product_id>/reserve", methods=["POST"])
def reserve_stock(product_id):
    
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object required"}), 400

    quantity = data.get("quantity")

    if type(quantity) is not int or quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400

    connection = get_db_connection()

    cursor = connection.execute(
        """UPDATE products
           SET stock = stock - ?
           WHERE id = ? AND stock >= ?""",
        (quantity, product_id, quantity)
    )

    connection.commit()

    if cursor.rowcount == 0:
        product = connection.execute(
            "SELECT id, stock FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()
        connection.close()

        if product is None:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({
            "error": "Insufficient stock",
            "available_stock": product["stock"]
        }), 409

    product = connection.execute(
        "SELECT id, stock FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    connection.close()

    return jsonify({
        "message": "Stock reserved successfully",
        "product_id": product_id,
        "reserved_quantity": quantity,
        "remaining_stock": product["stock"]
    })

    
@app.route("/products/<int:product_id>/restore", methods=["POST"])
def restore_stock(product_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object required"}), 400

    quantity = data.get("quantity")

    if type(quantity) is not int or quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400

    connection = get_db_connection()

    cursor = connection.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (quantity, product_id)
    )

    connection.commit()

    if cursor.rowcount == 0:
        connection.close()
        return jsonify({"error": "Product not found"}), 404

    product = connection.execute(
        "SELECT id, stock FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    connection.close()

    return jsonify({
        "message": "Stock restored successfully",
        "product_id": product_id,
        "restored_quantity": quantity,
        "remaining_stock": product["stock"]
    })

   

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
