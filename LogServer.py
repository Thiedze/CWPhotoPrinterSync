import os
import sys

from flask import Flask, render_template, redirect, url_for, jsonify, request
import subprocess

from Services.NextCloudService import NextCloudService

app = Flask(__name__)
process = None
next_cloud_service = NextCloudService(sys.argv[1], sys.argv[2], sys.argv[3])
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


if __name__ == "__main__":
    if os.path.exists("log.txt"):
        os.remove("log.txt")
    with open("log.txt", "w") as f:
        f.write("")
        
    app.run(host="0.0.0.0", port=5000)
