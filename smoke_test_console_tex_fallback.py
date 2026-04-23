"""Smoke test: tex-editor fallback when no YAML spec exists.

Selects L35_P2 (tex-only), asserts the editor mounts with .cm-editor,
toolbar label reads "Student tex", then clicks Teacher and asserts the
editor reloads with "Teacher tex".
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

PORT = 5186
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
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        wait_server()
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1600,1000")
        opts.set_capability("ms:loggingPrefs", {"browser": "ALL"})
        driver = webdriver.Edge(options=opts)
        try:
            driver.get(URL)
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".lesson-row")))

            rows = driver.find_elements(By.CSS_SELECTOR, ".lesson-row")
            target = next(r for r in rows if r.get_attribute("data-id") == "L35_P2")
            target.click()

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cm-host .cm-editor")))
            wait.until(lambda d:
                "Student tex" in d.find_element(By.CSS_SELECTOR, "#editor-toolbar .toolbar-label").text)

            student_content = driver.find_element(By.CSS_SELECTOR, "#cm-host .cm-content").text
            assert "documentclass" in student_content.lower() or "begin" in student_content.lower(), \
                "student tex content doesn't look like LaTeX"

            # Switch to Teacher — editor should reload with teacher tex
            driver.find_element(By.ID, "toggle-teacher").click()
            wait.until(lambda d:
                "Teacher tex" in d.find_element(By.CSS_SELECTOR, "#editor-toolbar .toolbar-label").text)
            teacher_content = driver.find_element(By.CSS_SELECTOR, "#cm-host .cm-content").text
            assert teacher_content != student_content, "teacher tex content matches student — switch didn't fire"

            logs = driver.get_log("browser")
            errs = [
                l for l in logs if l.get("level") == "SEVERE"
                and "favicon.ico" not in l.get("message", "")
                # Expected 404 that drives the tex-fallback path
                and "/yaml" not in l.get("message", "")
            ]
            if errs:
                for e in errs: print(f"SEVERE: {e}")
                return 1

            print(f"OK - tex fallback works: student->teacher switch updated editor, 0 JS errors")
            return 0
        finally:
            driver.quit()
    finally:
        srv.terminate()
        try: srv.wait(timeout=3)
        except subprocess.TimeoutExpired: srv.kill()


if __name__ == "__main__":
    sys.exit(main())
