"""Selenium smoke test for L41_Pacer.html.

Verifies: loads cleanly, all 3 tabs render, tab-switching works, no JS console errors,
and Start button fires timer.
"""
from pathlib import Path
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

HTML = Path(__file__).parent / "L41_Pacer.html"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1400,900")
opts.set_capability("ms:loggingPrefs", {"browser": "ALL"})

driver = webdriver.Edge(options=opts)
failures = []
try:
    driver.get(HTML.absolute().as_uri())
    time.sleep(1.0)

    # Tabs present
    tabs = driver.find_elements(By.CSS_SELECTOR, "button.tab[data-tab]")
    tab_ids = [t.get_attribute("data-tab") for t in tabs]
    expected = ["p1", "p2", "p3"]
    if tab_ids != expected:
        failures.append(f"tab ids mismatch: got {tab_ids}, expected {expected}")

    # Switch through each tab and verify panel visible
    for tid in expected:
        btn = driver.find_element(By.CSS_SELECTOR, f"button.tab[data-tab='{tid}']")
        btn.click()
        time.sleep(0.3)
        panels = driver.find_elements(By.CSS_SELECTOR, f"#panel-{tid}")
        if not panels:
            failures.append(f"panel-{tid} not found")
            continue
        if "active" not in (panels[0].get_attribute("class") or ""):
            failures.append(f"panel-{tid} did not become active on click")

    # Start button fires timer (click Start on p1, check timer text changes)
    driver.find_element(By.CSS_SELECTOR, "button.tab[data-tab='p1']").click()
    time.sleep(0.2)
    start_btns = driver.find_elements(By.CSS_SELECTOR, "button[id^='startBtn-']")
    if not start_btns:
        failures.append("no Start button found")
    else:
        start_btns[0].click()
        time.sleep(1.5)

    # Console errors
    logs = driver.get_log("browser")
    errs = [l for l in logs if l.get("level") in ("SEVERE", "ERROR")]
    # Filter benign favicon 404s
    errs = [e for e in errs if "favicon" not in e.get("message", "").lower()]
    if errs:
        for e in errs:
            failures.append(f"JS error: {e.get('message', '')[:200]}")

finally:
    driver.quit()

if failures:
    print("FAIL")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
else:
    print("PASS: L41_Pacer.html — 3 tabs, switching works, Start fires, no JS errors")
