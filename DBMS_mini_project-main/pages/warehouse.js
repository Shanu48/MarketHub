document.addEventListener("DOMContentLoaded", function () {
    const warehouseForm = document.getElementById("warehouse-form");
    const warehouseList = document.getElementById("warehouse-list");

    let warehouses = JSON.parse(localStorage.getItem("warehouses")) || [];

    function updateWarehouseList() {
        warehouseList.innerHTML = "";
        warehouses.forEach((warehouse, index) => {
            const div = document.createElement("div");
            div.classList.add("warehouse-item");
            div.innerHTML = `
                <p><strong>${warehouse.name}</strong> - Capacity: ${warehouse.capacity} units</p>
                <p>Stored Items: ${warehouse.items}</p>
                <button class="remove-btn" data-index="${index}">Remove</button>
            `;
            warehouseList.appendChild(div);
        });

        document.querySelectorAll(".remove-btn").forEach(btn => {
            btn.addEventListener("click", function () {
                const index = btn.getAttribute("data-index");
                warehouses.splice(index, 1);
                localStorage.setItem("warehouses", JSON.stringify(warehouses));
                updateWarehouseList();
            });
        });
    }

    warehouseForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const name = document.getElementById("warehouse-name").value;
        const capacity = parseInt(document.getElementById("capacity").value);
        const items = document.getElementById("stored-items").value;

        const newWarehouse = { name, capacity, items };
        warehouses.push(newWarehouse);
        localStorage.setItem("warehouses", JSON.stringify(warehouses));

        updateWarehouseList();
        warehouseForm.reset();
    });

    updateWarehouseList();
});
