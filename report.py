#!/usr/bin/env python3

import io
import boto3
import csv
import datetime
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def lambda_handler(event, context):
    ce = boto3.client('ce')
    
    services = ['AWSLambda', 'AmazonEC2']
    
    end_date = datetime.datetime.now().replace(day=1)
    start_date = (end_date - timedelta(days=1)).replace(day=1)
    month = datetime.datetime.now().replace(day=1) - timedelta(days=1)
    
    granularity = 'DAILY'
    metric = 'UnblendedCost'
    group_by = [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    
    filter = {
        'Not': {
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': ['Savings Plan Negation']
            }
        }
    }
    
    result = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity=granularity,
        Metrics=['UnblendedCost'],
        GroupBy=group_by,
        Filter=filter
    )
    
    csv_file = io.StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Service', 'Cost'])
    
    for group in result['ResultsByTime'][0]['Groups']:
        service = group['Keys'][0]
        if service in services:
            cost = group['Metrics']['UnblendedCost']['Amount']
            csv_writer.writerow([service, cost])
    
    csv_file.seek(0)
    
    ses = boto3.client('ses')
    
    from_address = "soetintaung@abccsmm.com"
    to_address = "soetintaung16@ucsmgy.edu.mm"
    subject = "AWS Cost Explorer Data"
    body = "Here is the AWS billing data from last month."
    
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body))
    
    part = MIMEApplication(csv_file.read(), _subtype='csv')
    part.add_header(
        'Content-Disposition',
        'attachment',
        filename=f'aws-cost-report-{month.strftime("%Y-%m")}.csv'
    )
    msg.attach(part)
    
    response = ses.send_raw_email(
        RawMessage={'Data': msg.as_bytes()},
        Source=from_address  # ✅ Corrected here
    )
    
    print(response)
