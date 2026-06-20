import subprocess
import time
import os
import random

FILE_TRIGGER = "trigger.txt"
COUNTRIES = ["us", "sg", "au", "mx", "de", "fr", "jp", "ca", "nl", "ch", "se", "no", "fi", "dk", "es", "it", "uk", "br", "in", "za", "kr", "id", "tr", "pl", "ae", "sa", "ae", "my", "th", "vn", "cl", "pe", "mx", "ru", "id"]

def get_ip():
    try:
        return subprocess.check_output(
            ["curl", "-s", "https://api.ipify.org"]
        ).decode().strip()
    except:
        return "IP Error"

def reset_trigger():
    with open(FILE_TRIGGER, "w") as f:
        f.write("0")

def read_trigger():
    if not os.path.exists(FILE_TRIGGER):
        reset_trigger()
        return "0"
    
    with open(FILE_TRIGGER, "r") as f:
        return f.read().strip()

def connect_random():
    country = random.choice(COUNTRIES)
    print(f"\n🔄 Random negara: {country.upper()}")

    subprocess.run(["nordvpn", "disconnect"],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)

    subprocess.run(["nordvpn", "connect", country])

    print("⏳ Tunggu 5 detik...")
    time.sleep(5)

    print("📍 IP Baru:", get_ip())

def main():
    print("🛰️ NordVPN Trigger Bot Aktif")
    print("trigger.txt = 1 → Random Connect")
    print("trigger.txt = 0 → Idle\n")

    reset_trigger()

    while True:
        if read_trigger() == "1":
            print("🔔 Trigger 1 terdeteksi!")
            connect_random()
            reset_trigger()

        time.sleep(2)

if __name__ == "__main__":
    main()
