from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64


transaction_source = FileSource(
    path="data/features/fraud_transactions.parquet",
    timestamp_field="event_timestamp",
)

customer = Entity(name="customer_id", join_keys=["customer_id"])

fraud_features_v1 = FeatureView(
    name="fraud_features_v1",
    entities=[customer],
    ttl=timedelta(days=2),
    schema=[
        Field(name="txn_count_24h", dtype=Int64),
        Field(name="avg_amount_24h", dtype=Float32),
        Field(name="chargeback_rate_30d", dtype=Float32),
    ],
    online=True,
    source=transaction_source,
    tags={"domain": "fraud", "version": "v1", "phase": "phase1"},
)
