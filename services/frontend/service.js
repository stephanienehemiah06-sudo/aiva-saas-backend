console.log("✅ service.js loaded");

const status = document.getElementById("status");

document.getElementById("saveBtn").onclick = async () => {

  status.innerText = "Saving…";

  const token = localStorage.getItem("aiva_token");

  if (!token) {
    status.innerText = "❌ Login required";
    return;
  }

  const payload = {
    name: document.getElementById("name").value,
    category: document.getElementById("category").value,
    price: Number(document.getElementById("price").value),
    duration: Number(document.getElementById("duration").value),
    notes: document.getElementById("notes").value
  };

  console.log("📦 Payload:", payload);

  try {
    const res = await fetch("http://127.0.0.1:8000/services", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok){
      const t = await res.text();
      throw new Error("Server error: " + t);
    }

    const data = await res.json();

    console.log("✅ SAVED:", data);

    status.innerText = "✅ Service saved successfully!";
    status.style.color = "green";

  } catch(err){
    console.error("❌ Save failed:", err);
    status.innerText = "❌ " + err.message;
    status.style.color = "crimson";
  }
};