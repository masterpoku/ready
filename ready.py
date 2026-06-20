import ssl
import concurrent.futures
import sys
from seleniumbase import Driver
from selenium.common.exceptions import TimeoutException
ssl._create_default_https_context = ssl._create_unverified_context
import requests
import gspread
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException
from typing import List
import os
import csv
import subprocess
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import random


# ==========================================================
# UTIL
# ==========================================================

def get_chrome_version():
    try:
        out = subprocess.check_output(['google-chrome', '--version']).decode()
        match = re.search(r'(\d+)\.', out)
        if match:
            return int(match.group(1))
    except:
        pass
    return 148

def profile_name_from_email(email):
    username = email.split('@')[0]
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', username)
    return f"profile_{safe}"

def safe_click(driver, element):
    try:
        element.click()
    except (ElementNotInteractableException, ElementClickInterceptedException):
        driver.execute_script("arguments[0].click();", element)

def type_slowly(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(0.03)


# ==========================================================
# CLEAR COOKIES OFFICIAL.LINK ONLY
# ==========================================================

def clear_official_link_cookies(driver):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Membersihkan session official.link...")
        driver.get("https://official.link")
        time.sleep(1)
        cookies = driver.get_cookies()
        removed = 0
        for cookie in cookies:
            domain = cookie.get("domain", "")
            if "official.link" in domain:
                try:
                    driver.delete_cookie(cookie["name"])
                    removed += 1
                except:
                    pass
        driver.execute_script("""
            try {
                localStorage.clear();
                sessionStorage.clear();
            } catch(e){}
        """)
        print(f"[+] {removed} cookies official.link dihapus")
        driver.refresh()
        time.sleep(1)
        return True
    except Exception as e:
        print(f"[!] Error clear cookies: {e}")
        return False

def upload_avatar_block(cf_clearance, phpsessid, token, link_id):
    url = "https://official.link/biolink-block-ajax"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": f"https://official.link/link/{link_id}?tab=blocks",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://official.link",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0"
    }

    cookies = {
        "cf_clearance": cf_clearance,
        "PHPSESSID": phpsessid
    }

    data = {
        "token": token,
        "request_type": "create",
        "link_id": str(link_id),
        "block_type": "avatar",
        "size": "150",
        "border_radius": "straight"
    }

    files = {
        "image": (
            "1.jpg",
            open("1.jpg", "rb"),
            "image/jpeg"
        )
    }

    response = requests.post(
        url,
        headers=headers,
        cookies=cookies,
        data=data,
        files=files
    )

    print("STATUS :", response.status_code)
    print("RESPONSE :")
    print(response.text)

    return response

def intercept_biolink_ajax(driver):
    print("\n[*] Intercept request biolink-block-ajax...")
    try:
        logs = driver.execute_cdp_cmd("Network.getAllCookies", {})
        all_cookies = logs.get("cookies", [])

        cf_clearance = None
        phpsessid = None

        for c in all_cookies:
            cookie_name = c.get("name", "")
            cookie_value = c.get("value", "")

            if cookie_name == "cf_clearance":
                cf_clearance = cookie_value
            elif cookie_name == "PHPSESSID":
                phpsessid = cookie_value

        token = driver.execute_script("""
            return (
                document.querySelector('input[name="token"]')?.value ||
                window.token ||
                window.csrf_token ||
                ''
            );
        """)

        current_url = driver.current_url
        link_id = None

        try:
            if "/link/" in current_url:
                link_id = current_url.split("/link/")[1].split("?")[0].strip("/")
        except Exception as parse_error:
            print(f"[!] Gagal parse link_id: {parse_error}")

        print("\n==============================")
        print("[+] DATA INTERCEPT")
        print("==============================")
        print(f"URL            : {current_url}")
        print(f"cf_clearance   : {cf_clearance}")
        print(f"PHPSESSID      : {phpsessid}")
        print(f"token          : {token}")
        print(f"link_id        : {link_id}")
        print("==============================\n")

        return {
            "cf_clearance": cf_clearance,
            "PHPSESSID": phpsessid,
            "token": token,
            "link_id": link_id
        }
    except Exception as e:
        print(f"[!] Intercept error: {e}")
        return None

# ==========================================================
# LOGIN GMAIL TO PROFILE
# ==========================================================

