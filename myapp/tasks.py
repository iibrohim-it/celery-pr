from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_activation_email(email, url):

    send_mail(
        'Activate your account!',
        f'Please activate your account: {url}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )