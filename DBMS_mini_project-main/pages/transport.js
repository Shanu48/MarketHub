document.addEventListener("DOMContentLoaded", function () {
    const transportForm = document.getElementById("transport-form");
    const transportList = document.getElementById("transport-list");

    let transports = JSON.parse(localStorage.getItem("transports")) || [];

    function updateTransportList() {
        transportList.innerHTML = "";
        transports.forEach((transport, index) => {
            const div = document.createElement("div");
            div.classList.add("transport-item");
            div.innerHTML = `
                <p><strong>Vehicle:</strong> ${transport.vehicleNumber}</p>
                <p><strong>Driver:</strong> ${transport.driverName}</p>
                <p><strong>Assigned Order ID:</strong> ${transport.assignedOrder}</p>
                <button class="remove-btn" data-index="${index}">Remove</button>
            `;
            transportList.appendChild(div);
        });

        document.querySelectorAll(".remove-btn").forEach(btn => {
            btn.addEventListener("click", function () {
                const index = btn.getAttribute("data-index");
                transports.splice(index, 1);
                localStorage.setItem("transports", JSON.stringify(transports));
                updateTransportList();
            });
        });
    }

    transportForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const vehicleNumber = document.getElementById("vehicle-number").value;
        const driverName = document.getElementById("driver-name").value;
        const assignedOrder = document.getElementById("assigned-order").value;

        const newTransport = { vehicleNumber, driverName, assignedOrder };
        transports.push(newTransport);
        localStorage.setItem("transports", JSON.stringify(transports));

        updateTransportList();
        transportForm.reset();
    });

    updateTransportList();
});
