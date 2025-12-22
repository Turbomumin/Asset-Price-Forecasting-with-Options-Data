import numpy as np
import pandas as pd
from scipy.stats import norm

def bs_delta(options_df, spot):
    df = options_df.copy()

    # Force spot into Series aligned with df
    if isinstance(spot, (int, float)):
        S = pd.Series(spot, index=df.index, dtype="float64")
    else:
        S = spot.reindex(df.index).astype("float64")

    r = 0.03
    q = 0.0

    K = df["strike"].astype(float)
    sigma = df["impliedVolatility"].astype(float)
    T = (df["days_to_expiry"].astype(float) / 365.0).clip(lower=0.0)

    denom = sigma * np.sqrt(T)
    valid = (S > 0) & (K > 0) & (sigma > 0) & (T > 0) & denom.notna()

    d1 = pd.Series(np.nan, index=df.index, dtype="float64")
    d1.loc[valid] = (
        (np.log(S.loc[valid] / K.loc[valid]) +
         (r - q + 0.5 * sigma.loc[valid] ** 2) * T.loc[valid])
        / denom.loc[valid]
    )

    # d2 for risk-neutral ITM probability at expiry
    d2 = pd.Series(np.nan, index=df.index, dtype="float64")
    d2.loc[valid] = d1.loc[valid] - denom.loc[valid]

    Nd1 = pd.Series(np.nan, index=df.index, dtype="float64")
    Nd1.loc[valid] = norm.cdf(d1.loc[valid])

    disc_q = np.exp(-q * T)

    delta = pd.Series(np.nan, index=df.index, dtype="float64")

    is_call = df["option_type"].str.upper() == "C"
    is_put = df["option_type"].str.upper() == "P"

    # Standard BS delta
    delta.loc[valid & is_call] = disc_q.loc[valid & is_call] * Nd1.loc[valid & is_call]
    delta.loc[valid & is_put] = disc_q.loc[valid & is_put] * (Nd1.loc[valid & is_put] - 1.0)

    # Expiry fallback for delta
    near_exp = (T <= 0) | (sigma <= 0) | S.isna()
    if near_exp.any():
        delta.loc[near_exp & is_call & (S > K)] = 1.0
        delta.loc[near_exp & is_call & (S <= K)] = 0.0
        delta.loc[near_exp & is_put & (S < K)] = -1.0
        delta.loc[near_exp & is_put & (S >= K)] = 0.0

    # Risk-neutral probability of expiring ITM (European-style, BS lognormal)
    prob_itm = pd.Series(np.nan, index=df.index, dtype="float64")
    prob_itm.loc[valid & is_call] = norm.cdf(d2.loc[valid & is_call])
    prob_itm.loc[valid & is_put] = norm.cdf(-d2.loc[valid & is_put])

    # Expiry fallback for prob_itm
    if near_exp.any():
        prob_itm.loc[near_exp & is_call & (S > K)] = 1.0
        prob_itm.loc[near_exp & is_call & (S <= K)] = 0.0
        prob_itm.loc[near_exp & is_put & (S < K)] = 1.0
        prob_itm.loc[near_exp & is_put & (S >= K)] = 0.0

    df["delta"] = delta.round(4)

    # Your earlier preference: force put deltas positive
    df.loc[is_put, "delta"] = df.loc[is_put, "delta"].abs()

    df["prob_itm_rn"] = prob_itm.round(4)

    return df
