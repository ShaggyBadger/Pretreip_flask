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

  // If valid, generate the form for the user to review and edit.
  generateForm(fileText);
}

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

async function checkBlueprintName() {
  const nameInput = document.getElementById('blueprint-name-input');
  const feedbackDiv = document.getElementById('name-validation-feedback');
  const name = nameInput.value.trim();

  // Reset state if the input is empty
  if (name === '') {
    nameInput.classList.remove('is-valid', 'is-invalid');
    feedbackDiv.textContent = '';
    return;
  }

  try {
    const response = await fetch(`/admin/pretrip/check-blueprint-name?name=${encodeURIComponent(name)}`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();

    if (data.exists) {
      nameInput.classList.add('is-invalid');
      nameInput.classList.remove('is-valid');
      feedbackDiv.textContent = 'This blueprint name already exists. Check the box to override.';
      feedbackDiv.style.display = 'block';

      // Show override option
      const overrideContainer = document.getElementById('override-container');
      overrideContainer.innerHTML = `
        <div class="form-check mt-2">
          <input class="form-check-input" type="checkbox" value="" id="overrideBlueprint">
          <label class="form-check-label" for="overrideBlueprint">
            Override existing blueprint
          </label>
        </div>
      `;
      overrideContainer.style.display = 'block';

    } else {
      nameInput.classList.add('is-valid');
      nameInput.classList.remove('is-invalid');
      feedbackDiv.textContent = '';
      feedbackDiv.style.display = 'none';

      // Hide override option
      document.getElementById('override-container').style.display = 'none';
    }
  } catch (error) {
    console.error('Error checking blueprint name:', error);
    nameInput.classList.remove('is-valid', 'is-invalid');
    feedbackDiv.textContent = 'Could not validate name.';
    feedbackDiv.style.display = 'block';
    document.getElementById('override-container').style.display = 'none';
  }
}

// Gathers all data from the current form state, populates a hidden input, and submits the form.
function handleFormSubmit(event) {
  event.preventDefault(); // Prevent the default submission to do our work
  console.log('Gathering final form data...');

  const nameInput = document.getElementById('blueprint-name-input');
  const overrideCheckbox = document.getElementById('overrideBlueprint');

  if (nameInput.classList.contains('is-invalid') && (!overrideCheckbox || !overrideCheckbox.checked)) {
    alert('The chosen blueprint name is already taken. Please choose another one, or check the override option.');
    return;
  }

  const blueprintName = nameInput.value.trim();
  if (!blueprintName) {
    alert('Blueprint name is required.');
    return; // Stop if the name is missing
  }

  const finalRows = [];
  const equipmentSections = document.querySelectorAll('.equipment-section');

  equipmentSections.forEach((equipmentDiv) => {
    const equipmentName = equipmentDiv.querySelector('.equipment-name-input').value;
    const itemContainers = equipmentDiv.querySelectorAll('.inspection-item-container');

    itemContainers.forEach((itemContainer) => {
      const rowObject = {};
      const sectionName = itemContainer.dataset.sectionName;

      rowObject['equipment'] = equipmentName;
      rowObject['section'] = sectionName;

      itemContainer.querySelectorAll('[data-key]').forEach((formElement) => {
        const key = formElement.dataset.key;
        let value;
        if (formElement.type === 'checkbox') {
          value = formElement.checked;
        } else {
          value = formElement.value;
        }
        rowObject[key] = value;
      });

      rowObject['pass_fail'] = itemContainer.dataset.passFail;
      rowObject['numeric'] = itemContainer.dataset.numeric;
      rowObject['date'] = itemContainer.dataset.date;

      finalRows.push(rowObject);
    });
  });

  const payload = {
    name: blueprintName,
    rows: finalRows,
  };

  if (overrideCheckbox && overrideCheckbox.checked) {
    payload.override = true;
  }

  // Set the stringified payload to the hidden input
  const hiddenInput = document.getElementById('payload-input');
  hiddenInput.value = JSON.stringify(payload);

  // Now, submit the form programmatically
  const form = document.getElementById('pretrip-model-form');
  form.submit();
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
  const submitBtn = document.getElementById('submitBtn');
  const csvFileInput = document.getElementById('csvFile');

  // Function to update the submit button's disabled state
  function updateSubmitButtonState() {
    if (!submitBtn || !csvFileInput) return;

    const hasFile = csvFileInput.files.length > 0;
    let isCsv = false;
    if (hasFile) {
      const ext = csvFileInput.files[0].name.split('.').pop().toLowerCase();
      isCsv = (ext === 'csv');
    }
    submitBtn.disabled = !(hasFile && isCsv);
  }

  // Initial state update
  updateSubmitButtonState();

  // Attach event listeners
  if (csvFileInput) {
    csvFileInput.addEventListener('change', updateSubmitButtonState);
  }

  if (submitBtn) {
    submitBtn.addEventListener('click', function (event) {
      event.preventDefault();
      handleFileSubmit();
    });
  }
});

