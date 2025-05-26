# Food Delivery System
## Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Scope
The Food Delivery System is designed to:
- Allow customers to register, log in, view a menu, and place orders.
- Enable customers to choose between home delivery (with automatic assignment of a delivery agent) and takeaway.
- Track the lifecycle of orders (from preparation to completion) with simulated delays.
- Provide a management interface for managers to view all orders and monitor the status of delivery agents.
- Maintain a persistent state using an SQLite database and support operation via a command-line interface (CLI).

### 1.2 Definitions
- **Customer:** End user who places food orders.
- **Manager:** Administrator who oversees system operations.
- **Delivery Agent:** Staff member assigned to deliver orders to customers (not directly interacting with the CLI).
- **Home Delivery:** Orders delivered to the customer’s location.
- **Takeaway:** Orders that the customer picks up.

---

## 2. System Requirements

### 2.1 Technical Requirements
- **Programming Language:** Python
- **Database:** SQLite (database file: `food_delivery.db`)
- **Libraries and Modules:**
  - `sqlite3` for database management.
  - `threading` for simulating order status updates.
  - `datetime` and `time` for handling timestamps and delays.
  - `os` for clearing the screen and interacting with the operating system.
  - `getpass` for secure password input.

### 2.2 Other Requirements
- The system uses threading (with fixed sleep delays) to simulate the order lifecycle.
- Default menu items, a manager account, and a set of delivery agents are automatically created during the initial database setup.
---

## 3. System Features and Requirements

### 3.1 Functional Requirements
1. **User Registration:**  
   - The system shall allow new customers to register by providing a unique username and password.

2. **User Authentication:**  
   - The system shall authenticate users (customers and managers) using their username and password.

3. **Menu Display:**  
   - The system shall display a list of available food items and their prices to all logged-in users.

4. **Order Placement:**  
   - The system shall allow customers to:  
     - Select menu items  
     - Specify quantities  
     - Choose a delivery type (home delivery or takeaway)  
     - Place an order

5. **Order Validation:**  
   - The system shall ensure that at least one menu item is selected before an order can be placed.

6. **Delivery Agent Assignment:**  
   - The system shall automatically assign an available delivery agent for home delivery orders.

7. **Order Lifecycle Management:**  
   - The system shall automatically update the status and time remaining for each order as time progresses.

8. **Order History and Status:**  
   - The system shall allow customers to view:  
     - Their order history  
     - The current status of each order

9. **Manager Order Monitoring:**  
   - The system shall allow managers to view:  
     - All orders  
     - Customer details  
     - Order statuses

10. **Delivery Agent Monitoring:**  
    - The system shall allow managers to view the status (available or busy) of all delivery agents.

11. **Persistent Data Storage:**  
    - The system shall store all user, menu, order, and delivery agent data in an SQLite database.


### 3.2 Non-Functional Requirements
1. **Performance:**  
   - The system should handle multiple concurrent users.
2. **Reliability:**  
   - The system should maintain a persistent state across multiple sessions.
   - Simulated order status updates must reliably reflect the order lifecycle.
3. **Usability:**  
   - The CLI interface should be intuitive and easy to navigate.

---

## 4. Use Case Diagram
![alt text](/src/use-case-diagram.png)

---

## 5.Detailed Use Case Descriptions

### Use Case 1: Customer Registration (UC01)
**Use Case Name:** Customer Registration  
**Overview:** New customers register in the system by entering a username and password.

**Actors:**  
- **Primary:** Customer

**Pre-condition:**  
- The system is operational.  
- The customer has access to the application.

**Main Flow:**  
1. The customer selects the "Register" option.  
2. The customer enters a username and password.  
3. The customer confirms the password.  
4. The system creates a new customer account.  
5. A success message is displayed.

**Alternate Flows:**  
- **Validation fails (e.g., password mismatch):**  
  - The system displays an error message "Passwords do not match!"
- **Username already exists:**  
  - The system notifies the customer.

**Post Condition:**  
- A new customer account is created, allowing the customer to log in.


### Use Case 2: User Login (UC02)
**Use Case Name:** User Login  
**Overview:** Registered users (customers or manager) log into the system.

**Actors:**  
- **Primary:** Customer or Manager

**Pre-condition:**  
- The user must have registered an account.

**Main Flow:**  
1. The user selects the "Login" option. 
2. The user enters their username and password.  
3. The system validates the credentials.  
4. The system authenticates the user and identifies their role.  
5. The appropriate menu is displayed based on the user role.

**Alternate Flows:**  
- **Invalid credentials:**  
  - The system displays an error message "Invalid username or password."

**Post Condition:**  
- The user is logged into the system with the appropriate access level.


### Use Case 3: Place Food Order (UC03)
**Use Case Name:** Place Food Order  
**Overview:** A logged-in customer creates an order by selecting menu items, specifying quantities, choosing a delivery type, and confirming the order.

**Actors:**  
- **Primary:** Customer  
- **Secondary:** System (assigns a delivery agent for home delivery orders)

**Pre-condition:**  
- The customer is logged in.  
- The menu items are available.

**Main Flow:**  
1. The system displays the menu with items and prices.
2. The customer chooses an item ID, enters the quantity.(customer can choose multiple items)
3. The customer selects the delivery type (Home Delivery or Takeaway).  
4. The system calculates and displays the total price.
5. The customer confirms the order.
6. A unique order number is displayed along with a confirmation message.
7. For home delivery, the system checks for available delivery agents.  
8. The system creates the order in the database and, if applicable, assigns a delivery agent.  

