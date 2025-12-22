document.getElementById("saveServiceBtn").addEventListener("click", async () => {
    try {
        //---------------------------
        // Get token
        //---------------------------
        const token = localStorage.getItem("auth_token");
        if (!token) {
            alert("Not logged in");
            return;
        }

        //---------------------------
        // Get fields safely
        //---------------------------
        const name = document.getElementById("service_name")?.value.trim();
        const category = document.getElementById("category")?.value.trim();
        const price = document.getElementById("price")?.value;
        const duration = document.getElementById("duration")?.value;
        const description = document.getElementById("description")?.value.trim();

        //---------------------------
        // Validation
        //---------------------------
        if (!name || !category || !price || !duration) {
            alert("Please fill all required fields");
            return;
        }

        //---------------------------
        // Payload
        //---------------------------
        const payload = {
            name,
            category,
            price: parseFloat(price),
            duration_minutes: parseInt(duration),
            booking_note: description
        };

        //---------------------------
        // POST Service
        //---------------------------
        const response = await fetch("http://127.0.0.1:8000/services", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        //---------------------------
        // Response Handling
        //---------------------------
        if (!response.ok) {
            console.error(result);
            alert(result.detail || "Service save failed");
            return;
        }

        alert("✅ Service saved successfully!");

        // Reset form
        document.getElementById("serviceForm").reset();

    } catch (error) {
        console.error("Save Service Error:", error);
        alert("Unexpected error saving service");
    }
});