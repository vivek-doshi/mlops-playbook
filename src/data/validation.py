import pandas as pd
from pydantic import BaseModel, Field, ValidationError


class DataSchema(BaseModel):
    feature_0: float
    feature_1: float
    feature_2: float
    feature_3: float
    feature_4: float
    feature_5: float
    feature_6: float
    feature_7: float
    feature_8: float
    feature_9: float
    target: int = Field(ge=0, le=1)


def validate_data(df: pd.DataFrame) -> bool:
    """Validates dataframe against Pydantic schema."""
    records = df.to_dict(orient="records")
    valid = True
    for idx, record in enumerate(records):
        try:
            DataSchema(**record)
        except ValidationError as e:
            print(f"Validation error at row {idx}: {e}")
            valid = False
            break

    if valid:
        print("Data validation passed.")
    return valid
