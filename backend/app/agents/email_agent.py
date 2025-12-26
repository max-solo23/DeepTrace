import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body to the configured recipient."""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email_value = os.environ.get("SENDGRID_FROM", "test@gmail.com")
    to_email_value = os.environ.get("SENDGRID_TO", "test@gmail.com")
    default_subject = os.environ.get("SENDGRID_DEFAULT_SUBJECT", "Deep Research Report")

    subject_value = (subject or "").strip() or default_subject
    from_email = Email(from_email_value)
    to_email = To(to_email_value)
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject_value, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return {"status": "success"}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email sender",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-5-nano",
)
