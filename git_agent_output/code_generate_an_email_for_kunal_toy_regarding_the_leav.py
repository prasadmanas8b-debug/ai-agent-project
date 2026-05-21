"""
Module to generate an email for Kunal Toy's summer leave request.
This script creates a draft email based on the provided template and allows for customization of the supervisor's name and leave dates.
"""

import os
from datetime import datetime, timedelta

def generate_email(supervisor_name, start_date, end_date):
    # Define the email template
    email_template = """
Subject: Request for Summer Leave

Dear {supervisor_name},

I hope this email finds you well. As the summer season approaches, I am writing to request a leave of 30 days to ensure I can take a substantial break and recharge. I understand that this is a busy period for the company, but I have reviewed our team's schedule and have made arrangements to ensure that my responsibilities are covered during my absence.

The dates for my leave would be from {start_date} to {end_date}, totaling 30 days. I have made sure that all my current projects are up to date, and I have discussed with the team to ensure a smooth transition of tasks while I am away. If there are any concerns or if there is any additional information needed from me, please let me know as soon as possible.

I would greatly appreciate it if you could approve my request. Please confirm once you have reviewed and approved my leave. If there are any issues, I am more than willing to discuss alternative dates or make necessary adjustments.

Thank you for your understanding and support. I look forward to hearing back from you.

Best regards,
Kunal Toy
"""

    # Format the email template with the provided details
    email = email_template.format(supervisor_name=supervisor_name, start_date=start_date, end_date=end_date)

    return email

def get_leave_dates(days):
    # Calculate the leave dates based on the current date
    current_date = datetime.now()
    start_date = current_date.strftime("%Y-%m-%d")
    end_date = (current_date + timedelta(days=days)).strftime("%Y-%m-%d")

    return start_date, end_date

if __name__ == "__main__":
    # Get the supervisor's name from the environment variable
    supervisor_name = os.getenv("SUPERVISOR_NAME", "John Doe")

    # Get the leave dates
    start_date, end_date = get_leave_dates(30)

    # Generate the email
    email = generate_email(supervisor_name, start_date, end_date)

    # Print the email
    print(email)