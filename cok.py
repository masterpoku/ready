import ssl

import concurrent.futures
import sys
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
ssl._create_default_https_context = ssl._create_unverified_context
_original_del = uc.Chrome.__del__
def _patched_del(self):
    try:
        _original_del(self)
    except OSError as e:
        if e.winerror == 6:  # The handle is invalid
            pass
        else:
            raise
uc.Chrome.__del__ = _patched_del
import requests
import gspread
import urllib3
# Menyembunyikan peringatan InsecureRequestWarning agar log CMD tetap bersih
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException, StaleElementReferenceException
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
import traceback


# ==========================================================
# UTIL (WINDOWS COMPATIBLE)
# ==========================================================

def get_chrome_version():
    """Mendapatkan versi utama Chrome/Chromium di sistem operasi."""
    commands = [
        r'powershell -command "(Get-Item \'C:\Program Files\Google\Chrome\Application\chrome.exe\').VersionInfo.ProductVersion"',
        r'powershell -command "(Get-Item \'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe\').VersionInfo.ProductVersion"',
        r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
        'google-chrome --version',
        'google-chrome-stable --version',
        'chromium-browser --version',
        'chromium --version'
    ]
    for cmd in commands:
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('utf-8')
            match = re.search(r'(\d+)\.', output)
            if match:
                return int(match.group(1))
        except:
            continue
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


def safe_click_element(driver, element, timeout=3):
    """Try multiple strategies to click an element safely."""
    try:
        # Prefer Selenium clickable wait if possible
        try:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, ".")))
        except Exception:
            pass

        try:
            element.click()
            return True
        except Exception:
            pass

        try:
            ActionChains(driver).move_to_element(element).pause(0.2).click().perform()
            return True
        except Exception:
            pass

        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", element)
            return True
        except Exception:
            return False
    except Exception:
        return False


def click_js(driver, by, selector, timeout=10):
    for _ in range(3):
        try:
            el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
            driver.execute_script("arguments[0].click();", el)
            return
        except StaleElementReferenceException:
            time.sleep(0.3)
            continue


def click_buttons_by_text(driver, texts):
    """Find buttons/links containing any of the texts (case-insensitive) and click them.

    texts: list of strings to search for (lowercased)
    Returns True if any button was clicked.
    """
    lowered = [t.lower() for t in texts]
    try:
        # include span because some Gmail dialogs render the continue button as a span inside a button
        elems = driver.find_elements(By.XPATH, "//button|//a|//div[@role='button']|//span")
        for el in elems:
            try:
                txt = (el.text or '').strip().lower()
                if not txt:
                    # try aria-label or innerText via JS
                    txt = (driver.execute_script('return arguments[0].innerText||arguments[0].ariaLabel||"";', el) or '').strip().lower()
                for t in lowered:
                    if t in txt:
                        if safe_click_element(driver, el):
                            print(f"[+] Clicked button with text: {txt}")
                            return True
            except Exception:
                continue
    except Exception:
        return False
    return False


