#!/bin/python3
import requests
import platform
import psutil
import time

# Server URL (change if Flask server is running on a different IP or port)
SERVER_URL = 'http://192.168.3.100:5000/report'
REPORT_INTERVAL = 5  # Interval in seconds to send data

def get_system_info(prev_net_io):
    disk_usage = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()

    # Calculate network speeds (bytes per second)
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
        'disk_total': round(disk_usage.total / (1024 ** 3)),  # Disk space in GB
        'disk_used': round(disk_usage.used / (1024 ** 3)),    # Used disk space in GB
        'network_sent': network_sent_speed,  # Sent bytes per second
        'network_received': network_received_speed  # Received bytes per second
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
    prev_net_io = None  # Initialize for tracking network activity
    while True:
        system_info, prev_net_io = get_system_info(prev_net_io)
        send_report(system_info)
        time.sleep(REPORT_INTERVAL)
