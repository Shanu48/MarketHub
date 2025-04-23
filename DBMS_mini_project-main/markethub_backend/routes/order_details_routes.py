from db import get_db_connection
from flask import Blueprint, jsonify, request
from flask_mysqldb import MySQL

order_details_bp = Blueprint('order_details', __name__)

def init_order_details_routes(mysql):
    @order_details_bp.route('/supplier/orders', methods=['GET'])
    def get_supplier_orders():
        supplier_id = request.args.get('supplierId')
        if not supplier_id:
            return jsonify({'error': 'Supplier ID is required'}), 400

        cursor = None  # Initialize cursor variable
        try:
            cursor = mysql.connection.cursor()
            
            # Get all orders containing products from this supplier
            cursor.execute('''
                SELECT DISTINCT o.orderID, o.date, o.status, c.cName AS customerName
                FROM Orders o
                JOIN Contains con ON o.orderID = con.orderID
                JOIN Product p ON con.productID = p.productID
                JOIN Customer c ON o.userID = c.userID
                WHERE p.userID = %s
                ORDER BY o.date DESC
            ''', (supplier_id,))
            orders = cursor.fetchall()

            # Convert to list of dicts
            column_names = [column[0] for column in cursor.description]
            orders = [dict(zip(column_names, row)) for row in orders]

            # Get products for each order
            for order in orders:
                cursor.execute('''
                    SELECT p.productID, p.pName, con.productQuantity, p.price, 
                        (con.productQuantity * p.price) AS itemTotal,
                        con.status AS confirmationStatus
                    FROM Contains con
                    JOIN Product p ON con.productID = p.productID
                    WHERE con.orderID = %s AND p.userID = %s
                ''', (order['orderID'], supplier_id))
                products = cursor.fetchall()
                product_columns = [column[0] for column in cursor.description]
                order['products'] = [dict(zip(product_columns, row)) for row in products]

            return jsonify(orders)

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if cursor:  # Only close if cursor was created
                cursor.close()


    @order_details_bp.route('/supplier/orders/confirm', methods=['POST'])
    def confirm_order_items():
        data = request.get_json()
        supplier_id = data.get('supplierId')
        order_id = data.get('orderId')
        product_ids = data.get('productIds')

        if not all([supplier_id, order_id, product_ids]):
            return jsonify({'error': 'Missing required fields'}), 400

        cursor = None  # Initialize cursor variable
        try:
            cursor = mysql.connection.cursor()
            
            # Rest of your existing confirmation logic
            
            mysql.connection.commit()
            return jsonify({'success': True, 'message': 'Order items confirmed successfully'})

        except Exception as e:
            mysql.connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            if cursor:  # Only close if cursor was created
                cursor.close()
