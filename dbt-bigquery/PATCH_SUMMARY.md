# dbt-bigquery Model Config Labels Patch - Summary

## Problem Statement
dbt doesn't natively support passing labels from model config to BigQuery job labels. This makes cost tracking and attribution difficult for teams running dbt at scale.

## Solution
This patch extends dbt-bigquery to extract labels from model configurations and pass them to BigQuery jobs, enabling granular cost tracking.

## Changes Made

### 1. Core Implementation (connections.py)

#### New Method: `get_labels_from_model_config()`
- **Location**: `src/dbt/adapters/bigquery/connections.py:224-255`
- **Purpose**: Extracts labels from the current model's config via `get_node_info()`
- **Features**:
  - Safely accesses node context
  - Extracts labels dictionary from config
  - Sanitizes keys/values to meet BigQuery requirements
  - Returns empty dict if no labels found

#### Modified Method: `raw_execute()`
- **Location**: `src/dbt/adapters/bigquery/connections.py:269-315`
- **Changes**:
  - Line 281: Call `get_labels_from_model_config()` first
  - Line 284-285: Merge with query comment labels (query comment takes precedence)
  - Line 288: Add `dbt_invocation_id` (highest precedence)
- **Label Precedence** (highest to lowest):
  1. `dbt_invocation_id` (system)
  2. Query comment labels
  3. Model config labels

### 2. Test Suite
- **File**: `tests/functional/adapter/query_comment_test/test_model_config_labels.py`
- **Coverage**:
  - `TestModelConfigJobLabels`: Tests basic label extraction from config
  - `TestModelConfigLabelsWithQueryComment`: Tests label merging behavior

### 3. Documentation
- `PATCH_USAGE.md`: Quick start guide with examples
- `docs/MODEL_CONFIG_LABELS.md`: Detailed documentation
- `PATCH_SUMMARY.md`: This file

## How It Works

```
Model Config (labels={...})
         ↓
get_labels_from_model_config()
         ↓
Sanitize labels
         ↓
Merge with query comment labels
         ↓
Add dbt_invocation_id
         ↓
Pass to QueryJobConfig
         ↓
BigQuery Job with labels
```

## Usage Example

```sql
-- models/my_model.sql
{{ config(
    materialized="table",
    labels={
        "team": "analytics",
        "cost_center": "cc_123"
    }
) }}

select * from {{ ref('source') }}
```

When this model runs, the BigQuery job will have:
- `team: analytics`
- `cost_center: cc_123`
- `dbt_invocation_id: <uuid>`

## Testing

```bash
# Run new tests
pytest tests/functional/adapter/query_comment_test/test_model_config_labels.py -v

# Run all tests
pytest tests/functional/adapter/ -v
```

## Benefits

1. **Cost Tracking**: Track BigQuery costs by team, project, or cost center
2. **Multi-tenant**: Bill clients based on their specific model runs
3. **Auditing**: Better visibility into which models drive costs
4. **Flexibility**: Combine with existing query comment labels
5. **No Breaking Changes**: Fully backward compatible

## Backward Compatibility

✅ Fully backward compatible:
- Existing query comment labels continue to work
- No changes to existing behavior if labels not configured
- Query comment labels still take precedence over model config

## Label Sanitization

All labels are automatically sanitized to meet BigQuery requirements:
- Converted to lowercase
- Special characters replaced with underscores
- Truncated to 63 characters
- Example: `Cost Center` → `cost_center`

## Technical Notes

### Why `get_node_info()`?
- Provides access to the current model's context during execution
- Available via `dbt_common.events.contextvars`
- Contains full node information including config

### Label Merging Strategy
1. Start with model config labels (base layer)
2. Overlay query comment labels (overrides conflicts)
3. Add system label `dbt_invocation_id` (always present)

### Performance Impact
- Minimal: Only adds dictionary lookups and sanitization
- No additional BigQuery API calls
- No impact on query execution time

## Future Enhancements

Potential improvements:
- Add environment variable interpolation in labels
- Support label templates
- Add validation warnings for invalid label formats
- Create dbt docs integration for label documentation

## Support

For issues or questions:
1. Check the test suite for examples
2. Review `PATCH_USAGE.md` for common patterns
3. See `docs/MODEL_CONFIG_LABELS.md` for detailed docs
