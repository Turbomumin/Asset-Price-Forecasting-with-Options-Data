import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def get_interest_rate(options_df):
    df = options_df.copy()

    # Removing (1) Options without a reliable call AND put price, and (2) Options expiring within 30 days
    df = df[df["days_to_expiry"] >= 90]

    df = (
        df.groupby(["expiry", "strike"])
          .filter(lambda x: set(x["option_type"]) == {"C", "P"})
    )

    wide = (
        df.pivot_table(
            index=["expiry", "days_to_expiry", "strike"],
            columns="option_type",
            values="mid_price",
            aggfunc="first"
        )
        .rename(columns={"C": "call_mid", "P": "put_mid"})
        .reset_index()
    )

    wide = wide.dropna(subset=["call_mid", "put_mid"])

    return wide

def box_spread_calc(rf_rate_df, min_width=0.5, max_width=None):
    df = rf_rate_df.copy()

    df = df.dropna(subset=["expiry", "days_to_expiry", "strike", "call_mid", "put_mid"])
    df = df.sort_values(["expiry", "strike"])

    rows = []

    for expiry, g in df.groupby("expiry", sort=False):
        g = g.sort_values("strike").reset_index(drop=True)
        T = float(g["days_to_expiry"].iloc[0]) / 365.0

        # Pair all strikes within the same expiry
        K = g["strike"].to_numpy()
        C = g["call_mid"].to_numpy()
        P = g["put_mid"].to_numpy()

        n = len(g)
        for i in range(n - 1):
            for j in range(i + 1, n):
                k1, k2 = K[i], K[j]
                width = k2 - k1

                if width < min_width:
                    continue
                if (max_width is not None) and (width > max_width):
                    break  # strikes sorted, width only grows

                # Long box price using mids
                # Long C(k1), short C(k2), short P(k1), long P(k2)
                box_price = (C[i] - C[j]) + (P[j] - P[i])

                # Basic sanity filters
                if not np.isfinite(box_price):
                    continue
                if box_price <= 0:
                    continue

                rows.append(
                    {
                        "expiry": expiry,
                        "days_to_expiry": g["days_to_expiry"].iloc[0],
                        "T_years": T,
                        "K1": k1,
                        "K2": k2,
                        "width": width,
                        "box_mid": box_price,
                    }
                )

    box_df = pd.DataFrame(rows)

    # Optional: implied rate from box price
    # PV = width * exp(-rT)  => r = -ln(PV/width)/T
    if not box_df.empty:
        box_df["implied_r"] = (((box_df["width"] / box_df["box_mid"]) - 1) * (365 / box_df["days_to_expiry"]))
        #box_df["implied_r"] = -np.log(box_df["box_mid"] / box_df["width"]) / box_df["T_years"]

    return box_df

def plot_box_rates(box_df):
    df = box_df.copy()

    # Drop nonsense values
    df = df[np.isfinite(df['implied_r'])]
    df = df[df['implied_r'] > -0.05]
    df = df[df['implied_r'] < 0.2]

    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='days_to_expiry', y='implied_r', data=df)
    plt.title('Box Spread Rates')
    plt.xlabel('days_to_expiry')
    plt.ylabel('Implied Rate')
    plt.show()

    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='width', y='implied_r', data=df)
    plt.title('Box Spread Rates')
    plt.xlabel('width')
    plt.ylabel('Implied Rate')
    plt.show()

def mean_and_std_r(box_df):
    df = box_df.copy()
    mean_r = df["implied_r"].mean()
    mean_r = round(float(mean_r), 4)
    std_r = df["implied_r"].std()
    std_r = round(float(std_r), 4)
    return mean_r, std_r

def run_all_box_rates(options_df):
    rf_rate_df = get_interest_rate(options_df)  # your wide df
    box_df = box_spread_calc(rf_rate_df, min_width=100, max_width=None)
    print(f"Interest rate box spreads: {len(box_df)}")
    #plot_box_rates(box_df) #TODO: Uncomment this if you want to see the box rates plot
    return mean_and_std_r(box_df)