**Alternate Flows:**  
- **No items selected:**  
  - The system prompts the customer to select at least one item.  
- **No available delivery agents (for Home Delivery):**  
  - The system notifies the customer and cancels the order.

**Post Condition:**  
- The order is recorded in the system.  
- For home delivery orders, a delivery agent is assigned.  
- The order status is initially set to "preparing" and updated over time.


### Use Case 4: View Order Status and History (UC04)
**Use Case Name:** View Order Status and History  
**Overview:** A customer views a list of their past orders and the current status of any active order.

**Actors:**  
- **Primary:** Customer

**Pre-condition:**  
- The customer is logged in.  
- At least one order has been placed.

**Main Flow:**  
1. The customer selects the "View My Orders" option.  
2. The system displays a list of all orders with basic details (order number, date/time, type, and status).  
3. The customer selects a specific order.  
4. The system displays detailed information about the selected order, including:
   - Order time and date  
   - Order type (Home Delivery or Takeaway)  
   - Current status (preparing, out for delivery, done)  
   - Assigned delivery agent (if applicable)  
   - Time remaining (if the order is in progress)  
   - Items ordered and total price  
5. The customer may refresh the information or return to the order list.

**Alternate Flows:**  
- **No orders found:**  
  - The system displays a message indicating that no orders have been placed.

**Post Condition:**  
- The customer obtains up-to-date information on their order history and current order status.


### Use Case 5: Monitor All Orders (Manager) (UC05)
**Use Case Name:** Monitor All Orders  
**Overview:** The manager views and monitors all orders in the system, including customer details and order statuses.

**Actors:**  
- **Primary:** Manager

**Pre-condition:**  
- The manager is logged in.

**Main Flow:**  
1. The manager selects the "View All Orders" option.  
2. The system displays a list of all orders with basic details (order number, customer username, date/time, type, and status).  
3. The manager selects an order for more details.  
4. The system displays detailed information about the order.  
5. The manager can refresh the list or return to the main menu.

**Alternate Flows:**  
- **No orders found:**  
  - The system informs the manager that no orders have been placed.

**Post Condition:**  
- The manager has real-time visibility into all orders in the system.


### Use Case 6: Monitor Delivery Agents (Manager) (UC06)
**Use Case Name:** Monitor Delivery Agents  
**Overview:** The manager views the status of all delivery agents.

**Actors:**  
- **Primary:** Manager

**Pre-condition:**  
- The manager is logged in.

**Main Flow:**  
1. The manager selects the "View All Delivery Agents" option.  
2. The system displays a list of delivery agents along with their current statuses (available or busy).  
3. The manager may refresh the list or return to the main menu.

**Post Condition:**  
- The manager receives up-to-date information on the availability and status of all delivery agents.


### Use Case 7: Order Management (System) (UC07)
**Use Case Name:** Order Management  
**Overview:** The system automatically manages the lifecycle of an order, updating its status based on the order type:
- **For home delivery:**  
  The order progresses from **"preparing" (0-1 min) → "out for delivery" (1-3 min) → "done" (after 3 min)**, and the assigned delivery agent’s status is reset after completion.
- **For takeaway:**  
  The order progresses from **"preparing" (0-1 min) → "done" (after 1 min)** without requiring a delivery agent.

**Actors:**  
- **Primary:** System  
- **Secondary:** Delivery Agent (for home delivery orders)

**Pre-condition:**  
- An order has been successfully placed.

**Main Flow (for Home Delivery):**  
1. The system sets the order status to "preparing" with an estimated time of 3 minutes.  
2. After 1 minute, the system updates the status to "out for delivery" with 2 minutes remaining.  
3. After 2 additional minutes, the system updates the status to "done".  
4. The system updates the assigned delivery agent’s status to "available".

**Main Flow (for Takeaway):**  
1. The system sets the order status to "preparing" with an estimated time of 1 minute.  
2. After 1 minute, the system updates the status to "done".

**Post Condition:**  
- The order lifecycle is completed.  
- Resources (delivery agents) are freed for new orders.

### Use Case 8: View Menu (UC08)
**Use Case Name:** View Menu  
**Overview:** Customers and managers can view the list of available food items along with their prices.  

**Actors:**  
- **Primary:** Customer, Manager  

**Pre-condition:**  
- The user must be logged in.  

**Main Flow:**  
1. The user selects the **"View Menu"** option from the main menu.  
2. The system displays the food items in a structured format with their prices.  


**Post Condition:**  
- The user has successfully viewed the list of available food items.  


---

### Assumptions
- **Delivery Agent Availability:**  
  If no delivery agents are available for home delivery, the system automatically cancels the order and notifies the customer.

- **Unlimited Item Availability:**  
  The system assumes an infinite stock of menu items, meaning customers can order any item without quantity restrictions.

- **Minimum Order Requirement:**  
  Customers must add at least **one item** to their order before proceeding. The system will prevent order placement if no items are selected.

- **Predefined Users**
  The system comes with hardcoded default users:  
  - Three delivery agents are preloaded into the system.  
  - One manager account is hardcoded into the system.  

---

## How to run:
- For running the app:
Go to src folder and run the command ```python3 food_delivery.py```

- For running testcases:
Stay in the root folder and run the command : ```python3 -m unittest discover -s testcases```

