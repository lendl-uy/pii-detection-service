Sample api call
```
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"essay": "Your essay text goes here."}' \
  http://127.0.0.1:5000/save-essay

curl -X POST \
  -H "Content-Type: application/json" \
  --data-binary "fulltext.txt" \
  http://localhost:5000/save-essay

curl -X POST \
  -H "Content-Type: application/json"   --data-binary "@fulltext.json"   http://localhost:5000/save-essay

```