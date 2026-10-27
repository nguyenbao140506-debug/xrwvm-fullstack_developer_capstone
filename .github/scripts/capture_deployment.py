"""Capture real browser-window evidence against the public capstone deployment."""
import json
import os
import secrets
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import mss
import mss.tools
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("DEPLOYMENT_BASE_URL", "").rstrip("/")
if BASE_URL != "https://fullstack-developer-capstone-36w2.onrender.com":
    raise RuntimeError("Unexpected deployment target.")
OUTPUT = Path("resubmission")
IMAGES = OUTPUT / "images"
COOKIE_JAR = Path(tempfile.gettempdir()) / "capstone-evidence-cookies.txt"
USERNAME = "bao" + os.environ.get("GITHUB_RUN_ID", "demo")[-5:] + secrets.token_hex(2)
PASSWORD = secrets.token_urlsafe(20)
REVIEW = (
    "Capstone demonstration review: Fantastic services, excellent information, "
    "and a friendly, helpful experience. This is sample feedback for the course project."
)


def run_curl(method, path, payload=None, authenticated=False, csrf=None):
    args = ["curl", "-sS", "--connect-timeout", "20", "--max-time", "150", "-X", method, "-b", str(COOKIE_JAR), "-c", str(COOKIE_JAR)]
    if payload is not None:
        args += ["-H", "Content-Type: application/json", "-H", "Origin: " + BASE_URL, "-H", "Referer: " + BASE_URL + "/", "--data", json.dumps(payload, separators=(",", ":"))]
    if csrf:
        args += ["-H", "X-CSRFToken: " + csrf]
    args += ["-w", "\nHTTP_STATUS=%{http_code}\n", BASE_URL + path]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"cURL {method} {path} failed: {result.stderr}")
    body, status = result.stdout.rsplit("\nHTTP_STATUS=", 1)
    status = int(status.strip())
    if status not in (200, 201):
        raise RuntimeError(f"{method} {path} returned HTTP {status}: {body}")
    return body, status


def csrf_token():
    body, _ = run_curl("GET", "/djangoapp/csrf")
    return json.loads(body)["csrfToken"]


def write_evidence(name, command, body, status):
    (OUTPUT / name).write_text(
        command + "\n\n" + body + f"\nHTTP_STATUS={status}\n",
        encoding="utf-8",
    )


def capture_curl_evidence():
    token = csrf_token()
    run_curl("POST", "/djangoapp/register", {
        "username": USERNAME,
        "first_name": "Bao",
        "last_name": "Demo",
        "email": USERNAME + "@example.test",
        "password": PASSWORD,
    }, csrf=token)
    token = csrf_token()
    payload = {"userName": USERNAME, "password": PASSWORD}
    body, status = run_curl("POST", "/djangoapp/login", payload, csrf=token)
    command = (
        f"BASE_URL='{BASE_URL}'\nCOOKIE_JAR='cookies.txt'\n"
        'CSRF_TOKEN="$(curl -sS -b "$COOKIE_JAR" -c "$COOKIE_JAR" "$BASE_URL/djangoapp/csrf"'
        ' | python3 -c "import json,sys; print(json.load(sys.stdin)[\'csrfToken\'])")"\n'
        'curl -sS -X POST "$BASE_URL/djangoapp/login" \\\n'
        '  -b "$COOKIE_JAR" -c "$COOKIE_JAR" \\\n'
        '  -H "Content-Type: application/json" \\\n'
        '  -H "Origin: ' + BASE_URL + '" \\\n'
        '  -H "Referer: ' + BASE_URL + '/" \\\n'
        '  -H "X-CSRFToken: $CSRF_TOKEN" \\\n'
        "  --data " + shlex.quote(json.dumps(payload, separators=(",", ":"))) + " \\\n"
        "  -w '\\nHTTP_STATUS=%{http_code}\\n'"
    )
    write_evidence("loginuser", command, body, status)
    body, status = run_curl("GET", "/djangoapp/logout", authenticated=True)
    write_evidence(
        "logoutuser",
        f'curl -sS -X GET -b cookies.txt "{BASE_URL}/djangoapp/logout" '
        "-w '\\nHTTP_STATUS=%{http_code}\\n'",
        body, status,
    )
    for name, path in [
        ("getdealerreviews", "/fetchReviews/dealer/15"),
        ("getalldealers", "/fetchDealers"),
        ("getdealerbyid", "/fetchDealer/15"),
        ("getdealersbyState", "/fetchDealers/Kansas"),
        ("getallcarmakes", "/djangoapp/get_cars"),
        ("analyzereview", "/analyze/Fantastic%20services"),
    ]:
        body, status = run_curl("GET", path)
        write_evidence(
            name,
            f'curl -sS -X GET "{BASE_URL}{path}" ' + "-w '\\nHTTP_STATUS=%{http_code}\\n'",
            body, status,
        )
    COOKIE_JAR.unlink(missing_ok=True)


def capture_window(name):
    time.sleep(0.5)
    with mss.MSS() as screen:
        monitor = screen.monitors[1]
        pixels = screen.grab(monitor)
        mss.tools.to_png(pixels.rgb, pixels.size, output=str(IMAGES / name))


def goto(page, path):
    page.goto(BASE_URL + path, wait_until="networkidle", timeout=120000)


