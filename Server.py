import os
import sys
import re

from flask import Flask, render_template, redirect, url_for, jsonify, request
import subprocess

from Services.NextCloudService import NextCloudService
from Services.WiFiService import WiFiService

app = Flask(__name__)
process = None

def load_configuration():
    try:
        with open('startup.sh', 'r') as f:
            content = f.read()
        
        # Pattern für python3 Server.py Aufruf
        pattern = r'python3\s+Server\.py\s+(\S+)\s+(\S+)\s+(\S+)'
        match = re.search(pattern, content)
        
        # Pattern für INTERVAL Variable
        interval_pattern = r'INTERVAL=(\d+)'
        interval_match = re.search(interval_pattern, content)
        
        # Pattern für AUTOSTART Variable
        autostart_pattern = r'AUTOSTART=(true|false)'
        autostart_match = re.search(autostart_pattern, content)
        
        if match:
            config = {
                "nextcloud": {
                    "url": match.group(1),
                    "username": match.group(2), 
                    "password": match.group(3)
                }
            }
            
            # Intervall aus INTERVAL Variable lesen
            if interval_match:
                config["interval"] = int(interval_match.group(1))
            else:
                config["interval"] = 60  # Standard-Wert
            
            # Autostart aus AUTOSTART Variable lesen
            if autostart_match:
                config["autostart"] = autostart_match.group(1) == "true"
            else:
                config["autostart"] = False  # Standard-Wert
                
            return config
        else:
            return {
                "nextcloud": {
                    "url": "",
                    "username": "",
                    "password": ""
                },
                "interval": 60,
                "autostart": False
            }
    except FileNotFoundError:
        if len(sys.argv) >= 5:
            return {
                "nextcloud": {
                    "url": sys.argv[1],
                    "username": sys.argv[2], 
                    "password": sys.argv[3]
                },
                "interval": int(sys.argv[4]),
                "autostart": False
            }
        elif len(sys.argv) >= 4:
            return {
                "nextcloud": {
                    "url": sys.argv[1],
                    "username": sys.argv[2], 
                    "password": sys.argv[3]
                },
                "interval": 60,
                "autostart": False
            }
        else:
            return {
                "nextcloud": {
                    "url": "",
                    "username": "",
                    "password": ""
                },
                "interval": 60,
                "autostart": False
            }

def save_config_to_startup(config):
    try:
        with open('startup.sh', 'r') as f:
            content = f.read()
        
        nextcloud_config = config.get("nextcloud", {})
        url = nextcloud_config.get("url", "")
        username = nextcloud_config.get("username", "")
        password = nextcloud_config.get("password", "")
        interval = config.get("interval", 60)
        autostart = config.get("autostart", False)
        
        # Neue Zeile mit Intervall als viertem Parameter
        new_line = f"python3 Server.py {url} {username} {password} $INTERVAL"
        pattern = r'python3\s+Server\.py.*'
        
        # INTERVAL Variable pattern
        interval_pattern = r'INTERVAL=\d+'
        new_interval_line = f"INTERVAL={interval}"
        
        # AUTOSTART Variable pattern
        autostart_pattern = r'AUTOSTART=(true|false)'
        new_autostart_line = f"AUTOSTART={'true' if autostart else 'false'}"
        
        # Python-Aufruf ersetzen
        if re.search(pattern, content):
            new_content = re.sub(pattern, new_line, content)
        else:
            lines = content.strip().split('\n')
            while lines and lines[-1].strip() == '':
                lines.pop()
            lines.append(new_line)
            new_content = '\n'.join(lines) + '\n'
        
        # INTERVAL Variable ersetzen oder hinzufügen
        if re.search(interval_pattern, new_content):
            new_content = re.sub(interval_pattern, new_interval_line, new_content)
        else:
            # INTERVAL nach der ersten Zeile (shebang) hinzufügen
            lines = new_content.split('\n')
            if lines[0].startswith('#!/bin/bash'):
                lines.insert(1, f"# Scan-Intervall in Sekunden")
                lines.insert(2, new_interval_line)
            else:
                lines.insert(0, new_interval_line)
            new_content = '\n'.join(lines)
        
        # AUTOSTART Variable ersetzen oder hinzufügen
        if re.search(autostart_pattern, new_content):
            new_content = re.sub(autostart_pattern, new_autostart_line, new_content)
        else:
            # AUTOSTART nach INTERVAL hinzufügen
            lines = new_content.split('\n')
            interval_line_index = -1
            for i, line in enumerate(lines):
                if line.startswith('INTERVAL='):
                    interval_line_index = i
                    break
            
            if interval_line_index >= 0:
                lines.insert(interval_line_index + 1, "# Autostart-Option (true/false)")
                lines.insert(interval_line_index + 2, new_autostart_line)
            else:
                # Falls INTERVAL nicht gefunden, nach shebang hinzufügen
                if lines[0].startswith('#!/bin/bash'):
                    lines.insert(1, "# Autostart-Option (true/false)")
                    lines.insert(2, new_autostart_line)
                else:
                    lines.insert(0, new_autostart_line)
            new_content = '\n'.join(lines)
        
        with open('startup.sh', 'w') as f:
            f.write(new_content)
            
        return True
    except Exception as e:
        print(f"Fehler beim Schreiben der startup.sh: {e}")
        return False

