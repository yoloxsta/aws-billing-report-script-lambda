#!/usr/bin/env python3

import boto3
import datetime
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    ce = boto3.client('ce')
    current_year = datetime.datetime.utcnow().year

    # Define months to include (January to June)
    months = range(1, 7)
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
        month_label = start.strftime('%B')  # January, February, etc.
        month_labels.append(month_label)

        print(f"Fetching costs for {month_label} ({start_str} to {end_str})...")

        response = ce.get_cost_and_usage(
            TimePeriod={'Start': start_str, 'End': end_str},
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        for group in response['ResultsByTime'][0]['Groups']:
            service = group['Keys'][0]
            amount = float(group['Metrics']['BlendedCost']['Amount'])

            if service not in service_costs:
                service_costs[service] = [0.0] * len(months)
            service_costs[service][month - 1] = amount  # month-1 as index

    # Create CSV content
    header = ["Service Name"] + month_labels
    csv_lines = [",".join(header)]

    for service, costs in service_costs.items():
        line = [f'"{service}"'] + [f"${c:.2f}" for c in costs]
        csv_lines.append(",".join(line))

    # Add Total row
    total_row = ["Total"]
    for i in range(len(months)):
        total = sum(costs[i] for costs in service_costs.values())
        total_row.append(f"${total:.2f}")
    csv_lines.append(",".join(total_row))

    # Send email
    send_email("Jan-Jun {}".format(current_year), "\n".join(csv_lines))


def send_email(subject_suffix, attachment):
    msg = MIMEMultipart()
    msg['From'] = "soetintaung16@ucsmgy.edu.mm"
    msg['To'] = "soetintaungxyzzz"
    msg['Subject'] = "AWS Cost by Service ({} Billing)".format(subject_suffix)

    msg.attach(MIMEText("Attached is the AWS billing breakdown by service for {}.".format(subject_suffix)))

    part = MIMEApplication(attachment)
    part.add_header('Content-Disposition', 'attachment',
                    filename="AWS-CostByService-{}.csv".format(subject_suffix.replace(" ", "_")))
    msg.attach(part)

    client = boto3.client('ses')

    try:
        response = client.send_raw_email(RawMessage={'Data': msg.as_string()})
        print("Email sent! Message ID:", response['ResponseMetadata']['RequestId'])
    except ClientError as e:
        print("Error sending email:", e.response['Error']['Message'])


if __name__ == "__main__":
    lambda_handler({}, {})
