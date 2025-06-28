import mysql.connector
from mysql.connector import Error

# Helper function to establish a database connection
def get_connection():
    """
    Establishes and returns a new database connection.
    """
    try:
        return mysql.connector.connect(
            host="localhost",        # Replace with your database host
            user="root",             # Replace with your MySQL username
            password="221251",       # Replace with your MySQL password
            database="eatopia"       # Replace with your database name
        )
    except Error as e:
        print(f"Error connecting to the database: {e}")
        raise e

def insert_order_tracking(cnx, order_id, status):
    """
    Inserts an order tracking record into the order_tracking table.
    """
    cursor = cnx.cursor()
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))
    cnx.commit()
    cursor.close()

def insert_order_item(cnx, food_item, quantity, order_id):
    """
    Inserts an item into the orders table using a stored procedure.
    """
    try:
        cursor = cnx.cursor()
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))
        cnx.commit()
        cursor.close()
        print("Order item inserted successfully!")
        return 1
    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")
        cnx.rollback()
        return -1
    except Exception as e:
        print(f"An error occurred: {e}")
        cnx.rollback()
        return -1

def get_next_order_id(cnx):
    """
    Fetches the next available order ID by finding the maximum order_id in the orders table.
    """
    cursor = cnx.cursor()
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()
    return 1 if result is None else result + 1

def get_total_order_price(cnx, order_id):
    """
    Fetches the total price of an order using a stored procedure or query.
    """
    cursor = cnx.cursor()
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)
    result = cursor.fetchone()[0]
    cursor.close()
    return result

def get_order_status(cnx, order_id):
    """
    Fetches the status of an order from the order_tracking table using order_id.
    """
    cursor = cnx.cursor()
    query = "SELECT status FROM order_tracking WHERE order_id = %s"
    cursor.execute(query, (order_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else "No order found for the provided order ID."