def login_gmail_to_profile(driver, email, password):
    wait = WebDriverWait(driver, 10)
    try:
        driver.get("https://accounts.google.com/signin")
        time.sleep(2)
        dismiss_dialogs(driver)


        print(f"{datetime.now().strftime('%H:%M:%S')} Login ke Gmail {email}...")
        email_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='email'] | //input[@name='identifier']")))
        email_input.clear()
        type_slowly(email_input, email)
        
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(., 'Berikutnya')] | //span[contains(., 'Next')]")))
        safe_click(driver, next_btn)
        time.sleep(3)

        password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password'] | //input[@name='password']")))
        type_slowly(password_input, password)
        
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(., 'Berikutnya')] | //span[contains(., 'Next')]")))
        safe_click(driver, next_btn)
        time.sleep(4)

        try:
            # 1. Cek & Klik Tombol `#confirm` (Jika ada)
            try:
                confirm_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#confirm"))
                )
                safe_click(driver, confirm_btn)
                print("[+] Tombol #confirm berhasil diklik")
                time.sleep(2)
            except:
                pass  # Lewati jika tidak muncul

            # 2. Cek & Klik Tombol "I understand" / "Saya mengerti" (Jika ada)
            try:
                # Menggunakan XPATH yang fleksibel untuk teks bahasa Inggris maupun Indonesia
                understand_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'understand')] | "
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mengerti')] | "
                        "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'understand')] | "
                        "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mengerti')]"
                    ))
                )
                safe_click(driver, understand_btn)
                print("[+] Tombol 'I understand / Mengerti' berhasil diklik")
                time.sleep(2)
            except:
                pass  # Lewati jika tidak muncul

            # 3. Verifikasi Akhir Login Berhasil
            wait.until(EC.presence_of_element_located((
                By.XPATH, "//img[@alt='Google Account'] | //a[contains(@href, 'myaccount')]"
            )))
            print(f"[+] Login {email} berhasil! Session tersimpan.")
            return True
            
        except Exception as e:
            print(f"[!] Login {email} gagal. Error: {e}")
            return False
    except Exception as e:
        print(f"[!] Error login Gmail: {e}")
        return False

# ==========================================================
# REQUEST RESET PASSWORD
# ==========================================================

def request_reset(driver, email):
    url = "https://official.link/lost-password?redirect=dashboard"
    try:
        driver.get(url)
        time.sleep(2)
        handle_ads_flow(driver)

        print(f"{datetime.now().strftime('%H:%M:%S')} Request reset untuk: {email}")
        email_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#email"))
        )
        email_input.clear()
        email_input.send_keys(email)

        submit_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Send me a recovery link')]"))
        )
        safe_click(driver, submit_btn)
        print("[+] Recovery link terkirim, mengalihkan ke pengecekan inbox...")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"[!] Gagal request reset: {e}")
        return False

def dismiss_gmail_popups(driver):
    try:
        driver.execute_script("""
            document.querySelectorAll('div[role="dialog"], div[role="alertdialog"]').forEach(el => {
                el.querySelectorAll('button, div[role="button"], span[role="button"]').forEach(btn => {
                    let t = (btn.innerText || "").toLowerCase().trim();
                    if (t.includes('got it') || t.includes('skip') || t.includes('close') || 
                        t.includes('ok') || t.includes('next') || t.includes('later') || 
                        t.includes('cancel') || t.includes('not now') || t.includes('understood')) {
                        try { btn.click(); } catch(e){}
                    }
                });
                try { el.remove(); } catch(e){}
            });
            document.querySelectorAll('.Kj-JD, .dw, .nn').forEach(el => {
                try { el.remove(); } catch(e){}
            });
            document.body.style.overflow = 'auto';
        """)
        print("[+] Popup Gmail dibersihkan")
    except Exception as e:
        print(f"[!] Gagal hapus popup Gmail: {e}")

