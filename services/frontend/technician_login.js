const API_URL = "http://127.0.0.1:8000/login";

const form = document.getElementById("login-form");
const toast = document.getElementById("toast");

function setToast(msg, type="error"){
  toast.textContent = msg;
  toast.className = type;
}

form.addEventListener("submit", async (e)=>{
  e.preventDefault();

  const payload = {
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value.trim()
  };

  if (!payload.email || !payload.password){
    setToast("⚠️ Enter your login details");
    return;
  }

  try{
    const res = await fetch(API_URL,{
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if(!res.ok){
      setToast(data.detail || "❌ Invalid login");
      return;
    }

    // ✅ SAVE TOKEN + TECH INFO
    localStorage.setItem("aiva_token", data.access_token);
    localStorage.setItem("aiva_technician_name", data.technician.full_name);
    localStorage.setItem("aiva_technician_email", data.technician.email);

    setToast("✅ Login successful!", "success");

    // ✅ REDIRECT TO DASHBOARD
    window.location.href = "dashboard.html";

  } catch(err){
    console.error(err);
    setToast("❌ Server unavailable.");
  }
});