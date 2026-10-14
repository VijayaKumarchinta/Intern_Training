from flask_mail import Message


def send_mail(subject: str, recipients: list[str], body: str) -> None:
    from flask import current_app
    from flask_mail import _mail

    message = Message(subject=subject, recipients=recipients, body=body)
    _mail.send(message)
