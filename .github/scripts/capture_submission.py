import json
import os
import re
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
DEMO_USER = "capstone-demo"
DEMO_PASSWORD = os.environ["CI_DEMO_PASSWORD"]
ROOT_USER = "root"
ROOT_PASSWORD = os.environ["CI_ROOT_PASSWORD"]
OUTPUT = Path("submission")
EVIDENCE = OUTPUT / "evidence"
COOKIE_JAR = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "capstone-cookies.txt"


def curl(args):
    result = subprocess.run(["curl", *args], capture_output=True, text=True, check=False)
    return result.returncode, result.stdout + result.stderr


def save_curl_file(name, sections):
    path = OUTPUT / name
    with path.open("w", encoding="utf-8") as stream:
        stream.write("cURL evidence — captured from the Django app running in GitHub Actions.\n")
        stream.write(f"Base URL: {BASE_URL}\n")
        stream.write("The demo account/password are temporary and expire when this CI job ends.\n\n")
        for command, args in sections:
            stream.write("Command:\n")
            stream.write(command + "\n\nOutput:\n")
            code, output = curl(args)
            output = re.sub(r"(?im)^(Set-Cookie:\s*(?:sessionid|csrftoken)=)[^;\r\n]+", r"\1[redacted]", output)
            output = re.sub(r'("csrfToken"\s*:\s*")[^"]+(")', r"\1[redacted]\2", output)
            stream.write(output)
            if not output.endswith("\n"):
                stream.write("\n")
            stream.write(f"[curl exit code: {code}]\n\n")
            if code:
                raise RuntimeError(f"cURL failed: {command}\n{output}")


def capture_api_outputs():
    csrf_args = ["-sS", "-i", "-c", str(COOKIE_JAR), f"{BASE_URL}/djangoapp/csrf"]
    csrf_code, csrf_output = curl(csrf_args)
    if csrf_code:
        raise RuntimeError("Could not get CSRF token: " + csrf_output)
    body = csrf_output.split("\r\n\r\n")[-1].split("\n\n")[-1]
    csrf_token = json.loads(body)["csrfToken"]

    login_payload = json.dumps(
        {"userName": DEMO_USER, "password": DEMO_PASSWORD}, separators=(",", ":")
    )
    csrf_command = f"curl -i -c cookies.txt {BASE_URL}/djangoapp/csrf"
    login_command = (
        "curl -i -b cookies.txt -c cookies.txt -H 'X-CSRFToken: <token from previous response>' "
        "-H 'Content-Type: application/json' "
        f"--data '{login_payload}' {BASE_URL}/djangoapp/login"
    )
    save_curl_file("loginuser", [
        (csrf_command, ["-sS", "-i", "-c", str(COOKIE_JAR), f"{BASE_URL}/djangoapp/csrf"]),
        (login_command, [
            "-sS", "-i", "-b", str(COOKIE_JAR), "-c", str(COOKIE_JAR),
            "-H", f"X-CSRFToken: {csrf_token}", "-H", "Content-Type: application/json",
            "--data", login_payload, f"{BASE_URL}/djangoapp/login",
        ]),
    ])
    save_curl_file("logoutuser", [
        (f"curl -i -b cookies.txt {BASE_URL}/djangoapp/logout",
         ["-sS", "-i", "-b", str(COOKIE_JAR), f"{BASE_URL}/djangoapp/logout"]),
    ])
    COOKIE_JAR.unlink(missing_ok=True)

    for name, command, url in [
        ("getdealerreviews", f"curl -i {BASE_URL}/fetchReviews/dealer/15", f"{BASE_URL}/fetchReviews/dealer/15"),
        ("getalldealers", f"curl -i {BASE_URL}/fetchDealers", f"{BASE_URL}/fetchDealers"),
        ("getdealerbyid", f"curl -i {BASE_URL}/fetchDealer/1", f"{BASE_URL}/fetchDealer/1"),
        ("getdealersbyState", f"curl -i {BASE_URL}/fetchDealers/Kansas", f"{BASE_URL}/fetchDealers/Kansas"),
        ("getallcarmakes", f"curl -i {BASE_URL}/djangoapp/get_cars", f"{BASE_URL}/djangoapp/get_cars"),
        ("analyzereview", f"curl -i '{BASE_URL}/analyze/Fantastic%20services'", f"{BASE_URL}/analyze/Fantastic%20services"),
    ]:
        save_curl_file(name, [(command, ["-sS", "-i", url])])

    save_curl_file("getallcarmakes", [
        (f"curl -i {BASE_URL}/djangoapp/get_cars", ["-sS", "-i", f"{BASE_URL}/djangoapp/get_cars"]),
        (f"curl -i '{BASE_URL}/djangoapp/get_cars?makeId=1'",
         ["-sS", "-i", f"{BASE_URL}/djangoapp/get_cars?makeId=1"]),
    ])


