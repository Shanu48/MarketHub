# import cx_Oracle
# import json

# def place_order(user_id, payment_method, total_amount, items):
#     """
#     Calls the PL/SQL place_order procedure
    
#     Args:
#         user_id: Customer user ID
#         payment_method: Payment method string
#         total_amount: Total order amount
#         items: List of dicts with product_id and quantity
    
#     Returns:
#         Dictionary with order_id and result message
#     """
#     try:
#         # Connect to Oracle database
#         connection = cx_Oracle.connect(
#             user="your_username",
#             password="your_password",
#             dsn="your_host:your_port/your_service"
#         )
        
#         # Prepare arrays for products and quantities
#         product_ids = [item['product_id'] for item in items]
#         quantities = [item['quantity'] for item in items]
        
#         # Create output variables
#         order_id = connection.cursor().var(cx_Oracle.STRING)
#         result = connection.cursor().var(cx_Oracle.STRING)
        
#         # Call the PL/SQL procedure
#         with connection.cursor() as cursor:
#             cursor.callproc("place_order", [
#                 user_id,
#                 payment_method,
#                 float(total_amount),
#                 product_ids,  # Array of product IDs
#                 quantities,   # Array of quantities
#                 order_id,     # Output parameter
#                 result        # Output parameter
#             ])
        
#         connection.commit()
        
#         return {
#             "success": True,
#             "order_id": order_id.getvalue(),
#             "message": result.getvalue()
#         }
        
#     except cx_Oracle.DatabaseError as e:
#         error, = e.args
#         return {
#             "success": False,
#             "error_code": error.code,
#             "message": error.message
#         }
#     finally:
#         if 'connection' in locals():
#             connection.close()

# # Example usage
# if __name__ == "__main__":
#     order_data = {
#         "user_id": "user123",
#         "payment_method": "Credit Card",
#         "total_amount": 99.99,
#         "items": [
#             {"product_id": "prod1", "quantity": 2},
#             {"product_id": "prod2", "quantity": 1}
#         ]
#     }
    
#     result = place_order(**order_data)
#     print(json.dumps(result, indent=2))