def set_text_input(driver, element, text):
    """Robustly set text on an input or editable element.

    Tries clear/click/send_keys first, falls back to JS assignment and dispatches input/change events.
    """
    try:
        try:
            element.clear()
        except Exception:
            pass

        try:
            element.click()
        except Exception:
            pass

        try:
            element.send_keys(text)
            return True
        except ElementNotInteractableException:
            # fallback to JS
            try:
                driver.execute_script(
                    "arguments[0].innerText = arguments[1]; arguments[0].value = arguments[1];"
                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                    element, text
                )
                return True
            except Exception:
                return False
        except Exception:
            try:
                driver.execute_script(
                    "arguments[0].value = arguments[1];"
                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                    element, text
                )
                return True
            except Exception:
                return False
    except Exception:
        return False


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

        # Coba deteksi password input dengan timeout singkat
        try:
            password_input = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='password'] | //input[@name='password']"))
            )
        except TimeoutException:
            # Password input tidak muncul — cek error email
            try:
                err_text = driver.execute_script("""
                    var el = document.querySelector('[role=alert], .o6cuMc, div[jsname] span, .OyEIQ u');
                    return el ? el.innerText : '';
                """) or ''
                page_text = (driver.execute_script("return document.body.innerText || ''") or '')
                if "couldn't find" in page_text.lower() or "tidak ditemukan" in page_text.lower() or "enter a valid email" in page_text.lower():
                    print(f"[!] Email {email} tidak ditemukan di Google")
                else:
                    print(f"[!] Login {email} gagal — tidak bisa lanjut ke password. Pesan: {err_text.strip() if err_text else '(kosong)'}")
            except:
                print(f"[!] Login {email} gagal — tidak bisa lanjut ke password")
            return False
        type_slowly(password_input, password)
        
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(., 'Berikutnya')] | //span[contains(., 'Next')]")))
        safe_click(driver, next_btn)
        time.sleep(4)

        try:
            click_buttons_by_text(driver, ['continue', 'lanjut', 'lanjutkan', 'ok', 'next', 'setuju', 'terima', 'izinkan'])
            WebDriverWait(driver, 15).until(
                lambda d: 'myaccount.google.com' in d.current_url or 'mail.google.com' in d.current_url
            )
            print(f"[+] Login {email} berhasil! Session tersimpan.")
            return True
            
        except Exception as e:
            try:
                cur_url = driver.current_url
            except:
                cur_url = "?"
            print(f"[!] Login {email} gagal. Error ({type(e).__name__}): {e} | URL: {cur_url}")
            return False
    except Exception as e:
        try:
            cur_url = driver.current_url
        except:
            cur_url = "?"
        print(f"[!] Error login Gmail ({type(e).__name__}): {e} | URL: {cur_url}")
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


def _click_continue_button(driver):
    texts = ['Continue', 'Lanjut', 'Lanjutkan', 'OK', 'Next']
    xpath = " | ".join(
        f"//button[descendant::*[contains(normalize-space(), '{t}')]]"
        for t in texts
    )
    buttons = driver.find_elements(By.XPATH, xpath)
    for btn in buttons:
        try:
            driver.execute_script("arguments[0].click();", btn)
            return True
        except:
            pass
    return False


def _handle_oauth_flow(driver, main_window, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        # Deteksi popup
        if len(driver.window_handles) > 1:
            for h in driver.window_handles:
                if h != main_window:
                    try:
                        driver.switch_to.window(h)
                        if _click_continue_button(driver):
                            time.sleep(0.5)
                    except:
                        pass
                    break
            continue

        # Switch balik ke main window
        try:
            driver.switch_to.window(main_window)
        except:
            pass

        try:
            url = driver.current_url.lower()
        except:
            url = ''

        if '/dashboard' in url:
            return True

        if 'signin/oauth' in url or 'accounts.google' in url:
            _click_continue_button(driver)

        time.sleep(0.5)

    return False


def login_with_google(driver):
    wait = WebDriverWait(driver, 20)
    print(f"{datetime.now().strftime('%H:%M:%S')} Mencari tombol Sign in with Google...")
    if not click_google_button(driver):
        print("[!] Gagal klik tombol Google")
        return

    main_window = driver.current_window_handle
    old_count = len(driver.window_handles)

    print(f"{datetime.now().strftime('%H:%M:%S')} Menunggu popup Google...")
    try:
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > old_count)
        for handle in driver.window_handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                break
        print(f"[+] Beralih ke popup Google")
    except:
        print(f"[!] Popup tidak muncul, cek URL tab utama")
        pass

    print(f"{datetime.now().strftime('%H:%M:%S')} Memilih akun Google pertama...")
    try:
        akun_btns = wait.until(EC.presence_of_all_elements_located((
            By.XPATH, "//div[@role='button' and contains(@aria-label, '@')] | //div[@data-identifier]"
        )))
        if akun_btns:
            safe_click_element(driver, akun_btns[0])
            print(f"[+] Akun dipilih.")
            time.sleep(3)
    except Exception as e:
        print(f"[!] Gagal memilih akun: {e}")

    _handle_oauth_flow(driver, main_window, timeout=30)

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
                text.includes('i agree') || text.includes('got it') ||
                text.includes('setuju') || text.includes('terima') ||
                text.includes('izinkan') || text.includes('ya') ||
                text.includes('ok')) {
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

    # Kadang muncul tombol "Continue" / "Lanjut" yang menghalangi interaksi.
    # Coba klik tombol-tombol berisi teks terkait jika ada.
    try:
        click_buttons_by_text(driver, ['continue', 'lanjut', 'lanjutkan', 'ok', 'setuju', 'terima', 'izinkan'])
    except Exception:
        pass

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

def update_result(ws, row, result_url, success=True):
    try:
        ws.update_acell(f"B{row}", result_url)
        color = {"red": 0, "green": 1, "blue": 0} if success else {"red": 1, "green": 0, "blue": 0}
        ws.format(f"B{row}", {"backgroundColor": color})
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
# MAIN EXECUTION CORE
# ==========================================================

def _init_driver_worker(options):
    """Worker khusus untuk menginisialisasi driver di dalam thread terpisah"""
    driver = uc.Chrome(
        options=options,
        version_main=get_chrome_version(),
        use_subprocess=True
    )
    # Set timeout halaman setelah browser sukses terbuka
    driver.set_page_load_timeout(20)
    return driver


# ==========================================================
# POTONGAN KODE UTAMA KAMU (YANG SUDAH DI-FIX TIMEOUT-NYA)
# ==========================================================
def buat_driver_aman():
    port = random.randint(9200, 9400)
    options = uc.ChromeOptions()
    
    chrome_paths = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        '/opt/google/chrome/google-chrome',
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium'
    ]
    for cp in chrome_paths:
        if os.path.exists(cp):
            options.binary_location = cp
            break

    options.add_argument(f'--remote-debugging-port={port}')
    options.add_argument('--remote-allow-origins=*') 
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-signin-promo')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--guest')

    # Tambahkan argumen ini bang, untuk meringankan beban render Chrome biar gak gampang timeout
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--blink-settings=imagesEnabled=false') # Matikan gambar biar nge-render-nya super cepat

    driver = None
    TIMEOUT_BUKA_BROWSER = 60
    
    print(f"[Sistem] Menjalankan Chrome pada port {port}...")
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(_init_driver_worker, options)
        try:
            driver = future.result(timeout=TIMEOUT_BUKA_BROWSER)
            print("[Sistem] Browser berhasil diluncurkan.")
        except concurrent.futures.TimeoutError:
            print(f"[PENTING] Proses buka browser STUCK!")
            return None 

    return driver

