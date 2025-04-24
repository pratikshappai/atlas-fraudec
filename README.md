# Transaction Monitoring Subsystem

## Objective
Build a transaction monitoring system to flag suspicious transactions based on some pre-defined rules

## Input
- A CSV file with up to **10,000 rows**
- **File:** `data/transactions.csv`  
- Fields: `user_id`, `timestamp`, `merchant_name`, `amount`


## Assumptions
- Only the current CSV file is used. We do not use any historical data to do behavioural analysis.
- We do offline processing, real-time processing is not covered
- If there are multiple fraudulent transactions, we append `fraud_reason` 
- We do not test this against any labeled dataset. The focus is to do rule based implementation, that's all.
- Amount in dollars and timestamp in UNIX timestamp format

---

## Fraud Detection Rules

### 1. High Frequency Transactions
**Condition:** ≥5 transactions by the same user within a 1-minute window  
**Reason:** Real users rarely transact this fast. This must be a bot or some kind of card testing. 

### 2. Blacklisted Merchants
**Condition:** Merchant in some known blacklist
**Reason:** Known suspicious merchant, often associated with scams or money laundering. Example, some merchants in the dataset like "Fake Charity, Unknown Gift Cards" are hard to miss :)

### 3. Merchant-Specific Amount Threshold
**Condition:** Transaction amount spent exceeds a certain threshold set for that merchant (from `merchant_thresholds.json`)  
**Reason:** It can be categorized as abnormal if say, a user is spending $500 on Netflix. Similarly I have set some (relaxed) thresholds per merchant over which it is considered fraud.

### 4. Multiple Merchants in 5 Minutes
**Condition:** Transactions with ≥3 different merchants in any 5-minute window  
**Reason:** A fraudster, I assume, would like to use stolen card to transact with multiple merchants in order to escape being detected.

### 5. User-Specific Spending Spike
**Condition:** Amount is more than 3× standard deviation above user's average
**Reason:** This might be some unauthorized high-value activity using the user's card, indicating fraud.

### 6. Unusual Hour
**Condition:** Transaction time is an outlier compared to user’s spending patterns 
**Reason:** This might be helpful in capturing fraud activities that was missed in the above 5 rules. A user transacting during unusual times compared to their previous patterns might suggest fraud. 

### 7. Burst Spending Over $5000 in 10 Minutes
**Condition:** Total spending by a user >$5000 across transactions within a 10-minute window  
**Reason:** Indicates high-value fraudulent transactions.

---

## Implementation Summary

- Processed and sorted transactions by `user_id` and `timestamp`
- Each hit appends an explanation to `fraud_reason` column
- Transactions with atleast one flagged reason present in output, the rest filtered out. 

---

## Output

- **File:** `data/flagged_transactions.csv`  
- **Contents:** All transactions flagged as suspicious, with associated fraud reason(s)

---

## Dependencies

- Python 3.x
- pandas
- numpy
- scipy

---

## Notes

- This subsystem includes **7 rules** instead of the original 5. Some improvements could be to remove the hardocded thresholds from code and add them in a config file. Another improvement could be to train ML models to check for anomalies, but I think this is out of scope. Thanks for reading!

