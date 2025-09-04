async function generate_chart(tank_id) {
  console.log("Heyyyyy this is firing off");
  try {
    let response = await fetch("/tankgauge/get-tank-chart-info", {
      method: "POST", // Use POST
      headers: {
        "Content-Type": "application/json", // Tell Flask we’re sending JSON
        "X-CSRFToken": csrfToken, // Include CSRF token if using Flask-WTF
      },
      body: JSON.stringify({ tank_id: tank_id }), // Send tank_id in the body
    });
  } catch (error) {
    console.error("Error generating chart:", error);
  }
}
