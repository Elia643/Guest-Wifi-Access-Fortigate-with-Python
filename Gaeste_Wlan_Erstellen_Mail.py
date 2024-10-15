#!/usr/bin/env python3

import sys
import paramiko
import random
import string
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Datei zum Speichern der letzten User-ID
USER_ID_FILE = 'last_user_id.txt'

# SSH-Verbindung zur FortiGate herstellen mit SSH-Key
def ssh_connect(hostname, port, username, ssh_key_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Privaten SSH-Schlüssel laden
    private_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)
    
    # SSH-Verbindung herstellen
    client.connect(hostname, port=port, username=username, pkey=private_key)
    return client

# Zufallspasswort generieren
def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for i in range(length))

# Letzte User-ID aus Datei laden
def load_last_user_id():
    if os.path.exists(USER_ID_FILE):
        with open(USER_ID_FILE, 'r') as file:
            return int(file.read().strip())
    else:
        return 0  # Start-ID, wenn die Datei nicht existiert

# Letzte User-ID in Datei speichern
def save_last_user_id(user_id):
    with open(USER_ID_FILE, 'w') as file:
        file.write(str(user_id))

# FortiGate-Befehl ausführen
def add_guest_user(ssh_client, user_id, username, password, mobile_phone, sponsor, company, email, expiration_value, comment):
    # Befehl zur Erstellung des Gastbenutzers mit allen Parametern
    command = f"diagnose test guest add guest {user_id} {username} {password} {mobile_phone} {sponsor} {company} {email} {expiration_value} {comment}"
    
    # Debugging: Den ausgeführten Befehl anzeigen
    print(f"Ausgeführter Befehl: {command}")
    
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    # Debugging: Ausgaben und Fehler anzeigen
    print(f"Command Output: {output}")
    print(f"Command Error: {error}")
    
    if error:
        print(f"Fehler beim Erstellen des Benutzers {username}: {error}")
    else:
        print(f"Benutzer {username} erfolgreich erstellt.")
        print(output)  # Zeigt das Ausgabeergebnis, um sicherzustellen, dass alles korrekt ist
    
    return username, password, output, error

# E-Mail-Versandfunktion ohne SMTP-Authentifizierung
def send_email(subject, message, from_email, to_email, smtp_server, smtp_port):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Text-Inhalt für E-Mail-Clients, die kein HTML unterstützen
    text = f"""
    Sehr geehrter Gast,

    Ihr Zugang zum Gäste-WLAN "visitors_guest" wurde erfolgreich erstellt.

    Benutzername: {message['username']}
    Passwort: {message['password']}

    Sie können sich für {message['anz_tage']} mit diesen Zugangsdaten im WLAN "visitors_guest" anmelden.

    Mit freundlichen Grüssen,
    Ihr IT-Team
    """

    # HTML-Inhalt der E-Mail
    html = f"""
    <html>
    <body>
        <p>Sehr geehrter Gast,</p>
        <p>Ihr Zugang zum Gäste-WLAN <strong>visitors_guest</strong> wurde erfolgreich erstellt.</p>
        <p><strong>Benutzername:</strong> {message['username']}<br>
        <strong>Passwort:</strong> {message['password']}</p>
        <p>Sie können sich für <strong>{message['anz_tage']}</strong> mit diesen Zugangsdaten im WLAN <strong>visitors_guest</strong> anmelden.</p>
        <p>Mit freundlichen Grüssen,<br>
        Ihr IT-Team</p>
    </body>
    </html>
    """

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.sendmail(from_email, to_email, msg.as_string())
    print("Email successfully sent.")

# Hauptfunktion
def main():
    # Die Eingabeparameter vom Formular auslesen
    email = sys.argv[1]
    kunde = sys.argv[2]
    anz_tage = sys.argv[3]
    
    hostname = '#Anpassen#}'  # IP-Adresse der FortiGate
    port = 22
    username = '#Anpassen#'  # Benutzername für SSH-Login
    ssh_key_path = '#Anpassen#'  # Pfad zum privaten SSH-Schlüssel
    
    # Benutzerinformationen
    mobile_phone = '-'  # Telefonnummer aus dem Formular
    sponsor = '-'  # Sponsor des Gastbenutzers
    company = '-'  # Name der Firma
    email = email  # Email des Gastbenutzers aus dem Formular
    comment = kunde  # Kommentar im Format "Email; Kunde: [Kundenname]"
    guest_username = '-'

    # Umrechnung der Anzahl Tage in Sekunden
    try:
        anz_tage = int(anz_tage)
        expiration_value = str(anz_tage * 86400)  # Anzahl Tage in Sekunden
    except ValueError:
        expiration_value = "86400"  # Standardmässig auf 1 Tag setzen bei Fehler

    # E-Mail Informationen
    recipient_email = email  # Das wird aus dem Formular abgerufen
    subject = "Gäste WLAN Zugang"
    from_email = "#Anpassen#"
    smtp_server = "#Anpassen#"
    smtp_port = 25

    # Letzte User-ID laden
    last_user_id = load_last_user_id()
    next_user_id = last_user_id + 1
    
    # SSH-Verbindung herstellen
    ssh_client = ssh_connect(hostname, port, username, ssh_key_path)
    
    try:
        # Passwort generieren (dieses Passwort wird im Klartext gespeichert)
        guest_password = generate_password()
        
        # Benutzer erstellen
        username, password, output, error = add_guest_user(
            ssh_client, 
            next_user_id, 
            guest_username, 
            guest_password,  # WLAN-Passwort im Klartext
            mobile_phone, 
            sponsor, 
            company, 
            email, 
            expiration_value, 
            comment  # Übergabe des Kommentars mit E-Mail und Kunde
        )
        
        if not error:
            print(f"Benutzer {next_user_id} erfolgreich erstellt.")
            
            # Letzte User-ID speichern
            save_last_user_id(next_user_id)  # Speichert die aktuelle User-ID für den nächsten Lauf
            
            # E-Mail-Text vorbereiten
            message = {
                'username': next_user_id,
                'password': guest_password,
                'anz_tage': '1 Tag' if anz_tage == 1 else f'{anz_tage} Tage'
            }
            
            # E-Mail versenden
            send_email(subject, message, from_email, recipient_email, smtp_server, smtp_port)
            
        else:
            print(f"Fehler beim Erstellen des Benutzers {next_user_id}: {error}")
            
    finally:
        ssh_client.close()

if __name__ == "__main__":
    main()
