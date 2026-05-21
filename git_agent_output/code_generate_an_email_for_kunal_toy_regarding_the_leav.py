"""
Module to generate an email for Kunal Toy regarding a summer leave request.
This script will create a draft email with a clear subject line, formal greeting,
introduction, details about the leave request, closing statement, and professional sign-off.
"""

import os
from datetime import datetime, timedelta

def generate_email(name, supervisor_name, start_date, end_date):
    # Define the email template
    email_template = """
Subject: Request for Summer Leave

Dear {supervisor_name},

I hope this email finds you well. As the summer season approaches, I am writing to request a leave of 30 days to ensure I can take a substantial break and recharge. I understand that this is a busy period for the company, but I have reviewed our team's schedule and have made arrangements to ensure that my responsibilities are covered during my absence.

The dates for my leave would be from {start_date} to {end_date}, totaling 30 days. I have made sure that all my current projects are up to date, and I have discussed with the team to ensure a smooth transition of tasks while I am away. If there are any concerns or if there is any additional information needed from me, please let me know as soon as possible.

I would greatly appreciate it if you could approve my request. Please confirm once you have reviewed and approved my leave. If there are any issues, I am more than willing to discuss alternative dates or make necessary adjustments.

Thank you for your understanding and support. I look forward to hearing back from you.

Best regards,
{name}
"""

    # Fill in the email template with the provided information
    email = email_template.format(
        name=name,
        supervisor_name=supervisor_name,
        start_date=start_date,
        end_date=end_date
    )

    return email

def get_dates(days):
    # Calculate the start and end dates for the leave
    today = datetime.today()
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")

    return start_date, end_date

if __name__ == "__main__":
    # Define the name and supervisor's name
    name = "Kunal Toy"
    supervisor_name = "Supervisor's Name"

    # Define the number of days for the leave
    days = 30

    # Get the start and end dates for the leave
    start_date, end_date = get_dates(days)

    # Generate the email
    email = generate_email(name, supervisor_name, start_date, end_date)

    # Print the email
    print(email)