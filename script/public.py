import paramiko
import os
import requests
import json
import subprocess
import time
import pyautogui
from config.model_config import IMAGE_YUNTAI_DIR, TEST_RECORD_DIR, get_result_file_path

def download_latest_image(ip):
    username = "youibot"
    password = "youibot"
    remote_dir = "/server/data/image/"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    sftp = None
    try:
        def get_sn_name():
            try:
                result_file = os.path.join(TEST_RECORD_DIR, f"{ip}.json")
                if not os.path.exists(result_file):
                    return "UNKNOWN_SN"
                with open(result_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sn = data.get("robot_info", {}).get("sn") or "UNKNOWN_SN"
                sn = str(sn).strip()
                for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                    sn = sn.replace(ch, "_")
                return sn if sn else "UNKNOWN_SN"
            except Exception:
                return "UNKNOWN_SN"

        sn_name = get_sn_name()

        ssh.connect(ip, username=username, password=password, timeout=10)
        sftp = ssh.open_sftp()
        mission_page_url = f"http://{ip}:8080/api/v3/missionWorks/page?pageNum=1&pageSize=20&sort=create_time+desc"
        mission_resp = requests.get(mission_page_url, timeout=10)
        if mission_resp.status_code != 200:
            return None

        mission_data = mission_resp.json()
        yuntai_tasks = [task for task in mission_data.get('list', []) if task.get('name') == '云台']
        if not yuntai_tasks:
            return None

        yuntai_tasks.sort(key=lambda x: x.get('createTime', 0), reverse=True)
        mission_work_id = yuntai_tasks[0].get('id')
        if not mission_work_id:
            return None

        actions_url = f"http://{ip}:8080/api/v3/missionWorks/{mission_work_id}/missionWorkActions?sort=create_time+desc"
        actions_resp = requests.get(actions_url, timeout=30)
        if actions_resp.status_code != 200:
            return None

        actions_data = actions_resp.json()

        def safe_load_json(raw):
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except Exception:
                return {}

        def extract_image_paths(action_name):
            for action in actions_data:
                if action.get('name') == action_name:
                    result_data = safe_load_json(action.get('resultData'))
                    image_url = result_data.get('imageUrl', {})
                    return {
                        '1': image_url.get('binocular_1', {}).get('image_path'),
                        '2': image_url.get('binocular_2', {}).get('image_path')
                    }
            return {'1': None, '2': None}

        ptz_paths = extract_image_paths('ptz拍照')
        preset_paths = extract_image_paths('预置点拍照')

        # 创建image_yuntai目录
        local_dir = IMAGE_YUNTAI_DIR
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        result_paths = {}

        download_targets = [
            ("ptz_1", ptz_paths.get('1'), f"{sn_name}_ptz1"),
            ("ptz_2", ptz_paths.get('2'), f"{sn_name}_ptz2"),
            ("preset_1", preset_paths.get('1'), f"{sn_name}_预置点1"),
            ("preset_2", preset_paths.get('2'), f"{sn_name}_预置点2")
        ]

        for key, remote_path, local_name_prefix in download_targets:
            if not remote_path:
                continue
            remote_file = remote_path.replace("\\", "/").replace("//", "/")
            _, ext = os.path.splitext(os.path.basename(remote_file))
            local_filename = f"{local_name_prefix}{ext if ext else '.jpg'}"
            local_path = os.path.join(local_dir, local_filename)
            try:
                sftp.get(remote_file, local_path)
                result_paths[key] = local_path
            except Exception:
                continue

        return result_paths if result_paths else None

    except Exception as e:
        print("发生错误:", e)
        return None
    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        try:
            ssh.close()
        except Exception:
            pass


def get_temperature(ip):
    url = f"http://{ip}:8080/api/v3/missionWorks/76361032-b5a9-44b9-af39-7f0d66233ff8/missionWorkActions?sort=create_time+desc"

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()

        data = resp.json()

        results = []

        for action in data:
            if action.get("actionType") == "MEASURE_TEMPERATURE":
                result_data_str = action.get("resultData")

                if not result_data_str:
                    continue

                result_data = json.loads(result_data_str)
                temp_list = result_data.get("professional_temp_data", [])

                for item in temp_list:
                    min_temp = item.get("fMinTemperature")
                    max_temp = item.get("fMaxTemperature")

                    results.append({
                        "fMinTemperature": min_temp,
                        "fMaxTemperature": max_temp
                    })

        return results

    except Exception as e:
        print("request error:", e)
        return None

def upload_file_to_server(host):
    # 使用绝对路径，确保无论从哪个目录执行都能找到文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(script_dir, "read_topic.py")
    remote_path = "/home/youibot/read_topic.py"

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"{local_path} not found")

    transport = paramiko.Transport((host, 22))
    try:
        transport.connect(username="youibot", password="youibot")
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(local_path, remote_path)
    finally:
        transport.close()


def close_ssh_window_by_exit():
    """
    向当前激活的 cmd 窗口发送 exit 命令关闭
    """
    time.sleep(0.5)
    pyautogui.write("exit")
    pyautogui.press("enter")


def auto_ssh(ip):
    subprocess.Popen(f"start cmd /k ssh youibot@{ip}", shell=True)

    time.sleep(1)  # 等待窗口稳定

    pyautogui.write("youibot")
    pyautogui.press("enter")

    # time.sleep(1)

    # 执行脚本
    pyautogui.write("python read_topic.py")
    pyautogui.press("enter")

def get_sn_from_ip(ip):
    """
    从测试记录文件中获取 SN 号
    
    Args:
        ip: 机器人IP地址
    
    Returns:
        SN 号，如果失败返回 UNKNOWN_SN
    """
    try:
        result_file = get_result_file_path(ip)
        legacy_file = os.path.join(TEST_RECORD_DIR, f"{ip}.json")
        if not os.path.exists(result_file):
            result_file = legacy_file
        if not os.path.exists(result_file):
            return "UNKNOWN_SN"
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        sn = data.get("robot_info", {}).get("sn") or "UNKNOWN_SN"
        sn = str(sn).strip()
        for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            sn = sn.replace(ch, "_")
        return sn if sn else "UNKNOWN_SN"
    except Exception:
        return "UNKNOWN_SN"


def download_mos_file(ip, remote_path, local_filename):
    """
    从机器人下载文件到 image_yuntai 目录
    
    Args:
        ip: 机器人IP地址
        remote_path: 远程文件路径
        local_filename: 本地文件名（不含路径）
    
    Returns:
        本地文件路径，如果失败返回 None
    """
    username = "youibot"
    password = "youibot"
    
    if not remote_path:
        return None
    
    # 获取 SN 号
    sn_name = get_sn_from_ip(ip)
    
    # 构建新的文件名：SN_原文件名
    filename_with_sn = f"{sn_name}_{local_filename}"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sftp = None
    
    try:
        # 创建 image_yuntai 目录
        local_dir = IMAGE_YUNTAI_DIR
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        
        ssh.connect(ip, username=username, password=password, timeout=10)
        sftp = ssh.open_sftp()
        
        # 处理远程路径
        remote_file = remote_path.replace("\\", "/").replace("//", "/")
        
        # 构建本地路径
        local_path = os.path.join(local_dir, filename_with_sn)
        
        # 下载文件
        sftp.get(remote_file, local_path)
        return local_path
        
    except Exception as e:
        print(f"下载文件失败: {e}")
        return None
    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        try:
            ssh.close()
        except Exception:
            pass


# ip = "192.168.16.64"
# upload_file_to_server(ip)
# # close_ssh_window_by_exit()
# auto_ssh(ip)
