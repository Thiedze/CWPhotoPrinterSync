# CWPhotoPrinterSync

Ein automatisches System zur Synchronisation und zum Drucken von Fotos aus NextCloud mit integriertem Web-Interface für die Verwaltung.

## 🔍 Überblick

CWPhotoPrinterSync ist ein Python-basiertes System, das automatisch Fotos aus einem NextCloud-Server herunterlädt und sie über CUPS an einen Drucker weiterleitet. Das System bietet ein benutzerfreundliches Web-Interface zur Konfiguration und Überwachung aller Funktionen.

### Hauptkomponenten

- **Server.py**: Flask-basierter Webserver mit REST-API
- **Worker.py**: Hintergrundprozess für die Foto-Synchronisation
- **startup.sh**: Startskript mit konfigurierbaren Parametern
- **Services/**: Modulare Services für NextCloud, WiFi, CUPS etc.
- **templates/**: HTML-Templates für das Web-Interface

## ✨ Features

### 🌐 Web-Interface
- **Dashboard** mit Live-Status-Anzeige
- **Server-Steuerung** mit Start/Stop-Funktionalität
- **WiFi-Konfiguration** mit Netzwerk-Scanner
- **NextCloud-Setup** mit Verbindungstest
- **Live-Log-Anzeige** mit automatischer Aktualisierung
- **Responsive Design** für Desktop und Mobile

### 🔄 Automatisierung
- **Configurable Scan-Intervall** (Standard: 60 Sekunden)
- **Autostart-Funktion** beim Systemstart
- **Automatische Foto-Erkennung** in NextCloud
- **Intelligente Verarbeitung** (Download → Druck → Archivierung)
- **Fehlerbehandlung** mit Retry-Mechanismen

### 🖨️ Druckfunktionen
- **CUPS-Integration** für alle unterstützten Drucker
- **Automatische Druckaufträge** für neue Fotos
- **Druckstatus-Überwachung**
- **Format-Optimierung** für verschiedene Papiergrößen

### 🌐 Netzwerk-Management
- **WiFi-Konfiguration** über Web-Interface
- **Netzwerk-Scanner** für verfügbare WLANs
- **Verbindungsstatusanzeige**
- **IP-Adress-Anzeige**

## 🔧 Systemanforderungen

### Hardware
- **Raspberry Pi** (3B+ oder neuer empfohlen) oder vergleichbarer Linux-Computer
- **WiFi-Adapter** (falls nicht integriert)
- **USB-Drucker** oder Netzwerkdrucker mit CUPS-Unterstützung
- **Mindestens 1GB RAM** und 8GB Speicherplatz

### Software
- **Linux-Betriebssystem** (Ubuntu, Debian, Raspberry Pi OS)
- **Python 3.8+**
- **CUPS** (Common Unix Printing System)
- **NetworkManager** für WiFi-Management
- **Git** für Installation

### Python-Abhängigkeiten
```bash
Flask>=2.0.0
requests>=2.25.0
schedule>=1.1.0
```

## 🚀 Installation

### 1. Repository klonen
```bash
git clone https://github.com/Thiedze/CWPhotoPrinterSync.git
cd CWPhotoPrinterSync
```

### 2. Python Virtual Environment erstellen
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 4. CUPS installieren und konfigurieren
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install cups cups-client

# CUPS-Service starten
sudo systemctl enable cups
sudo systemctl start cups

# Benutzer zur lpadmin-Gruppe hinzufügen
sudo usermod -a -G lpadmin $USER
```

### 5. Drucker einrichten
```bash
# Verfügbare Drucker anzeigen
lpstat -p

# Drucker über CUPS Web-Interface konfigurieren
# http://localhost:631
```

### 6. Berechtigung für startup.sh setzen
```bash
chmod +x startup.sh
```

## ⚙️ Konfiguration

### Startup-Konfiguration (startup.sh)

Das Startskript enthält die Basiskonfiguration:

```bash
#!/bin/bash
# Scan-Intervall in Sekunden
INTERVAL=60
# Autostart-Option (true/false)
AUTOSTART=false
cd /home/photobox/CWPhotoPrinterSync
source venv/bin/activate
python3 Server.py http://nx.lnienhaus.de wedding 1ganzlangespasswort! $INTERVAL
```

**Parameter:**
- `INTERVAL`: Scan-Intervall in Sekunden (anpassbar über Web-Interface)
- `AUTOSTART`: Automatischer Worker-Start beim Server-Start
- **URL, Username, Password**: NextCloud-Zugangsdaten

### Verzeichnisstruktur vorbereiten

```bash
# In-Progress-Ordner erstellen
mkdir -p in_progress

# Log-Datei wird automatisch erstellt
```

## 🎮 Verwendung

### Manueller Start
```bash
./startup.sh
```

### Service-Installation (optional)
```bash
[Unit]
Description=CWPhotoPrinterSync
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c "/home/photobox/CWPhotoPrinterSync/startup.sh"
WorkingDirectory=/home/photobox/CWPhotoPrinterSync
StandardOutput=append:/home/photobox/CWPhotoPrinterSync/startup.log
StandardError=append:/home/photobox/CWPhotoPrinterSync/startup.log
Restart=always
User=photobox

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren
sudo systemctl enable photoprinter.service
sudo systemctl start photoprinter.service
```

## 🌐 Web-Interface

Das Web-Interface ist unter `http://[IP-Adresse]:5000` erreichbar.

### Dashboard-Übersicht
- **Server-Status**: Läuft/Gestoppt mit farblicher Kennzeichnung
- **WiFi-Status**: Aktuelles Netzwerk und IP-Adresse
- **Datei-Status**: Anzahl Dateien im in_progress-Ordner
- **NextCloud-Status**: Verbindungsstatus zur Cloud

### Server-Steuerung
- **Scan-Intervall**: 1-3600 Sekunden konfigurierbar
- **Autostart-Option**: Checkbox für automatischen Start
- **Start/Stop-Buttons**: Intelligente Aktivierung je nach Status
- **Cloud bereinigen**: Reset der NextCloud-Verarbeitung
- **In-Progress löschen**: Lokale Dateien entfernen

### WiFi-Konfiguration
- **Netzwerk-Scanner**: Automatische Erkennung verfügbarer WLANs
- **Signalstärke-Anzeige**: Visuelle Darstellung der WLAN-Qualität
- **Passwort-Eingabe**: Sichere Konfiguration neuer Netzwerke
- **Status-Feedback**: Sofortige Rückmeldung bei Konfigurationsänderungen

### NextCloud-Konfiguration
- **URL-Validierung**: Automatische Überprüfung der Server-Erreichbarkeit
- **Credential-Management**: Sichere Speicherung der Zugangsdaten
- **Verbindungstest**: Sofortige Überprüfung der Konfiguration
- **Konfiguration laden/speichern**: Persistent storage in startup.sh

### Live-Log
- **Echtzeit-Updates**: Automatische Aktualisierung alle 5 Sekunden
- **Farbkodierung**: Strukturierte Darstellung der Log-Einträge
- **Auto-Scroll**: Automatisches Scrollen zu neuesten Einträgen
- **Vollbild-Ansicht**: Optimiert für Terminal-ähnliche Darstellung

## 🔌 API-Endpunkte

### Server-Management
```http
GET  /status                 # Server-Status abfragen
GET  /start?interval=60      # Worker starten
GET  /stop                   # Worker stoppen
GET  /log                    # Log-Inhalt abrufen
```

### Server-Konfiguration
```http
GET  /server/config          # Server-Einstellungen laden
POST /server/config          # Server-Einstellungen speichern
```

### WiFi-Management
```http
GET  /wifi/scan              # Verfügbare Netzwerke scannen
GET  /wifi/current           # Aktuelles Netzwerk abfragen
POST /wifi/configure         # WiFi konfigurieren
```

### NextCloud-Management
```http
GET  /nextcloud/config       # NextCloud-Konfiguration laden
POST /nextcloud/config       # NextCloud-Konfiguration speichern
GET  /next_cloud_clear       # NextCloud-Status zurücksetzen
```

### Datei-Management
```http
GET  /files/count            # Anzahl Dateien in in_progress
POST /files/clear            # In-Progress-Ordner leeren
```

### API-Request-Beispiele

**Server-Konfiguration speichern:**
```bash
curl -X POST http://localhost:5000/server/config \
  -H "Content-Type: application/json" \
  -d '{"interval": 30, "autostart": true}'
```

**WiFi konfigurieren:**
```bash
curl -X POST http://localhost:5000/wifi/configure \
  -H "Content-Type: application/json" \
  -d '{"ssid": "MeinWiFi", "password": "meinpasswort"}'
```

**NextCloud-Setup:**
```bash
curl -X POST http://localhost:5000/nextcloud/config \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://cloud.example.com",
    "username": "photouser",
    "password": "cloudpass",
    "interval": 60
  }'
```

## 📁 Verzeichnisstruktur

```
CWPhotoPrinterSync/
├── README.md                 # Diese Datei
├── startup.sh               # Hauptstartskript
├── Server.py                # Flask-Webserver
├── Worker.py                # Synchronisations-Worker
├── requirements.txt         # Python-Abhängigkeiten
├── log.txt                  # Automatisch generierte Log-Datei
├── in_progress/             # Temporäre Foto-Verarbeitung
├── Services/                # Service-Module
│   ├── __init__.py
│   ├── NextCloudService.py  # NextCloud-API-Client
│   ├── WiFiService.py       # WiFi-Management
│   ├── CupsService.py       # Drucker-Integration
│   ├── SchedulerService.py  # Task-Scheduling
│   ├── ServerService.py     # Server-Utilities
│   └── StdOutService.py     # Logging-Service
└── templates/               # Web-Templates
    └── index.html           # Haupt-Web-Interface
```

## 🔧 Services-Übersicht

### NextCloudService.py
- **Foto-Download** aus NextCloud-Ordnern
- **Metadaten-Management** für verarbeitete Dateien
- **API-Integration** mit NextCloud-REST-API
- **Fehlerbehandlung** bei Netzwerkproblemen

### WiFiService.py
- **WLAN-Scanner** für verfügbare Netzwerke
- **NetworkManager-Integration** für Ubuntu/Debian
- **Verbindungsmanagement** mit automatischen Fallbacks
- **Signalstärke-Monitoring**

### CupsService.py
- **Drucker-Discovery** und -Management
- **Print-Job-Scheduling** mit Warteschlange
- **Status-Monitoring** für Druckaufträge
- **Format-Optimierung** für verschiedene Medien

### SchedulerService.py
- **Task-Coordination** zwischen Services
- **Interval-Management** für periodische Aufgaben
- **Error-Recovery** mit exponential backoff
- **Resource-Management** zur Performance-Optimierung

## 📝 Changelog

### Version 2.0.0 (2025-01-25)
- ✨ Vollständig überarbeitetes Web-Interface
- ✨ Autostart-Funktionalität
- ✨ Intelligente Button-Deaktivierung
- ✨ Erweiterte WiFi-Konfiguration
- ✨ Server-Konfiguration über Web-Interface
- 🐛 Verbesserte Fehlerbehandlung
- 🐛 Performance-Optimierungen

### Version 1.0.0 (Initial Release)
- ✨ Basis-Synchronisation mit NextCloud
- ✨ CUPS-Drucker-Integration
- ✨ Einfaches Web-Interface
- ✨ WiFi-Management
- ✨ Grundlegende Konfiguration

*Letzte Aktualisierung: Januar 2025*
