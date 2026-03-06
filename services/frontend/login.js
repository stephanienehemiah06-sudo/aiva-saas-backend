document.getElementById("loginBtn").addEventListener("click", async () => {
  const API_URL = (localStorage.getItem("API_URL") || window.location.origin).replace(/\/+$/, "");
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const errorMsg = document.getElementById("errorMsg");

  errorMsg.innerText = "";

  if (!email || !password) {
    errorMsg.innerText = "Please fill in all fields";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      errorMsg.innerText = data.detail || "Invalid credentials";
      return;
    }

    // Save session
    localStorage.setItem("aiva_token", data.token);
    localStorage.setItem("token", data.token);
    localStorage.setItem("technician_id", data.technician_id);
    localStorage.setItem("full_name", data.full_name);
    localStorage.setItem("business_name", data.business_name);

    // Redirect
    window.location.href = "dashboard.html";

  } catch (err) {
    errorMsg.innerText = "Server error. Try again.";
  }
});