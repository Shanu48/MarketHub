document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch("http://127.0.0.1:5000/api/products");
        if (!response.ok) throw new Error("Failed to load products");
        const products = await response.json();

        const productContainer = document.querySelector(".product-container");
        productContainer.innerHTML = "";

        products.forEach(product => {
            const productCard = document.createElement("div");
            productCard.className = "product-card";
            
            productCard.innerHTML = `
                <img src="/images/products/${product.productID}.jpg" alt="${product.pName}">
                <h3>${product.pName}</h3>
                <p class="description">${product.description}</p>
                <p class="category">Category: ${product.categoryName}</p>
                <p class="price">Rs.${product.price.toFixed(2)} <span class="units">per ${product.unit}</span></p>
                <button class="add-to-cart" 
                        data-id="${product.productID}" 
                        data-name="${product.pName}" 
                        data-price="${product.price}">
                    Add to Cart
                </button>
            `;

            productContainer.appendChild(productCard);
        });

    } catch (error) {
        console.error("Error:", error);
        productContainer.innerHTML = `<p class="error">Failed to load products. Please try again later.</p>`;
    }
});
