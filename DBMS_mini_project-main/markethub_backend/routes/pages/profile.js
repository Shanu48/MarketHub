document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Fetch profile details from the backend
        const response = await fetch("http://127.0.0.1:5000/auth/profile");
        
        if (!response.ok) {
            throw new Error("Failed to fetch profile details!");
        }

        const data = await response.json();

        // Check for errors in response data
        if (data.error) {
            alert(data.error);
            return;
        }

        // Populate profile page with fetched data
        document.getElementById("user-id").textContent = data.userID;
        document.getElementById("user-name").textContent = data.name;
        document.getElementById("user-email").textContent = data.email;
        document.getElementById("user-contact").textContent = data.phoneNo;
        document.getElementById("user-address").textContent = data.address;

    } catch (error) {
        console.error("Error fetching profile details:", error);
    }
});
