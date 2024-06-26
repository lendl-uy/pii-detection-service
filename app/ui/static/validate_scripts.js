const labelOptions = [
    'O', 'STREET_ADDRESS',
    'PHONE_NUM',
    'URL_PERSONAL',
    'ID_NUM',
    'NAME_STUDENT',
    'USERNAME', 'EMAIL'
];
let data = {};
let activeDropdown = null;
let labelChanges = [];

$(document).ready(function() {
    const docId = window.location.pathname.split('/').pop();
    fetchDocument(docId);
});

function fetchDocument(docId) {
    $.get(`/document/${docId}`, function(doc) {
        data = doc;
        renderTokens();
    });
}

function renderTokens() {
    const container = document.getElementById('document-viewer');
    container.innerHTML = ''; // Clear existing tokens

    let isFirstToken = true; // To manage spacing correctly

    data.tokens.forEach((token, index) => {
        // Check if token starts with "▁" for new word indication
        // console.log("token: " + token);
        if (token.startsWith("▁")) {
            if (!isFirstToken) {
                // Add a space before tokens that start a new word but are not the first token
                container.appendChild(document.createTextNode(' '));
            }
            // Remove the "▁" from the token before displaying it
            token = token.slice(1);
            isFirstToken = false; // Update flag since we've processed a token
        } else {
            // For tokens that do not start with "▁" and are not the first token, add a space
            if (!isFirstToken) {
                container.appendChild(document.createTextNode(''));
            }
        }

        // Create a span for the token
        const span = document.createElement('span');
        span.classList.add('token');

        // Add class based on label, which affects color through CSS potentially
        let className = cssClassNameFromLabel(index);
        if (className) { // Only add if className is not empty
            span.classList.add(className);
        }

        // Set the text color based on the label
        span.style.color = data.labels[index] !== 'O' ? 'red' : 'black';

        // Set token text
        span.textContent = token;

        // Make token clickable
        span.onclick = function() { toggleDropdown(this, index); };

        // Append the span to the container
        container.appendChild(span);
    });
}


function cssClassNameFromLabel(index) {
    return data.labels[index] !== 'O' ? 'highlight' : '';
}

function toggleDropdown(span, index) {
    let dropdown = span.querySelector('.dropdown');
    if (activeDropdown && activeDropdown !== dropdown) {
        activeDropdown.style.display = 'none'; // Hide currently active dropdown
        activeDropdown.parentNode.classList.remove('active-token');
        activeDropdown = null;
    }
    if (!dropdown) {
        dropdown = createDropdown(labelOptions, index);
        span.appendChild(dropdown);
        span.classList.add('active-token');
        dropdown.style.display = 'block'; // Ensure dropdown is shown immediately
    } else {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
    activeDropdown = dropdown;
}

function createDropdown(options, index) {
    const dropdown = document.createElement('div');
    dropdown.className = 'dropdown';
    options.forEach(option => {
        const button = document.createElement('button');
        button.textContent = option;
        console.log(option + ': ' + data.labels[index]);
        // Apply 'active-label' class only if the option is the current label of the token
        if (option === data.labels[index]) {
            button.classList.add('active-label');  // Highlight the active label
            let className = cssClassNameFromLabel(index);
            if (className) { // Add highlight class only to the active label if it is a PII
                button.classList.add(className);
            }
        }

        button.onclick = function() {
            setLabel(index, option);
            dropdown.style.display = 'none';
            updateDropdownHighlight(dropdown, button, index); // Pass index here
        };
        dropdown.appendChild(button);
    });
    return dropdown;
}

// Additional function to update highlight
function updateDropdownHighlight(dropdown, activeButton, index) {
    Array.from(dropdown.children).forEach(button => {
        button.classList.remove('active-label', 'highlight'); // Remove both classes
    });
    activeButton.classList.add('active-label');
    let className = cssClassNameFromLabel(index);
    if (className) {
        activeButton.classList.add(className); // Add highlight class if needed
    }
}

function setLabel(index, label) {
    console.log(`Token ${index} labeled as: ${label}`);
    data.labels[index] = label;
    console.log('Token ' + data.tokens[index])
    labelChanges.push({ docId: data.doc_id, tokenIndex: index, tokens: data.tokens, newLabel: label });
    renderTokens();
}

function submitLabelChanges() {
    if (labelChanges.length > 0) {
        $.ajax({
            url: '/update-labels',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(labelChanges),
            success: function(response) {
                console.log('Labels updated successfully:', response);
                labelChanges = [];  // Clear the changes after successful update
                window.location.href = '/predictions-view';  // Redirect to the predictions view page
            },
            error: function() {
                alert('Failed to update labels');
            }
        });
    }
}

window.onclick = function(event) {
    if (!event.target.matches('.token, .dropdown, .dropdown *')) {
        if (activeDropdown) {
            activeDropdown.style.display = 'none';
            activeDropdown.parentNode.classList.remove('active-token');
            activeDropdown = null;
        }
    }
};