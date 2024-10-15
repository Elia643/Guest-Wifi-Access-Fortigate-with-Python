#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cgi
import cgitb
import re
import subprocess
import shlex

cgitb.enable()
print("Content-Type: text/html; charset=utf-8\n")

form = cgi.FieldStorage()

email = form.getvalue('email')
kunde = form.getvalue('kunde')
anzahl_tage = form.getvalue('anzahl_tage')
anzahl_logins = int(form.getvalue('anzahl_logins'))
auswahl = form.getvalue('auswahl')

def render_page(title, heading, message, button_text="Zurück zur Startseite", button_link="/index.html"):
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f0f0f0;
            }}
            .container {{
                background-color: #ffffff;
                padding: 20px;
                border: 1px solid #ccc;
                border-radius: 5px;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            h1 {{
                color: #333;
            }}
            p {{
                font-size: 1.1em;
                margin: 20px 0;
            }}
            .button {{
                padding: 10px 20px;
                font-size: 1em;
                color: #ffffff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                cursor: pointer;
            }}
            .button:hover {{
                background-color: #0056b3;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{heading}</h1>
            <p>{message}</p>
            <a class="button" href="{button_link}">{button_text}</a>
        </div>
    </body>
    </html>
    """

if not re.match(r"^[a-zA-Z0-9._%+-]+@bachmann\.ch$", email):
    print(render_page(
        title="Fehler: Ungültige E-Mail-Adresse",
        heading="Fehler: Ungültige E-Mail-Adresse",
        message="Die E-Mail-Adresse muss mit @bachmann.ch enden.",
        button_text="Zurück zur Startseite",
        button_link="/index.html"
    ))
else:
    try:
        kunde_escaped = shlex.quote(kunde)
        anzahl_tage = int(anzahl_tage)
        
        if anzahl_tage > 5:
            print(render_page(
                title="Fehler: Ungültige Eingabe",
                heading="Fehler: Ungültige Eingabe",
                message="Die Anzahl der Tage darf nicht mehr als 5 betragen.",
                button_text="Zurück zur Startseite",
                button_link="/index.html"
            ))
        else:
            for i in range(anzahl_logins):
                if auswahl == "email":
                    result = subprocess.run(
                        ['python3', '/usr/lib/cgi-bin/Gaeste_Wlan_Erstellen_Mail.py', email, kunde_escaped, str(anzahl_tage)],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                elif auswahl == "druck":
                    result = subprocess.run(
                        ['python3', '/usr/lib/cgi-bin/Gaeste_Wlan_Erstellen_Druck.py', email, kunde_escaped, str(anzahl_tage)],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
            
            print(render_page(
                title="Erfolg: WLAN Zugang erstellt",
                heading="Gäste WLAN wurde erstellt.",
                message=f"Der WLAN-Zugang wurde erfolgreich erstellt!<br>E-Mail: {email}<br>Kunde: {kunde}<br>Anzahl Tage: {anzahl_tage}<br>Anzahl Logins: {anzahl_logins}",
                button_text="Weitere Logins erstellen",
                button_link="/index.html"
            ))

    except ValueError:
        print(render_page(
            title="Fehler: Ungültige Eingabe",
            heading="Fehler: Ungültige Eingabe",
            message="Die Anzahl der Tage muss eine Zahl sein.",
            button_text="Zurück zur Startseite",
            button_link="/index.html"
        ))

    except subprocess.CalledProcessError as e:
        print(render_page(
            title="Fehler aufgetreten",
            heading="Fehler aufgetreten",
            message=f"Beim Verarbeiten Ihrer Anfrage ist ein Fehler aufgetreten.<br><pre>{e.stderr.decode('utf-8')}</pre>",
            button_text="Zurück zur Startseite",
            button_link="/index.html"
        ))
