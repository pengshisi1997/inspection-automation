import hashlib
import hmac
import json
import time
import uuid
import os
import requests


BASE_URL = "http://192.168.17.253:5000"
CLIENT_ID = "cli_hPHLVfVpUNBbcjtg"
API_SECRET = "oas_HKvEP9jAJuzg9qDakJpWRhWYe6SQCchXABeLWRZ8mAg"


class AGVClient:

    def __init__(self, client_id, api_secret, base_url):
        self.client_id = client_id
        self.api_secret = api_secret
        self.base_url = base_url

    def _sign(self, method, path, body=""):
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex

        body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        canonical = "\n".join([
            method.upper(),
            path,
            timestamp,
            nonce,
            body_hash
        ])

        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Client-Id": self.client_id,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature,
        }

        return headers

    def _post(self, path, body_dict):
        body = json.dumps(body_dict, separators=(",", ":"))
        headers = self._sign("POST", path, body)

        resp = requests.post(
            self.base_url + path,
            data=body,
            headers=headers,
            timeout=240
        )

        return resp.json()

    def _download_file(self, file_id, save_path):
        path = f"/api/open/v1/agv-photo/files/{file_id}"
        query = "?mode=download"

        headers = self._sign("GET", path + query, "")

        resp = requests.get(
            self.base_url + path + query,
            headers=headers,
            timeout=60
        )

        with open(save_path, "wb") as f:
            f.write(resp.content)

        return save_path

    def execute(self, ip, save_dir=None, sn_prefix=None):
        """
        执行任务：
        1. 可见光拍照
        2. 热成像拍照
        3. 测温
        
        参数:
            ip: 机器人IP
            save_dir: 图片保存目录，默认当前目录
            sn_prefix: SN号前缀，用于命名文件，如 {sn_prefix}_可见光拍照.jpg
        """

        results = {
            "photos": [],
            "temperature": None
        }

        # 确定保存目录
        if save_dir is None:
            save_dir = os.getcwd()
        else:
            os.makedirs(save_dir, exist_ok=True)

        actions = [
            ("/api/open/v1/agv-photo/visible", "可见光拍照"),
            ("/api/open/v1/agv-photo/thermal", "热成像拍照"),
            ("/api/open/v1/agv-photo/thermal-temperature", None)
        ]

        for path, photo_type in actions:
            print(f"\n调用接口: {path}")

            resp = self._post(path, {"ip": ip})

            if not resp.get("success"):
                print("失败:", resp)
                continue

            data = resp.get("data") or {}
            action = data.get("action") or {}

            # ---- 处理照片 ----
            photos = action.get("photos") or []

            for p in photos:
                if len(results["photos"]) >= 2:
                    break
                file_id = p["file_id"]
                name = p["name"]
                
                # 确定文件名
                if sn_prefix and photo_type:
                    # 使用SN号前缀和类型命名
                    file_ext = os.path.splitext(name)[1] or ".jpg"
                    local_name = f"{sn_prefix}_{photo_type}{file_ext}"
                else:
                    # 保持原有命名方式
                    local_name = f"{int(time.time())}_{name}"
                
                save_path = os.path.join(save_dir, local_name)

                print("下载图片:", local_name)

                self._download_file(file_id, save_path)

                results["photos"].append(save_path)

            # ---- 处理温度 ----
            temperature = data.get("temperature") or action.get("temperature")
            if temperature:
                results["temperature"] = temperature

        return results


# =========================
# 使用示例
# =========================
if __name__ == "__main__":
    client = AGVClient(CLIENT_ID, API_SECRET, BASE_URL)

    ip = "192.168.16.178"   # 这里换成你的机器人IP

    result = client.execute(ip)

    print("\n===== 最终结果 =====")
    print("温度数据:", json.dumps(result["temperature"], ensure_ascii=False, indent=2))
    print("图片文件:")
    for p in result["photos"]:
        print(p)