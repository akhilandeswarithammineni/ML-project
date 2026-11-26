
import pandas as pd


def detect_anomalies(readings):
    values = pd.Series(readings).astype(float)

    median = values.median()
    mad = (values - median).abs().median()

    if mad == 0:
        return values.index[
            (values - median).abs() > 0
        ].tolist()

    robust_score = 0.6745 * (values - median).abs() / mad

    return values.index[robust_score > 3.5].tolist()

