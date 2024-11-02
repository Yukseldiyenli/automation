import requests
import platform
import psutil
import time

SERVER_URL = 'http://127.0.0.1:5000/report'
REPORT_INTERVAL = 5  # Rapportage-interval in 5 seconde

def get_system_info(prev_net_io):
    disk_usage = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()

    # Bereken de verzend- en ontvangsnelheid (bytes per seconde)
    if prev_net_io:
        network_sent_speed = (net_io.bytes_sent - prev_net_io.bytes_sent) / REPORT_INTERVAL
        network_received_speed = (net_io.bytes_recv - prev_net_io.bytes_recv) / REPORT_INTERVAL
    else:
        network_sent_speed = 0
        network_received_speed = 0

    info = {
        'hostname': platform.node(),
        'os': platform.system(),
        'os_version': platform.version(),
        'cpu_count': psutil.cpu_count(logical=True),
        'cpu_percent': psutil.cpu_percent(interval=None),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_total': round(disk_usage.total / (1024 ** 3)),  # Totale schijfruimte in GB
        'disk_used': round(disk_usage.used / (1024 ** 3)),    # Gebruikte schijfruimte in GB
        'network_sent': network_sent_speed,  # Verzonden bytes per seconde
        'network_received': network_received_speed  # Ontvangen bytes per seconde
    }
    return info, net_io

def send_report(info):
    try:
        response = requests.post(SERVER_URL, json=info, verify=False)
        response.raise_for_status()
        print(f"Report sent successfully: {info}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending report: {e}")

if __name__ == "__main__":
    prev_net_io = None  # Voor het bijhouden van de vorige netwerkscore
    while True:
        system_info, prev_net_io = get_system_info(prev_net_io)
        send_report(system_info)
        time.sleep(REPORT_INTERVAL)
