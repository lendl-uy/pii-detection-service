####Vanilla JS UI for AI 231

Index has a JS script that renders a datum, a single json of {document: ... full_text: ... labels } based on PII detection dataset.

Current feature.
-- Render document with color coded background to indicated PII label.
-- Can be used for validation as selection for label classification can be changed via menu.

Current limitation.
-- hard coded data


TODO:
-- accept json from external source(from postgres via backend_service).
-- save validated document (through backend_service)
-- Document selection(need list/pagination from backend_service)