def capture_pages():
    with sync_playwright() as driver:
        browser = driver.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1600,1400", "--window-position=0,0"],
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.set_default_timeout(30000)
        try:
            goto(page, "/")
            page.wait_for_function("window.innerWidth >= 1500 && window.innerHeight >= 1200")
            page.locator(".dealer-card").first.wait_for()
            capture_window("deployed_landingpage.png")
            page.locator("#dealer-list").scroll_into_view_if_needed()
            capture_window("get_dealers.png")

            goto(page, "/static/About.html")
            page.locator(".team-card").last.wait_for()
            page.wait_for_function(
                "Array.from(document.querySelectorAll('.team-portrait')).every(image => image.complete && image.naturalWidth > 0)"
            )
            page.locator(".team-grid").scroll_into_view_if_needed()
            capture_window("about_team.png")
            goto(page, "/static/Contact.html")
            page.get_by_role("heading", name="Contact Us", exact=True).wait_for()
            page.locator("main").scroll_into_view_if_needed()
            capture_window("contact_us.png")

            goto(page, "/login")
            page.get_by_label("Username", exact=True).fill(USERNAME)
            page.get_by_label("Password", exact=True).fill(PASSWORD)
            page.get_by_role("button", name="Log in", exact=True).click()
            page.get_by_role("button", name="Log out", exact=True).wait_for()
            page.locator(".dealer-card").first.wait_for()
            page.locator("#dealer-list").scroll_into_view_if_needed()
            capture_window("deployed_loggedin.png")
            shutil.copyfile(IMAGES / "deployed_loggedin.png", IMAGES / "get_dealers_loggedin.png")

            goto(page, "/dealers/state/Kansas")
            page.locator(".dealer-card").first.wait_for()
            page.locator("#dealer-list").scroll_into_view_if_needed()
            capture_window("dealersbystate.png")

            goto(page, "/dealers/15")
            page.get_by_role("heading", name="Reviews", exact=True).wait_for()
            capture_window("deployed_dealer_detail.png")
            shutil.copyfile(IMAGES / "deployed_dealer_detail.png", IMAGES / "dealer_id_reviews.png")

            goto(page, "/dealers/15/review")
            page.get_by_role("heading", name="Post Review", exact=True).wait_for()
            page.locator("#review-text").fill(REVIEW)
            page.locator("#review-purchase-date").fill("2026-10-20")
            page.locator("#review-car-make").select_option("Toyota")
            page.locator("#review-car-model").select_option("Camry")
            page.locator("#review-car-year").fill("2023")
            page.get_by_role("button", name="Post Review", exact=True).scroll_into_view_if_needed()
            page.wait_for_function(
                "['review-text', 'review-purchase-date', 'review-car-make', 'review-car-model', 'review-car-year'].every(id => { const box = document.getElementById(id).getBoundingClientRect(); return box.top >= 0 && box.bottom <= window.innerHeight; })"
            )
            capture_window("dealership_review_submission.png")
            page.get_by_role("button", name="Post Review", exact=True).click()
            page.get_by_role("heading", name="Reviews", exact=True).wait_for()
            page.reload(wait_until="networkidle")
            card = page.locator(".review-card").filter(has_text=REVIEW).filter(has_text=USERNAME)
            card.wait_for()
            card.locator('img[alt="positive sentiment"]').wait_for()
            page.wait_for_function(
                "Array.from(document.querySelectorAll('.sentiment-image')).every(image => image.complete && image.naturalWidth > 0)"
            )
            card.scroll_into_view_if_needed()
            capture_window("deployed_add_review.png")
            shutil.copyfile(IMAGES / "deployed_add_review.png", IMAGES / "added_review.png")
            page.get_by_role("button", name="Log out", exact=True).click()
            page.get_by_role("link", name="Log in", exact=True).wait_for()
            goto(page, "/")
            page.locator(".dealer-card").first.wait_for()
            page.bring_to_front()
            page.screenshot()
            capture_window("deployed_landingpage.png")
        except Exception:
            capture_window("capture_failure.png")
            raise
        finally:
            browser.close()


def main():
    OUTPUT.mkdir(exist_ok=True)
    IMAGES.mkdir(exist_ok=True)
    capture_curl_evidence()
    capture_pages()
    (OUTPUT / "deploymentURL").write_text(BASE_URL + "/\n", encoding="utf-8")
    repo = "https://github.com/nguyenbao140506-debug/xrwvm-fullstack_developer_capstone/blob/main"
    (OUTPUT / "SUBMISSION_GUIDE.md").write_text(
        "# Corrected capstone submissions\n\n"
        f"Task 3: {repo}/server/frontend/static/About.html\n\n"
        f"Task 4: {repo}/server/frontend/static/Contact.html\n\n"
        "For text tasks, paste the complete contents of the corresponding file, including both cURL command and output.\n\n"
        "- Task 5: loginuser\n- Task 6: logoutuser\n- Task 8: getdealerreviews\n"
        "- Task 10: getdealerbyid\n- Task 11: getdealersbyState\n- Task 16: analyzereview\n\n"
        "The images folder contains real Chromium window screenshots including its address bar.\n"
        "The demo account and review are course sample data. Its credentials are only in the login evidence file and are not committed as source.\n\n"
        "Task 24: deploymentURL contains the real Render address. The grading report separately requires an IBM Cognitive Class proxy address; that needs a real running IBM lab and cannot be inferred or fabricated.\n",
        encoding="utf-8",
    )
    print("Captured cURL responses, company pages, and all corrected application screenshots.")


if __name__ == "__main__":
    main()
