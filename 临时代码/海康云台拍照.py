import requests
from requests.auth import HTTPDigestAuth

# 配置（拆分IP和端口，更清晰且避免拼接错误）
DEVICE_IP = "192.168.16.64"  # 仅IP地址，不含端口
DEVICE_PORT = 8083           # 单独指定端口
USER = "admin"
PWD = "robot2020"
CHANNEL = "101"  # 主码流（子码流用102，按需调整）

# 拼接URL（重点：端口要放在IP后，格式为 http://IP:端口/...）
URL = f"http://{DEVICE_IP}:{DEVICE_PORT}/ISAPI/Streaming/channels/{CHANNEL}/picture"

try:
    # 抓图（添加verify=False，解决部分设备证书问题）
    resp = requests.get(
        URL,
        auth=HTTPDigestAuth(USER, PWD),
        timeout=10,
        verify=False  # 海康设备常需关闭SSL验证，否则可能报错
    )

    # 保存图片
    if resp.status_code == 200:
        with open("capture.jpg", "wb") as f:
            f.write(resp.content)
        print("✅ 抓图成功，图片已保存为 capture.jpg")
    else:
        print(f"❌ 抓图失败：状态码 {resp.status_code}，响应信息 {resp.text[:200]}")

except requests.exceptions.ConnectTimeout:
    print("❌ 连接超时：请检查设备IP/端口是否正确，或网络是否通")
except requests.exceptions.ConnectionError:
    print("❌ 连接失败：请确认设备在线，且8083端口已开放")
except Exception as e:
    print(f"❌ 未知错误：{str(e)}")