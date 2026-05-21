"""
Module to generate an email for Kunal Toy regarding a leave request for summer.
This module creates a professional email template that can be customized as needed.
"""

import os
from email.message import EmailMessage
from datetime import datetime, timedelta

def generate_email(subject, recipient, start_date, end_date):
    # Create a new email message
    msg = EmailMessage()
    
    # Set the subject of the email
    msg['Subject'] = subject
    
    # Set the recipient of the email
    msg['To'] = recipient
    
    # Set the sender of the email
    msg['From'] = 'kunal.toy@example.com'
    
    # Create the body of the email
    body = f"""
Dear {recipient.split('@')[0].capitalize()},

I hope this email finds you well. As the summer season approaches, I am writing to request a leave of 30 days to ensure I can take a substantial break and recharge. I understand that this is a busy period for the company, but I have reviewed our team's schedule and have made arrangements to ensure that my responsibilities are covered during my absence.

The dates for my leave would be from {start_date} to {end_date}, totaling 30 days. I have made sure that all my current projects are up to date, and I have discussed with the team to ensure a smooth transition of tasks while I am away. If there are any concerns or if there is any additional information needed from me, please let me know as soon as possible.

I would greatly appreciate it if you could approve my request. Please confirm once you have reviewed and approved my leave. If there are any issues, I am more than willing to discuss alternative dates or make necessary adjustments.

Thank you for your understanding and support. I look forward to hearing back from you.

Best regards,
Kunal Toy
"""
    
    # Set the body of the email
    msg.set_content(body)
    
    return msg

if __name__ == "__main__":
    # Set the subject of the email
    subject = "Request for Summer Leave"
    
    # Set the recipient of the email
    recipient = "supervisor@example.com"
    
    # Set the start and end dates of the leave
    start_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=44)).strftime("%Y-%m-%d")
    
    # Generate the email
    email = generate_email(subject, recipient, start_date, end_date)
    
    # Print the email
    print(email)