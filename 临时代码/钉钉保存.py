import requests
import json

webhook = "https://oapi.dingtalk.com/robot/send?access_token=d4032db44488f1336845f48ae17b2ba716a59300400ce34d895c1848a9ac996c"

headers = {
    "Content-Type": "application/json"
}

data = {
    "msgtype": "text",
    "text": {
        # ⚠️ 必须包含关键词：测hi报告
        "content": "测试报告\n测试消息发送成功111"
    }
}

response = requests.post(webhook, headers=headers, data=json.dumps(data))
print(response.text)