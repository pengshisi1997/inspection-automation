import socket
import json
import time
import paramiko
from datetime import datetime

# 目标地址
HOST = "192.168.16.53"
PORT = 18211

# SSH配置
SSH_HOST = "192.168.16.53"
SSH_PORT = 23
SSH_USERNAME = "youibot"
SSH_PASSWORD = "youibot"

# 你的JSON数据
data = {
    "id": "1",
    "operation_type": "PTZCONTROL",
    "target": "MOS",
    "operation_detail": "DETECT",
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

# 等待1秒
print("\n等待1秒...")
time.sleep(1)

# SSH连接并读取日志
print("正在连接SSH...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SSH_HOST, SSH_PORT, SSH_USERNAME, SSH_PASSWORD)

# 查找最近的日期文件夹
base_log_path = "/mos/log/mos_log"
print(f"基础日志路径: {base_log_path}")

# 列出日期文件夹并选择最新的
stdin, stdout, stderr = ssh.exec_command(f"ls -1rt {base_log_path}")
date_dirs = stdout.read().decode().strip().splitlines()
date_dirs = [d for d in date_dirs if d.isdigit() and len(d) == 8]

if not date_dirs:
    print("未找到日期文件夹")
    ssh.close()
    exit()

latest_date = date_dirs[-1]
log_path = f"{base_log_path}/{latest_date}/INFO"
print(f"最新日期: {latest_date}, 日志路径: {log_path}")

# 列出日志文件
stdin, stdout, stderr = ssh.exec_command(f"ls -1rt {log_path}")
file_list = stdout.read().decode().strip().splitlines()
file_list = [f for f in file_list if f.startswith("INFO_")]

if not file_list:
    print("未找到日志文件")
else:
    latest_file = file_list[-1]
    print(f"最新文件: {latest_file}")
    
    # 获取最后50行
    full_path = f"{log_path}/{latest_file}"
    stdin, stdout, stderr = ssh.exec_command(f"tail -n 50 {full_path}")
    log_content = stdout.read().decode()
    print("\n日志最后50行:")
    print(log_content)
    
    # 解析数据
    result = {
        "温度": None,
        "湿度": None,
        "PM1.0": None,
        "PM2.5": None,
        "PM10": None,
        "一氧化碳(CO)": None,
        "可燃气体(EX)": None,
        "硫化氢(H2S)": None,
        "六氟化硫(SF6)": None,
        "氨气(NH3)": None,
        "氢气(H2)": None,
        "声纹数据(td_energy)": None
    }
    
    import re
    for line in log_content.splitlines():
        # 温度
        if "Temperature" in line:
            match = re.search(r"Temperature = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["温度"] = float(val) if val != "nan" else None
        # PM1.0
        if "PM1_0" in line:
            match = re.search(r"PM1_0 = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["PM1.0"] = float(val) if val != "nan" else None
        # PM2.5
        if "PM2_5" in line:
            match = re.search(r"PM2_5 = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["PM2.5"] = float(val) if val != "nan" else None
        # PM10
        if "PM10" in line:
            match = re.search(r"PM10 = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["PM10"] = float(val) if val != "nan" else None
        # CO
        if "Data.CO" in line and not "Data.CO2" in line:
            match = re.search(r"CO = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["一氧化碳(CO)"] = float(val) if val != "nan" else None
        # EX
        if "Data.EX" in line:
            match = re.search(r"EX = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["可燃气体(EX)"] = float(val) if val != "nan" else None
        # H2S
        if "Data.H2S" in line:
            match = re.search(r"H2S = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["硫化氢(H2S)"] = float(val) if val != "nan" else None
        # SF6
        if "Data.SF6" in line:
            match = re.search(r"SF6 = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["六氟化硫(SF6)"] = float(val) if val != "nan" else None
        # NH3
        if "Data.NH3" in line:
            match = re.search(r"NH3 = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["氨气(NH3)"] = float(val) if val != "nan" else None
        # H2
        if "Data.H2" in line and not "Data.H2S" in line:
            match = re.search(r"H2 = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["氢气(H2)"] = float(val) if val != "nan" else None
        # 声纹
        if "td_energy" in line:
            match = re.search(r"td_energy = ([\d.]+|nan)", line)
            if match:
                val = match.group(1)
                result["声纹数据(td_energy)"] = float(val) if val != "nan" else None
    
    print("\n提取结果:")
    print(result)

# 关闭SSH连接
ssh.close()