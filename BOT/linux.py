import os
import subprocess
import time
import requests
import sys
import random
import signal

# ================= KONFIGURASI =================
OPENVPN_PATH = "openvpn"   # Biasanya sudah ada di PATH Linux
FOLDER_VPN = "cinta"
FILE_PASS = os.path.join(FOLDER_VPN, "pass.txt")
FILE_TRIGGER = "trigger.txt"
# ===============================================

current_process = None

def is_root():
    return os.geteuid() == 0

def get_current_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return "Koneksi Bermasalah"

def kill_ovpn():
    global current_process
    try:
        subprocess.run(["pkill", "-f", "openvpn"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if current_process:
            current_process.terminate()
    except:
        pass

def reset_trigger():
    with open(FILE_TRIGGER, "w") as f:
        f.write("0")

def check_trigger():
    if not os.path.exists(FILE_TRIGGER):
        reset_trigger()
        return False
    
    with open(FILE_TRIGGER, "r") as f:
        return f.read().strip() == "1"

def connect_random_vpn():
    global current_process
    
    ovpn_files = [f for f in os.listdir(FOLDER_VPN) if f.endswith('.ovpn')]
    if not ovpn_files:
        print("❌ Folder .ovpn kosong!")
        return None

    selected = random.choice(ovpn_files)
    config_path = os.path.join(FOLDER_VPN, selected)
    
    print(f"\n🔄 Rotasi ke: {selected}")
    kill_ovpn()
    time.sleep(2)

    command = [
        OPENVPN_PATH,
        "--config", config_path,
        "--auth-user-pass", FILE_PASS,
        "--redirect-gateway", "def1",
        "--route-delay", "5",
        "--verb", "1"
    ]

    current_process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )

    print("⏳ Menunggu stabil (10 detik)...")
    time.sleep(10)
    print(f"📍 IP Sekarang: {get_current_ip()}")

    return current_process

def main():
    if not is_root():
        print("❌ Jalankan dengan sudo!")
        sys.exit(1)

    print("🛰️ Bot Trigger VPN Aktif (Linux)")
    print(f"Monitor file: {FILE_TRIGGER} (Ubah isi ke '1' untuk rotasi)")

    reset_trigger()
    connect_random_vpn()

    try:
        while True:
            if check_trigger():
                print("\n🔔 Trigger terdeteksi! Rotasi dimulai...")
                reset_trigger()
                connect_random_vpn()

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 Memutus koneksi...")
        kill_ovpn()
        sys.exit(0)

if __name__ == "__main__":
    main()
