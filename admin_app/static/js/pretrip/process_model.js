// get the crsf token from the meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

// Build the controller that handles the logic for processing this file
async function controller(file) {
  const fileText = await file.text();

  // Extract column names
  const results = Papa.parse(fileText, { header: true, preview: 1 });
  const columns = results.meta.fields;

  // Validate columns with the server
  const validationResponse = await validateColumns(columns);

  if (!validationResponse.valid) {
    alert('Column validation failed: ' + validationResponse.message);
    return;
  }

  // If valid, proceed with further processing (if any)
  const payloadResponse = await sendDataToServer(fileText);

  if (payloadResponse.status === 'success') {
    alert('File processed successfully!');
  } else {
    alert(
      'Error processing file: ' + (payloadResponse.error || 'Unknown error'),
    );
  }
}

// send full data payload to the server for database entry
async function sendDataToServer(data) {
  // Parse CSV data into JSON using PapaParse
  const results = Papa.parse(data, { header: true });
  const jsonData = results.data;

  // Send the JSON data to the server
  try {
    const response = await fetch('/admin/pretrip/blueprint-payload-upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ rows: jsonData }),
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const respData = await response.json();
    return respData;
  } catch (error) {
    console.error('Error sending data to server:', error);
    throw error;
  }
}

// send columns to the server for validation
async function validateColumns(columns) {
  try {
    const response = await fetch('/admin/pretrip/validate-headers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ columns: columns }),
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    return data; // { valid: bool, message: str }
  } catch (error) {
    console.error('Error during column validation:', error);
    throw error;
  }
}

// Separate function to handle the file & call controller
async function handleFileSubmit() {
  let fileInput = document.getElementById('csvFile');
  let file = fileInput.files[0];

  // make sure a file is selected
  if (!file) {
    alert('Please select a file.');
    return;
  }

  // Validate file type (only CSV allowed)
  let ext = file.name.split('.').pop().toLowerCase();
  if (ext !== 'csv') {
    alert('Only CSV files allowed!');
    return;
  }

  try {
    // Call the controller
    await controller(file);
  } catch (error) {
    console.error('Error processing file:', error);
    alert('An error occurred while processing the file.');
  }
}

// Attach event listener to button
document.addEventListener('DOMContentLoaded', function () {
  let submitBtn = document.getElementById('submitBtn');
  let csvFileInput = document.getElementById('csvFile');

  // Initially disable the button
  submitBtn.disabled = true;

  // Add an event listener to the file input to enable/disable the button
  csvFileInput.addEventListener('change', function () {
    if (
      csvFileInput.files.length > 0 &&
      csvFileInput.files[0].name.split('.').pop().toLowerCase() === 'csv'
    ) {
      submitBtn.disabled = false;
    } else {
      submitBtn.disabled = true;
    }
  });

  submitBtn.addEventListener('click', function (event) {
    event.preventDefault();
    handleFileSubmit();
  });
});
