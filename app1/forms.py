import os
import threading
from django import forms
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.conf import settings
from app1.models import User as App1User


class App1PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        login_ts = getattr(user, 'last_login', '')
        return f"{user.pk}{user.password}{timestamp}{login_ts}"


app1_token_generator = App1PasswordResetTokenGenerator()


class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Correo Electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "ejemplo@correo.com"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email:
            app1_users = App1User.objects.filter(email__iexact=email, bloqueado=False)
            if not app1_users.exists():
                raise forms.ValidationError(
                    "No existe ninguna cuenta activa registrada con este correo electrónico."
                )
        return email

    def get_users(self, email):
        email = email.strip()
        return App1User.objects.filter(email__iexact=email, bloqueado=False)

    def save(
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=app1_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        email = self.cleaned_data["email"].strip()
        if not domain_override and request:
            from django.contrib.sites.shortcuts import get_current_site
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override or "samanito.com"

        for user in self.get_users(email):
            user_email = user.email.strip() if user.email else email
            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                **(extra_email_context or {}),
            }
            self.send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user_email,
                html_email_template_name=html_email_template_name,
            )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject = render_to_string(subject_template_name, context)
        subject = "".join(subject.splitlines())

        body = render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])

        if html_email_template_name:
            html_email = render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, "text/html")

            # Adjuntar el logo oficial como imagen inline CID (Content-ID)
            logo_path = os.path.join(settings.BASE_DIR, 'app1', 'static', 'img', 'Samanito_logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_image = MIMEImage(f.read())
                    logo_image.add_header('Content-ID', '<samanito_logo>')
                    logo_image.add_header('Content-Disposition', 'inline', filename='Samanito_logo.png')
                    email_message.attach(logo_image)

        # Envío en hilo secundario (asíncrono) para respuesta instantánea en la interfaz
        def _send_async():
            try:
                email_message.send(fail_silently=False)
            except Exception as e:
                print("Error enviando correo de recuperación en segundo plano:", e)

        threading.Thread(target=_send_async, daemon=True).start()


import re

def validar_complejidad_password(password):
    """
    Valida que la contraseña cumpla con:
    - Mínimo 6 caracteres
    - Al menos un número (0-9)
    - Al menos un símbolo o carácter especial
    Retorna (es_valido: bool, error_msg: str | None)
    """
    if not password or len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if not re.search(r'\d', password):
        return False, "La contraseña debe incluir al menos un número (0-9)."
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False, "La contraseña debe incluir al menos un símbolo o carácter especial (ej: !@#$%)."
    return True, None


class CustomSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Nueva contraseña"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Confirma la nueva contraseña"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2:
            if p1 != p2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
            valid, msg = validar_complejidad_password(p1)
            if not valid:
                raise forms.ValidationError(msg)
        return cleaned_data

    def save(self, commit=True):
        if self.user:
            hashed_pwd = make_password(self.cleaned_data['new_password1'])
            self.user.password = hashed_pwd
            if commit:
                self.user.save()
        return self.user