def get_reset_link(driver, max_retry=5, refresh_delay=5):  # default max_retry diubah ke 5 kali sesuai request
    gmail_url = "https://mail.google.com/mail/u/0/#search/official.link"
    driver.get(gmail_url)
    print(f"{datetime.now().strftime('%H:%M:%S')} Menunggu email reset masuk di inbox Gmail...")

    for attempt in range(max_retry):
        try:
            print(f"{datetime.now().strftime('%H:%M:%S')} Percobaan cek email ke-{attempt + 1}")
            driver.refresh()
            time.sleep(4)
            dismiss_gmail_popups(driver)
            time.sleep(1)

            mails = driver.find_elements(By.CSS_SELECTOR, "tr[jscontroller], tr.zA, .zA")
            if not mails:
                print("[!] Inbox kosong / email belum masuk")
                time.sleep(refresh_delay)
                continue

            safe_click(driver, mails[0])
            print("[+] Email berhasil dibuka, menunggu konten dirender...")
            time.sleep(5)

            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"{datetime.now().strftime('%H:%M:%S')} Total link ditemukan: {len(links)}")

            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    href = href.strip()
                    text = driver.execute_script("return arguments[0].textContent;", link)
                    text = text.strip().lower() if text else ""
                    if "reset password" in text or ("reset" in text and "password" in text):
                        print("\n[SUCCESS] RESET LINK DITEMUKAN!")
                        return href
                except Exception:
                    pass
            print("[!] Link reset belum ditemukan pada percobaan ini.")
        except Exception as e:
            print(f"[!] Error Gmail UI: {e}")

        time.sleep(refresh_delay)
        
    # JIKA MAX RETRY HABIS DAN BELUM KETEMU
    print("[FAILED] Reset link tidak ditemukan setelah 5x percobaan.")
    return "tidak ada inbox"

# ==========================================================
# SET PASSWORD BARU
# ==========================================================

def set_new_password(driver, password):
    try:
        wait = WebDriverWait(driver, 20)
        handle_ads_flow(driver)
        print(f"{datetime.now().strftime('%H:%M:%S')} Mengisi formulir password baru...")

        new_password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#new_password")))
        new_password_input.clear()
        new_password_input.send_keys(password)

        repeat_password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#repeat_password")))
        repeat_password_input.clear()
        repeat_password_input.send_keys(password)

        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Set password')]")))
        safe_click(driver, submit_btn)
        print("[SUCCESS] Form password baru disubmit.")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"[!] Gagal set password: {e}")
        return False
def reset_account(email, driver, password):
    print("=" * 60)
    print(f"{datetime.now().strftime('%H:%M:%S')} START RESET ACCOUNT FOR: {email}")
    print("=" * 60)
    try:
        clear_official_link_cookies(driver)
        if not request_reset(driver, email):
            return False

        # Cari Tautan di Gmail
        reset_link = get_reset_link(driver, max_retry=5) # Di-set limit 5 kali cek
        
        # OPER OPER LOGIKA TERBARU JIKA KATA KUNCI TERDETEKSI
        if reset_link == "tidak ada inbox":
            return "tidak ada inbox"
            
        if not reset_link:
            return False

        print(f"{datetime.now().strftime('%H:%M:%S')} Membuka tautan formulir reset password...")
        driver.get(reset_link)
        time.sleep(3)
        
        page_title = driver.title.lower()
        page_source = driver.page_source.lower()
        if "404" in page_title or "not found" in page_title or "404 not found" in page_source:
            print(f"[!] Tautan reset merespon 404 / Not Found. Mengabaikan alur dan menganggap password sudah diganti.")
            return True
            
        wait = WebDriverWait(driver, 30)
        wait.until(lambda d: "reset-password" in d.current_url or "official.link" in d.current_url)
        print(f"[+] Tiba di lokasi formulir: {driver.current_url}")
        result = set_new_password(driver, password)
        return result
    except Exception as e:
        print(f"[!] Error flow utama reset_account: {e}")
        return False

def move_to_result(keyword, email, password, valid_keyword):
    headers = ["keyword", "email", "password", "keyword valid"]
    file_exists = os.path.exists("result.csv")
    with open("result.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "keyword": keyword, "email": email, "password": password, 
            "keyword valid": f"https://official.link/{valid_keyword}"
        })

