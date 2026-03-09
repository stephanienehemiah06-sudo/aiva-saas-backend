document.addEventListener("DOMContentLoaded", () => {
  const DEFAULT_API_URL = "https://web-production-6a7e4.up.railway.app";
  const API_URL = DEFAULT_API_URL.replace(/\/+$/, "");
  const form = document.getElementById("signupForm");

  if (!form) {
    console.error("Signup form not found");
    return;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const inputs = form.querySelectorAll("input");

    const payload = {
      full_name: inputs[0].value.trim(),
      business_name: inputs[1].value.trim(),
      email: inputs[2].value.trim(),
      password: inputs[3].value,
    };

    try {
      const res = await fetch(`${API_URL}/signup`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      let data = {};
      try { data = await res.json(); } catch(_) { data = {}; }

      if (!res.ok) {
        alert(data.detail || "Signup failed");
        return;
      }

      alert("Signed up successfully. Redirecting to login...");
      setTimeout(() => {
        window.location.href = "/login";
      }, 400);

    } catch (err) {
      console.error(err);
      alert("Server error. Try again.");
    }
  });
});