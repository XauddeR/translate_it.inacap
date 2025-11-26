from flask import url_for
from flask_mail import Message
from utils.extensions import mail
from markupsafe import Markup
from utils.tokens import generate_reset_token

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Restablecer contraseña</title>
</head>

<body style="margin:0; padding:0; background-color:#f5f6fa; font-family:Arial, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f6fa; padding:40px 0;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; background:white; border-radius:12px; overflow:hidden; box-shadow:0 3px 12px rgba(0,0,0,0.08);">
          
          <!-- Header -->
          <tr>
            <td style="background:#0b4ea1; padding:22px 28px;">
              <h1 style="color:white; margin:0; font-size:22px; font-weight:700;">
                Restablecer tu contraseña
              </h1>
            </td>
          </tr>

          <!-- Content -->
          <tr>
            <td style="padding:28px 35px; color:#333; font-size:15px; line-height:1.6;">
              <p>Hola <strong>{name}</strong>,</p>

              <p>
                Hemos recibido una solicitud para restablecer tu contraseña de 
                <strong>Translate It</strong>.  
                Haz clic en el siguiente botón para continuar:
              </p>

              <div style="text-align:center; margin:32px 0;">
                <a href="{reset_url}" 
                   style="background:#0b4ea1; color:white; padding:14px 26px; text-decoration:none; font-size:16px; border-radius:8px; font-weight:600; display:inline-block;">
                   Restablecer contraseña
                </a>
              </div>

              <p style="font-size:14px; color:#555;">
                Si no solicitaste este cambio, simplemente ignora este mensaje.
              </p>

              <p style="font-size:13px; color:#777; margin-top:35px;">
                Este enlace es válido por <strong>1 hora</strong>.
              </p>

              <p style="margin-top:35px;">Saludos,<br>Equipo de Translate It</p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f0f3f7; padding:18px 28px; text-align:center; font-size:12px; color:#777;">
              © 2025 Translate It. Todos los derechos reservados.
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def send_password_reset_email(user):
    token = generate_reset_token(user['email'])

    reset_url = url_for(
        'auth.reset_password',
        token = token,
        _external = True
    )

    subject = 'Recuperación de contraseña - Translate It'

    html_body = HTML_TEMPLATE.format(
        name = user['usuario'],
        reset_url = reset_url
    )

    msg = Message(
        subject = subject,
        recipients = [user['email']]
    )
    msg.html = Markup(html_body)

    msg.body = f'''
        Hola {user['usuario']},

        Para restablecer tu contraseña, visita este enlace:
        {reset_url}

        Si no solicitaste este cambio, puedes ignorar este mensaje.
    '''
    
    mail.send(msg)
