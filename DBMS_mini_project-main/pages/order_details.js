document.addEventListener("DOMContentLoaded", function() {
    const ordersList = document.getElementById("orders-list");

    // Example order data - replace with actual data from API or localStorage
    const orders = [
        {
            orderId: 12345,
            status: "Shipped",
            date: "2025-03-30",  // Date of order
            items: [
                { name: "Tomatoes", quantity: 2, price: 8.00 },
                { name: "Apples", quantity: 1, price: 12.00 }
            ],
            total: 28.00
        },
        {
            orderId: 12346,
            status: "Pending",
            date: "2025-03-28",  // Date of order
            items: [
                { name: "Pineapples", quantity: 3, price: 12.00 },
                { name: "Potatoes", quantity: 5, price: 4.00 }
            ],
            total: 72.00
        }
    ];

    // Function to format date to a readable format (e.g., "March 30, 2025")
    function formatDate(dateString) {
        const date = new Date(dateString);
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // Function to display the orders dynamically
    function displayOrders(orders) {
        ordersList.innerHTML = ''; // Clear any existing content

        if (orders.length === 0) {
            ordersList.innerHTML = "<p>No orders placed yet.</p>";
            return;
        }

        orders.forEach(order => {
            const orderCard = document.createElement("div");
            orderCard.classList.add("order-card");

            let orderItems = "";
            order.items.forEach(item => {
                orderItems += `
                    <div class="order-item">
                        <p class="item-name">${item.name}</p>
                        <p class="item-quantity">x${item.quantity}</p>
                        <p class="item-price">Rs. ${item.price}</p>
                    </div>
                `;
            });

            orderCard.innerHTML = `
                <h3>Order #${order.orderId}</h3>
                <p class="order-date">Date: ${formatDate(order.date)}</p>  <!-- Display formatted date -->
                <p>Status: <span class="status-${order.status.toLowerCase()}">${order.status}</span></p>
                <div class="order-items">${orderItems}</div>
                <div class="order-total">
                    <p>Total: Rs. ${order.total.toFixed(2)}</p>
                </div>
            `;
            ordersList.appendChild(orderCard);
        });
    }

    // Display the orders
    displayOrders(orders);
});
