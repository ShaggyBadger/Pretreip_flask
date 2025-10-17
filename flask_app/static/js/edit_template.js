document.addEventListener('DOMContentLoaded', function() {
    const blueprintEditor = document.getElementById('blueprint-editor');
    const addSectionBtn = document.getElementById('add-section-btn');
    const submitTemplateBtn = document.getElementById('submit-template-btn');

    let sectionCounter = 0; // To generate unique IDs for new sections
    let itemCounter = 0;    // To generate unique IDs for new items

    // Function to generate a unique ID
    function generateUniqueId(prefix) {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    // Function to create an editable item row
    function createItemRow(item = {}) {
        const itemId = item.id || generateUniqueId('new-item');
        const itemName = item.name || '';
        const itemDetails = item.details || '';
        const itemNotes = item.notes || '';
        const dateRequired = item.date_field_required || false;
        const numericRequired = item.numeric_field_required || false;
        const booleanRequired = item.boolean_field_required || false;
        const textRequired = item.text_field_required || false;

        const row = document.createElement('tr');
        row.dataset.itemId = itemId;
        row.classList.add('blueprint-item-row'); // Class for Sortable.js

        row.innerHTML = `
            <td class="drag-handle"><i class="bi bi-grip-vertical"></i></td> <!-- New drag handle -->
            <td><input type="text" class="form-control item-name" value="${itemName}"></td>
            <td><textarea class="form-control item-details">${itemDetails}</textarea></td>
            <td><textarea class="form-control item-notes">${itemNotes}</textarea></td>
            <td>
                <div class="form-check form-check-inline">
                    <input class="form-check-input item-date-required" type="checkbox" ${dateRequired ? 'checked' : ''}>
                    <label class="form-check-label">Date</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input item-numeric-required" type="checkbox" ${numericRequired ? 'checked' : ''}>
                    <label class="form-check-label">Numeric</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input item-boolean-required" type="checkbox" ${booleanRequired ? 'checked' : ''}>
                    <label class="form-check-label">Boolean</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input item-text-required" type="checkbox" ${textRequired ? 'checked' : ''}>
                    <label class="form-check-label">Text</label>
                </div>
            </td>
            <td>
                <button type="button" class="btn btn-sm btn-outline-primary duplicate-item-btn">Duplicate</button>
                <button type="button" class="btn btn-sm btn-outline-danger delete-item-btn">Delete</button>
            </td>
        `;

        // Event listeners for item buttons (delegated later or added here)
        row.querySelector('.duplicate-item-btn').addEventListener('click', function() {
            const clonedRow = createItemRow(item); // Pass original item data to duplicate
            this.closest('tbody').appendChild(clonedRow);
            // Re-initialize Sortable for this tbody if needed
        });

        row.querySelector('.delete-item-btn').addEventListener('click', function() {
            this.closest('tr').remove();
        });

        return row;
    }

    // Function to create a section container
    function createSection(sectionName = '', items = []) {
        const sectionId = generateUniqueId('section');
        const sectionDiv = document.createElement('div');
        sectionDiv.classList.add('blueprint-section', 'card', 'mb-3');
        sectionDiv.dataset.sectionId = sectionId; // For Sortable.js
        sectionDiv.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <input type="text" class="form-control section-name-input" value="${sectionName}" placeholder="Section Name">
                <div>
                    <button type="button" class="btn btn-sm btn-outline-success add-item-btn">Add Item</button>
                    <button type="button" class="btn btn-sm btn-outline-danger delete-section-btn">Delete Section</button>
                </div>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead>
                            <tr>
                                <th></th> <!-- For the drag handle -->
                                <th>Name</th>
                                <th>Details</th>
                                <th>Notes</th>
                                <th>Required Fields</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody class="section-items-sortable">
                            <!-- Items will be appended here -->
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        const tbody = sectionDiv.querySelector('.section-items-sortable');
        items.forEach(item => {
            tbody.appendChild(createItemRow(item));
        });

        // Initialize Sortable for items within this new section
        new Sortable(tbody, {
            animation: 150,
            handle: 'tr', // Drag entire row
        });

        // Event listeners for section buttons
        sectionDiv.querySelector('.add-item-btn').addEventListener('click', function() {
            tbody.appendChild(createItemRow());
            // Sortable for tbody is already initialized, new items will be draggable
        });

        sectionDiv.querySelector('.delete-section-btn').addEventListener('click', function() {
            sectionDiv.remove();
            // Re-initialize Sortable for blueprintEditor if needed
        });

        return sectionDiv;
    }

    // Initialize editor with existing data
    if (initialBlueprintData && initialBlueprintData.length > 0) {
        initialBlueprintData.forEach(([sectionName, items]) => {
            blueprintEditor.appendChild(createSection(sectionName, items));
        });
    } else {
        blueprintEditor.appendChild(createSection('New Section')); // Add a default section if no data
    }

    // Global Add Section button
    addSectionBtn.addEventListener('click', function() {
        blueprintEditor.appendChild(createSection('New Section'));
        // Re-initialize Sortable for blueprintEditor if needed
    });

    // Submit Template button
    submitTemplateBtn.addEventListener('click', function() {
        const originalButtonText = this.innerHTML;
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...';

        const templateData = {
            name: document.getElementById('template-name').value,
            description: document.getElementById('template-description').value,
            template_id: templateId, // From Flask context
            sections: {}
        };

        document.querySelectorAll('.blueprint-section').forEach(sectionDiv => {
            const sectionNameInput = sectionDiv.querySelector('.section-name-input');
            const sectionName = sectionNameInput.value;
            const items = [];

            sectionDiv.querySelectorAll('.blueprint-item-row').forEach(itemRow => {
                const item = {
                    name: itemRow.querySelector('.item-name').value,
                    details: itemRow.querySelector('.item-details').value,
                    notes: itemRow.querySelector('.item-notes').value,
                    date_field_required: itemRow.querySelector('.item-date-required').checked,
                    numeric_field_required: itemRow.querySelector('.item-numeric-required').checked,
                    boolean_field_required: itemRow.querySelector('.item-boolean-required').checked,
                    text_field_required: itemRow.querySelector('.item-text-required').checked,
                };
                items.push(item);
            });
            templateData.sections[sectionName] = items;
        });

        console.log('Submitting Template Data:', templateData);

        fetch(`/pretrip/api/template/update/${templateId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(templateData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = data.redirect_url;
            } else {
                console.error('Error:', data.message);
                alert('Error updating template: ' + data.message);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('An unexpected error occurred. Check the console for details.');
        })
        .finally(() => {
            this.disabled = false;
            this.innerHTML = originalButtonText;
        });
    });

    // --- Sortable.js Integration ---
    function initializeSectionSortable() {
        new Sortable(blueprintEditor, {
            animation: 150,
            handle: '.card-header',
            filter: '.form-control',
            onMove: function (evt) {
                return evt.related.className.indexOf('form-control') === -1;
            }
        });
    }

    initializeSectionSortable();

    addSectionBtn.addEventListener('click', function() {
        blueprintEditor.appendChild(createSection('New Section'));
    });
});
