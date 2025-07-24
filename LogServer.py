import os
import sys
import re

from flask import Flask, render_template, redirect, url_for, jsonify, request
import subprocess

from Services.NextCloudService import NextCloudService
from Services.WiFiService import WiFiService

app = Flask(__name__)
process = None

# Funktionen zum Lesen und Schreiben der startup.sh
def load_config_from_startup():
    try:
        with open('startup.sh', 'r') as f:
            content = f.read()
        
        # Regex um die Parameter aus der startup.sh zu extrahieren
        # Sucht nach: python3 LogServer.py <URL> <USERNAME> <PASSWORD>
        pattern = r'python3\s+LogServer\.py\s+(\S+)\s+(\S+)\s+(\S+)'
        match = re.search(pattern, content)
        
        if match:
            return {
                "nextcloud": {
                    "url": match.group(1),
                    "username": match.group(2), 
                    "password": match.group(3)
                }
            }
        else:
            # Fallback für startup.sh ohne Parameter
            return {
                "nextcloud": {
                    "url": "",
                    "username": "",
                    "password": ""
                }
            }
    except FileNotFoundError:
        # Fallback auf Kommandozeilenargumente falls startup.sh nicht existiert
        if len(sys.argv) >= 4:
            return {
                "nextcloud": {
                    "url": sys.argv[1],
                    "username": sys.argv[2], 
                    "password": sys.argv[3]
                }
            }
        else:
            return {
                "nextcloud": {
                    "url": "",
                    "username": "",
                    "password": ""
                }
            }

def save_config_to_startup(config):
    try:
        with open('startup.sh', 'r') as f:
            content = f.read()
        
        nextcloud_config = config.get("nextcloud", {})
        url = nextcloud_config.get("url", "")
        username = nextcloud_config.get("username", "")
        password = nextcloud_config.get("password", "")
        
        # Neue Zeile mit Parametern
        new_line = f"python3 LogServer.py {url} {username} {password}"
        
        # Regex um die bestehende LogServer.py Zeile zu finden und zu ersetzen
        pattern = r'python3\s+LogServer\.py.*'
        
        if re.search(pattern, content):
            # Bestehende Zeile ersetzen
            new_content = re.sub(pattern, new_line, content)
        else:
            # Falls keine LogServer.py Zeile gefunden wird, am Ende hinzufügen
            lines = content.strip().split('\n')
            # Entferne leere Zeile am Ende falls vorhanden
            while lines and lines[-1].strip() == '':
                lines.pop()
            lines.append(new_line)
            new_content = '\n'.join(lines) + '\n'
        
        with open('startup.sh', 'w') as f:
            f.write(new_content)
            
        return True
    except Exception as e:
        print(f"Fehler beim Schreiben der startup.sh: {e}")
        return False

# Konfiguration aus startup.sh laden und NextCloud Service initialisieren
config = load_config_from_startup()
nextcloud_config = config.get("nextcloud", {})

if nextcloud_config.get("url") and nextcloud_config.get("username"):
    next_cloud_service = NextCloudService(
        nextcloud_config["url"], 
        nextcloud_config["username"], 
        nextcloud_config["password"]
    )
else:
    next_cloud_service = None

wifi_service = WiFiService()
@app.route("/")
def index():
    status = "läuft" if process and process.poll() is None else "gestoppt"
    return render_template("index.html", status=status)

@app.route("/start")
def start():
    global process
    interval = request.args.get("interval", type=int)
    print("interval:", interval)

    if not process or process.poll() is not None:
        config = load_config_from_startup()
        nextcloud_config = config.get("nextcloud", {})
        process = subprocess.Popen([
            "python3", "Main.py", 
            nextcloud_config.get("url", ""), 
            nextcloud_config.get("username", ""), 
            nextcloud_config.get("password", ""), 
            str(interval)
        ])
    return redirect(url_for("index"))

@app.route("/stop")
def stop():
    global process
    if process and process.poll() is None:
        process.terminate()
    return redirect(url_for("index"))

