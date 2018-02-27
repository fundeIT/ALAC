import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import trust

def send(to, msg):
    s = smtplib.SMTP_SSL(trust.email_server, trust.email_port)
    s.login(trust.email_user, trust.email_password)
    s.sendmail(trust.email_user, to, msg.as_string())
    s.quit()   

def notify(year, ticket, email):
    if email == '':
        return
    text = """

Su ticket en trámite con la ALAC contiene nueva información.
Para consultarlo, abra en su navegador la siguiente dirección:

https://alac.funde.org/followup

En el cuadro "Seguimiento", introduzca los siguientes datos:

Año: %s
Número de ticket: %s

Y su dirección de correo.

Atentamente.

Equipo ALAC

----------

El Centro de Asesoría Legal (ALAC) ofrece apoyo
a peticionarios de información pública y
denunciantes de corrupción en el ejercicio de
sus derechos  Es una iniciativa de la Fundación
Nacional para el Desarrollo (FUNDE), capítulo
nacional de Transparencia Internacional.

Dirección: Calle Arturo Ambrogi No. 411
           Colonia Escalón, San Salvador,
           El Salvador, C.A.
Teléfono:  +503 2209 5324

"""
    text = text % (str(year), str(ticket))
    msg = MIMEText(text)
    msg['Subject'] = "ALAC: actualizacion de ticket No. %s" % str(ticket)
    msg['From'] = trust.email_user
    msg['To'] = email
    msg['Bcc'] = trust.email_user 
    send(email, msg)
