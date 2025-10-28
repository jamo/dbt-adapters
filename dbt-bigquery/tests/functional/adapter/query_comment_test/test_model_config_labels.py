import pytest

from google.cloud.bigquery.client import Client

from dbt.tests.util import run_dbt


_MODEL__TABLE_WITH_LABELS = """
{{ config(
    materialized="table",
    labels={
        "cost_center": "analytics",
        "environment": "production",
        "team": "data_engineering"
    }
) }}
select 1 as id, 'test' as value
"""

_MODEL__TABLE_WITH_LABELS_AND_QUERY_COMMENT = """
{{ config(
    materialized="table",
    labels={
        "cost_center": "analytics",
        "model_label": "from_config"
    }
) }}
select 1 as id, 'test' as value
"""

_MACRO__BQ_LABELS = """
{% macro bq_labels() %}{
    "query_comment_label": "from_query_comment"
}{% endmacro %}
"""


class TestModelConfigJobLabels:
    """Test that labels from model config are passed to BigQuery job labels."""
    
    @pytest.fixture(scope="class")
    def models(self):
        return {"my_table.sql": _MODEL__TABLE_WITH_LABELS}

    def test_model_config_labels_in_job(self, project):
        """
        Test that labels defined in model config are passed to BigQuery job labels.
        This enables cost tracking for dbt runs.
        """
        results = run_dbt(["run"])
        job_id = results.results[0].adapter_response.get("job_id")
        
        with project.adapter.connection_named("_test"):
            client: Client = project.adapter.connections.get_thread_connection().handle
            job = client.get_job(job_id=job_id)

        # Verify model config labels are present
        assert job.labels.get("cost_center") == "analytics"
        assert job.labels.get("environment") == "production"
        assert job.labels.get("team") == "data_engineering"
        
        # Verify dbt_invocation_id is still present
        assert "dbt_invocation_id" in job.labels


class TestModelConfigLabelsWithQueryComment:
    """Test that model config labels work alongside query comment labels."""
    
    @pytest.fixture(scope="class")
    def models(self):
        return {"my_table.sql": _MODEL__TABLE_WITH_LABELS_AND_QUERY_COMMENT}
    
    @pytest.fixture(scope="class")
    def macros(self):
        return {"bq_labels.sql": _MACRO__BQ_LABELS}

    @pytest.fixture(scope="class")
    def project_config_update(self):
        return {
            "query-comment": {
                "comment": "{{ bq_labels() }}",
                "job-label": True,
                "append": True,
            }
        }

    def test_model_config_and_query_comment_labels_merge(self, project):
        """
        Test that labels from model config and query comment are merged correctly.
        Query comment labels should take precedence in case of conflicts.
        """
        results = run_dbt(["run"])
        job_id = results.results[0].adapter_response.get("job_id")
        
        with project.adapter.connection_named("_test"):
            client: Client = project.adapter.connections.get_thread_connection().handle
            job = client.get_job(job_id=job_id)

        # Verify model config labels are present
        assert job.labels.get("cost_center") == "analytics"
        assert job.labels.get("model_label") == "from_config"
        
        # Verify query comment labels are present
        assert job.labels.get("query_comment_label") == "from_query_comment"
        
        # Verify dbt_invocation_id is still present
        assert "dbt_invocation_id" in job.labels