def wait_for_ready(base):
    import urllib.request

    for _ in range(30):
        try:
            with urllib.request.urlopen(base + "/djangoapp/health", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Django did not become ready on " + base)


def take_screenshots():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1150}, device_scale_factor=1)
        page = context.new_page()

        page.goto(BASE_URL + "/", wait_until="networkidle")
        page.locator(".dealer-card").first.wait_for()
        page.screenshot(path=str(EVIDENCE / "get_dealers.png"), full_page=True)

        page.goto(BASE_URL + "/login", wait_until="networkidle")
        page.get_by_label("Username").fill(DEMO_USER)
        page.get_by_label("Password").fill(DEMO_PASSWORD)
        page.get_by_role("button", name="Log in").click()
        page.wait_for_url(BASE_URL + "/")
        page.locator(".dealer-card").first.wait_for()
        page.screenshot(path=str(EVIDENCE / "get_dealers_loggedin.png"), full_page=True)

        page.goto(BASE_URL + "/dealers/state/Kansas", wait_until="networkidle")
        page.locator(".dealer-card").first.wait_for()
        page.screenshot(path=str(EVIDENCE / "dealersbystate.png"), full_page=True)

        page.goto(BASE_URL + "/dealers/15", wait_until="networkidle")
        page.get_by_role("heading", name="Reviews").wait_for()
        page.screenshot(path=str(EVIDENCE / "dealer_id_reviews.png"), full_page=True)

        page.goto(BASE_URL + "/dealers/15/review", wait_until="networkidle")
        page.get_by_role("heading", name="Review Dealer").wait_for()
        review_text = "Excellent service, clear communication, and a smooth purchase."
        page.locator("#review-text").fill(review_text)
        page.locator("#review-purchase-date").fill("2024-04-12")
        page.locator(".checkbox-label input[type=checkbox]").check()
        make_select = page.locator("#review-car-make")
        page.wait_for_function("document.querySelector('#review-car-make').options.length > 1")
        make_select.select_option(make_select.locator("option").nth(1).get_attribute("value"))
        model_select = page.locator("#review-car-model")
        page.wait_for_function("document.querySelector('#review-car-model').options.length > 1")
        model_select.select_option(model_select.locator("option").nth(1).get_attribute("value"))
        page.locator("#review-car-year").fill("2022")
        page.screenshot(path=str(EVIDENCE / "dealership_review_submission.png"), full_page=True)
        page.get_by_role("button", name="Submit review").click()
        page.get_by_text(review_text, exact=True).wait_for()
        page.screenshot(path=str(EVIDENCE / "added_review.png"), full_page=True)

        admin = context.new_page()
        admin.goto(BASE_URL + "/admin/", wait_until="networkidle")
        if "/admin/login/" in admin.url:
            admin.get_by_label("Username").fill(ROOT_USER)
            admin.get_by_label("Password").fill(ROOT_PASSWORD)
            admin.get_by_role("button", name="Log in").click()
        admin.get_by_text("Welcome,", exact=False).wait_for()
        admin.screenshot(path=str(EVIDENCE / "admin_login.png"), full_page=True)
        logout_button = admin.locator("#user-tools form button")
        if logout_button.count():
            logout_button.click()
        else:
            admin.locator("#user-tools a[href*='logout']").click()
        admin.wait_for_url("**/admin/login/**")
        admin.screenshot(path=str(EVIDENCE / "admin_logout.png"), full_page=True)
        browser.close()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    wait_for_ready(BASE_URL)
    capture_api_outputs()
    take_screenshots()

    server_log = Path(os.environ["DJANGO_SERVER_LOG"])
    (OUTPUT / "django_server").write_text(server_log.read_text(encoding="utf-8"), encoding="utf-8")
    workflow_url = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    (OUTPUT / "CICD").write_text(
        "GitHub Actions CI evidence\n"
        f"Workflow run: {workflow_url}\n"
        f"Run number: {os.environ.get('GITHUB_RUN_NUMBER', 'unknown')}\n"
        f"Python job: {os.environ.get('CAPSTONE_PYTHON_JOB_STATUS', 'unknown')}\n"
        f"JavaScript job: {os.environ.get('CAPSTONE_JS_JOB_STATUS', 'unknown')}\n"
        "The workflow output includes test/build logs and the captured Django server startup.\n",
        encoding="utf-8",
    )
    (EVIDENCE / "README.txt").write_text(
        "Screenshots were captured by Chromium against the Django and React app running in this GitHub Actions job. "
        "CI-only accounts and database rows are discarded when the job ends. These screenshots show the app "
        "running in CI and are not screenshots from a public Render deployment.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
