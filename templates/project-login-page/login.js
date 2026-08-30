const DEMO_EMAIL = "demo@support.com";
const DEMO_PASSWORD = "demo1234";

const form = document.getElementById("login-form");
const alertEl = document.getElementById("alert");
const submitBtn = document.getElementById("submit-btn");

function showAlert(message, type = "error") {
  alertEl.textContent = message;
  alertEl.className = `alert ${type}`;
  alertEl.classList.remove("hidden");
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  alertEl.classList.add("hidden");

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const role = document.getElementById("role").value;

  submitBtn.disabled = true;
  submitBtn.textContent = "Signing in…";

  setTimeout(() => {
    if (email === DEMO_EMAIL && password === DEMO_PASSWORD) {
      showAlert(`Welcome, ${role}! Login test passed (page 1).`, "success");
    } else {
      showAlert("Invalid credentials. Use demo@support.com / demo1234");
    }
    submitBtn.disabled = false;
    submitBtn.textContent = "Sign in";
  }, 400);
});
