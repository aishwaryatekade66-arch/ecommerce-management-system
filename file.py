import mysql.connector


class EcommerceApp:

    # ================= CONSTRUCTOR =================
    def __init__(self):
        self.current_user = None

    # ================= DATABASE CONNECTION =================
    def get_db(self):
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345@tekade",
            database="ecommerce_db"
        )
        return conn

    # ================= MAIN MENU =================
    def run(self):

        while True:

            # -------- NOT LOGGED IN --------
            if not self.current_user:

                print("\n=================================")
                print("       ECOMMERCE SYSTEM")
                print("=================================")
                print("1. BROWSE CATALOG")
                print("2. LOGIN")
                print("3. REGISTER")
                print("4. EXIT")

                choice = input("Select an option (1-4): ").strip()

                if choice == "1":
                    self.view_products()

                elif choice == "2":
                    self.login()

                elif choice == "3":
                    self.register()

                elif choice == "4":
                    print("Thank you for using Ecommerce System!")
                    break

                else:
                    print("[!] Invalid choice.")

            # -------- LOGGED IN --------
            else:

                print(
                    f"\n---- Logged in as: "
                    f"{self.current_user['name']} "
                    f"[{self.current_user['role'].upper()}] ----"
                )

                print("1. Browse Catalog")
                print("2. Add Item to Cart")
                print("3. View Cart")
                print("4. Checkout")
                print("5. Order History")

                if self.current_user["role"] == "admin":
                    print("6. [Admin] Add New Product")
                    print("7. [Admin] View All Customer Orders")

                print("0. LOGOUT")

                choice = input("Select an option: ").strip()

                if choice == "1":
                    self.view_products()

                elif choice == "2":
                    self.add_to_cart()

                elif choice == "3":
                    self.view_cart()

                elif choice == "4":
                    self.checkout()

                elif choice == "5":
                    self.view_order_history()

                elif choice == "6":
                    self.admin_add_product()

                elif choice == "7":
                    self.admin_view_orders()

                elif choice == "0":
                    self.logout()

                else:
                    print("[!] Invalid choice.")

    # ================= VIEW PRODUCTS =================
    def view_products(self):

        print("\n" + "=" * 80)
        print(
            f"{'ID':<5}"
            f"{'PRODUCT NAME':<30}"
            f"{'CATEGORY':<15}"
            f"{'PRICE':<12}"
            f"{'STOCK':<8}"
        )
        print("=" * 80)

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT * FROM products ORDER BY id ASC"
            )

            products = cursor.fetchall()

            if not products:
                print("Catalog is empty.")
                return

            for p in products:

                print(
                    f"{p['id']:<5}"
                    f"{p['name']:<30}"
                    f"{p['category']:<15}"
                    f"Rs.{float(p['price']):<10.2f}"
                    f"{p['stock']:<8}"
                )

            print("=" * 80)

        except mysql.connector.Error as err:
            print(f"[!] Database Error: {err}")

        finally:
            cursor.close()
            conn.close()

    # ================= REGISTER =================
    def register(self):

        print("\n------ REGISTER NEW USER ------")

        name = input("Enter full name: ").strip()
        email = input("Enter Email: ").strip()
        pwd = input("Enter password: ").strip()

        if not name or not email or not pwd:
            print("[!] All fields are required.")
            return

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                print("[!] Email is already registered. Please login.")
                return

            # UPDATED: password instead of password_hash
            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (name, email, pwd)
            )

            conn.commit()

            print("[+] Registration successful!")
            print("[+] You can now login.")

        except mysql.connector.Error as err:

            conn.rollback()
            print(f"[!] DATABASE ERROR: {err}")

        finally:

            cursor.close()
            conn.close()

    # ================= LOGIN =================
    def login(self):

        print("\n----------- LOGIN -----------")

        email = input("Email: ").strip()
        pwd = input("Enter password: ").strip()

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )

            user = cursor.fetchone()

            # UPDATED: password instead of password_hash
            if user and user["password"] == pwd:

                self.current_user = {
                    "id": user["id"],
                    "name": user["name"],
                    "role": user["role"]
                }

                print(
                    f"\n[+] Welcome back, "
                    f"{user['name']}! "
                    f"(Role: {user['role']})"
                )

            else:

                print("[!] INVALID EMAIL OR PASSWORD.")

        except mysql.connector.Error as err:

            print(f"[!] DATABASE ERROR: {err}")

        finally:

            cursor.close()
            conn.close()

    # ================= ADD TO CART =================
    def add_to_cart(self):

        self.view_products()

        try:

            prod_id = int(
                input("\nEnter Product ID to add: ")
            )

            qty = int(
                input("Enter Quantity: ")
            )

            if qty <= 0:
                print("[!] Quantity must be at least 1.")
                return

        except ValueError:

            print("[!] Invalid input. Numbers only.")
            return

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute(
                """
                SELECT stock
                FROM products
                WHERE id = %s
                """,
                (prod_id,)
            )

            product = cursor.fetchone()

            if not product:

                print("[!] Product not found.")
                return

            if product["stock"] < qty:

                print(
                    f"[!] Insufficient stock. "
                    f"Only {product['stock']} available."
                )
                return

            # Check if product already exists in cart
            cursor.execute(
                """
                SELECT id, quantity
                FROM cart_items
                WHERE user_id = %s
                AND product_id = %s
                """,
                (self.current_user["id"], prod_id)
            )

            existing = cursor.fetchone()

            if existing:

                cursor.execute(
                    """
                    UPDATE cart_items
                    SET quantity = quantity + %s
                    WHERE id = %s
                    """,
                    (qty, existing["id"])
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO cart_items
                    (user_id, product_id, quantity)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        self.current_user["id"],
                        prod_id,
                        qty
                    )
                )

            conn.commit()

            print("[+] Item added to cart successfully.")

        except mysql.connector.Error as err:

            conn.rollback()
            print(f"[!] DATABASE ERROR: {err}")

        finally:

            cursor.close()
            conn.close()

    # ================= VIEW CART =================
    def view_cart(self):

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute(
                """
                SELECT
                    ci.product_id,
                    p.name,
                    p.price,
                    ci.quantity,
                    (p.price * ci.quantity) AS subtotal

                FROM cart_items ci

                JOIN products p
                ON ci.product_id = p.id

                WHERE ci.user_id = %s
                """,
                (self.current_user["id"],)
            )

            items = cursor.fetchall()

            print("\n" + "-" * 75)

            print(
                f"{'PID':<6}"
                f"{'PRODUCT NAME':<30}"
                f"{'PRICE':<12}"
                f"{'QTY':<8}"
                f"{'SUBTOTAL':<12}"
            )

            print("-" * 75)

            if not items:

                print("Your cart is empty.")
                print("-" * 75)

                return False

            total = 0

            for item in items:

                total += float(item["subtotal"])

                print(
                    f"{item['product_id']:<6}"
                    f"{item['name']:<30}"
                    f"Rs.{float(item['price']):<9.2f}"
                    f"{item['quantity']:<8}"
                    f"Rs.{float(item['subtotal']):<10.2f}"
                )

            print("-" * 75)

            print(
                f"Total Cart Value: Rs.{total:.2f}"
            )

            print("-" * 75)

            return True

        except mysql.connector.Error as err:

            print(f"[!] DATABASE ERROR: {err}")
            return False

        finally:

            cursor.close()
            conn.close()

    # ================= CHECKOUT =================
    def checkout(self):

        if not self.view_cart():
            return

        confirm = input(
            "\nProceed to checkout? (y/n): "
        ).strip().lower()

        if confirm != "y":

            print("Checkout canceled.")
            return

        address = input(
            "Enter delivery address: "
        ).strip()

        if not address:

            print("[!] Delivery address cannot be empty.")
            return

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            conn.start_transaction()

            cursor.execute(
                """
                SELECT
                    ci.product_id,
                    ci.quantity,
                    p.price,
                    p.stock

                FROM cart_items ci

                JOIN products p
                ON ci.product_id = p.id

                WHERE ci.user_id = %s

                FOR UPDATE
                """,
                (self.current_user["id"],)
            )

            items = cursor.fetchall()

            if not items:

                conn.rollback()

                print("[!] Cart is empty.")
                return

            total_amount = 0

            # Check stock
            for item in items:

                if item["stock"] < item["quantity"]:

                    conn.rollback()

                    print(
                        f"[!] Checkout failed. "
                        f"Product ID {item['product_id']} "
                        f"has insufficient stock."
                    )

                    return

                total_amount += (
                    float(item["price"])
                    * item["quantity"]
                )

            # Create order
            cursor.execute(
                """
                INSERT INTO orders
                (user_id, total_amount, delivery_address)
                VALUES (%s, %s, %s)
                """,
                (
                    self.current_user["id"],
                    total_amount,
                    address
                )
            )

            order_id = cursor.lastrowid

            # Insert order items
            for item in items:

                cursor.execute(
                    """
                    INSERT INTO order_items
                    (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        item["product_id"],
                        item["quantity"],
                        item["price"]
                    )
                )

                # Update product stock
                cursor.execute(
                    """
                    UPDATE products
                    SET stock = stock - %s
                    WHERE id = %s
                    """,
                    (
                        item["quantity"],
                        item["product_id"]
                    )
                )

            # Clear cart
            cursor.execute(
                """
                DELETE FROM cart_items
                WHERE user_id = %s
                """,
                (self.current_user["id"],)
            )

            conn.commit()

            print(
                f"\n[+] Order #{order_id} "
                f"placed successfully!"
            )

            print(
                f"Total Paid: Rs.{total_amount:.2f}"
            )

        except Exception as e:

            conn.rollback()

            print(
                f"[!] Order processing error: {e}"
            )

        finally:

            cursor.close()
            conn.close()

    # ================= ORDER HISTORY =================
    def view_order_history(self):

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute(
                """
                SELECT
                    o.id,
                    o.total_amount,
                    o.status,
                    o.created_at,

                    GROUP_CONCAT(
                        CONCAT(
                            p.name,
                            ' (x',
                            oi.quantity,
                            ')'
                        )
                        SEPARATOR ', '
                    ) AS items

                FROM orders o

                JOIN order_items oi
                ON o.id = oi.order_id

                JOIN products p
                ON oi.product_id = p.id

                WHERE o.user_id = %s

                GROUP BY
                    o.id,
                    o.total_amount,
                    o.status,
                    o.created_at

                ORDER BY o.created_at DESC
                """,
                (self.current_user["id"],)
            )

            orders = cursor.fetchall()

            print("\n------- YOUR ORDER HISTORY -------")

            if not orders:

                print("No previous orders found.")
                return

            for order in orders:

                print(
                    f"\nOrder ID: #{order['id']}"
                )

                print(
                    f"Date: {order['created_at']}"
                )

                print(
                    f"Status: {order['status']}"
                )

                print(
                    f"Items: {order['items']}"
                )

                print(
                    f"Total Amount: "
                    f"Rs.{float(order['total_amount']):.2f}"
                )

                print("-" * 50)

        except mysql.connector.Error as err:

            print(f"[!] DATABASE ERROR: {err}")

        finally:

            cursor.close()
            conn.close()

    # ================= ADMIN ADD PRODUCT =================
    def admin_add_product(self):

        if self.current_user.get("role") != "admin":

            print("[!] Unauthorized access.")
            return

        print("\n-------- ADD NEW PRODUCT --------")

        name = input(
            "Product Name: "
        ).strip()

        category = input(
            "Category: "
        ).strip()

        try:

            price = float(
                input("Price (INR): ")
            )

            stock = int(
                input("Stock Quantity: ")
            )

            if price < 0 or stock < 0:

                print(
                    "[!] Price and stock "
                    "cannot be negative."
                )

                return

        except ValueError:

            print(
                "[!] Invalid numeric values."
            )

            return

        conn = self.get_db()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO products
                (name, category, price, stock)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    name,
                    category,
                    price,
                    stock
                )
            )

            conn.commit()

            print(
                f"[+] Product '{name}' "
                f"added successfully."
            )

        except mysql.connector.Error as err:

            conn.rollback()

            print(
                f"[!] DATABASE ERROR: {err}"
            )

        finally:

            cursor.close()
            conn.close()

    # ================= ADMIN VIEW ORDERS =================
    def admin_view_orders(self):

        if self.current_user.get("role") != "admin":

            print("[!] Unauthorized access.")
            return

        conn = self.get_db()
        cursor = conn.cursor(dictionary=True)

        try:

            cursor.execute(
                """
                SELECT
                    o.id AS order_id,
                    u.name AS customer_name,
                    u.email,
                    o.total_amount,
                    o.status,
                    o.delivery_address,
                    o.created_at

                FROM orders o

                JOIN users u
                ON o.user_id = u.id

                ORDER BY o.created_at DESC
                """
            )

            orders = cursor.fetchall()

            print("\n" + "=" * 90)
            print("              ALL CUSTOMER ORDERS")
            print("=" * 90)

            if not orders:

                print("No orders found.")
                return

            for order in orders:

                print(
                    f"\nOrder ID: #{order['order_id']}"
                )

                print(
                    f"Customer: {order['customer_name']}"
                )

                print(
                    f"Email: {order['email']}"
                )

                print(
                    f"Amount: Rs."
                    f"{float(order['total_amount']):.2f}"
                )

                print(
                    f"Status: {order['status']}"
                )

                print(
                    f"Address: "
                    f"{order['delivery_address']}"
                )

                print(
                    f"Date: {order['created_at']}"
                )

                print("-" * 60)

        except mysql.connector.Error as err:

            print(
                f"[!] DATABASE ERROR: {err}"
            )

        finally:

            cursor.close()
            conn.close()

    # ================= LOGOUT =================
    def logout(self):

        self.current_user = None

        print(
            "[+] Logged out successfully."
        )


# ================= START APPLICATION =================

ecom = EcommerceApp()
ecom.run()