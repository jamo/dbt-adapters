# BigQuery Job Labels from Model Config

## Overview

This feature allows you to pass labels from dbt model config to BigQuery job labels for cost tracking.

## Usage

Define labels in your model config:

```sql
-- models/my_model.sql
{{ config(
    materialized="table",
    labels={
        "cost_center": "analytics",
        "team": "data_engineering",
        "environment": "production"
    }
) }}

select * from {{ ref('source_table') }}
```

## Label Precedence

When labels are defined in multiple places:
1. `dbt_invocation_id` (highest - always present)
2. Query comment labels
3. Model config labels (lowest)

## Cost Tracking Example

```sql
-- Define labels in model config
{{ config(
    labels={
        "department": "sales",
        "cost_center": "cc_1234"
    }
) }}

select sum(revenue) as total_revenue
from {{ ref('orders') }}
```

Then query BigQuery billing exports by these labels to track costs.

## Implementation

The patch modifies `connections.py` to extract labels from model config via `get_node_info()` and merge them with existing job labels.
