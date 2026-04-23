"""Smoke test: /api/graph serves curriculum DAG, ?lesson= focuses a group.

Loads /api/graph?lesson=4-1, waits for network stabilization, asserts the
"Focused: lesson 4-1" banner appears and no SEVERE console errors fire.
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PORT = 5183
REPO = Path(__file__).resolve().parent
URL = f"http://127.0.0.1:{PORT}"


def wait_server(timeout=10):
    for _ in range(timeout * 4):
        try:
            urllib.request.urlopen(f"{URL}/api/health", timeout=0.5).read()
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("console.py did not come up")


def main() -> int:
    srv = subprocess.Popen(
        [sys.executable, "console.py", "--no-open", "--port", str(PORT)],
        cwd=str(REPO),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_server()
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1600,1000")
        opts.set_capability("ms:loggingPrefs", {"browser": "ALL"})
        driver = webdriver.Edge(options=opts)
        try:
            driver.get(f"{URL}/api/graph?lesson=4-1")
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "net")))
            # Focus banner is created after physics stabilizes — vis-network
            # fires "stabilizationIterationsDone" once layout settles.
            banner = wait.until(lambda d: next(
                (el for el in d.find_elements(By.TAG_NAME, "div")
                 if "Focused: lesson 4-1" in (el.text or "")),
                None))
            assert banner, "focus banner not found"

            logs = driver.get_log("browser")
            errs = [
                l for l in logs
                if l.get("level") == "SEVERE"
                and "favicon.ico" not in l.get("message", "")
            ]
            if errs:
                for e in errs: print(f"SEVERE: {e}")
                return 1

            print(f"OK — DAG loaded with focus banner, 0 JS errors")
            return 0
        finally:
            driver.quit()
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=3)
        except subprocess.TimeoutExpired:
            srv.kill()


if __name__ == "__main__":
    sys.exit(main())
