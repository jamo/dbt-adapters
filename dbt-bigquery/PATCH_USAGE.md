# BigQuery Model Config Labels Patch

## What This Patch Does

Adds support for passing `labels` from dbt model config to BigQuery job labels. This enables cost tracking and attribution for all dbt runs.

## Quick Start

### 1. Add labels to your dbt models

```sql
-- models/my_model.sql
{{ config(
    materialized="table",
    labels={
        "team": "analytics",
        "cost_center": "cc_001",
        "project": "revenue_reporting"
    }
) }}

select * from {{ ref('source_data') }}
```

### 2. Set default labels in dbt_project.yml

```yaml
# dbt_project.yml
models:
  my_project:
    +labels:
      environment: "production"
      team: "data"
    
    marts:
      finance:
        +labels:
          cost_center: "finance"
```

### 3. Run your models

```bash
dbt run
```

The BigQuery jobs will now include your custom labels alongside the automatic `dbt_invocation_id` label.

### 4. Track costs in BigQuery billing exports

```sql
SELECT
    labels.value as team,
    labels2.value as cost_center,
    SUM(cost) as total_cost
FROM `project.billing_dataset.gcp_billing_export_v1_*`
CROSS JOIN UNNEST(labels) as labels
CROSS JOIN UNNEST(labels) as labels2
WHERE labels.key = 'team'
    AND labels2.key = 'cost_center'
    AND service.description = 'BigQuery'
    AND DATE(usage_start_time) >= CURRENT_DATE() - 30
GROUP BY 1, 2
ORDER BY 3 DESC
```

## Files Modified

- `src/dbt/adapters/bigquery/connections.py`
  - Added `get_labels_from_model_config()` method
  - Modified `raw_execute()` to merge model config labels with query comment labels

## Files Added

- `tests/functional/adapter/query_comment_test/test_model_config_labels.py` - Test suite
- `docs/MODEL_CONFIG_LABELS.md` - Detailed documentation

## Label Rules

BigQuery labels must follow these rules (automatically sanitized):
- Lowercase letters, numbers, hyphens, underscores only
- Max 63 characters per key/value
- Example: `Cost Center` becomes `cost_center`

## Testing

```bash
# Run the new tests
pytest tests/functional/adapter/query_comment_test/test_model_config_labels.py -v

# Run all BigQuery tests
pytest tests/functional/adapter/ -v
```

## Example: Multi-tenant Cost Tracking

```sql
-- models/client_reports/client_a_metrics.sql
{{ config(
    labels={
        "client": "client_a",
        "report_type": "metrics",
        "billing_code": "ba_001"
    }
) }}

select * from {{ ref('base_metrics') }}
where client_id = 'client_a'
```

```sql
-- models/client_reports/client_b_metrics.sql
{{ config(
    labels={
        "client": "client_b",
        "report_type": "metrics",
        "billing_code": "bb_002"
    }
) }}

select * from {{ ref('base_metrics') }}
where client_id = 'client_b'
```

Now you can track BigQuery costs per client using the labels in your billing exports.
