function goToSubmitEssay() {
    window.location.href = "/save-essay-view";
}

function goToPredictionsView() {
    window.location.href = "/predictions-view";
}

function submitDocument() {
    var essayText = document.getElementById("essay-textbox").value;
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
    })
    .catch((error) => {
        console.error("Error:", error);
        alert("Failed to detect PII.");
    });
}