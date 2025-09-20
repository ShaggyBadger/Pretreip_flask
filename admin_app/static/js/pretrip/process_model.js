// process_model.js
(function () {
  // small helper to get config (injected by template)
  const cfg = window.PRETRIP_CONFIG || {};
  const fetchColumnsUrl = cfg.fetch_columns_url;
  const csrfToken = cfg.csrf_token || '';

  const form = document.getElementById('pretripForm');
  const fileInput = document.getElementById('csvFile');
  const submitBtn = document.getElementById('submitBtn');
  const modelJsonInput = document.getElementById('model_json_input');

  if (!form || !fileInput || !submitBtn || !modelJsonInput) {
    console.warn('pretrip: missing expected DOM elements');
    return;
  }

  // robust CSV parser that handles quoted commas/newlines
  function parseCSV(text) {
    // Normalize line endings
    text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    const rows = [];
    let cur = '';
    let row = [];
    let inQuotes = false;
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      const next = text[i + 1];
      if (ch === '"') {
        if (inQuotes && next === '"') {
          // escaped quote
          cur += '"';
          i++; // skip next
        } else {
          inQuotes = !inQuotes;
        }
        continue;
      }
      if (ch === ',' && !inQuotes) {
        row.push(cur);
        cur = '';
        continue;
      }
      if (ch === '\n' && !inQuotes) {
        row.push(cur);
        rows.push(row);
        row = [];
        cur = '';
        continue;
      }
      cur += ch;
    }
    // push last field/row if any
    if (cur !== '' || row.length) {
      row.push(cur);
      rows.push(row);
    }

    // remove possible trailing empty lines
    return rows.filter(r => !(r.length === 1 && r[0].trim() === ''));
  }

  function normalizeHeader(h) {
    if (h == null) return '';
    return h.toString().trim().toLowerCase().replace(/\s+/g, '_');
  }

  async function fetchRequiredColumns() {
    if (!fetchColumnsUrl) {
      throw new Error('fetch_columns_url not provided in PRETRIP_CONFIG');
    }

    // POST to the endpoint. Send CSRF both as header and in JSON body.
    const resp = await fetch(fetchColumnsUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ csrf_token: csrfToken })
    });

    if (!resp.ok) {
      const text = await resp.text();
      throw new Error('Failed to fetch column names: ' + resp.status + ' — ' + text);
    }
    const data = await resp.json();
    // expected shape: { "required_columns": [...] }
    if (!data || !Array.isArray(data.required_columns)) {
      throw new Error('fetch returned unexpected shape: ' + JSON.stringify(data));
    }
    return data.required_columns.map(c => normalizeHeader(c));
  }

  // When user clicks submit — validate and process
  submitBtn.addEventListener('click', async function (evt) {
    evt.preventDefault();
    submitBtn.disabled = true; // prevent double-click

    const file = fileInput.files[0];
    if (!file) {
      alert('Please select a CSV file.');
      submitBtn.disabled = false;
      return;
    }

    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'csv') {
      alert('Please upload a valid CSV file.');
      submitBtn.disabled = false;
      return;
    }

    try {
      // fetch required columns from server
      const requiredCols = await fetchRequiredColumns();

      // read file
      const text = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.onload = () => resolve(String(reader.result));
        reader.readAsText(file, 'utf-8');
      });

      // strip BOM if present
      const content = text.replace(/^\uFEFF/, '');

      const rows = parseCSV(content);
      if (!rows || rows.length === 0) {
        alert('CSV appears empty.');
        submitBtn.disabled = false;
        return;
      }

      const rawHeaders = rows[0];
      const headers = rawHeaders.map(h => normalizeHeader(h));

      // check for required columns presence
      const missing = requiredCols.filter(rc => !headers.includes(rc));
      if (missing.length) {
        alert(
          'CSV is missing required columns:\n' +
            missing.join(', ') +
            '\n\nHeader detected: ' +
            headers.join(', ')
        );
        submitBtn.disabled = false;
        return;
      }

      // build objects for each data row (skip header row)
      const items = [];
      for (let r = 1; r < rows.length; r++) {
        const row = rows[r];
        // skip fully empty rows
        if (row.every(cell => cell == null || cell.toString().trim() === '')) continue;

        const obj = {};
        for (let i = 0; i < headers.length; i++) {
          const key = headers[i] || `col_${i}`;
          // store trimmed value
          obj[key] = row[i] != null ? row[i].toString().trim() : '';
        }
        items.push(obj);
      }

      const modelJson = {
        items: items,
        metadata: {
          original_filename: file.name,
          uploaded_at: new Date().toISOString()
        }
      };

      // put JSON into hidden input then submit the form
      modelJsonInput.value = JSON.stringify(modelJson);

      // if you instead want to send to a dedicated endpoint via fetch, do it here.
      // but to keep compatibility with your current add_pretrip_model, submit the form:
      form.submit();
    } catch (err) {
      console.error(err);
      alert('Error processing CSV: ' + (err.message || err));
      submitBtn.disabled = false;
    }
  });
})();
