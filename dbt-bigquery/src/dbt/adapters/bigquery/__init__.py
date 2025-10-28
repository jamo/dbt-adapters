from dbt.adapters.bigquery.column import BigQueryColumn  # noqa
from dbt.adapters.bigquery.connections import BigQueryConnectionManager, set_model_labels  # noqa
from dbt.adapters.bigquery.credentials import BigQueryCredentials  # noqa
from dbt.adapters.bigquery.impl import BigQueryAdapter  # noqa
from dbt.adapters.bigquery.relation import BigQueryRelation  # noqa

__all__ = [
    "BigQueryRelation",
    "BigQueryColumn",
    "BigQueryConnectionManager",
    "BigQueryCredentials",
    "BigQueryAdapter",
    "set_model_labels",
]

from dbt.adapters.base import AdapterPlugin
from dbt.include import bigquery

Plugin = AdapterPlugin(
    adapter=BigQueryAdapter,  # type:ignore
    credentials=BigQueryCredentials,
    include_path=bigquery.PACKAGE_PATH,
)
