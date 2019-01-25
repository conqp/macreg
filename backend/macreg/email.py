"""Emailing of registration notifications."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from logging import getLogger
from smtplib import SMTP

from macreg.config import CONFIG, emails


__all__ = ['email']


LOGGER = getLogger(__file__)


def _emails(record):
    """Yields emails for the respective record."""

    text = CONFIG['email']['body'].fomat(record)

    for recipient in emails():
        message = MIMEMultipart(subtype='alternative')
        message['Subject'] = CONFIG['email']['subject'].format(
            record.mac_address)
        message['From'] = CONFIG['email']['sender']
        message['To'] = recipient
        message['Date'] = formatdate(localtime=True, usegmt=True)
        body = MIMEText(text, 'plain', 'utf-8')
        message.attach(body)
        yield message


def email(record):
    """Emails a MAC list record."""

    with SMTP(CONFIG['smtp']['server'], int(CONFIG['smtp']['port'])) as smtp:
        smtp.starttls()
        smtp.ehlo()
        smtp.login(CONFIG['smtp']['user'], CONFIG['smtp']['passwd'])

        for email_ in _emails(record):
            smtp.send_message(email_)

        smtp.quit()
