#!/usr/bin/env python3

import boto3
import datetime
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    now = datetime.datetime.utcnow()
    current_year = now.year
    current_month = now.month

    # If it's January, no previous full month billing data yet
    if current_month == 1:
        print("No full months billing data available yet.")
        return

    months = range(1, current_month)  # January to previous month
    ce = boto3.client('ce')

    service_costs = {}
    month_labels = []

    for month in months:
        start = datetime.datetime(current_year, month, 1)
        if month == 12:
            end = datetime.datetime(current_year + 1, 1, 1)
        else:
            end = datetime.datetime(current_year, month + 1, 1)

        start_str = start.strftime('%Y-%m-%d')
        end_str = end.strftime('%Y-%m-%d')
        month_label = start.strftime('%B')
        month_labels.append(month_label)

        print(f"Fetching costs for {month_label} ({start_str} to {end_str})...")

        try:
            response = ce.get_cost_and_usage(
                TimePeriod={'Start': start_str, 'End': end_str},
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
        except ClientError as e:
            print(f"Error fetching cost for {month_label}: {e.response['Error']['Message']}")
            continue

        for group in response['ResultsByTime'][0]['Groups']:
            service = group['Keys'][0]
            amount = float(group['Metrics']['BlendedCost']['Amount'])

            if service not in service_costs:
                service_costs[service] = [0.0] * len(months)
            service_costs[service][month - 1] = amount  # month-1 is the index

    # Prepare CSV content
    header = ["Service Name"] + month_labels
    csv_lines = [",".join(header)]

    for service, costs in service_costs.items():
        line = [f'"{service}"'] + [f"${c:.2f}" for c in costs]
        csv_lines.append(",".join(line))

    # Add total row per month
    total_row = ["Total"]
    for i in range(len(months)):
        total = sum(costs[i] for costs in service_costs.values())
        total_row.append(f"${total:.2f}")
    csv_lines.append(",".join(total_row))

    # Send email with the CSV attachment
    send_email(f"Jan to {month_labels[-1]} {current_year}", "\n".join(csv_lines))


def send_email(subject_suffix, attachment):
    msg = MIMEMultipart()
    msg['From'] = "soetintaung..."  # Change as needed
    msg['To'] = "soetintaungxyzz"                # Change as needed
    msg['Subject'] = f"AWS Cost by Service ({subject_suffix} Billing)"

    msg.attach(MIMEText(f"Attached is the AWS billing breakdown by service for {subject_suffix}."))

    part = MIMEApplication(attachment)
    part.add_header(
        'Content-Disposition',
        'attachment',
        filename=f"AWS-CostByService-{subject_suffix.replace(' ', '_')}.csv"
    )
    msg.attach(part)

    client = boto3.client('ses')

    try:
        response = client.send_raw_email(RawMessage={'Data': msg.as_string()})
        print("Email sent! Message ID:", response['ResponseMetadata']['RequestId'])
    except ClientError as e:
        print("Error sending email:", e.response['Error']['Message'])


if __name__ == "__main__":
    lambda_handler({}, {})
