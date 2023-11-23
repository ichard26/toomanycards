# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import dataclasses
import smtplib
from email.message import EmailMessage

from fastapi import FastAPI, Response
from florapi.configuration import Options

app_opt = Options("TMC_EMAIL")

FOOTER = "(This email was sent automatically by a script. Please reach out if you encounter abuse.)"
SENDER_ADDRESS = app_opt("sender-address", type=str)
SENDER_PASSWORD = app_opt("sender-password", type=str)
REPLY_TO_ADDRESS = app_opt("reply-to", type=str)
LOG_ADDRESS = app_opt("log-address", type=str)
app_opt.report_errors()

app = FastAPI(
    title="TooManyCards Email Service API",
    contact={"name": "Richard Si"},
)

UnsuccessfulAddress = str


@dataclasses.dataclass(frozen=True)
class Email:
    sender_name: str
    subject: str
    body: str
    recipients: list[str]
    html: bool = False


def _smtp_send_email(
    smtp_session: smtplib.SMTP_SSL,
    sender_address: str,
    reply_to_address: str,
    email: Email,
    *,
    log: bool,
) -> list[UnsuccessfulAddress]:
    msg = EmailMessage()
    if email.html:
        msg.set_content(f"{email.body.strip()}<br><br>{FOOTER}", "html")
    else:
        msg.set_content(f"{email.body.strip()}\n\n{FOOTER}")
    if log:
        if LOG_ADDRESS.startswith("BCC:"):
            msg["Bcc"] = LOG_ADDRESS.removeprefix("BCC:")
        elif LOG_ADDRESS.startswith("CC:"):
            msg["Cc"] = LOG_ADDRESS.removeprefix("CC:")
        elif LOG_ADDRESS.startswith("TO:"):
            email = dataclasses.replace(email, recipients=[*email.recipients, LOG_ADDRESS.removeprefix("TO:")])
        else:
            raise AssertionError("need log address type prefix!")
    msg["Subject"] = email.subject
    msg["From"] = f"{email.sender_name} <{sender_address}>"
    msg["To"] = ", ".join(email.recipients)
    msg["reply-to"] = reply_to_address
    smtp_session.send_message(msg)
    print(f"[outgoing {log=}] Mail '{email.subject}' sent to {', '.join(email.recipients)}")


@app.post("/send")
def send_email_endpoint(emails: list[Email], response: Response, log: bool = True) -> object:
    errors = []
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_session:
        smtp_session.login(SENDER_ADDRESS, SENDER_PASSWORD)
        for mail in emails:
            errors.append(_smtp_send_email(smtp_session, SENDER_ADDRESS, REPLY_TO_ADDRESS, mail, log=log))

    errors = [e for e in errors if e is not None]
    if errors:
        response.status_code = 400
    return errors
