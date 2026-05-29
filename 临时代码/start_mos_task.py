import socket
import json

# 目标地址
HOST = "192.168.16.53"
PORT = 18211

# 你的JSON数据
data = {
    "id": "1",
    "operation_type": "PTZCONTROL",
    "target": "MOS",
    "operation_detail": "LAOHUA",
    "action_type": "111",
    "operate_params": {
        "marker": "1_1_2",
        "pallet": ["anniu_hezha", "anniu_fenzha"],
        "safe_area": "",
        "gripper_param": {
            "recipe": ""
        },
        "switch_rotate_param": {},
        "discharge_param": {
            "mode": ""
        },
        "handcar_param": {},
        "GroundSwtich_param": {}
    }
}

# 转JSON字符串（注意：不要格式化换行）
json_str = json.dumps(data, separators=(',', ':'))

# 构造协议报文
msg = b'\x02'                                # STX
msg += b'11051'                              # 命令字
msg += json_str.encode('utf-8')              # JSON
msg += b'0000'                               # 固定字段
msg += b'\x03'                               # ETX

print("发送报文:", msg)

# 创建TCP连接并发送
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(msg)

    # 接收返回
    response = s.recv(4096)
    print("返回数据:", response)

    # 如果需要解析JSON（去头尾）
    if response.startswith(b'\x02') and response.endswith(b'\x03'):
        body = response[1:-1]  # 去掉 02 和 03
        print("有效负载:", body.decode(errors='ignore'))