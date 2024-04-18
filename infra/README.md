# Infra

## Setting up the network
```
docker network create datastack-network
```

## Initialize PostgreSQL
1. Create the schema
```
create schema docs;
```
2. Create the table needed
```
CREATE TABLE docs.document_table (
    doc_id SERIAL PRIMARY KEY,
    fulltext TEXT,
    token TEXT[],
    labels TEXT[] DEFAULT NULL,
    validated_labels TEXT[] DEFAULT NULL,
    for_retrain BOOLEAN DEFAULT FALSE
);
```