const form = document.getElementById("visitor-form");
const statusEl = document.getElementById("location-status");
const submitBtn = document.getElementById("submit-btn");

form.addEventListener("submit", (event) => {
  event.preventDefault();

  if (!form.reportValidity()) return;
  if (!document.getElementById("consent-checkbox").checked) {
    statusEl.textContent = "Please agree to share your location before submitting.";
    return;
  }
  if (!("geolocation" in navigator)) {
    statusEl.textContent = "This browser does not support GPS location. Try a modern browser.";
    return;
  }

  submitBtn.disabled = true;
  statusEl.textContent = "Requesting your location permission…";

  navigator.geolocation.getCurrentPosition(
    (position) => {
      document.getElementById("latitude").value = position.coords.latitude;
      document.getElementById("longitude").value = position.coords.longitude;
      document.getElementById("accuracy").value = position.coords.accuracy || "";
      document.getElementById("location_consent").value = "yes";
      statusEl.textContent = "Location received. Submitting your registration…";
      form.submit();
    },
    (error) => {
      submitBtn.disabled = false;
      const messages = {
        1: "Location permission was denied. Allow location access in your browser settings to continue.",
        2: "Your device could not determine a location. Try again where GPS or location services are available.",
        3: "Location request timed out. Please try again."
      };
      statusEl.textContent = messages[error.code] || "Could not obtain your location. Please try again.";
    },
    { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
  );
});
