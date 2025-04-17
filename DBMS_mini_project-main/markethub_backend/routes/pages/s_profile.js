document.addEventListener("DOMContentLoaded", function () {
    // Dummy user data (Replace with API fetch later)
    let user = JSON.parse(localStorage.getItem("user")) || {
        userId: "CUST12345",
        name: "John Doe",
        address: "123 Street, City, Country",
        contact: "+91 9876543210",
        role: "Supplier"
    };

    // Display user data
    document.getElementById("user-id").textContent = user.userId;
    document.getElementById("user-name").textContent = user.name;
    document.getElementById("user-address").textContent = user.address;
    document.getElementById("user-contact").textContent = user.contact;
});

