import hashlib
import hmac
import time
import uuid
import requests

BASE_URL = "http://192.168.17.253:5000"
CLIENT_ID = "cli_lmZtGtSNoL40EWVb"
API_SECRET = "oas_blCYpz8g7AHbJ-PHmbqW8h7bYpS_zVtB01eLkNcyfaY"
ROBOT_IP = "192.168.17.145"


def build_headers(method, path, body=b""):
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = "\n".join([method.upper(), path, timestamp, nonce, body_hash])
    signature = hmac.new(
        API_SECRET.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-Client-Id": CLIENT_ID,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature,
    }


list_path = f"/api/open/v1/accuracy-reports/pass-pdfs?ip={ROBOT_IP}"
list_headers = build_headers("GET", list_path)
list_response = requests.get(BASE_URL + list_path, headers=list_headers, timeout=60)
list_result = list_response.json()

print("列表HTTP:", list_response.status_code)
print("列表结果:", list_result.get("success"), list_result.get("code"), list_result.get("message"))
print("request_id:", list_result.get("request_id"))

reports = (list_result.get("data") or {}).get("reports") or []
print("合格PDF数量:", len(reports))

for report in reports:
    print("报告名:", report.get("filename"))
    print("报告ID:", report.get("report_id"))
    print("生成时间:", report.get("created_at"))
    print("大小:", report.get("size"))
    print("file_id:", report.get("file_id"))
    print("下载:", report.get("download_url"))


if reports:
    first = reports[0]
    file_id = first["file_id"]
    download_path = f"/api/open/v1/accuracy-reports/files/{file_id}"
    download_headers = build_headers("GET", download_path)
    download_response = requests.get(BASE_URL + download_path, headers=download_headers, timeout=120)

    print("下载HTTP:", download_response.status_code)
    print("Content-Type:", download_response.headers.get("Content-Type"))
    print("PDF字节数:", len(download_response.content))

    with open(first["filename"], "wb") as handle:
        handle.write(download_response.content)