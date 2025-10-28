# Proper Implementation Guide for Model Config Labels

## Summary

We've implemented the infrastructure for passing model config labels to BigQuery jobs using context variables. However, we need dbt-core integration to complete the solution.

## What We've Built

### 1. Context Variable Infrastructure (`connections.py`)
```python
# Context variable for storing labels
_model_labels: ContextVar[Optional[Dict[str, str]]] = ContextVar('_model_labels', default=None)

# Helper function to set labels
def set_model_labels(labels: Optional[Dict[str, str]]) -> None:
    _model_labels.set(labels)

# Method to retrieve labels in raw_execute
def get_labels_from_model_config(self) -> Dict:
    labels = _model_labels.get()
    # Sanitize and return
```

### 2. Label Merging in `raw_execute()`
```python
# Start with labels from model config
labels = self.get_labels_from_model_config()

# Merge with query comment labels
query_comment_labels = self.get_labels_from_query_comment()
labels.update(query_comment_labels)

# Add invocation_id
labels["dbt_invocation_id"] = get_invocation_id()
```

## What's Missing

**The adapter needs to call `set_model_labels()` before executing queries.**

The challenge: The connection manager doesn't have access to the node's config during execution. We need the BigQueryAdapter (impl.py) to extract labels from the node and set them in the context.

## Solution Options

### Option 1: Intercept in Adapter (Requires dbt-core patch)

Add a method in `BigQueryAdapter` that's called before execution:

```python
# In impl.py
def execute(self, sql, **kwargs):
    # Extract labels from current node
    node_info = get_node_info()
    if node_info:
        node = self._get_node_from_manifest(node_info['unique_id'])
        if node and hasattr(node, 'config'):
            labels = getattr(node.config, 'labels', {})
            from dbt.adapters.bigquery.connections import set_model_labels
            set_model_labels(labels)
    
    return super().execute(sql, **kwargs)
```

### Option 2: Query Comment Approach (Current Workaround) ✅

Use the existing query-comment feature which already works:

```sql
-- macros/bigquery_job_labels.sql
{% macro bigquery_job_labels() %}
{%- set labels_dict = {} -%}
{%- if model is defined and model.config.labels is defined -%}
    {%- set labels_dict = model.config.labels -%}
{%- endif -%}
{{- return(tojson(labels_dict)) -}}
{% endmacro %}
```

```yaml
# dbt_project.yml
query-comment:
  comment: "{{ bigquery_job_labels() }}"
  job-label: true
  append: true
```

This works because the macro has access to the full `model` object with its config.

### Option 3: dbt-core Integration (Proper Fix)

Modify dbt-core to pass node config through execution context:

1. In `dbt/task/run.py` or similar, before calling adapter.execute():
```python
from dbt.adapters.bigquery import set_model_labels
if node.config and hasattr(node.config, 'labels'):
    set_model_labels(node.config.labels)
adapter.execute(compiled_sql)
```

2. This would require:
   - Changes to dbt-core
   - Conditional import (only if BigQuery adapter is loaded)
   - Or, make it generic for all adapters

## Recommendation

**Use Option 2 (query-comment approach)** for now. It's:
- ✅ Officially supported by dbt
- ✅ Works reliably
- ✅ No dbt-core patches needed
- ✅ Access to full model context
- ✅ Already battle-tested

For a proper long-term fix, submit a PR to dbt-core to support passing arbitrary execution context (like labels) to adapters.

## Testing the Current Implementation

The infrastructure is ready, but labels won't flow through automatically. To test once dbt-core integration is added:

```python
# Manual test in Python
from dbt.adapters.bigquery.connections import set_model_labels

set_model_labels({"team": "data", "cost_center": "cc_001"})
# Now execute a query - labels should appear on the BigQuery job
```

## Files Modified

- `connections.py`: Added context variable infrastructure and label extraction
- `__init__.py`: Exported `set_model_labels` function
- Implementation ready for dbt-core integration
