import unittest
from src.food_delivery import (
    AuthManager,
    MenuManager,
    OrderManager,
    DeliveryAgentManager,
    setup_database,
    FoodDeliveryApp
)
import sqlite3
import uuid
import time
import io
from unittest.mock import patch

class TestFoodDeliverySystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Setting up TestFoodDeliverySystem")
        setup_database()
        cls.auth_manager = AuthManager()
        cls.menu_manager = MenuManager()
        cls.order_manager = OrderManager()
        cls.agent_manager = DeliveryAgentManager()
        existing_user = cls.auth_manager.login("valid_user", "password123")
        if not existing_user:
            cls.auth_manager.register_user("valid_user", "password123")
        existing_manager = cls.auth_manager.login("manager_user", "adminpass")
        if not existing_manager:
            cls.auth_manager.register_user("manager_user", "adminpass", "manager")

    def setUp(self):
        print("Resetting delivery agents to available")
        conn = sqlite3.connect('food_delivery.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE delivery_agents SET status = 'available'")
        conn.commit()
        conn.close()

    def test_user_registration(self):
        print("Running test_user_registration")
        unique_username = "test_user_" + str(uuid.uuid4())
        result = self.auth_manager.register_user(unique_username, "password123")
        self.assertTrue(result)
    
    def test_duplicate_user_registration(self):
        print("Running test_duplicate_user_registration")
        unique_username = "duplicate_user_" + str(uuid.uuid4())
        self.auth_manager.register_user(unique_username, "password123")
        result = self.auth_manager.register_user(unique_username, "password123")
        self.assertFalse(result)
    
    def test_user_login_valid(self):
        print("Running test_user_login_valid")
        self.auth_manager.register_user("valid_user", "password123")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user)
    
    def test_user_login_invalid(self):
        print("Running test_user_login_invalid")
        user = self.auth_manager.login("invalid_user", "wrongpass")
        self.assertIsNone(user)
    
    def test_fetch_menu(self):
        print("Running test_fetch_menu")
        menu = self.menu_manager.get_menu()
        self.assertGreater(len(menu), 0)
    
    def test_place_order_takeaway(self):
        print("Running test_place_order_takeaway")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 2)], "takeaway")
        self.assertGreater(order_id, 0)
    
    def test_place_order_home_delivery(self):
        print("Running test_place_order_home_delivery")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 2)], "home_delivery")
        self.assertGreater(order_id, 0)
    
    def test_place_order_no_available_agent(self):
        print("Running test_place_order_no_available_agent")
        conn = sqlite3.connect('food_delivery.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE delivery_agents SET status = 'busy'")
        conn.commit()
        conn.close()
        
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 2)], "home_delivery")
        self.assertEqual(order_id, -1)
    
    def test_fetch_order(self):
        print("Running test_fetch_order")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 2)], "takeaway")
        order = self.order_manager.get_order(order_id)
        self.assertIsNotNone(order)
        self.assertEqual(order.order_id, order_id)
    
    def test_fetch_all_orders(self):
        print("Running test_fetch_all_orders")
        orders = self.order_manager.get_all_orders()
        self.assertGreaterEqual(len(orders), 0)
    
    def test_fetch_agents(self):
        print("Running test_fetch_agents")
        agents = self.agent_manager.get_all_agents()
        self.assertGreater(len(agents), 0)
    
    def test_order_status_update(self):
        print("Running test_order_status_update")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 1)], "home_delivery")
        order = self.order_manager.get_order(order_id)
        self.assertIsNotNone(order, "Order creation failed")
        self.assertIn(order.status, ["preparing", "out for delivery", "done"])
    
    def test_invalid_order_fetch(self):
        print("Running test_invalid_order_fetch")
        order = self.order_manager.get_order(99999)
        self.assertIsNone(order)
    
    def test_fetch_user_orders(self):
        print("Running test_fetch_user_orders")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        orders = self.order_manager.get_user_orders(user.user_id)
        self.assertGreaterEqual(len(orders), 0)
    
    def test_register_manager(self):
        print("Running test_register_manager")
        unique_manager = "manager_user_" + str(uuid.uuid4())
        result = self.auth_manager.register_user(unique_manager, "adminpass", "manager")
        self.assertTrue(result)
    
    def test_login_manager(self):
        print("Running test_login_manager")
        user = self.auth_manager.login("mngr", "123")
        self.assertIsNotNone(user)
        self.assertEqual(user.user_type, "manager")
    
    def test_menu_not_empty(self):
        print("Running test_menu_not_empty")
        menu = self.menu_manager.get_menu()
        self.assertGreater(len(menu), 0)
    
    def test_invalid_login(self):
        print("Running test_invalid_login")
        user = self.auth_manager.login("unknown", "wrong")
        self.assertIsNone(user)
    
    def test_add_multiple_orders(self):
        print("Running test_add_multiple_orders")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order1 = self.order_manager.create_order(user.user_id, [(1, 1)], "takeaway")
        order2 = self.order_manager.create_order(user.user_id, [(2, 1)], "home_delivery")
        self.assertGreater(order1, 0)
        self.assertGreater(order2, 0)
        
    def test_order_with_invalid_menu_item(self):
        print("Running test_order_with_invalid_menu_item")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(9999, 1)], "takeaway")
        order = self.order_manager.get_order(order_id)
        self.assertEqual(len(order.items), 0)
    
    def test_order_with_zero_quantity(self):
        print("Running test_order_with_zero_quantity")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 0)], "takeaway")
        order = self.order_manager.get_order(order_id)
        if order.items:
            self.assertEqual(order.items[0][1], 0)
        else:
            self.assertEqual(len(order.items), 0)
    
    def test_order_with_negative_quantity(self):
        print("Running test_order_with_negative_quantity")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, -5)], "takeaway")
        order = self.order_manager.get_order(order_id)
        if order.items:
            self.assertEqual(order.items[0][1], -5)
        else:
            self.assertEqual(len(order.items), 0)
    
    def test_register_empty_username(self):
        print("Running test_register_empty_username")
        result = self.auth_manager.register_user("", "password123")
        self.assertTrue(isinstance(result, bool))
    
    def test_register_empty_password(self):
        print("Running test_register_empty_password")
        unique_username = "empty_password_" + str(uuid.uuid4())
        result = self.auth_manager.register_user(unique_username, "")
        self.assertTrue(result)
    
    def test_get_user_orders_empty(self):
        print("Running test_get_user_orders_empty")
        unique_username = "no_orders_" + str(uuid.uuid4())
        self.auth_manager.register_user(unique_username, "password123")
        user = self.auth_manager.login(unique_username, "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        orders = self.order_manager.get_user_orders(user.user_id)
        self.assertEqual(len(orders), 0)
    
    def test_invalid_delivery_type(self):
        print("Running test_invalid_delivery_type")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 1)], "invalid_type")
        order = self.order_manager.get_order(order_id)
        self.assertIsNone(order.assigned_agent)
        self.assertEqual(order.time_remaining, 1)
    
    def test_initial_order_status_takeaway(self):
        print("Running test_initial_order_status_takeaway")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 2)], "takeaway")
        order = self.order_manager.get_order(order_id)
        self.assertEqual(order.status, "preparing")
    
    def test_initial_order_status_home_delivery(self):
        print("Running test_initial_order_status_home_delivery")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id = self.order_manager.create_order(user.user_id, [(1, 2)], "home_delivery")
        order = self.order_manager.get_order(order_id)
        self.assertEqual(order.status, "preparing")
    
    def test_get_all_orders_ordering(self):
        print("Running test_get_all_orders_ordering")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        order_id1 = self.order_manager.create_order(user.user_id, [(1, 1)], "takeaway")
        time.sleep(1)
        order_id2 = self.order_manager.create_order(user.user_id, [(2, 1)], "takeaway")
        orders = self.order_manager.get_all_orders()
        self.assertGreaterEqual(orders[0].order_time, orders[1].order_time)
    
    def test_order_total_calculation(self):
        print("Running test_order_total_calculation")
        user = self.auth_manager.login("valid_user", "password123")
        self.assertIsNotNone(user, "Login failed: User is None")
        menu = {item.item_id: item for item in self.menu_manager.get_menu()}
        order_items = [(1, 2), (2, 3)]
        order_id = self.order_manager.create_order(user.user_id, order_items, "takeaway")
        order = self.order_manager.get_order(order_id)
        expected_total = 0
        for item_id, qty in order_items:
            if item_id in menu:
                expected_total += menu[item_id].price * qty
        calculated_total = sum(qty * price for _, qty, _, price in order.items)
        self.assertAlmostEqual(expected_total, calculated_total, places=2)
    
    def test_view_menu_output(self):
        print("Running test_view_menu_output")
        app = FoodDeliveryApp()
        with patch('builtins.input', return_value=''):
            captured_output = io.StringIO()
            with patch('sys.stdout', new=captured_output):
                app.view_menu()
            output = captured_output.getvalue()
            self.assertIn("Menu Items:", output)
    
    def test_show_customer_menu_view_menu(self):
        print("Running test_show_customer_menu_view_menu")
        app = FoodDeliveryApp()
        class DummyUser:
            username = "dummy_customer"
            user_id = 1
        app.current_user = DummyUser()
        with patch('builtins.input', side_effect=["1", ""]):
            captured_output = io.StringIO()
            with patch('sys.stdout', new=captured_output):
                app.show_customer_menu()
            output = captured_output.getvalue()
            self.assertIn("Menu Items:", output)
    
    def test_show_manager_menu_view_menu(self):
        print("Running test_show_manager_menu_view_menu")
        app = FoodDeliveryApp()
        class DummyUser:
            username = "dummy_manager"
            user_id = 1
            user_type = "manager"
        app.current_user = DummyUser()
        with patch('builtins.input', side_effect=["3", ""]):
            captured_output = io.StringIO()
            with patch('sys.stdout', new=captured_output):
                app.show_manager_menu()
            output = captured_output.getvalue()
            self.assertIn("Menu Items:", output)
    
if __name__ == '__main__':
    unittest.main()
