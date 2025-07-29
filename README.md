### Monthly Billing Report by using Lambda,SES,EventBridge

#### Pre requirements 

- I'll write later.

```
now = datetime.datetime.utcnow()
end = datetime.datetime(year=now.year, month=now.month, day=1)  # Start of current month
start = end - datetime.timedelta(days=1)  # Last day of previous month
start = datetime.datetime(year=start.year, month=start.month, day=1)  # First day of previous month

# Converts datetime to string format
start_str = start.strftime('%Y-%m-%d')
end_str = end.strftime('%Y-%m-%d')

For example, if today is July 11, 2025, this will resolve to:
start_str = "2025-06-01"
end_str = "2025-07-01"
✅ So this will fetch data for June 2025, exactly as you want.

---

# Set time range to last full calendar month
now = datetime.datetime.utcnow()

# Start of the current month (exclusive end date for AWS Cost Explorer)
current_month_start = datetime.datetime(year=now.year, month=now.month, day=1)

# Go one day back to land in the previous month
last_day_of_previous_month = current_month_start - datetime.timedelta(days=1)

# Get the first day of the previous month
previous_month_start = datetime.datetime(year=last_day_of_previous_month.year, month=last_day_of_previous_month.month, day=1)

# For display
billing_month = previous_month_start.strftime('%Y-%m')

# Convert to strings for AWS API
start_str = previous_month_start.strftime('%Y-%m-%d')
end_str = current_month_start.strftime('%Y-%m-%d')

print(f"Getting cost data for {start_str} to {end_str}")
```