# ==========================================================
# MAIN EXECUTION CORE
# ==========================================================

def main():
    # Auto-update dari GitHub
    try:
        print(f"{datetime.now().strftime('%H:%M:%S')} Auto-update: git pull...")
        result = subprocess.run(
            ["git", "pull"],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            if "Already up to date" in result.stdout:
                print("[+] Script sudah versi terbaru")
            else:
                print("[+] Script diupdate, pull ulang:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"    {line.strip()}")
        else:
            print(f"[!] Gagal git pull: {result.stderr.strip()}")
    except Exception as e:
        print(f"[!] Auto-update skip: {e}")

    print(f"{datetime.now().strftime('%H:%M:%S')} Memulai proses official.link di Windows...")
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

        if not login_gmail_to_profile(driver, email, password):
            print("[!] Login Gmail gagal. Update sheet...")
            update_result(ws, row, "email invalid", success=False)
            driver.quit()
            del driver
            return
        wait = WebDriverWait(driver, 20)
        
        driver.get("https://official.link/register")
        handle_ads_flow(driver)
        login_with_google(driver)

        print(f"{datetime.now().strftime('%H:%M:%S')} Menunggu redirect ke dashboard...")
        try:
            wait.until(EC.url_contains("/dashboard"))
        except:
            pass
        delete_all_links(driver)
        driver.get("https://official.link/dashboard")

        click_js(driver, By.CSS_SELECTOR, "body > div.app-container > section > div.py-4.p-lg-5 > main > div > div.row.mb-4 > div.col-12.col-lg-auto.d-flex.flex-wrap.gap-3.d-print-none > div:nth-child(1) > div > button")
        time.sleep(1)

        click_js(driver, By.CSS_SELECTOR, "div.show:nth-child(2) > a:nth-child(1)")
        time.sleep(2)

        candidates = build_username_variants(keyword)
        current_keyword = None

        for candidate in candidates:
            current_keyword = candidate
            print(f" Mencoba kandidat: {candidate}")

            url_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#biolink_url"))
            )
            url_input.clear()
            time.sleep(0.5)
            set_text_input(driver, url_input, candidate)
            time.sleep(2)

            create_btn_sel = "#create_biolink form button[type='submit'], #create_biolink .btn-primary"
            try:
                click_js(driver, By.CSS_SELECTOR, create_btn_sel, timeout=5)
            except Exception:
                click_js(driver, By.CSS_SELECTOR, "#create_biolink > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > form:nth-child(2) > div:nth-child(8) > button:nth-child(1)")

            try:
                notif_xpath = "//*[contains(@class, 'notification') and contains(., 'already exists')]"
                notif = WebDriverWait(driver, 4).until(
                    EC.presence_of_element_located((By.XPATH, notif_xpath))
                )
                if "already exists" in notif.text:
                    print(f" URL '{candidate}' sudah terpakai. Lanjut kandidat berikutnya...")
                    try:
                        close_btn = driver.find_element(By.CSS_SELECTOR, "button.close")
                        driver.execute_script("arguments[0].click();", close_btn)
                    except:
                        pass
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((By.XPATH, notif_xpath))
                        )
                    except:
                        pass
                    time.sleep(0.5)
                    continue

            except TimeoutException:
                print(" Notifikasi error tidak muncul, mengecek status sukses...")
                pass

            time.sleep(2)
            if "/link/" in driver.current_url:
                print(f" BERHASIL! Menggunakan URL: {candidate}")
                break

        # ---- HEADING BLOCK ----
        click_js(driver, By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)")
        click_js(driver, By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(2) > button:nth-child(1)")

        heading_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#heading_text")))
        set_text_input(driver, heading_input, keyword)

        create_block_btn_sel = "#create_biolink_heading > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(9) > button:nth-child(1)"
        click_js(driver, By.CSS_SELECTOR, create_block_btn_sel)
        wait_modal_close(driver, "#create_biolink_heading")

        # ---- TITLE BLOCK ----
        click_js(driver, By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)")
        click_js(driver, By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(2) > button:nth-child(1)")

        heading_title_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#heading_text")))
        set_text_input(driver, heading_title_input, title)

        create_heading_title_btn_sel = "#create_biolink_heading > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(9) > button:nth-child(1)"
        click_js(driver, By.CSS_SELECTOR, create_heading_title_btn_sel)
        wait_modal_close(driver, "#create_biolink_heading")

        # ---- PARAGRAPH BLOCK ----
        click_js(driver, By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)")
        click_js(driver, By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(3) > button:nth-child(1)")

        paragraph_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#create_biolink_paragraph > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(6) > div:nth-child(4) > div:nth-child(1)")))
        set_text_input(driver, paragraph_input, desc)

        create_paragraph_btn_sel = "#create_biolink_paragraph > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(8) > button:nth-child(1)"
        click_js(driver, By.CSS_SELECTOR, create_paragraph_btn_sel)
        wait_modal_close(driver, "#create_biolink_paragraph")

        # ---- LINK BLOCK (5x) ----
        link_suffixes = ["", " Login", " Daftar", " Alternatif", " Whatsapp"]
        for i, suffix in enumerate(link_suffixes):
            link_text = keyword + suffix
            print(f"{datetime.now().strftime('%H:%M:%S')} Menambahkan link ke-{i+1} dengan text: {link_text}")

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengklik tombol Add Block (link)...")
            click_js(driver, By.CSS_SELECTOR, ".flex-sm-row > div:nth-child(2) > button:nth-child(1)")
            time.sleep(1)

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengklik add link element...")
            click_js(driver, By.CSS_SELECTOR, "div.mb-4:nth-child(4) > div:nth-child(2) > div:nth-child(1) > button:nth-child(1)")
            time.sleep(1)

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengisi input link url...")
            link_url_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#link_location_url")))
            set_text_input(driver, link_url_input, url)
            print(f"[+] Link url diisi: {url}")

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengisi input link name...")
            link_name_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#link_name")))
            set_text_input(driver, link_name_input, link_text)
            print(f"[+] Link name diisi: {link_text}")

            print( f"{datetime.now().strftime('%H:%M:%S')} Mengklik tombol Create Biolink Link...")
            create_link_sel = "#create_biolink_link > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > form:nth-child(1) > div:nth-child(9) > button:nth-child(1)"
            click_js(driver, By.CSS_SELECTOR, create_link_sel)
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
        print(f"[-] Terjadi Fatal Error: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        if driver:
            try: 
                driver.quit()
                del driver # Hapus juga di blok exception
            except: 
                pass

if __name__ == "__main__":
    main()
