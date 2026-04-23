"""Smoke test: Teacher Console diff modal renders +/- lines correctly.

Injects a synthetic unified-diff into JS state, clicks Diff, asserts
.diff-add / .diff-del / .diff-hunk classes render. Avoids the overhead
and side effects of a real regen.
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

PORT = 5181
REPO = Path(__file__).resolve().parent
URL = f"http://127.0.0.1:{PORT}"

SAMPLE_DIFF = (
    "--- L41_P2_student.tex (before)\n"
    "+++ L41_P2_student.tex (after)\n"
    "@@ -10,5 +10,5 @@\n"
    " context line\n"
    "-removed line\n"
    "+added line\n"
    " another context\n"
    "-another removed\n"
    "+another added\n"
)


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
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".lesson-row")))

            # Select L41_P2 so activeLessonId is populated (required by openDiff title)
            rows = driver.find_elements(By.CSS_SELECTOR, ".lesson-row")
            target = next(r for r in rows if r.get_attribute("data-id") == "L41_P2")
            target.click()
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#cm-host .cm-editor")))

            # Inject a synthetic diff into the JS module state, then click Diff.
            # console.js is an ES module — its bindings aren't window-globals, so
            # we drive the UI the same way the regen response would: set the flag
            # + enable the button via the button element, then invoke openDiff
            # via the click handler attached in the module.
            driver.execute_script(
                """
                // Find console.js module scope via a synthetic dispatch. Since we
                // can't reach module-scoped `lastDiff` directly, simulate a regen
                // response by patching fetch once and calling regen.
                window.__origFetch = window.fetch;
                window.fetch = async (url, opts) => {
                    if (url.includes('/regenerate')) {
                        return new Response(JSON.stringify({
                            ok: true, student_pdf: null, teacher_pdf: null,
                            diff: { student_tex: arguments[1]?._fake_diff || window.__sampleDiff, teacher_tex: '' }
                        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
                    }
                    return window.__origFetch(url, opts);
                };
                window.__sampleDiff = arguments[0];
                """,
                SAMPLE_DIFF,
            )

            # Trigger regen → stub fetch fires → lastDiff populated → Diff button enabled
            driver.find_element(By.ID, "btn-regen").click()
            wait.until(lambda d: not d.find_element(By.ID, "btn-diff").get_attribute("disabled"))

            driver.find_element(By.ID, "btn-diff").click()
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#diff-view")))

            adds = driver.find_elements(By.CSS_SELECTOR, "#diff-view .diff-add")
            dels = driver.find_elements(By.CSS_SELECTOR, "#diff-view .diff-del")
            hunks = driver.find_elements(By.CSS_SELECTOR, "#diff-view .diff-hunk")
            metas = driver.find_elements(By.CSS_SELECTOR, "#diff-view .diff-meta")

            assert len(adds) == 2, f"expected 2 add lines, got {len(adds)}"
            assert len(dels) == 2, f"expected 2 del lines, got {len(dels)}"
            assert len(hunks) == 1, f"expected 1 hunk line, got {len(hunks)}"
            assert len(metas) == 2, f"expected 2 meta lines, got {len(metas)}"

            logs = driver.get_log("browser")
            errs = [
                l for l in logs
                if l.get("level") == "SEVERE"
                and "favicon.ico" not in l.get("message", "")
            ]
            if errs:
                for e in errs: print(f"SEVERE: {e}")
                return 1

            print(f"OK — diff modal: {len(adds)} add, {len(dels)} del, {len(hunks)} hunk, 0 JS errors")
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