// generate form with data from csv file
function generateForm(data) {
  const results = Papa.parse(data, { header: true });
  const groupedData = groupCSVData(results.data);
  console.log('Parsed CSV Data:', results.data);
  console.log('Grouped CSV Data:', groupedData);
  const formContainer = document.getElementById('formContainer');
  formContainer.innerHTML = ''; // Clear previous content

  // Create a form element
  const form = document.createElement('form');
  form.id = 'pretrip-model-form';
  form.action = '/admin/pretrip/blueprint-payload-upload';
  form.method = 'POST';

  // Add a hidden input for the CSRF token
  const csrfInput = document.createElement('input');
  csrfInput.type = 'hidden';
  csrfInput.name = 'csrf_token';
  csrfInput.value = csrfToken;
  form.appendChild(csrfInput);

  // Add a hidden input to hold the final JSON payload
  const hiddenInput = document.createElement('input');
  hiddenInput.type = 'hidden';
  hiddenInput.id = 'payload-input';
  hiddenInput.name = 'payload';
  form.appendChild(hiddenInput);

  // Function to handle equipment name updates
  const handleEquipmentNameChange = (e) => {
    const input = e.target;
    const newName = input.value.trim();
    const oldName = input.dataset.oldName;

    if (newName === oldName || !newName) {
      if (!newName) input.value = oldName; // Revert if empty
      return;
    }

    // Check for name conflicts by checking other input values
    let conflict = false;
    document.querySelectorAll('.equipment-name-input').forEach(otherInput => {
        if (otherInput !== input && otherInput.value === newName) {
            conflict = true;
        }
    });

    if (conflict) {
      alert(`Error: Equipment name "${newName}" already exists.`);
      input.value = oldName; // Revert
      return;
    }
    
    // Update the DOM
    const equipmentDiv = input.closest('.equipment-section');
    equipmentDiv.querySelectorAll('.info-header-equipment').forEach((header) => {
      header.textContent = newName;
    });
    input.dataset.oldName = newName; // Update the reference for future edits
  };

  // Loop through each equipment in the grouped data
  for (const equipmentName in groupedData) {
    if (Object.hasOwnProperty.call(groupedData, equipmentName)) {
      const equipmentDiv = document.createElement('div');
      equipmentDiv.className = 'equipment-section mb-5';

      // Create an editable input for the equipment name
      const equipmentInput = document.createElement('input');
      equipmentInput.type = 'text';
      equipmentInput.value = equipmentName;
      equipmentInput.dataset.oldName = equipmentName;
      equipmentInput.className = 'form-control form-control-lg mb-3 equipment-name-input';
      equipmentInput.addEventListener('blur', handleEquipmentNameChange);
      equipmentDiv.appendChild(equipmentInput);

      const sections = groupedData[equipmentName];
      // Loop through each section for the equipment
      for (const sectionName in sections) {
        if (Object.hasOwnProperty.call(sections, sectionName)) {
          const sectionDiv = document.createElement('div');
          sectionDiv.className = 'section-container mb-4'; // Add margin bottom

          const sectionHeader = document.createElement('h3');
          sectionHeader.textContent = sectionName;
          sectionDiv.appendChild(sectionHeader);

          const inspectionItems = sections[sectionName];
          if (inspectionItems.length === 0) continue;

          // Loop through each inspection item
          inspectionItems.forEach((item, index) => {
            const itemContainer = document.createElement('div');
            itemContainer.className =
              'inspection-item-container border p-3 mb-3 position-relative'; // Add positioning context
            
            // Store data on the container for easy access during submission
            itemContainer.dataset.sectionName = sectionName;
            itemContainer.dataset.passFail = item['pass_fail'] || '';
            itemContainer.dataset.numeric = item['numeric'] || '';
            itemContainer.dataset.date = item['date'] || '';


            // Add a header for equipment and section info
            const infoHeader = document.createElement('div');
            infoHeader.className =
              'position-absolute top-0 end-0 p-2 text-muted small';
            // Add specific classes to equipment/section parts to make them updatable
            infoHeader.innerHTML = `<strong>Eq:</strong> <span class="info-header-equipment">${equipmentName}</span> / <strong>Sec:</strong> ${sectionName}`;
            itemContainer.appendChild(infoHeader);

            const table = document.createElement('table');
            table.className = 'table mt-4'; // Add margin-top for spacing

            const tbody = document.createElement('tbody');
            const nonEditableFields = ['pass_fail', 'numeric', 'date'];

            // Create rows for editable fields
            for (const key in item) {
              if (
                Object.hasOwnProperty.call(item, key) &&
                !nonEditableFields.includes(key)
              ) {
                const row = document.createElement('tr');
                const inputId = `input-${equipmentName}-${sectionName}-${index}-${key}`;

                // Cell for the label
                const labelCell = document.createElement('td');
                const label = document.createElement('label');
                label.htmlFor = inputId;
                label.textContent = key.replace(/_/g, ' ');
                labelCell.appendChild(label);
                labelCell.style.width = '20%';

                // Cell for the input
                const inputCell = document.createElement('td');
                let formElement;

                // Use a checkbox for boolean-type fields
                if (key === 'numeric_required' || key === 'date_required') {
                  const formCheckDiv = document.createElement('div');
                  formCheckDiv.className = 'form-check';

                  formElement = document.createElement('input');
                  formElement.type = 'checkbox';
                  formElement.className = 'form-check-input';

                  const value = (item[key] || '').toString().toLowerCase();
                  formElement.checked = value === 'true' || value === '1';

                  formCheckDiv.appendChild(formElement);
                  inputCell.appendChild(formCheckDiv);
                } else {
                  // Use a textarea for fields that might contain long text
                  if (
                    key === 'details' ||
                    key === 'notes' ||
                    key === 'inspection_item'
                  ) {
                    formElement = document.createElement('textarea');
                    formElement.className = 'form-control';
                    formElement.rows = 3; // Set a default height
                    formElement.textContent = item[key] || '';
                  } else {
                    formElement = document.createElement('input');
                    formElement.type = 'text';
                    formElement.className = 'form-control';
                    formElement.value = item[key] || '';
                  }
                  inputCell.appendChild(formElement);
                }
                
                formElement.id = inputId;
                formElement.dataset.key = key; // Store the key for easy gathering

                row.appendChild(labelCell);
                row.appendChild(inputCell);
                tbody.appendChild(row);
              }
            }

            table.appendChild(tbody);
            itemContainer.appendChild(table);

            // Display non-editable fields
            const nonEditableDiv = document.createElement('div');
            nonEditableDiv.className = 'non-editable-info mt-2';

            const passFailP = document.createElement('p');
            passFailP.innerHTML = `<strong>Pass/Fail:</strong> ${item['pass_fail'] || 'N/A'}`;
            nonEditableDiv.appendChild(passFailP);

            const numericP = document.createElement('p');
            numericP.innerHTML = `<strong>Initial Numeric Value:</strong> ${item['numeric'] || 'N/A'}`;
            nonEditableDiv.appendChild(numericP);

            const dateP = document.createElement('p');
            dateP.innerHTML = `<strong>Initial Date Value:</strong> ${item['date'] || 'N/A'}`;
            nonEditableDiv.appendChild(dateP);

            itemContainer.appendChild(nonEditableDiv);

            // Add a delete button for the item
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button'; // Important to prevent form submission
            deleteButton.className = 'btn btn-danger btn-sm mt-3';
            deleteButton.textContent = 'Delete Item';
            deleteButton.addEventListener('click', (e) => {
              e.preventDefault();
              // Remove the entire container for this inspection item
              itemContainer.remove();
            });

            itemContainer.appendChild(deleteButton);
            sectionDiv.appendChild(itemContainer);
          });

          equipmentDiv.appendChild(sectionDiv);
        }
      }
      form.appendChild(equipmentDiv);
    }
  }

  // Create an input for the blueprint name
  const nameInputDiv = document.createElement('div');
  nameInputDiv.className = 'mb-3';

  const nameLabel = document.createElement('label');
  nameLabel.htmlFor = 'blueprint-name-input';
  nameLabel.className = 'form-label';
  nameLabel.textContent = 'Blueprint Name';
  nameInputDiv.appendChild(nameLabel);

  const nameInput = document.createElement('input');
  nameInput.type = 'text';
  nameInput.id = 'blueprint-name-input';
  nameInput.className = 'form-control';
  nameInput.placeholder = 'Enter a unique name for this blueprint';
  nameInput.required = true;
  nameInput.addEventListener('input', checkBlueprintName);
  nameInputDiv.appendChild(nameInput);

  const validationFeedback = document.createElement('div');
  validationFeedback.id = 'name-validation-feedback';
  // Bootstrap class for validation messages
  validationFeedback.className = 'invalid-feedback'; 
  nameInputDiv.appendChild(validationFeedback);

  const overrideContainer = document.createElement('div');
  overrideContainer.id = 'override-container';
  overrideContainer.style.display = 'none'; // Hidden by default
  nameInputDiv.appendChild(overrideContainer);

  form.appendChild(nameInputDiv);

  // Create and add a submit button
  const submitButton = document.createElement('button');
  submitButton.type = 'submit'; // Use type="submit" for standard form behavior
  submitButton.id = 'submit-pretrip-model-btn';
  submitButton.className = 'btn btn-primary mt-3';
  submitButton.textContent = 'Submit Model';
  form.appendChild(submitButton);

  formContainer.appendChild(form);
  
  // Add the final submission listener to the form itself
  form.addEventListener('submit', handleFormSubmit);


  return results;
}

function groupCSVData(flatArray) {
  const grouped = {};

  flatArray.forEach((item) => {
    const {
      equipment,
      section,
      inspection_item,
      details,
      pass_fail,
      notes,
      numeric_required,
      numeric,
      date_required,
      date,
    } = item;

    // skip empty or invalid entries
    if (!equipment || !section || !inspection_item) return;

    // ensure the equipment exists
    if (!grouped[equipment]) {
      grouped[equipment] = {};
    }

    // ensure the section exists
    if (!grouped[equipment][section]) {
      grouped[equipment][section] = [];
    }

    // add the inspection item to the section
    grouped[equipment][section].push({
      inspection_item,
      details,
      pass_fail,
      notes,
      numeric_required,
      numeric,
      date_required,
      date,
    });
  });

  return grouped;
}
