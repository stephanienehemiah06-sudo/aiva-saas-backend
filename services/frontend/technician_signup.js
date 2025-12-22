const API_URL = "http://127.0.0.1:8000/signup-technician";

const form = document.getElementById("signup-form");
const toast = document.getElementById("toast");

function setToast(msg, type="error"){
  toast.innerText = msg;
  toast.className = type;
}

form.addEventListener("submit", async e=>{
  e.preventDefault();

  const payload = {
    full_name: full_name.value.trim(),
    business_name: business_name.value.trim(),
    email: email.value.trim(),
    phone: phone.value.trim(),
    country: country.value.trim(),
    assistant_name: assistant_name.value.trim(),
    password: password.value.trim()
  };

  if(Object.values(payload).some(v=>!v)){
    setToast("⚠ Please fill all fields");
    return;
  }

  if(payload.password.length < 6){
    setToast("🔐 Password must be 6+ characters");
    return;
  }

  setToast("⏳ Creating account...", "success");

  try{
    const res = await fetch(API_URL,{
      method:"POST",
      headers:{ "Content-Type": "application/json" },
      body:JSON.stringify(payload)
    });

    const data = await res.json();

    if(!res.ok){
      setToast(data.detail || "❌ Signup failed.");
      return;
    }

    setToast("✅ Account created successfully", "success");

    setTimeout(()=>{
      window.location.href = "technician_login.html";
    },1200);

  } catch(err){
    console.error(err);
    setToast("❌ Backend unreachable. Is FastAPI running?");
  }
});