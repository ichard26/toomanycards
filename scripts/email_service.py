# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import dataclasses
import smtplib
from email.mime.text import MIMEText

from fastapi import FastAPI, Response
from florapi.configuration import Options

app_opt = Options("TMC_EMAIL")

SENDER_ADDRESS = app_opt("sender-address", type=str)
SENDER_PASSWORD = app_opt("sender-password", type=str)
LOG_ADDRESS = app_opt("log-address", type=str)

app_opt.report_errors()
app = FastAPI(
    title="TooManyCards Email Service API",
    contact={"name": "Richard Si"},
)

UnsuccessfulAddress = str


@dataclasses.dataclass(frozen=True)
class Email:
    subject: str
    body: str
    recipients: list[str]


def _smtp_send_email(smtp_session: smtplib.SMTP_SSL, sender: str, email: Email) -> list[UnsuccessfulAddress]:
    msg = MIMEText(email.body)
    msg["Subject"] = email.subject
    msg["From"] = sender
    msg["To"] = ", ".join(email.recipients)
    smtp_session.sendmail(sender, email.recipients, msg.as_string())
    print(f"Mail '{email.subject}' sent to {', '.join(email.recipients)}")


@app.post("/send")
def send_email_endpoint(emails: list[Email], response: Response) -> object:
    errors = []
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_session:
        smtp_session.login(SENDER_ADDRESS, SENDER_PASSWORD)
        for mail in emails:
            logging_mail = dataclasses.replace(
                mail,
                subject=f"[automated mail log] {mail.subject}", recipients=[LOG_ADDRESS]
            )
            errors.append(_smtp_send_email(smtp_session, SENDER_ADDRESS, mail))
            errors.append(_smtp_send_email(smtp_session, SENDER_ADDRESS, logging_mail))

    errors = [e for e in errors if e is not None]
    if errors:
        response.status_code = 400
    return errors
