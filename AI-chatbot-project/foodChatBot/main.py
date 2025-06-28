from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

import db_helper
from db_helper import get_connection, get_order_status
import generic_helper

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

# In-progress orders dictionary
inprogress_orders = {}


def add_to_order(parameters: dict, session_id: str) -> str:
    """
    Handles adding items to the order based on parameters.
    """
    food_items = parameters.get("food-item", [])
    quantities = parameters.get("number", [])

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't understand. Can you please specify food items and quantities?"
    else:
        new_food_dict = dict(zip(food_items, quantities))
        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
        else:
            current_food_dict = new_food_dict

        inprogress_orders[session_id] = current_food_dict
        logging.info(f"Updated in-progress orders: {inprogress_orders}")

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return fulfillment_text


def track_order(cnx, parameters: dict) -> str:
    """
    Handles the logic for tracking an order based on parameters.
    """
    order_id = parameters.get('order_id')
    logging.info(f"Tracking order with parameters: {parameters}")

    if not order_id:
        return "Order ID is missing. Please provide a valid order ID."

    # Convert to integer, with error handling
    try:
        order_id = int(order_id)
    except ValueError:
        return "Invalid Order ID. Please provide a numeric order ID."

    # Fetch order status from the database
    order_status = get_order_status(cnx, order_id)

    if order_status and order_status.lower() != "no order found for the provided order id.":
        return f"The order status for order ID {order_id} is: {order_status}."
    else:
        return f"No order found with order ID: {order_id}."


def save_to_db(cnx, order: dict):
    """
    Saves an order to the database.
    """
    next_order_id = db_helper.get_next_order_id(cnx)

    # Insert individual items along with quantity in orders table
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(cnx, food_item, quantity, next_order_id)

        if rcode == -1:
            return -1

    # Now insert order tracking status
    db_helper.insert_order_tracking(cnx, next_order_id, "in progress")

    return next_order_id


def complete_order(cnx, parameters: dict, session_id: str):
    """
    Completes the user's order by saving it to the database.
    """
    if session_id not in inprogress_orders:
        return "I'm having trouble finding your order. Sorry! Can you place a new order, please?"

    order = inprogress_orders[session_id]
    order_id = save_to_db(cnx, order)
    if order_id == -1:
        fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                           "Please place a new order again."
    else:
        order_total = db_helper.get_total_order_price(cnx, order_id)

        fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order ID # {order_id}. " \
                           f"Your order total is {order_total}, which you can pay at the time of delivery!"

    del inprogress_orders[session_id]
    return fulfillment_text


def remove_from_order(parameters: dict, session_id: str) -> str:
    """
    Handles removing items from the order based on parameters.
    """
    if session_id not in inprogress_orders:
        return "I'm having trouble finding your order. Sorry! Can you place a new order, please?"

    food_items_to_remove = parameters.get("food-item", [])

    if not food_items_to_remove:
        return "I didn't understand what you want to remove. Please specify the food items."

    current_food_dict = inprogress_orders[session_id]

    # Remove specified items from the current order
    for item in food_items_to_remove:
        if item in current_food_dict:
            del current_food_dict[item]
        else:
            return f"I couldn't find {item} in your order. Please check again."

    # Update the session's order
    inprogress_orders[session_id] = current_food_dict

    # If the order is empty after removal, clear the session
    if not current_food_dict:
        del inprogress_orders[session_id]
        return "Your order is now empty. You can start a new order if you'd like."

    order_str = generic_helper.get_str_from_food_dict(current_food_dict)
    return f"Okay, I've removed the specified items. Your updated order is: {order_str}. Do you need anything else?"


@app.post("/")
async def handle_request(request: Request):
    """
    Main handler for processing requests from Dialogflow.
    """
    try:
        payload = await request.json()
        logging.info(f"Payload received: {payload}")

        # Extract intent, parameters, and session ID
        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']
        session_id = payload['session'].split('/')[-1]  # Extract session ID

        cnx = get_connection()  # Get database connection

        # Intent handler dictionary
        intent_handler_dict = {
            'order.add-context: ongoing-order': lambda params: add_to_order(params, session_id),
            'order.remove - context: ongoing-order': lambda params: remove_from_order(params, session_id),
            'order-complete-context:ongoing order': lambda params: complete_order(cnx, params, session_id),
            'track.order-context: ordering-ongoing': lambda params: track_order(cnx, params),
        }

        # Match the intent and call the corresponding handler function
        if intent in intent_handler_dict:
            fulfillment_text = intent_handler_dict[intent](parameters)
            return JSONResponse(content={
                "fulfillmentText": fulfillment_text
            })

        # Default response for unrecognized intents
        return JSONResponse(content={
            "fulfillmentText": "Intent not recognized"
        })

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return JSONResponse(content={
            "fulfillmentText": "An error occurred while processing your request."
        })

    finally:
        # Close the database connection
        if 'cnx' in locals() and cnx.is_connected():
            cnx.close()


# Entry point for the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
