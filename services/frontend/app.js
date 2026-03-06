const API = "http://127.0.0.1:8000";

async function signup() {
  const payload = {
    full_name: document.getElementById("full_name").value,
    business_name: document.getElementById("business_name").value,
    email: document.getElementById("email").value,
    password: document.getElementById("password").value
  };

  const res = await fetch(`${API}/api/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();

  if (res.ok) {
    alert("Account created successfully ≡ƒÄë");
    window.location.href = "login.html";
  } else {
    alert(data.detail);
  }
}
