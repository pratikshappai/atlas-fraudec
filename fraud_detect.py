import pandas as pd
import numpy as np
import json
from scipy.stats import zscore

# load and preprocess data
df = pd.read_csv("data/transactions.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s')
df = df.sort_values(by=["user_id", "timestamp"]).reset_index(drop=True)
df["fraud_reason"] = None 

# helper to append to fraud_reason col
def append_reason(mask, reason):
    df.loc[mask, "fraud_reason"] = df.loc[mask, "fraud_reason"].apply(
        lambda x: reason if pd.isna(x) or x == "" else x + " | " + reason
    )

# high frequency transactions, i.e, ≥5 in 1 minute
def flag_high_freq(group):
    group = group.sort_values("timestamp")
    times = group["timestamp"].values
    mask = [False] * len(times)
    for i in range(4, len(times)):
        if (times[i] - times[i - 4]) <= np.timedelta64(60, 's'):
            mask[i] = mask[i - 1] = mask[i - 2] = mask[i - 3] = mask[i - 4] = True
    group["high_freq_flag"] = mask
    return group

df = df.groupby("user_id", group_keys=False).apply(flag_high_freq)
append_reason(df["high_freq_flag"], "high frequency")


# blacklisted sellers 
blacklist = {"Unknown Gift Cards", "Luxury Watches", "Crypto Exchange", "Fake Charity"}
append_reason(df["merchant_name"].isin(blacklist), "blacklisted merchant")

# check whether user is spending unusual amount of money for a specific merchant 
# i have specified a very relaxed threshold for the merchants currently
with open("merchant_thresholds.json", "r") as f:
    thresholds = json.load(f)
for merchant, threshold in thresholds.items():
    mask = (df["merchant_name"] == merchant) & (df["amount"] > threshold)
    append_reason(mask, f"{merchant} txn > ${threshold}")

# multiple merchants in 5 min
def merchant_window_count(group):
    group = group.sort_values("timestamp").set_index("timestamp")
    group["merchant_count_5min"] = group["merchant_name"].rolling("5min").count()
    return group.reset_index()

df = df.groupby("user_id", group_keys=False).apply(merchant_window_count)
append_reason(df["merchant_count_5min"] >= 3, "multiple merchants in 5min")

# unusual spending spike for the user
user_avg = df.groupby("user_id")["amount"].transform("mean")
user_std = df.groupby("user_id")["amount"].transform("std")
append_reason(df["amount"] > (user_avg + 3 * user_std), "user spending spike")

# unusual hour based on user's behaviour 
df["hour"] = df["timestamp"].dt.hour

def flag_unusual_hours(group):
    if len(group) < 3:
        return pd.Series([False] * len(group), index=group.index)
    z_scores = zscore(group["hour"])
    return np.abs(z_scores) > 2

df["odd_hour_flag"] = df.groupby("user_id", group_keys=False).apply(flag_unusual_hours)
append_reason(df["odd_hour_flag"], "unusual hour")

# burst spending in 10 min 
df = df.set_index("timestamp").sort_index()
df["rolling_10min_amount"] = (
    df.groupby("user_id")["amount"]
      .rolling("10min")
      .sum()
      .reset_index(level=0, drop=True)
)
df["rolling_10min_amount"] = df["rolling_10min_amount"].round(2)
df = df.reset_index()
append_reason(df["rolling_10min_amount"] > 5000, "burst spending > $5000 in 10min")

# flagged transactions
df.drop(columns=["high_freq_flag", "merchant_count_5min", "hour", "odd_hour_flag", "rolling_10min_amount"], inplace=True)
flagged_df = df[df["fraud_reason"].notnull()]
flagged_df.to_csv("data/flagged_transactions.csv", index=False)
