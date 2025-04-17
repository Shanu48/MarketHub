document.addEventListener("DOMContentLoaded", function () {
    const productForm = document.getElementById("product-form");
    const productList = document.getElementById("product-list");

    // Load products from storage
    let products = JSON.parse(localStorage.getItem("supplierProducts")) || [];

    function updateProductList() {
        productList.innerHTML = "";
        products.forEach((product, index) => {
            const div = document.createElement("div");
            div.classList.add("product-item");
            div.innerHTML = `
                <p><strong>${product.name}</strong> (${product.category})</p>
                <p>Price: Rs. ${product.price} - Discount: ${product.discount}%</p>
                <button class="remove-btn" data-index="${index}">Remove</button>
            `;
            productList.appendChild(div);
        });
    }

    productForm.addEventListener("submit", function (event) {
        event.preventDefault();
        alert("order supply confirmed");
        const name = document.getElementById("product-name").value;
        const category = document.getElementById("category").value;
        const price = parseFloat(document.getElementById("price").value);
        const discount = parseFloat(document.getElementById("discount").value) || 0;

        const newProduct = { name, category, price, discount };
        products.push(newProduct);
        localStorage.setItem("supplierProducts", JSON.stringify(products));

        updateProductList();
        productForm.reset();
    });

    updateProductList();
});
