-- Order Sequence for generating order IDs
CREATE SEQUENCE order_seq
START WITH 1
INCREMENT BY 1
NOCACHE
NOCYCLE;

-- Order Table
CREATE TABLE Orders (
    orderID VARCHAR2(10) PRIMARY KEY,
    order_date DATE DEFAULT SYSDATE NOT NULL,
    totalPrice NUMBER(10,2) NOT NULL,
    userID VARCHAR2(36) NOT NULL,
    paymentMethod VARCHAR2(20) NOT NULL,
    status VARCHAR2(20) DEFAULT 'Pending'
);

-- Order Items Table
CREATE TABLE Contains (
    orderID VARCHAR2(10) REFERENCES Orders(orderID),
    productID VARCHAR2(36) NOT NULL,
    quantity NUMBER(5) NOT NULL,
    PRIMARY KEY (orderID, productID)
);

-- PL/SQL Procedure for Placing Orders
CREATE OR REPLACE PROCEDURE place_order(
    p_userID IN VARCHAR2,
    p_paymentMethod IN VARCHAR2,
    p_totalAmount IN NUMBER,
    p_items IN SYS.ODCIVARCHAR2LIST, -- Array of product IDs
    p_quantities IN SYS.ODCINUMBERLIST, -- Array of quantities
    p_orderID OUT VARCHAR2,
    p_result OUT VARCHAR2
)
IS
    v_order_num NUMBER;
    v_stock_check NUMBER;
BEGIN
    -- Generate order ID
    SELECT order_seq.NEXTVAL INTO v_order_num FROM dual;
    p_orderID := 'O' || LPAD(v_order_num, 3, '0');
    
    -- Start transaction
    SAVEPOINT start_order;
    
    -- Insert order header
    INSERT INTO Orders (orderID, totalPrice, userID, paymentMethod)
    VALUES (p_orderID, p_totalAmount, p_userID, p_paymentMethod);
    
    -- Insert order items and update stock
    FOR i IN 1..p_items.COUNT LOOP
        -- Check stock availability
        SELECT stock INTO v_stock_check 
        FROM Product 
        WHERE productID = p_items(i) FOR UPDATE;
        
        IF v_stock_check < p_quantities(i) THEN
            RAISE_APPLICATION_ERROR(-20001, 'Insufficient stock for product ' || p_items(i));
        END IF;
        
        -- Insert order item
        INSERT INTO Contains (orderID, productID, quantity)
        VALUES (p_orderID, p_items(i), p_quantities(i));
        
        -- Update stock
        UPDATE Product 
        SET stock = stock - p_quantities(i)
        WHERE productID = p_items(i);
    END LOOP;
    
    -- Clear cart
    DELETE FROM Cart WHERE userID = p_userID;
    
    COMMIT;
    p_result := 'SUCCESS';
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK TO start_order;
        p_result := 'ERROR: ' || SQLERRM;
END;
/