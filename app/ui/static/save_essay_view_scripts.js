function detectPII() {
    var modalEl = document.getElementById('confirmationModal');
    var modal = bootstrap.Modal.getInstance(modalEl);
    modal.hide();
    submitDocument(); // Call the existing function that submits the document
}

function submitDocument() {
    var essayText = document.getElementById("essay-textbox").value;
    var spinner = document.getElementById("spinner");
    spinner.style.display = "block"; // Show the spinner

    fetch("/save-essay", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ essay: essayText })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Success:", data);
        spinner.style.display = "none"; // Hide the spinner after success
        window.location.href = '/predictions-view'; // Navigate to predictions view
    })
    .catch((error) => {
        console.error("Error:", error);
        alert("Failed to detect PII.");
        spinner.style.display = "none"; // Hide the spinner if there is an error
    });
}