config = load_configuration()
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

@app.route("/status")
def get_status():
    is_running = process and process.poll() is None
    return jsonify({
        "running": is_running,
        "status": "läuft" if is_running else "gestoppt"
    })

@app.route("/start")
def start():
    global process
    interval = request.args.get("interval", type=int)
    autostart = request.args.get("autostart") == 'true'
    print("interval from request:", interval)
    print("autostart from request:", autostart)

    if not process or process.poll() is not None:
        config = load_configuration()
        nextcloud_config = config.get("nextcloud", {})
        
        # Verwende Intervall aus Request oder aus Konfiguration
        if interval is None:
            interval = config.get("interval", 60)
        
        # Speichere Konfiguration wenn über Web-Interface übergeben
        if interval is not None or autostart is not None:
            updated_config = {
                "nextcloud": nextcloud_config,
                "interval": interval,
                "autostart": autostart if autostart is not None else config.get("autostart", False)
            }
            save_config_to_startup(updated_config)
            print(f"Konfiguration gespeichert: Intervall {interval}, Autostart {autostart}")
        
        print("using interval:", interval)
        
        process = subprocess.Popen([
            "python3", "Worker.py",
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

@app.route("/server/config")
def server_get_config():
    config = load_configuration()
    return jsonify({
        "interval": config.get("interval", 60),
        "autostart": config.get("autostart", False)
    })

@app.route("/server/config", methods=["POST"])
def server_set_config():
    try:
        data = request.get_json()
        
        # Aktuelle Konfiguration laden
        config = load_configuration()
        
        # Nur Server-spezifische Werte aktualisieren
        config["interval"] = data.get("interval", 60)
        config["autostart"] = data.get("autostart", False)
        
        if not save_config_to_startup(config):
            return jsonify(success=False, message="Fehler beim Schreiben der startup.sh")
        
        return jsonify(success=True, message="Server-Konfiguration wurde gespeichert")
    except Exception as e:
        return jsonify(success=False, message=f"Fehler beim Speichern: {str(e)}")

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
    current_ip = wifi_service.get_current_ip()
    return jsonify(networks=networks, current=current_network, ip=current_ip)

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
    current_ip = wifi_service.get_current_ip()
    return jsonify(current=current_network, ip=current_ip)

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
    config = load_configuration()
    nextcloud_config = config.get("nextcloud", {})
    return jsonify({
        "url": nextcloud_config.get("url", ""),
        "username": nextcloud_config.get("username", ""),
        "configured": bool(nextcloud_config.get("url") and nextcloud_config.get("username")),
        "interval": config.get("interval", 60),
        "autostart": config.get("autostart", False)
    })

@app.route("/nextcloud/config", methods=["POST"])
def nextcloud_set_config():
    global next_cloud_service
    
    try:
        data = request.get_json()
        
        if not data or 'url' not in data or 'username' not in data:
            return jsonify(success=False, message="URL und Benutzername sind erforderlich"), 400
        
        config = {
            "nextcloud": {
                "url": data["url"],
                "username": data["username"],
                "password": data.get("password", "")
            },
            "interval": data.get("interval", 60),
            "autostart": data.get("autostart", False)
        }
        
        if not save_config_to_startup(config):
            return jsonify(success=False, message="Fehler beim Schreiben der startup.sh")
        
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

    # Autostart-Logik: Prüfe ob Autostart aktiviert ist
    config = load_configuration()
    if config.get("autostart", False):
        print("Autostart aktiviert - starte Worker automatisch...")
        nextcloud_config = config.get("nextcloud", {})
        interval = config.get("interval", 60)
        
        if nextcloud_config.get("url") and nextcloud_config.get("username"):
            process = subprocess.Popen([
                "python3", "Worker.py",
                nextcloud_config.get("url", ""), 
                nextcloud_config.get("username", ""), 
                nextcloud_config.get("password", ""), 
                str(interval)
            ])
            print(f"Worker automatisch gestartet mit Intervall {interval} Sekunden (PID: {process.pid})")
        else:
            print("Autostart aktiviert, aber NextCloud-Konfiguration unvollständig")

    app.run(host="0.0.0.0", port=5000)
