document.addEventListener("DOMContentLoaded", function () {
    let cart = JSON.parse(localStorage.getItem("cart")) || []; // Load cart from storage
    const addToCartButtons = document.querySelectorAll(".add-to-cart");
    const cartItemsContainer = document.querySelector(".cart-items");
    const totalPrice = document.getElementById("total-price");

    function updateCart() {
        if (!cartItemsContainer) return; // Prevent error if not on cart page
    
        cartItemsContainer.innerHTML = "";
        let total = 0;
    
        if (cart.length === 0) {
            cartItemsContainer.innerHTML = `<p class="empty-cart-message">Your cart is empty.</p>`;
            totalPrice.textContent = "0.00";
            return;
        }
    
        cart.forEach((product, index) => {
            const item = document.createElement("div");
            item.classList.add("cart-item");
            item.innerHTML = `
                <div class="item-info">
                    <p class="item-name">${product.name}</p>
                    <p class="item-price">Rs. ${product.price} x ${product.quantity}</p>
                </div>
                <div class="quantity-controls">
                    <button class="quantity-btn decrease" data-index="${index}">-</button>
                    <span>${product.quantity}</span>
                    <button class="quantity-btn increase" data-index="${index}">+</button>
                </div>
                <button class="remove-btn" data-index="${index}">Remove</button>
            `;
            cartItemsContainer.appendChild(item);
            total += product.price * product.quantity;
        });
    
        totalPrice.textContent = total.toFixed(2);
        localStorage.setItem("cart", JSON.stringify(cart)); // Always save cart
    }    

    // Add to cart functionality
    addToCartButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const name = button.getAttribute("data-name");
            const price = parseFloat(button.getAttribute("data-price"));
            let product = cart.find((item) => item.name === name);

            if (!product) {
                product = { name, price, quantity: 1 };
                cart.push(product);
            } else {
                product.quantity++;
            }

            localStorage.setItem("cart", JSON.stringify(cart)); // Save cart
            updateCart();
        });
    });

    // Increase/Decrease Quantity in Cart
    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("increase")) {
            let index = event.target.getAttribute("data-index");
            cart[index].quantity++;
        } else if (event.target.classList.contains("decrease")) {
            let index = event.target.getAttribute("data-index");
            cart[index].quantity--;
            if (cart[index].quantity === 0) {
                cart.splice(index, 1);
            }
        } else if (event.target.classList.contains("remove-btn")) {
            let index = event.target.getAttribute("data-index");
            cart.splice(index, 1);
        }

        localStorage.setItem("cart", JSON.stringify(cart)); // Save cart
        updateCart();
    });

    updateCart(); // Load cart on page load
});
