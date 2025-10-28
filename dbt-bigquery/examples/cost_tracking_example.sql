-- Example: Cost Tracking with Model Config Labels
-- This shows how to use the new label feature for cost attribution

-- =============================================================================
-- Example 1: Simple cost center tracking
-- =============================================================================

-- models/finance/revenue_report.sql
{{ config(
    materialized="table",
    labels={
        "department": "finance",
        "cost_center": "cc_finance_001",
        "priority": "high"
    }
) }}

select
    order_date,
    sum(revenue) as total_revenue
from {{ ref('orders') }}
group by 1;


-- =============================================================================
-- Example 2: Multi-tenant client billing
-- =============================================================================

-- models/client_reports/client_abc_dashboard.sql
{{ config(
    materialized="view",
    labels={
        "client_id": "abc_corp",
        "client_tier": "enterprise",
        "billing_code": "bc_abc_001"
    }
) }}

select *
from {{ ref('base_metrics') }}
where client_id = 'abc_corp';


-- =============================================================================
-- Example 3: Team-based cost allocation
-- =============================================================================

-- models/analytics/user_engagement.sql
{{ config(
    materialized="incremental",
    labels={
        "team": "analytics",
        "project": "user_growth",
        "owner": "data_team"
    },
    incremental_strategy="merge",
    unique_key="user_id"
) }}

select
    user_id,
    count(*) as session_count,
    current_timestamp() as updated_at
from {{ ref('sessions') }}
{% if is_incremental() %}
    where session_timestamp > (select max(updated_at) from {{ this }})
{% endif %}
group by 1;


-- =============================================================================
-- Example 4: Using dbt_project.yml for default labels
-- =============================================================================

-- dbt_project.yml
-- models:
--   my_project:
--     # Default labels for all models
--     +labels:
--       environment: "production"
--       managed_by: "dbt"
--     
--     # Finance models get specific labels
--     finance:
--       +labels:
--         department: "finance"
--         cost_center: "cc_finance_001"
--     
--     # Analytics models get different labels
--     analytics:
--       +labels:
--         department: "analytics"
--         cost_center: "cc_analytics_002"

-- Then in your model, these labels are automatically applied:
-- models/finance/monthly_revenue.sql
select sum(revenue) from {{ ref('orders') }};
-- This will have labels: environment=production, managed_by=dbt, 
--                         department=finance, cost_center=cc_finance_001


-- =============================================================================
-- Example 5: Query BigQuery billing to see costs by label
-- =============================================================================

-- Run this query in BigQuery to analyze costs by team
select
    team_label.value as team,
    cost_center_label.value as cost_center,
    count(distinct job_id) as job_count,
    sum(total_slot_ms) / 1000 / 60 / 60 as slot_hours,
    sum(cost) as total_cost_usd
from `your-project.billing_dataset.gcp_billing_export_v1_*`
cross join unnest(labels) as team_label
cross join unnest(labels) as cost_center_label
where service.description = 'BigQuery'
    and team_label.key = 'team'
    and cost_center_label.key = 'cost_center'
    and date(usage_start_time) >= current_date() - 30
group by 1, 2
order by 5 desc;


-- =============================================================================
-- Example 6: Combining with query comments
-- =============================================================================

-- macros/bq_labels.sql
-- {% macro bq_labels() %}{
--     "system": "dbt",
--     "environment": "{{ target.name }}"
-- }{% endmacro %}

-- dbt_project.yml
-- query-comment:
--   comment: "{{ bq_labels() }}"
--   job-label: true
--   append: true

-- models/my_model.sql
{{ config(
    labels={
        "team": "data",
        "model_type": "mart"
    }
) }}

select * from {{ ref('source') }};

-- This will have labels:
--   - team: data (from model config)
--   - model_type: mart (from model config)
--   - system: dbt (from query comment)
--   - environment: prod (from query comment, based on target)
--   - dbt_invocation_id: <uuid> (automatic)