@app.route("/next_cloud_clear")
def next_cloud_clear():
    global next_cloud_service
    if next_cloud_service:
        photos = next_cloud_service.get_photos()
        next_cloud_service.reset_in_progress(photos)
    return redirect(url_for("index"))

@app.route("/log")
def get_log():
    if os.path.exists("log.txt"):
        with open("log.txt", "r") as f:
            return jsonify(log=f.read())
    return jsonify(log="(Keine Log-Datei gefunden)")

@app.route("/wifi/scan")
def wifi_scan():
    networks = wifi_service.get_available_networks()
    current_network = wifi_service.get_current_network()
    return jsonify(networks=networks, current=current_network)

@app.route("/wifi/configure", methods=["POST"])
def wifi_configure():
    data = request.get_json()
    
    if not data or 'ssid' not in data:
        return jsonify(success=False, message="SSID ist erforderlich"), 400
    
    ssid = data['ssid']
    password = data.get('password', '')
    
    success = wifi_service.configure_wifi(ssid, password)
    
    if success:
        return jsonify(success=True, message=f"WiFi erfolgreich konfiguriert: {ssid}")
    else:
        return jsonify(success=False, message="WiFi-Konfiguration fehlgeschlagen")

@app.route("/wifi/current")
def wifi_current():
    current_network = wifi_service.get_current_network()
    return jsonify(current=current_network)

@app.route("/files/count")
def files_count():
    try:
        in_progress_path = "in_progress"
        if os.path.exists(in_progress_path):
            files = os.listdir(in_progress_path)
            file_count = len([file for file in files if os.path.isfile(os.path.join(in_progress_path, file))])
            return jsonify(count=file_count)
        else:
            return jsonify(count=0)
    except Exception as e:
        return jsonify(count=0, error=str(e))

@app.route("/files/clear", methods=["POST"])
def files_clear():
    try:
        in_progress_path = "in_progress"
        deleted_count = 0
        
        if os.path.exists(in_progress_path):
            files = os.listdir(in_progress_path)
            for file in files:
                file_path = os.path.join(in_progress_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
        
        return jsonify(success=True, deleted_count=deleted_count, message=f"{deleted_count} Dateien wurden gelöscht")
    except Exception as e:
        return jsonify(success=False, message=f"Fehler beim Löschen: {str(e)}")

@app.route("/nextcloud/config")
def nextcloud_get_config():
    config = load_config_from_startup()
    nextcloud_config = config.get("nextcloud", {})
    return jsonify({
        "url": nextcloud_config.get("url", ""),
        "username": nextcloud_config.get("username", ""),
        "configured": bool(nextcloud_config.get("url") and nextcloud_config.get("username"))
    })

@app.route("/nextcloud/config", methods=["POST"])
def nextcloud_set_config():
    global next_cloud_service
    
    try:
        data = request.get_json()
        
        if not data or 'url' not in data or 'username' not in data:
            return jsonify(success=False, message="URL und Benutzername sind erforderlich"), 400
        
        # Konfiguration erstellen
        config = {
            "nextcloud": {
                "url": data["url"],
                "username": data["username"],
                "password": data.get("password", "")
            }
        }
        
        # Konfiguration in startup.sh speichern
        if not save_config_to_startup(config):
            return jsonify(success=False, message="Fehler beim Schreiben der startup.sh")
        
        # NextCloud Service neu initialisieren
        if config["nextcloud"]["url"] and config["nextcloud"]["username"]:
            next_cloud_service = NextCloudService(
                config["nextcloud"]["url"],
                config["nextcloud"]["username"], 
                config["nextcloud"]["password"]
            )
        else:
            next_cloud_service = None
        
        return jsonify(success=True, message="NextCloud-Konfiguration wurde in startup.sh gespeichert")
    except Exception as e:
        return jsonify(success=False, message=f"Fehler beim Speichern: {str(e)}")


if __name__ == "__main__":
    if os.path.exists("log.txt"):
        os.remove("log.txt")
    with open("log.txt", "w") as f:
        f.write("")
        
    app.run(host="0.0.0.0", port=5000)
