$(document).ready(function() {
    fetchDocuments();

    function fetchDocuments() {
        $.get('/documents', function(documents) {
            var content = '';
            documents.forEach(function(doc, index) {
                var highlightedText = integrateTokens(doc.full_text, doc.tokens, doc.labels);
                content += `<div class="accordion-item">
                    <h2 class="accordion-header" id="heading${index}">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}" aria-expanded="false" aria-controls="collapse${index}">
                            ${doc.truncated_text}
                        </button>
                    </h2>
                    <div id="collapse${index}" class="accordion-collapse collapse" aria-labelledby="heading${index}">
                        <div class="accordion-body" id="body${index}">
                            ${highlightedText}<br>
                            <button class="btn btn-primary mt-3" onclick="redirectToValidate(${doc.doc_id})">Validate</button>
                        </div>
                    </div>
                </div>`;
            });
            $('#documentAccordion').html(content);
        });
    }

    function integrateTokens(fullText, tokens, labels) {
        let tokenIndex = 0;
        let lastIndex = 0;
        let resultText = '';

        tokens.forEach((token, index) => {
            let position = fullText.indexOf(token, lastIndex);
            if (position !== -1) {
                let beforeText = fullText.substring(lastIndex, position);
                resultText += beforeText;
                let tokenHtml = `<span class="token ${labels[index] !== 'O' ? 'highlight' : ''}"
                                data-bs-toggle="tooltip" data-bs-placement="top" title="Label: ${labels[index]}">
                                ${token}</span>`;
                resultText += tokenHtml;
                lastIndex = position + token.length;
            }
        });

        resultText += fullText.substring(lastIndex);
        return resultText;
    }

    window.redirectToValidate = function(docId) {
        window.location.href = `/validate/${docId}`;
    };
});