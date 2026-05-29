import requests
import os

def login_request(ip):
    url = f"http://{ip}:8080/robot/api/v1/login"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": f"http://{ip}:8081",
        "Referer": f"http://{ip}:8081/",
        "User-Agent": "Mozilla/5.0",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache"
    }

    payload = {
        "userName": "admin",
        "password": "admin"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        # 安全提取 token
        token = data.get("data", {}).get("token")
        return token

    except requests.exceptions.RequestException:
        return None
    except ValueError:
        # JSON解析失败
        return None

#获取机器人信息
def get_vehicles(ip: str):
    url = f"http://{ip}:8080/robot/api/v1/vehicles"
    
    headers = {
        "Authorization": f"Bearer;{login_request(ip)}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 如果不是 200 会抛异常
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

#获取环境数据（温度、湿度、O2、CO）
def get_environment_data(ip: str):
    """从机器人API获取环境数据
    
    Args:
        ip: 机器人IP地址
        
    Returns:
        dict: 包含温度、湿度、O2、CO的数据字典
    """
    vehicle_data = get_vehicles(ip)
    if not vehicle_data:
        return None
    
    try:
        environment = vehicle_data.get('data', {}).get('environment', {})
        return {
            'temperature': environment.get('temperature'),
            'humidity': environment.get('humidity'),
            'o2': environment.get('o2'),
            'co': environment.get('co')
        }
    except Exception as e:
        print(f"获取环境数据失败: {e}")
        return None



#上传地图
def upload_agv_map(ip, file_path="1.zip"):
    url = f"http://{ip}:8080/robot/api/v1/AGVMaps/import"

    headers = {
        "Authorization": f"Bearer;{login_request(ip)}",  # ⚠️ 保持分号格式
        "Accept": "application/json, text/plain, */*",
        "Origin": f"http://{ip}:8081",
        "Referer": f"http://{ip}:8081/",
    }

    with open(file_path, "rb") as f:
        files = {
            "file": ("1.zip", f, "application/x-zip-compressed")
        }

        response = requests.post(url, headers=headers, files=files)

    print("Status Code:", response.status_code)
    print("Response:", response.text)

    return response

#刷新地图，上传后需要刷新地图，不然不显示地图
def reload_agv_maps(ip: str):
    url = f"http://{ip}:8080/robot/api/v1/AGVMaps/reload"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer;{login_request(ip)}",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "Origin": f"http://{ip}:8081",
        "Referer": f"http://{ip}:8081/",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.post(url, headers=headers, timeout=10)

        return {
            "status_code": response.status_code,
            "response_text": response.text,
            "cookies": response.cookies.get_dict()
        }

    except requests.exceptions.RequestException as e:
        return {
            "error": str(e)
        }


#指定地图
def set_current_map(ip: str):
    url = f"http://{ip}:8080/robot/api/v1/vehicleMap/set-current"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer;{login_request(ip)}",
    }

    payload = {
        "mapId": "new0418"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        print (response.json)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def set_manual_mode(ip: str) -> dict:
    url = f"http://{ip}:8080/robot/api/v1/vehicles/controls/manualMode"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer;{login_request(ip)}",
        "Content-Type": "application/json",
        "Origin": f"http://{ip}:8081",
        "Referer": f"http://{ip}:8081/",
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}

def set_auto_mode(ip: str) -> dict:
    url = f"http://{ip}:8080/robot/api/v1/vehicles/controls/autoMode"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer;{login_request(ip)}",
        "Content-Type": "application/json",
        "Origin": f"http://{ip}:8081",
        "Referer": f"http://{ip}:8081/",
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()

    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}



