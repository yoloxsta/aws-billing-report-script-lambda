#!/usr/bin/env python3

import boto3
import datetime

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    # Create a Cost Explorer client
    client = boto3.client('ce')

    # Set time range to last full calendar month
    now = datetime.datetime.utcnow()
    end = datetime.datetime(year=now.year, month=now.month, day=1)
    start = end - datetime.timedelta(days=1)
    start = datetime.datetime(year=start.year, month=start.month, day=1)

    # For display
    month = start.strftime('%Y-%m')

    # Convert to strings
    start_str = start.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')

    print(f"Getting cost data for {start_str} to {end_str}")

    # Get cost data grouped by service
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_str,
            'End':  end_str
        },
        Granularity='MONTHLY',
        Metrics=['BlendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            },
        ]
    )

    tsv_lines = []
    tsv_lines.append("Service Name\tAmount (USD)")

    total = 0.0
    for group in response["ResultsByTime"][0]["Groups"]:
        service_name = group['Keys'][0]
        amount = float(group['Metrics']['BlendedCost']['Amount'])
        total += amount
        line = "{}\t${:,.2f}".format(service_name, amount)
        print(line)
        tsv_lines.append(line)

    tsv_lines.append("Total\t${:,.2f}".format(total))

    # Send email with TSV attachment
    send_email(month, "\n".join(tsv_lines))


def send_email(month, attachment):
    msg = MIMEMultipart()
    msg['From'] = "soetintaung16@ucsmgy.edu.mm"
    msg['To'] = "soetintaungxxxxx"
    msg['Subject'] = "Monthly AWS Cost by Service: {}".format(month)

    # Email body
    part = MIMEText('Attached is the AWS billing breakdown by service for {}.'.format(month))
    msg.attach(part)

    # Attachment
    part = MIMEApplication(attachment)
    part.add_header('Content-Disposition', 'attachment', filename="AWS-MonthlyCostByService-{}.tsv".format(month))
    msg.attach(part)

    # SES client
    client = boto3.client('ses')

    try:
        response = client.send_raw_email(
            RawMessage={
                'Data': msg.as_string(),
            }
        )
    except ClientError as e:
        print("Error sending email:", e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:", response['ResponseMetadata']['RequestId'])


if __name__ == "__main__":
    lambda_handler({}, {})
