"""
Module to generate an email for Kunal Toy's summer leave request.

This module creates a professional email template for requesting a leave of 30 days during the summer.
It includes a clear subject line, a formal greeting, an introduction stating the purpose of the email,
details about the leave request, a closing statement, and a professional sign-off.
"""

import os
import datetime

def generate_email(supervisor_name, start_date, end_date):
    # Define the email template
    email_template = f"""
Subject: Request for Summer Leave

Dear {supervisor_name},

I hope this email finds you well. As the summer season approaches, I am writing to request a leave of 30 days to ensure I can take a substantial break and recharge. I understand that this is a busy period for the company, but I have reviewed our team's schedule and have made arrangements to ensure that my responsibilities are covered during my absence.

The dates for my leave would be from {start_date} to {end_date}, totaling 30 days. I have made sure that all my current projects are up to date, and I have discussed with the team to ensure a smooth transition of tasks while I am away. If there are any concerns or if there is any additional information needed from me, please let me know as soon as possible.

I would greatly appreciate it if you could approve my request. Please confirm once you have reviewed and approved my leave. If there are any issues, I am more than willing to discuss alternative dates or make necessary adjustments.

Thank you for your understanding and support. I look forward to hearing back from you.

Best regards,
Kunal Toy
"""

    return email_template

if __name__ == "__main__":
    # Define the supervisor's name
    supervisor_name = "John Doe"

    # Define the start and end dates of the leave
    start_date = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.date.today() + datetime.timedelta(days=60)).strftime("%Y-%m-%d")

    # Generate the email
    email = generate_email(supervisor_name, start_date, end_date)

    # Print the email
    print(email)