def remove_from_csv(email):
    rows = []
    with open("data.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row["email"].strip() != email:
                rows.append(row)
    with open("data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def dismiss_dialogs(driver):
    try:
        driver.execute_script("""
            document.querySelectorAll('div[role="dialog"], div[role="alertdialog"]').forEach(el => {
                el.querySelectorAll('button, span[role="button"]').forEach(b => {
                    let t = b.innerText.toLowerCase().trim();
                    if (t.includes('skip') || t.includes('no thanks') || t.includes('close') || t.includes('tutup')) {
                        try { b.click(); } catch(e) {}
                    }
                });
                el.remove();
            });
        """)
    except:
        pass

def wait_modal_close(driver, selector, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))
    except:
        pass
import re
from typing import List

def build_username_variants(username: str) -> List[str]:

    # spasi -> underscore
    username = re.sub(r"\s+", "_", username.strip())

    # huruf + angka
    username = re.sub(
        r'([A-Za-z]+)(\d+)([A-Za-z]{1,2})$',
        r'\1_\2\3',
        username
    )

    # huruf -> angka
    username = re.sub(
        r'([A-Za-z])(\d+)',
        r'\1_\2',
        username
    )

    # angka -> huruf
    username = re.sub(
        r'(\d+)([A-Za-z]+)',
        r'\1_\2',
        username
    )

    # rapikan underscore ganda
    username = re.sub(r'_+', '_', username).strip('_')

    return [username]

def click_google_button(driver, timeout=20):
    wait = WebDriverWait(driver, timeout)

    xpaths = [
        "//a[contains(., 'Sign in with Google')]",
        "//button[contains(., 'Sign in with Google')]",
        "//a[contains(@href, 'google')]",
        "//button[contains(., 'Google')]",
        "//a[contains(., 'Google')]"
    ]

    last_error = None

    for xpath in xpaths:
        try:
            # tunggu element muncul
            element = wait.until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            # scroll ke tengah
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                element
            )

            time.sleep(1)

            # cara 1 -> klik normal
            try:
                wait.until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                ).click()

                print(f"Clicked with normal click -> {xpath}")
                return True

            except:
                pass

            # cara 2 -> ActionChains
            try:
                ActionChains(driver)\
                    .move_to_element(element)\
                    .pause(0.5)\
                    .click()\
                    .perform()

                print(f"Clicked with ActionChains -> {xpath}")
                return True

            except:
                pass

            # cara 3 -> JS click (paling ampuh)
            try:
                driver.execute_script(
                    "arguments[0].click();",
                    element
                )

                print(f"Clicked with JS -> {xpath}")
                return True

            except Exception as e:
                last_error = e

        except Exception as e:
            last_error = e

    print("Gagal klik tombol Google")
    print(last_error)
    return False

def login_with_google(driver):
    wait = WebDriverWait(driver, 20)
    print(f"{datetime.now().strftime('%H:%M:%S')} Mencari tombol Sign in with Google...")
    click_google_button(driver)

    time.sleep(3)
    main_window = driver.current_window_handle
    all_windows = driver.window_handles
    for handle in all_windows:
        if handle != main_window:
            driver.switch_to.window(handle)
            break

    print(f"{datetime.now().strftime('%H:%M:%S')} Memilih akun Google pertama...")
    try:
        akun_btns = wait.until(EC.presence_of_all_elements_located((
            By.XPATH, "//div[@role='button' and contains(@aria-label, '@')] | //div[@data-identifier]"
        )))
        if akun_btns:
            akun_btns[0].click()
            print(f"[+] Akun dipilih.")
            time.sleep(3)
    except Exception as e:
        print(f"[!] Gagal memilih akun: {e}")

    try:
        lanjut_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Lanjut')] | //button[contains(., 'Continue')]")))
        lanjut_btn.click()
    except:
        pass

    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(1))
    driver.switch_to.window(main_window)

def handle_ads_flow(driver):
    print(f"{datetime.now().strftime('%H:%M:%S')} Memeriksa banner cookie...")
    time.sleep(3)
    accept_cookies_js = """
    function acceptAllCookies() {
        let allElements = document.querySelectorAll('button, a, span, div[role="button"]');
        for (let el of allElements) {
            let text = el.innerText.toLowerCase().trim();
            if (text.includes('accept all') || text.includes('accept') || 
                text.includes('allow all') || text.includes('allow') ||
                text.includes('agree') || text.includes('consent') ||
                text.includes('i agree') || text.includes('got it')) {
                try { el.click(); return true; } catch(e) {}
            }
        }
        return false;
    }
    return acceptAllCookies();
    """
    try:
        if driver.execute_script(accept_cookies_js):
            print("[+] Banner Cookie disetujui.")
            time.sleep(1)
    except Exception as e:
        print(f"[!] Gagal eksekusi cookie: {e}")

SPREADSHEET_ID = "11y5rg2XN2rHZDeY0ktA_ly_QfGC-jE2sdH3Ol--B9xw"
SHEET_NAME = "data"

def get_data():
    try:
        gc = gspread.service_account(filename="service-account.json")
        sh = gc.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet(SHEET_NAME)
        records = ws.get_all_records()
        for i, rec in enumerate(records, start=2):
            if not str(rec.get("Short", "")).strip():
                ws.update_acell(f"B{i}", "Process")
                ws.format(f"B{i}", {
                    "backgroundColor": {"red": 1, "green": 1, "blue": 0}
                })
                print(f"[+] Row {i} dikunci dengan status 'Process'.")
                return rec, i, ws
        print("[!] Semua baris sudah terisi.")
        return None, None, None
    except Exception as e:
        print(f"[!] Error get_data: {e}")
        return None, None, None

