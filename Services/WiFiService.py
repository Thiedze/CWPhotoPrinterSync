import os
import subprocess

from Services.StdOutService import StdOutService


class WiFiService:

    def get_available_networks(self):
        try:
            result = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                StdOutService.print(f"WiFi-Scan Fehler: {result.stderr}")
                return []

            networks = self.parse_scan_results(result.stdout)
            return networks

        except subprocess.TimeoutExpired:
            StdOutService.print("WiFi-Scan Timeout")
            return []
        except Exception as e:
            StdOutService.print(f"WiFi-Scan Fehler: {str(e)}")
            return []

    def configure_wifi(self, ssid, password):
        try:
            StdOutService.print(f"Konfiguriere WiFi für Netzwerk: {ssid}")

            if self.update_wpa_supplicant(ssid, password):
                if self.restart_wifi():
                    import time
                    time.sleep(10)

                    if self.test_connection():
                        StdOutService.print(f"WiFi erfolgreich konfiguriert: {ssid}")
                        return True
                    else:
                        StdOutService.print("WiFi konfiguriert, aber keine Internetverbindung")
                        return True
                else:
                    StdOutService.print("Fehler beim Neustart des WiFi-Interfaces")
                    return False
            else:
                StdOutService.print("Fehler beim Aktualisieren der WiFi-Konfiguration")
                return False

        except Exception as e:
            StdOutService.print(f"WiFi-Konfigurationsfehler: {str(e)}")
            return False

    @staticmethod
    def update_wpa_supplicant(ssid, password):
        try:
            result = subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password], capture_output=True,
                                    text=True)

            if result.returncode == 0:
                StdOutService.print("WiFi aktualisiert")
                return True
            else:
                StdOutService.print(f"Fehler beim Ausführen von nmcli: {result.stderr}")
                return False

        except Exception as e:
            StdOutService.print(f"Fehler beim Ausführen von nmcli: {str(e)}")
            return False

    @staticmethod
    def parse_scan_results(scan_output):
        networks = []
        lines = scan_output.split('\n')

        current_network = {}
        for line in lines:
            line = line.strip()

            if 'Cell ' in line and 'Address:' in line:
                if current_network and 'ssid' in current_network:
                    networks.append(current_network)
                current_network = {}

            elif 'ESSID:' in line:
                ssid = line.split('ESSID:')[1].strip().strip('"')
                if ssid and ssid != '<hidden>':
                    current_network['ssid'] = ssid

            elif 'Quality=' in line:
                try:
                    quality_part = line.split('Quality=')[1].split(' ')[0]
                    if '/' in quality_part:
                        quality_num, quality_max = quality_part.split('/')
                        quality_percent = int((int(quality_num) / int(quality_max)) * 100)
                        current_network['quality'] = quality_percent
                except:
                    current_network['quality'] = 0

            elif 'Encryption key:' in line:
                encrypted = 'on' in line.lower()
                current_network['encrypted'] = encrypted

        if current_network and 'ssid' in current_network:
            networks.append(current_network)

        networks.sort(key=lambda x: x.get('quality', 0), reverse=True)

        unique_networks = []
        seen_ssids = set()
        for network in networks:
            if network['ssid'] not in seen_ssids:
                unique_networks.append(network)
                seen_ssids.add(network['ssid'])

        return unique_networks

    @staticmethod
    def get_current_network():
        try:
            result = subprocess.run(['iwconfig', 'wlan0'], capture_output=True, text=True)

            if result.returncode == 0:
                output = result.stdout
                if 'ESSID:' in output:
                    ssid = output.split('ESSID:')[1].split(' ')[0].strip().strip('"')
                    if ssid and ssid != 'off/any':
                        return ssid
            return None

        except Exception as e:
            StdOutService.print(f"Fehler beim Abrufen des aktuellen Netzwerks: {str(e)}")
            return None

    @staticmethod
    def restart_wifi():
        try:
            subprocess.run(['sudo', 'ifdown', 'wlan0'], capture_output=True)

            import time
            time.sleep(2)

            result = subprocess.run(['sudo', 'ifup', 'wlan0'], capture_output=True, text=True)

            if result.returncode == 0:
                StdOutService.print("WiFi-Interface neu gestartet")
                return True
            else:
                subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'], capture_output=True)
                subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'], capture_output=True)
                StdOutService.print("WiFi-Services neu gestartet")
                return True

        except Exception as e:
            StdOutService.print(f"Fehler beim Neustart des WiFi: {str(e)}")
            return False

    @staticmethod
    def test_connection():
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '5', '8.8.8.8'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
