#!/usr/bin/env python3

import sys
import paramiko
import random
import string
import os
import cairo

# Datei zum Speichern der letzten User-ID
USER_ID_FILE = 'last_user_id.txt'

# SSH-Verbindung zur FortiGate herstellen mit SSH-Schlüssel
def ssh_connect(hostname, port, username, ssh_key_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Laden des privaten Schlüssels
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

# Funktion zum Erstellen eines Labels als Bild mit reinem Cairo und anschliessendes Drucken
def print_label(user_id, guest_password):
    # Bildgrösse festlegen (Breite x Höhe in Pixeln)
    img_width, img_height = 696, 200  # 696px Breite entspricht 90mm bei 8dpi
    
    # Cairo-Surface und -Context erstellen
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_width, img_height)
    context = cairo.Context(surface)

    # Hintergrund weiss machen
    context.set_source_rgb(1, 1, 1)
    context.paint()

    # Textinhalt und Schriftart festlegen
    context.set_source_rgb(0, 0, 0)  # Schwarzer Text
    context.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    context.set_font_size(30)  # Grössere Schriftgrösse

    # Text zeichnen
    text = "GAST WLAN ZUGANG"
    context.move_to(20, 50)  # Etwas mehr Abstand vom linken Rand
    context.show_text(text)
    
    text = f"Benutzername: {user_id}"
    context.move_to(20, 110)  # Etwas mehr Abstand vom linken Rand
    context.show_text(text)
    
    text = f"Passwort: {guest_password}"
    context.move_to(20, 170)  # Etwas mehr Abstand vom linken Rand
    context.show_text(text)

    # Speichern als temporäre Datei
    label_image_path = "/tmp/label.png"
    surface.write_to_png(label_image_path)

    # Sende den Druckauftrag an den Drucker
    result = os.system(f"lp -d #DruckerName# -o media=Custom.90x29mm -o fit-to-page {label_image_path}")
    if result != 0:
        print(f"Druckauftrag fehlgeschlagen mit Fehlercode: {result}")
    else:
        print("Druckauftrag erfolgreich gesendet.")

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
    comment = kunde # Kommentar im Format "Email; Kunde: [Kundenname]"
    guest_username = '-'
    
    # Umrechnung der Anzahl Tage in Sekunden
    try:
        anz_tage = int(anz_tage)
        expiration_value = str(anz_tage * 86400)  # Anzahl Tage in Sekunden
    except ValueError:
        expiration_value = "86400"  # Standardmässig auf 1 Tag setzen bei Fehler

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
            
            # Benutzername und Passwort auf dem Brother-Drucker ausdrucken
            print_label(next_user_id, guest_password)
            
        else:
            print(f"Fehler beim Erstellen des Benutzers {next_user_id}: {error}")
            
    finally:
        ssh_client.close()

if __name__ == "__main__":
    main()
