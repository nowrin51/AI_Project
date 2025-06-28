CREATE DATABASE IF NOT EXISTS eatopia /!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /!80016 DEFAULT ENCRYPTION='N' */;
USE eatopia;

-- Table structure for food_items
DROP TABLE IF EXISTS food_items;
CREATE TABLE food_items (
  item_id int NOT NULL,
  name varchar(255) DEFAULT NULL,
  price decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO food_items VALUES 
(1,'Biryani',300),
(2,'Tehari',280),
(3,'Mutton Rezala',600),
(4,'Shake',150),
(5,'Dosa',350),
(6,'Burger',250),
(7,'Pizza',450),
(8,'Pasta',400);

-- Table structure for order_tracking
DROP TABLE IF EXISTS order_tracking;
CREATE TABLE order_tracking (
  order_id int NOT NULL,
  status varchar(255) DEFAULT NULL,
  PRIMARY KEY (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO order_tracking VALUES 
(40,'delivered'),
(41,'in transit');

-- Table structure for orders
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
  order_id int NOT NULL,
  item_id int NOT NULL,
  quantity int DEFAULT NULL,
  total_price decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (order_id,item_id),
  KEY orders_ibfk_1 (item_id),
  CONSTRAINT orders_ibfk_1 FOREIGN KEY (item_id) REFERENCES food_items (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO orders VALUES 
(40,1,2,600.00),
(40,3,1,500.00),
(41,4,3,750.00),
(41,6,2,840.00),
(41,9,4,460.00);

-- Function: get_price_for_item
DELIMITER ;;
CREATE FUNCTION get_price_for_item(p_item_name VARCHAR(255)) RETURNS decimal(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_price DECIMAL(10, 2);
    IF (SELECT COUNT(*) FROM food_items WHERE name = p_item_name) > 0 THEN
        SELECT price INTO v_price FROM food_items WHERE name = p_item_name;
        RETURN v_price;
    ELSE
        RETURN -1;
    END IF;
END ;;
DELIMITER ;

-- Function: get_total_order_price
DELIMITER ;;
CREATE FUNCTION get_total_order_price(p_order_id INT) RETURNS decimal(10,2)
DETERMINISTIC
BEGIN
    DECLARE v_total_price DECIMAL(10, 2);
    IF (SELECT COUNT(*) FROM orders WHERE order_id = p_order_id) > 0 THEN
        SELECT SUM(total_price) INTO v_total_price FROM orders WHERE order_id = p_order_id;
        RETURN v_total_price;
    ELSE
        RETURN -1;
    END IF;
END ;;
DELIMITER ;

-- Procedure: insert_order_item
DELIMITER ;;
CREATE PROCEDURE insert_order_item(
  IN p_food_item VARCHAR(255),
  IN p_quantity INT,
  IN p_order_id INT
)
BEGIN
    DECLARE v_item_id INT;
    DECLARE v_price DECIMAL(10, 2);
    DECLARE v_total_price DECIMAL(10, 2);

    SET v_item_id = (SELECT item_id FROM food_items WHERE name = p_food_item);
    SET v_price = (SELECT get_price_for_item(p_food_item));
    SET v_total_price = v_price * p_quantity;

    INSERT INTO orders (order_id, item_id, quantity, total_price)
    VALUES (p_order_id, v_item_id, p_quantity, v_total_price);
END ;;
DELIMITER ;

