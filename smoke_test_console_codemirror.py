"""Smoke test: Teacher Console CodeMirror 6 editor mounts without JS errors.

Starts console.py on a free port, loads the UI, selects a lesson with YAML,
waits for .cm-editor to render, asserts no SEVERE console errors.
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

PORT = 5179
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
            driver.get(URL)
            wait = WebDriverWait(driver, 10)

            wait.until(EC.presence_of_element_located((By.ID, "lesson-list")))
            wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, ".lesson-row"))

            # Pick the first lesson that has a YAML spec (we know L41_P2 does).
            rows = driver.find_elements(By.CSS_SELECTOR, ".lesson-row")
            target = next(
                (r for r in rows if r.get_attribute("data-id") == "L41_P2"),
                rows[0],
            )
            target.click()

            # CodeMirror mounts .cm-editor inside #cm-host
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cm-host .cm-editor")))
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cm-host .cm-content")))

            # Assert editor actually has YAML content
            content = driver.find_element(By.CSS_SELECTOR, "#cm-host .cm-content").text
            assert content.strip(), "CodeMirror editor has empty content"

            # Assert YAML syntax highlighting spans rendered (lang-yaml loaded)
            tokens = driver.find_elements(By.CSS_SELECTOR, "#cm-host .cm-content .tok-keyword, #cm-host .cm-content .tok-atom, #cm-host .cm-content span")
            assert tokens, "no tokenized spans — lang-yaml may not have loaded"

            logs = driver.get_log("browser")
            errs = [
                l for l in logs
                if l.get("level") == "SEVERE"
                and "favicon.ico" not in l.get("message", "")
            ]
            if errs:
                print("SEVERE browser logs:")
                for e in errs:
                    print(f"  {e}")
                return 1

            print(f"OK — editor mounted with {len(content.splitlines())} lines, {len(tokens)} tokens, 0 SEVERE errors")
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
