import os
import sys

from flask import Flask, render_template, redirect, url_for, jsonify, request
import subprocess

from Services.NextCloudService import NextCloudService
from Services.WiFiService import WiFiService

app = Flask(__name__)
process = None
next_cloud_service = NextCloudService(sys.argv[1], sys.argv[2], sys.argv[3])
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
        process = subprocess.Popen(["python3", "Main.py", sys.argv[1], sys.argv[2], sys.argv[3], str(interval)])
    return redirect(url_for("index"))

@app.route("/stop")
def stop():
    global process
    if process and process.poll() is None:
        process.terminate()
    return redirect(url_for("index"))

@app.route("/next_cloud_clear")
def next_cloud_clear():
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
    """Scannt verfügbare WiFi-Netzwerke"""
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


if __name__ == "__main__":
    if os.path.exists("log.txt"):
        os.remove("log.txt")
    with open("log.txt", "w") as f:
        f.write("")
        
    app.run(host="0.0.0.0", port=5000)