def update_result(ws, row, result_url):
    try:
        ws.update_acell(f"B{row}", result_url)
        ws.format(f"B{row}", {
            "backgroundColor": {"red": 0, "green": 1, "blue": 0}
        })
        print(f"[+] DONE UPDATE GS Baris {row}: {result_url}")
        return True
    except Exception as e:
        print(f"[!] Error update result: {e}")
        return False

def delete_all_links(driver):

    wait = WebDriverWait(driver, 10)

    print("[*] Memulai hapus semua link...")

    while True:

        try:

            # ==========================================
            # KLIK DROPDOWN ACTION
            # ==========================================

            dropdown_btn = wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    ".btn.btn-link.text-secondary.dropdown-toggle.dropdown-toggle-simple"
                ))
            )

            driver.execute_script(
                "arguments[0].click();",
                dropdown_btn
            )

            time.sleep(1)

            # ==========================================
            # CARI TOMBOL DELETE
            # ==========================================

            delete_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-target="#link_delete_modal"]'
            )

            visible_delete = None

            for btn in delete_buttons:

                if btn.is_displayed():

                    visible_delete = btn
                    break

            if not visible_delete:

                print("[+] Tidak ada tombol delete lagi")

                break

            # ==========================================
            # KLIK DELETE
            # ==========================================

            driver.execute_script(
                "arguments[0].click();",
                visible_delete
            )

            print("[+] Tombol delete diklik")

            time.sleep(1)

            # ==========================================
            # KLIK CONFIRM DELETE
            # ==========================================

            confirm_btn = wait.until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    "div.mt-4:nth-child(5) > button:nth-child(1)"
                ))
            )

            driver.execute_script(
                "arguments[0].click();",
                confirm_btn
            )

            print("[+] Confirm delete diklik")

            time.sleep(2)

        except Exception as e:

            print(f"[!] Selesai")

            break

    print("[SUCCESS] Semua link selesai dihapus")
# ==========================================================
# DRIVER - SeleniumBase UC Mode (bypass Cloudflare)
# ==========================================================

def _init_driver_worker():
    driver = Driver(uc=True, headless=False, browser_args=["--guest"])
    driver.set_page_load_timeout(20)
    return driver


