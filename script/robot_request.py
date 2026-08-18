import requests
import os
import csv
from datetime import datetime

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
    payload = {"userName": "admin","password": "admin"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        token = data.get("data", {}).get("token")
        return token
    except requests.exceptions.RequestException:
        return None
    except ValueError:
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


def get_environment_data(ip: str):
    """获取TW机型的环境数据（温度、湿度等）"""
    vehicles = get_vehicles(ip)
    if vehicles and "data" in vehicles and "environment" in vehicles["data"]:
        return vehicles["data"]["environment"]
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

    reload_agv_maps(ip)

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
def set_current_map(ip: str, map_id: str = "new0418"):
    url = f"http://{ip}:8080/robot/api/v1/vehicleMap/set-current"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer;{login_request(ip)}",
    }

    payload = {
        "mapId": map_id
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        print (response.json)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

#设置手动模式
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

#设置自动模式
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

#手动重定位
def manual_relocation(ip, init_x, init_y, init_angle):
    url = f"http://{ip}:8080/robot/api/v1/vehicles/controls/manualRelocation"

    headers = {
        "Authorization": f"Bearer;{login_request(ip)}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }

    payload = {
        "init_x": init_x,
        "init_y": init_y,
        "init_angle": init_angle
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }


#自动重定位
def auto_relocation(ip):
    url = f"http://{ip}:8080/robot/api/v1/vehicles/controls/autoRelocation"

    headers = {
        "Authorization": f"Bearer;{login_request(ip)}",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        # 有些接口返回空body
        if response.text:
            try:
                return response.json()
            except ValueError:
                return response.text
        else:
            return {
                "success": True,
                "status_code": response.status_code
            }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

#创建任务
def create_mission(ip, missionName, model_type="EX"):
    # 根据机型从对应的 mission_model.csv 读取任务配置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "..", "mission", model_type, "mission_model.csv")

    device_list = ""
    device_level = "2"
    priority = 4

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("mission_name") == missionName:
                    device_list = row.get("device_list", "")
                    device_level = row.get("device_level", "2")
                    priority = int(row.get("priority", 4))
                    print(f"[create_mission] 从CSV读取到任务配置: missionName={missionName}, device_list={device_list}, device_level={device_level}, priority={priority}")
                    break
            else:
                print(f"[create_mission] 警告: 未在CSV中找到 missionName={missionName} 的配置，将使用默认值")
    except (FileNotFoundError, IOError):
        print(f"[create_mission] 警告: CSV文件不存在或无法读取: {csv_path}")

    url = f"http://{ip}:8080/robot/api/v1/mission"
    headers = {
        "Authorization": f"Bearer;{login_request(ip)}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*"
    }

    payload = {
        "missionName": missionName,
        "type": "1",
        "deviceList": device_list,
        "deviceLevel": device_level,
        "priority": priority,
        "missionType": "FREQ_CREATE",
        "fixedStartTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def stop_all_tasks(ip, timeout=10):
    url = f"http://{ip}:8080/robot/api/v1/missionPlan/stopAll"

    headers = {
        "Authorization": f"Bearer;{login_request(ip)}",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        response = requests.put(
            url,
            headers=headers,
            timeout=timeout
        )

        response.raise_for_status()

        # 有些接口返回空body
        if response.text:
            try:
                return response.json()
            except ValueError:
                return response.text
        else:
            return {
                "success": True,
                "status_code": response.status_code
            }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def is_task_running(ip: str, mission_name: str) -> bool:
    """查询指定任务名是否有正在运行的任务"""
    url = f"http://{ip}:8080/robot/api/v1/missionPlan/page"
    params = {
        "pageSize": 10,
        "pageNum": 1,
        "missionName": mission_name,
        "missionType": "",
        "status": "",
        "endExecuteTime": "",
        "startExecuteTime": ""
    }
    headers = {
        "Authorization": f"Bearer;{login_request(ip)}",
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache",
        "Origin": f"http://{ip}:8081",
        "Referer": f"http://{ip}:8081/",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        task_list = data.get("data", {}).get("list", [])
        for task in task_list:
            if task.get("status") in ["RUNNING", "CREATED"]:
                print(f"任务 {mission_name} 正在运行")
                return True
        print(f"任务 {mission_name} 未运行")
        return False
    except requests.exceptions.RequestException:
        return False
    except ValueError:
        return False
# set_auto_mode()


# set_current_map("192.168.16.200")

# upload_agv_map("192.168.16.200")
# reload_agv_maps("192.168.16.200")


# vehicles = get_vehicles("192.168.16.201")
# print(vehicles["data"]["environment"])

# print(vehicles["data"])



# create_mission("192.168.16.232", "沟壑")
# 示例调用
if __name__ == "__main__":
    # create_mission("192.168.16.232", "沟壑")
    # is_task_running("192.168.16.232", "沟壑")
    stop_all_tasks("192.168.16.232")
    pass
