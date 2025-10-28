# Build Instructions for Patched dbt-bigquery

## Quick Build

From the `dbt-bigquery` directory:

```bash
docker build -f docker/Dockerfile -t dbt-bigquery:patched-model-labels .
```

## Test the Image

```bash
# Check version
docker run --rm dbt-bigquery:patched-model-labels --version

# Test with a simple dbt project
docker run --rm -v $(pwd)/my-dbt-project:/usr/app dbt-bigquery:patched-model-labels run
```

## Using in tt-dbt-runtime

The tt-dbt-runtime Dockerfile has been updated to use this patched image:

```dockerfile
FROM dbt-bigquery:patched-model-labels
```

Build your runtime image:

```bash
cd /Users/jarmo/git/tokenterminal/tt-analytics/tt-services/tt-dbt-runtime
docker build -t tt-dbt-runtime:latest .
```

## Test Model Config Labels

Create a test model with labels:

```sql
-- models/test_model.sql
{{ config(
    materialized="table",
    labels={
        "team": "analytics",
        "cost_center": "test_cc",
        "environment": "dev"
    }
) }}

select 1 as id
```

Run it and check the BigQuery job labels in the console or via API.

## What's Patched

- **Version**: 1.11.0rc1 (based on dbt-bigquery 1.11.0b1)
- **Feature**: Model config labels are passed to BigQuery job labels
- **Files Modified**:
  - `src/dbt/adapters/bigquery/connections.py`
    - Added `get_labels_from_model_config()` method
    - Modified `raw_execute()` to merge model config labels with query comment labels

## Label Precedence

1. `dbt_invocation_id` (system - highest)
2. Query comment labels
3. Model config labels (lowest)

All labels are automatically sanitized to meet BigQuery requirements.