def buat_driver_aman():
    TIMEOUT_BUKA_BROWSER = 60
    print("[Sistem] Menjalankan Chrome (SeleniumBase UC Mode)...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_init_driver_worker)
        try:
            driver = future.result(timeout=TIMEOUT_BUKA_BROWSER)
            print("[Sistem] Browser berhasil diluncurkan.")
        except concurrent.futures.TimeoutError:
            print("[PENTING] Proses buka browser STUCK!")
            return None

    return driver

# ==========================================================
# MAIN EXECUTION CORE
# ==========================================================

def main():
    print(f"{datetime.now().strftime('%H:%M:%S')} Memulai proses official.link...")
    data, row, ws = get_data()
    if not data:
        return

    keyword = data["Kw"]
    password = data["Password"]
    new_password = data["Password Link"]
    email = data["Email"]
    url = data["url"]
    title = data["title"]
    desc = data["DESC"]

    print(f"{datetime.now().strftime('%H:%M:%S')} Membuka browser...")
    driver = buat_driver_aman()
    if driver is None:
        print("[Sistem] Gagal inisialisasi driver. Close project.")
        sys.exit()
    try:
        driver.set_page_load_timeout(20)

        login_gmail_to_profile(driver, email, password)
        wait = WebDriverWait(driver, 20)
        
        driver.get("https://official.link/register")
        handle_ads_flow(driver)
        login_with_google(driver)

        print(f"{datetime.now().strftime('%H:%M:%S')} Menunggu redirect ke dashboard...")
        wait.until(EC.url_contains("/dashboard"))
        delete_all_links(driver)
        driver.get("https://official.link/dashboard")

        create_link_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > div.app-container > section > div.py-4.p-lg-5 > main > div > div.row.mb-4 > div.col-12.col-lg-auto.d-flex.flex-wrap.gap-3.d-print-none > div:nth-child(1) > div > button")))
        driver.execute_script("arguments[0].click();", create_link_btn)
        time.sleep(1)

        biolink_item = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.show:nth-child(2) > a:nth-child(1)")))
        driver.execute_script("arguments[0].click();", biolink_item)
        time.sleep(2)

        candidates = build_username_variants(keyword)
        current_keyword = None

        for candidate in candidates:
            current_keyword = candidate
            url_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#biolink_url")))
            url_input.clear()
            url_input.send_keys(current_keyword)

            create_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#create_biolink > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > form:nth-child(2) > div:nth-child(8) > button:nth-child(1)")))
            driver.execute_script("arguments[0].click();", create_btn)
            time.sleep(3)

            if '/link/' in driver.current_url:
                break
            try:
                if driver.find_element(By.CSS_SELECTOR, ".alert").is_displayed():
                    continue
            except NoSuchElementException:
                pass

        # ---- HEADING BLOCK ----
        add_block_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", add_block_btn)
        
        heading_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(2) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", heading_btn)

        heading_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#heading_text")))
        heading_input.send_keys(keyword)

        create_block_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#create_biolink_heading > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(9) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", create_block_btn)
        wait_modal_close(driver, "#create_biolink_heading")

        # ---- TITLE BLOCK ----
        add_block_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", add_block_btn)
        
        heading_title_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(2) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", heading_title_btn)

        heading_title_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#heading_text")))
        heading_title_input.send_keys(title)

        create_heading_title_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#create_biolink_heading > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(9) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", create_heading_title_btn)
        wait_modal_close(driver, "#create_biolink_heading")

        # ---- PARAGRAPH BLOCK ----
        add_block_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", add_block_btn)

        paragraph_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(3) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", paragraph_btn)

        paragraph_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#create_biolink_paragraph > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(6) > div:nth-child(4) > div:nth-child(1)")))
        paragraph_input.send_keys(desc)

        create_paragraph_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#create_biolink_paragraph > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(8) > button:nth-child(1)")))
        driver.execute_script("arguments[0].click();", create_paragraph_btn)
        wait_modal_close(driver, "#create_biolink_paragraph")

        # ---- LINK BLOCK (5x) ----
        link_suffixes = ["", " Login", " Daftar", " Alternatif", " Whatsapp"]
        for i, suffix in enumerate(link_suffixes):
            link_text = keyword + suffix
            print(f"{datetime.now().strftime('%H:%M:%S')} Menambahkan link ke-{i+1} dengan text: {link_text}")

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengklik tombol Add Block (link)...")
            add_block_btn = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)"
            )))
            driver.execute_script("arguments[0].click();", add_block_btn)
            time.sleep(1)

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengklik add link element...")
            link_btn = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(1) > button:nth-child(1)"
            )))
            driver.execute_script("arguments[0].click();", link_btn)
            time.sleep(1)

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengisi input link url...")
            link_url_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#link_location_url")))
            link_url_input.clear()
            link_url_input.send_keys(url)
            print(f"[+] Link url diisi: {url}")

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengisi input link name...")
            link_name_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#link_name")))
            link_name_input.clear()
            link_name_input.send_keys(link_text)
            print(f"[+] Link name diisi: {link_text}")

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengklik tombol Create Biolink Link...")
            create_link_btn = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "#create_biolink_link > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(9) > button:nth-child(1)"
            )))
            driver.execute_script("arguments[0].click();", create_link_btn)
            print(f"[+] Tombol Create Biolink Link ke-{i+1} diklik.")
            wait_modal_close(driver, "#create_biolink_link")

        # ==========================================================
        # KONDISI PROSES RESET DAN UPDATE GS
        # ==========================================================
        # status_reset = reset_account(email, driver, new_password)
        
        # if status_reset == "tidak ada inbox":
        #     print("[!] Status: Inbox kosong 5x. Mengirim teks 'tidak ada inbox' ke Google Sheets.")
        #     update_result(row, "tidak ada inbox")
            
        # elif status_reset == True:
        #     final_url = f"https://official.link/{current_keyword}"
        #     update_result(row, final_url)
            
        # else:
        #     print("[!] Reset account gagal karena error sistem lainnya.")
        final_url = f"https://official.link/{current_keyword}"
        update_result(ws, row, final_url)
        # ==========================================================

        # PENTING: Panggil quit lalu hapus objek dari memori
        driver.quit()
        del driver 

    except Exception as e:
        print(f"[-] Terjadi Fatal Error: {e}")
        if driver:
            try: 
                driver.quit()
                del driver # Hapus juga di blok exception
            except: 
                pass

if __name__ == "__main__":
    main()