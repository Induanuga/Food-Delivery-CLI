import os
import sqlite3
import time
import threading
import getpass
from datetime import datetime

def setup_database():
    conn = sqlite3.connect('food_delivery.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        user_type TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        order_time TEXT,
        delivery_type TEXT,
        status TEXT,
        assigned_agent TEXT,
        time_remaining INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        menu_item_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (menu_item_id) REFERENCES menu (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS delivery_agents (
        id INTEGER PRIMARY KEY,
        name TEXT,
        status TEXT
    )
    ''')
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        menu_items = [
            ('Burger', 8.99),
            ('Pizza', 12.99),
            ('Salad', 6.99),
            ('Pasta', 9.99),
            ('Fries', 3.99),
            ('Soda', 1.99)
        ]
        cursor.executemany("INSERT INTO menu (name, price) VALUES (?, ?)", menu_items)
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_type = 'manager'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)", 
                      ('mngr', '123', 'manager'))
    cursor.execute("SELECT COUNT(*) FROM delivery_agents")
    if cursor.fetchone()[0] == 0:
        agents = [
            ('John Doe', 'available'),
            ('Jane Smith', 'available'),
            ('Mike Johnson', 'available')
        ]
        cursor.executemany("INSERT INTO delivery_agents (name, status) VALUES (?, ?)", agents)
    conn.commit()
    conn.close()

class User:
    def __init__(self, user_id, username, user_type):
        self.user_id = user_id
        self.username = username
        self.user_type = user_type

class MenuItem:
    def __init__(self, item_id, name, price):
        self.item_id = item_id
        self.name = name
        self.price = price

class Order:
    def __init__(self, order_id, user_id, order_time, delivery_type, status="preparing", assigned_agent=None, time_remaining=None):
        self.order_id = order_id
        self.user_id = user_id
        self.order_time = order_time
        self.delivery_type = delivery_type
        self.status = status
        self.assigned_agent = assigned_agent
        self.time_remaining = time_remaining
        self.items = []

class DeliveryAgent:
    def __init__(self, agent_id, name, status):
        self.agent_id = agent_id
        self.name = name
        self.status = status

class AuthManager:
    def __init__(self, db_path='food_delivery.db'):
        self.db_path = db_path
    
    def register_user(self, username, password, user_type='customer'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)", 
                          (username, password, user_type))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            print("Username already exists!")
            return False
        finally:
            conn.close()
    
    def login(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, user_type FROM users WHERE username = ? AND password = ?", 
                      (username, password))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
        return None

class MenuManager:
    def __init__(self, db_path='food_delivery.db'):
        self.db_path = db_path
    
    def get_menu(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price FROM menu")
        menu_items = [MenuItem(item[0], item[1], item[2]) for item in cursor.fetchall()]
        conn.close()
        return menu_items

class OrderManager:
    def __init__(self, db_path='food_delivery.db'):
        self.db_path = db_path
        
    def create_order(self, user_id, order_items, delivery_type):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        time_remaining = 3 if delivery_type == 'home_delivery' else 1
        if delivery_type == 'home_delivery':
            cursor.execute("SELECT id, name FROM delivery_agents WHERE status = 'available' LIMIT 1")
            agent = cursor.fetchone()
            if not agent:
                conn.close()
                return -1
            assigned_agent = agent[1]
            cursor.execute("UPDATE delivery_agents SET status = 'busy' WHERE id = ?", (agent[0],))
        else:
            assigned_agent = None
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO orders (user_id, order_time, delivery_type, status, assigned_agent, time_remaining) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, order_time, delivery_type, 'preparing', assigned_agent, time_remaining))
        order_id = cursor.lastrowid
        for item_id, quantity in order_items:
            cursor.execute("INSERT INTO order_items (order_id, menu_item_id, quantity) VALUES (?, ?, ?)",
                          (order_id, item_id, quantity))
        conn.commit()
        threading.Thread(target=self._handle_order_lifecycle, args=(order_id, delivery_type, assigned_agent), daemon=True).start()
        conn.close()
        return order_id
    
    def _handle_order_lifecycle(self, order_id, delivery_type, assigned_agent):
        if delivery_type == 'home_delivery':
            # For home delivery: preparing (0-1 min) -> out for delivery (1-3 min) -> done (after 3 min)
            time.sleep(60)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET status = 'out for delivery', time_remaining = 2 WHERE id = ?", (order_id,))
            conn.commit()
            conn.close()
            time.sleep(60)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET time_remaining = 1 WHERE id = ?", (order_id,))
            conn.commit()
            conn.close()
            time.sleep(60)
        else:
            # For takeaway: preparing (0-1 min) -> done (after 1 min)
            time.sleep(60)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = 'done', time_remaining = 0 WHERE id = ?", (order_id,))
        if delivery_type == 'home_delivery' and assigned_agent:
            cursor.execute("UPDATE delivery_agents SET status = 'available' WHERE name = ?", (assigned_agent,))
        conn.commit()
        conn.close()
    
    def get_order(self, order_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, order_time, delivery_type, status, assigned_agent, time_remaining 
            FROM orders WHERE id = ?
        """, (order_id,))
        order_data = cursor.fetchone()
        if not order_data:
            conn.close()
            return None
        order = Order(order_data[0], order_data[1], order_data[2], order_data[3], 
                      order_data[4], order_data[5], order_data[6])
        cursor.execute("""
            SELECT oi.menu_item_id, oi.quantity, m.name, m.price
            FROM order_items oi
            JOIN menu m ON oi.menu_item_id = m.id
            WHERE oi.order_id = ?
        """, (order_id,))
        items = cursor.fetchall()
        order.items = [(item[0], item[1], item[2], item[3]) for item in items]
        conn.close()
        return order
    
    def get_user_orders(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, order_time, delivery_type, status, assigned_agent, time_remaining 
            FROM orders WHERE user_id = ? ORDER BY order_time DESC
        """, (user_id,))
        orders = []
        for order_data in cursor.fetchall():
            order = Order(order_data[0], order_data[1], order_data[2], order_data[3], 
                          order_data[4], order_data[5], order_data[6])
            cursor.execute("""
                SELECT oi.menu_item_id, oi.quantity, m.name, m.price
                FROM order_items oi
                JOIN menu m ON oi.menu_item_id = m.id
                WHERE oi.order_id = ?
            """, (order.order_id,))
            items = cursor.fetchall()
            order.items = [(item[0], item[1], item[2], item[3]) for item in items]
            orders.append(order)
        conn.close()
        return orders
    
    def get_all_orders(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id, o.user_id, o.order_time, o.delivery_type, o.status, o.assigned_agent, o.time_remaining, u.username
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.order_time DESC
        """)
        orders = []
        for order_data in cursor.fetchall():
            order = Order(order_data[0], order_data[1], order_data[2], order_data[3], 
                          order_data[4], order_data[5], order_data[6])
            order.username = order_data[7]
            cursor.execute("""
                SELECT oi.menu_item_id, oi.quantity, m.name, m.price
                FROM order_items oi
                JOIN menu m ON oi.menu_item_id = m.id
                WHERE oi.order_id = ?
            """, (order.order_id,))
            items = cursor.fetchall()
            order.items = [(item[0], item[1], item[2], item[3]) for item in items]
            orders.append(order)
        conn.close()
        return orders

class DeliveryAgentManager:
    def __init__(self, db_path='food_delivery.db'):
        self.db_path = db_path
    
    def get_all_agents(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status FROM delivery_agents")
        agents = [DeliveryAgent(agent[0], agent[1], agent[2]) for agent in cursor.fetchall()]
        conn.close()
        return agents

class FoodDeliveryApp:
    def __init__(self):
        setup_database()
        self.auth_manager = AuthManager()
        self.menu_manager = MenuManager()
        self.order_manager = OrderManager()
        self.agent_manager = DeliveryAgentManager()
        self.current_user = None
    
    def start(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 50)
        print("           FOOD DELIVERY SYSTEM")
        print("=" * 50)
        while True:
            if not self.current_user:
                self.show_auth_menu()
            elif self.current_user.user_type == 'customer':
                self.show_customer_menu()
            elif self.current_user.user_type == 'manager':
                self.show_manager_menu()
            time.sleep(0.1)
    
    def show_auth_menu(self):
        print("\nAuthentication Menu:")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            self.login()
        elif choice == '2':
            self.register()
        elif choice == '3':
            print("Thank you for using the Food Delivery System!")
            exit(0)
        else:
            print("Invalid choice. Please try again.")
    
    def login(self):
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        user = self.auth_manager.login(username, password)
        if user:
            self.current_user = user
            print(f"Welcome, {user.username}!")
        else:
            print("Invalid username or password.")
    
    def register(self):
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match!")
            return
        if self.auth_manager.register_user(username, password):
            print("Registration successful! You can now login.")
        else:
            print("Registration failed. Please try again.")

    def view_menu(self):
        menu_items = self.menu_manager.get_menu()
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\nMenu Items:")
        print("=" * 40)
        print(f"{'ID':<5}{'Name':<20}{'Price':<10}")
        print("-" * 40)
        for item in menu_items:
            print(f"{item.item_id:<5}{item.name:<20}${item.price:<10.2f}")
        print("=" * 40)
        input("\nPress Enter to continue...")
    
    def show_customer_menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\nWelcome, {self.current_user.username}!")
        print("\nCustomer Menu:")
        print("1. View Menu")
        print("2. Place Order")
        print("3. View My Orders")
        print("4. Logout")
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            self.view_menu()
        elif choice == '2':
            self.place_order()
        elif choice == '3':
            self.view_my_orders()
        elif choice == '4':
            self.current_user = None
            print("Logged out successfully.")
        else:
            print("Invalid choice. Please try again.")
    
    def place_order(self):
        menu_items = self.menu_manager.get_menu()
        print("\nMenu:")
        for item in menu_items:
            print(f"{item.item_id}. {item.name} - ${item.price:.2f}")
        order_items = []
        total_price = 0
        while True:
            item_choice = input("\nEnter item number to add (or 'done' to finish): ")
            if item_choice.lower() == 'done':
                if not order_items:
                    print("You must add at least one item to your order.")
                    continue
                break
            try:
                item_id = int(item_choice)
                item = next((i for i in menu_items if i.item_id == item_id), None)
                if not item:
                    print("Invalid item number.")
                    continue
                quantity = int(input(f"Enter quantity for {item.name}: "))
                if quantity <= 0:
                    print("Quantity must be positive.")
                    continue
                order_items.append((item_id, quantity))
                total_price += item.price * quantity
                print(f"Added {quantity} x {item.name}")
            except ValueError:
                print("Please enter a valid number.")
        print("\nDelivery Type:")
        print("1. Home Delivery")
        print("2. Takeaway")
        delivery_choice = input("Enter your choice (1-2): ")
        if delivery_choice == '1':
            delivery_type = 'home_delivery'
        elif delivery_choice == '2':
            delivery_type = 'takeaway'
        else:
            print("Invalid choice. Defaulting to takeaway.")
            delivery_type = 'takeaway'
        print(f"\nTotal Price: ${total_price:.2f}")
        confirm = input("Confirm order (y/n): ")
        if confirm.lower() == 'y':
            order_id = self.order_manager.create_order(
                self.current_user.user_id,
                order_items,
                delivery_type
            )
            if order_id == -1:
                print("Sorry, your order has been cancelled. No delivery agents are currently available.")
            else:
                print(f"Order #{order_id} placed successfully!")
            input("Press Enter to continue...")
        else:
            print("Order cancelled.")
    
    def view_my_orders(self):
        while True:
            orders = self.order_manager.get_user_orders(self.current_user.user_id)
            if not orders:
                print("You don't have any orders yet.")
                input("Press Enter to continue...")
                return
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nMy Orders:")
            for i, order in enumerate(orders):
                delivery_type = "Home Delivery" if order.delivery_type == 'home_delivery' else "Takeaway"
                print(f"{i+1}. Order #{order.order_id} - {order.order_time} - {delivery_type} - Status: {order.status}")
            print("\n0. Back to Menu")
            choice = input("Enter order number to view details (or 0 to go back): ")
            if choice == '':
                continue
            try:
                if choice == '0':
                    break
                idx = int(choice) - 1
                if 0 <= idx < len(orders):
                    self.show_order_details(orders[idx])
                else:
                    print("Invalid choice.")
                    time.sleep(1)
            except ValueError:
                print("Please enter a valid number.")
                time.sleep(1)
    
    def show_order_details(self, order):
        while True:
            order = self.order_manager.get_order(order.order_id)
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"\nOrder #{order.order_id} Details:")
            print(f"Time: {order.order_time}")
            print(f"Type: {'Home Delivery' if order.delivery_type == 'home_delivery' else 'Takeaway'}")
            print(f"Status: {order.status}")
            if order.delivery_type == 'home_delivery':
                print(f"Delivery Agent: {order.assigned_agent}")
            if order.status != 'done' and order.time_remaining is not None:
                print(f"Time Remaining: {order.time_remaining} min")
            print("\nItems:")
            total = 0
            for item in order.items:
                price = item[1] * item[3]
                total += price
                print(f"- {item[1]} x {item[2]} - ${price:.2f}")
            print(f"\nTotal: ${total:.2f}")
            print("\nPress Enter to refresh or '0' to go back")
            choice = input()
            if choice == '0':
                break

    def show_manager_menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\nWelcome, Manager {self.current_user.username}!")
        print("\nManager Menu:")
        print("1. View All Orders")
        print("2. View All Delivery Agents")
        print("3. View Menu")
        print("4. Logout")
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            self.view_all_orders()
        elif choice == '2':
            self.view_all_agents()
        elif choice == '3':
            self.view_menu()
        elif choice == '4':
            self.current_user = None
            print("Logged out successfully.")
        else:
            print("Invalid choice. Please try again.")
    
    def view_all_orders(self):
        while True:
            orders = self.order_manager.get_all_orders()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nAll Orders:")
            if not orders:
                print("No orders found.")
            else:
                for i, order in enumerate(orders):
                    delivery_type = "Home Delivery" if order.delivery_type == 'home_delivery' else "Takeaway"
                    print(f"{i+1}. Order #{order.order_id} - User: {order.username} - {order.order_time} - {delivery_type} - Status: {order.status}")
            print("\n0. Back to Menu")
            choice = input("Enter order number to view details (or 0 to go back): ")
            try:
                if choice == '0':
                    break
                idx = int(choice) - 1
                if 0 <= idx < len(orders):
                    self.show_order_details(orders[idx])
                else:
                    print("Invalid choice.")
                    time.sleep(1)
            except ValueError:
                print("Please enter a valid number.")
                time.sleep(1)
    
    def view_all_agents(self):
        while True:
            agents = self.agent_manager.get_all_agents()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nAll Delivery Agents:")
            for agent in agents:
                print(f"ID: {agent.agent_id} - Name: {agent.name} - Status: {agent.status}")
            print("\nPress Enter to refresh or '0' to go back")
            choice = input()
            if choice == '0':
                break

if __name__ == "__main__":
    app = FoodDeliveryApp()
    app.start()