async function getValidColumnNames(csrfToken) {
  // the csrf token is in the main file a little earlier. We can use it here.
  let response = await fetch('/admin/pretrip/fetch-column-names', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: JSON.stringify({ dummy: true }),
  });

  let data = await response.json();
  console.log(data);
  return data.valid_column_names; // assuming the server returns { valid_column_names: [...] }
}

function readFile(file, csrfToken) {
  // ok, first read the file contents
  // then, send that data to processContents.
  let reader = new FileReader();

  // make helper function to send both the event and the csrf token to fetchFileData
  reader.onload = function (event) {
    fetchFileData(event, csrfToken);
  };

  // Start reading the file as text
  reader.readAsText(file);
}

async function fetchFileData(eventOjb, csrfToken) {
  console.log('processing file contents');
  let file_contents = eventOjb.target.result;
  let valid_column_names = await getValidColumnNames(csrfToken);
}

function verifyColumnNames(csv_file) {
  let reader = new FileReader();
}

function controller(csrfToken) {}
