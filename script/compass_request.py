import os
import requests
import json
import pandas as pd
import numpy as np
import mysql.connector
import time
import paramiko


def ensure_remote_map_permissions(
    ip: str,
    remote_path: str = "/home/youibot/youibot_map/",
    username: str = "youibot",
    password: str = "youibot",
    port: int = 22,
):
    """上传地图前通过 SSH 放开机器人地图目录权限。"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=ip,
            port=port,
            username=username,
            password=password,
            timeout=10,
        )
        stdin, stdout, stderr = client.exec_command(
            f"sudo -S -p '' chmod 777 {remote_path}",
            timeout=15,
        )
        stdin.write(password + "\n")
        stdin.flush()
        exit_code = stdout.channel.recv_exit_status()
        error_text = stderr.read().decode("utf-8", errors="replace").strip()
        if exit_code != 0:
            raise RuntimeError(error_text or f"chmod 退出码: {exit_code}")
    finally:
        client.close()


def ensure_remote_image_directory(
    ip: str,
    remote_path: str = "/server/data/image/",
    username: str = "youibot",
    password: str = "youibot",
    port: int = 22,
):
    """云台任务前确保远程图片目录存在，并将权限设置为 777。"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=ip,
            port=port,
            username=username,
            password=password,
            timeout=10,
        )
        command = (
            f"if [ ! -d {remote_path} ]; then "
            f"sudo -S -p '' sh -c 'mkdir -p {remote_path} && chmod 777 {remote_path}'; "
            f"else sudo -S -p '' chmod 777 {remote_path}; "
            f"fi; test -d {remote_path} && "
            f"[ \"$(stat -c '%a' {remote_path})\" = \"777\" ]"
        )
        stdin, stdout, stderr = client.exec_command(command, timeout=15)
        stdin.write(password + "\n")
        stdin.flush()
        exit_code = stdout.channel.recv_exit_status()
        error_text = stderr.read().decode("utf-8", errors="replace").strip()
        if exit_code != 0:
            raise RuntimeError(error_text or f"创建目录退出码: {exit_code}")
    finally:
        client.close()


def get_yuntai_task(ip):

    # API URL
    url = f"http://{ip}:8080/api/v3/missionWorks/page?pageNum=1&pageSize=20&sort=create_time+desc"

    # Send GET request
    response = requests.get(url)

    # Parse JSON response
    if response.status_code == 200:
        data = response.json()
        
        # Filter tasks with name "云台"
        yuntai_tasks = [task for task in data['list'] if task['name'] == '云台']
        
        if yuntai_tasks:
            # Sort by createTime descending (though the API should already return sorted)
            yuntai_tasks.sort(key=lambda x: x['createTime'], reverse=True)
            
            # Get the most recent one
            most_recent = yuntai_tasks[0]
            return most_recent['id']
            
        else:
            print("没有找到名称为'云台'的任务")
    else:
        print(f"请求失败，状态码: {response.status_code}")


def get_temperature(ip):
    mission_work_id = get_yuntai_task(ip)
    if not mission_work_id:
        return None

    url = f"http://{ip}:8080/api/v3/missionWorks/{mission_work_id}/missionWorkActions?sort=create_time+desc"
    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        return None

    actions_data = response.json()

    def safe_load_json(raw):
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def normalize_image_paths(action):
        result_data = safe_load_json(action.get("resultData"))
        image_url = result_data.get("imageUrl", {})
        return {
            "1": image_url.get("binocular_1", {}).get("image_path"),
            "2": image_url.get("binocular_2", {}).get("image_path")
        }

    def parse_normal_temperature(action):
        result_data = safe_load_json(action.get("resultData"))
        thermometry_data = result_data.get("thermometryData", {})
        if not isinstance(thermometry_data, dict):
            thermometry_data = {}
        min_temp = thermometry_data.get("lowestTemp")
        max_temp = thermometry_data.get("highestTemp")
        return {
            "min_temperature": min_temp if isinstance(min_temp, (int, float)) else None,
            "max_temperature": max_temp if isinstance(max_temp, (int, float)) else None
        }

    def parse_expert_temperature(action):
        result_data = safe_load_json(action.get("resultData"))
        professional_temp_data = result_data.get("professional_temp_data", [])
        if not isinstance(professional_temp_data, list):
            professional_temp_data = []

        min_list = []
        avg_list = []
        max_list = []

        for item in professional_temp_data:
            min_temp = item.get("fMinTemperature")
            avg_temp = item.get("fAverageTemperature")
            max_temp = item.get("fMaxTemperature")
            if isinstance(min_temp, (int, float)) and min_temp != -100:
                min_list.append(min_temp)
            if isinstance(avg_temp, (int, float)) and avg_temp != -100:
                avg_list.append(avg_temp)
            if isinstance(max_temp, (int, float)) and max_temp != -100:
                max_list.append(max_temp)

        return {
            "min_temperature": min(min_list) if min_list else None,
            "average_temperature": round(sum(avg_list) / len(avg_list), 2) if avg_list else None,
            "max_temperature": max(max_list) if max_list else None
        }

    def find_action(name):
        for action in actions_data:
            if action.get("name") == name:
                return action
        return None

    ptz_action = find_action("ptz拍照")
    preset_action = find_action("预置点拍照")
    normal_temp_action = find_action("普通测温")
    expert_temp_action = find_action("专家测温")

    result = {
        "ptz_images": normalize_image_paths(ptz_action) if ptz_action else {"1": None, "2": None},
        "preset_images": normalize_image_paths(preset_action) if preset_action else {"1": None, "2": None},
        "normal_temperature": parse_normal_temperature(normal_temp_action) if normal_temp_action else {
            "min_temperature": None,
            "max_temperature": None
        },
        "expert_temperature": parse_expert_temperature(expert_temp_action) if expert_temp_action else {
            "min_temperature": None,
            "average_temperature": None,
            "max_temperature": None
        }
    }

    return result


def upload_map_folder(ip: str, local_folder_path: str, remote_base_path: str = "/home/youibot/youibot_map/"):
    if not os.path.isdir(local_folder_path):
        raise FileNotFoundError(f"文件夹不存在: {local_folder_path}")

    username = "youibot"
    password = "youibot"
    port = 22

    transport = None
    sftp = None

    try:
        transport = paramiko.Transport((ip, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        folder_name = os.path.basename(os.path.abspath(local_folder_path))
        remote_folder_path = remote_base_path.rstrip('/') + '/' + folder_name

        def mkdir_p(remote_path):
            parts = remote_path.split('/')
            current = ''
            for part in parts:
                if part:
                    current += '/' + part
                    try:
                        sftp.stat(current)
                    except FileNotFoundError:
                        sftp.mkdir(current)

        mkdir_p(remote_folder_path)

        for root, dirs, files in os.walk(local_folder_path):
            rel_path = os.path.relpath(root, local_folder_path)
            if rel_path == '.':
                remote_dir = remote_folder_path
            else:
                rel_path_unix = rel_path.replace('\\', '/')
                remote_dir = remote_folder_path.rstrip('/') + '/' + rel_path_unix
                mkdir_p(remote_dir)

            for file in files:
                local_file = os.path.join(root, file)
                remote_file = remote_dir.rstrip('/') + '/' + file
                sftp.put(local_file, remote_file)

        return True, f"文件夹上传成功: {local_folder_path} -> {remote_folder_path}"

    except Exception as e:
        return False, f"文件夹上传失败: {str(e)}"
    finally:
        if sftp:
            try:
                sftp.close()
            except:
                pass
        if transport:
            try:
                transport.close()
            except:
                pass


# 上传地图
def import_map_data(ip: str, local_path: str, model: str = None):
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"文件不存在: {local_path}")

    ensure_remote_map_permissions(ip)

    url = f"http://{ip}:8080/api/v3/export/importMapData"

    # 这些头可选；不要手动设置 Content-Type，让 requests 自动带 boundary
    headers = {
        "Accept": "*/*",
        "Origin": f"http://{ip}:8081",
        "Referer": f"http://{ip}:8081/",
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/145.0.0.0 Mobile Safari/537.36 Edg/145.0.0.0"
        ),
    }

    with open(local_path, "rb") as f:
        files = {
            # 字段名必须和抓包一致
            "multiPartFile": (os.path.basename(local_path), f, "application/json")
        }
        resp = requests.post(url, headers=headers, files=files, timeout=60)

    if model == "HSR":
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        hsr_map_folder = os.path.join(project_root, "map", "HSR", "7640a72f-53e5-11f1-9b5e-0242ac110002")
        if os.path.isdir(hsr_map_folder):
            success, msg = upload_map_folder(ip, hsr_map_folder)
            print(f"HSR地图文件夹上传: {msg}")
            if not success:
                raise RuntimeError(msg)

    return resp.status_code, resp.text

# 切换手自动模式
def set_mode(ip: str, mode: str):
    url = f"http://{ip}:8080/api/v3/vehicles/controls/{mode}"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json={}, timeout=2)
        print(f"响应内容: {response.text}")
    except Exception:
        # 忽略请求失败（超时或其他网络错误）
        print(f"[{ip}] 切换到 {mode} 失败，可能是网络问题")

#启用/禁用地图
def set_map(ip: str, mode: str, map_id: str):
    url = f"http://{ip}:8080/api/v3/AGVMaps/{map_id}/{mode}"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.put(url, headers=headers, json={}, timeout=2)
        print(f"响应内容: {response.text}")
    except Exception:
        # 忽略请求失败（超时或其他网络错误）
        print(f"[{ip}] 切换到 {mode} 失败，可能是网络问题")



# 同步地图
def sync_vehicle_map(ip: str, map_id: str):
    url = f"http://{ip}:8080/api/v3/vehicles/maps/sync"

    payload = {"agvMapId": map_id}

    response = requests.post(
        url,
        json=payload,
        timeout=10
    )

    response.raise_for_status()

    # 有些同步接口不返回 JSON
    if not response.text.strip():
        return {"success": True}

    try:
        return response.json()
    except ValueError:
        return {
            "success": True,
            "raw_response": response.text
        }

# 切换手自动模式
def auto_relocation(ip: str):
    url = f"http://{ip}:8080/api/v3/vehicles/maps/relocation/auto"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json={}, timeout=2)
        print(f"响应内容: {response.text}")
    except Exception:
        # 忽略请求失败（超时或其他网络错误）
        print(f"[{ip}] 切换到自动模式失败，可能是网络问题")

# 手动重定位
def manual_relocation(
    ip: str,
    init_x: float,
    init_y: float,
    init_angle: float,
    port: int = 8080,
    timeout: int = 5,
) -> None:
    """
    手动地图重定位
    成功：无返回
    失败：抛异常
    """
    url = f"http://{ip}:{port}/api/v3/vehicles/maps/relocation/manual"

    payload = {
        "init_x": init_x,
        "init_y": init_y,
        "init_angle": init_angle,
    }

    resp = requests.post(url, json=payload, timeout=timeout)

    # 非 2xx 直接抛异常
    resp.raise_for_status()
    time.sleep(2)

    auto_relocation(ip)

# 启动任务
def start_mission(ip: str, mission_id: str, timeout: int = 10):
    url = f"http://{ip}:8080/api/v3/missionWorks"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": f"http://{ip}:8081",
        "Pragma": "no-cache",
        "Referer": f"http://{ip}:8081/",
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/145.0.0.0 Mobile Safari/537.36 Edg/145.0.0.0"
        )
    }

    payload = {
        "missionId": mission_id
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=timeout
    )

    # 根据返回类型处理
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, response.text



# 上传任务
def upload_task(
    ip: str,
    mission_dir: str = "mission",
    progress_callback=None,
    lookup_batch_size: int = 2000,
    insert_batch_size: int = 1000,
):
    """
    该函数用于将当前路径中的 CSV 文件数据批量导入到 MySQL 数据库对应的表中。
    涉及的表包括 'mission'、'mission_action'、'mission_work'、'mission_work_action'。

    为避免每次动态测试都重复传输全部任务数据，会先按主键查询机器人中已存在
    的记录，只上传缺失行。progress_callback 用于向前端报告分表进度。
    """
    def report(message):
        if progress_callback:
            progress_callback(message)

    # 目标数据库连接信息
    connection = mysql.connector.connect(
        host=ip,
        user='root',
        password='root',
        database='youicompass'
    )

    # 表名列表
    tables = ['mission', 'mission_action', 'mission_work', 'mission_work_action', 'mission_action_parameter']

    cursor = None
    summary = {}

    try:
        cursor = connection.cursor()

        for table_index, table in enumerate(tables, start=1):
            # 拼接 CSV 文件的完整路径
            if os.path.isabs(mission_dir):
                csv_file_path = os.path.join(mission_dir, f"{table}.csv")
            else:
                current_path = os.getcwd()
                csv_file_path = os.path.join(current_path, mission_dir, f"{table}.csv")

            # 检查 CSV 文件是否存在
            if not os.path.exists(csv_file_path):
                print(f"文件 {csv_file_path} 不存在，跳过该表的导入。")
                summary[table] = {"total": 0, "uploaded": 0, "skipped": True}
                continue

            # 先只读取主键列。任务已导入过时，可以避免反复解析包含大段
            # parameters/result_data 的完整 CSV。
            try:
                id_df = pd.read_csv(
                    csv_file_path,
                    usecols=["id"],
                    dtype={"id": str},
                    keep_default_na=False,
                )
            except ValueError as e:
                raise RuntimeError(f"{csv_file_path} 缺少 id 列，无法增量导入") from e
            except Exception as e:
                raise RuntimeError(f"读取文件 {csv_file_path} 时出错：{e}") from e

            total_rows = len(id_df.index)
            report(f"上传任务（{table_index}/{len(tables)}）：检查 {table}，共 {total_rows} 条")

            if total_rows == 0:
                summary[table] = {"total": 0, "uploaded": 0, "skipped": True}
                continue

            # 分批查询本次 CSV 中已经存在的主键。相比重复发送整行数据，
            # UUID 查询的数据量很小，尤其能显著缩短 MS 大任务文件的重复导入。
            local_ids = id_df["id"].tolist()
            existing_ids = set()
            for start in range(0, total_rows, lookup_batch_size):
                id_batch = local_ids[start:start + lookup_batch_size]
                placeholders = ", ".join(["%s"] * len(id_batch))
                cursor.execute(
                    f"SELECT id FROM `{table}` WHERE id IN ({placeholders})",
                    tuple(id_batch),
                )
                existing_ids.update(str(row[0]) for row in cursor.fetchall())

            missing_ids = set(local_ids) - existing_ids
            missing_rows = sum(local_id in missing_ids for local_id in local_ids)

            if missing_rows == 0:
                print(f"{table} 已是最新，跳过 {total_rows} 条重复数据")
                report(f"上传任务（{table_index}/{len(tables)}）：{table} 已是最新")
                summary[table] = {
                    "total": total_rows,
                    "uploaded": 0,
                    "skipped": True,
                }
                continue

            # 只有确实存在缺失记录时才加载完整数据。
            try:
                df = pd.read_csv(csv_file_path)
            except Exception as e:
                raise RuntimeError(f"读取文件 {csv_file_path} 时出错：{e}") from e
            df = df.replace({np.nan: None})
            missing_df = df.loc[df["id"].astype(str).isin(missing_ids)]

            # 生成插入 SQL 语句
            value_placeholders = ", ".join(["%s"] * len(df.columns))
            columns = ", ".join(f"`{column}`" for column in df.columns)
            sql = f"INSERT IGNORE INTO `{table}` ({columns}) VALUES ({value_placeholders})"

            # 将 DataFrame 数据转换为列表形式
            data = missing_df.values.tolist()

            # 控制单次数据包大小，并按实际完成量更新页面进度。
            for start in range(0, missing_rows, insert_batch_size):
                batch = data[start:start + insert_batch_size]
                cursor.executemany(sql, batch)
                completed = min(start + len(batch), missing_rows)
                percent = int(completed * 100 / missing_rows)
                report(
                    f"上传任务（{table_index}/{len(tables)}）："
                    f"{table} {completed}/{missing_rows}（{percent}%）"
                )

            connection.commit()
            print(f"{table} 数据库增量导入成功，新增 {missing_rows}/{total_rows} 条")
            summary[table] = {
                "total": total_rows,
                "uploaded": missing_rows,
                "skipped": False,
            }

    except mysql.connector.Error as err:
        connection.rollback()
        raise RuntimeError(f"数据库连接或操作出错：{err}") from err
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        connection.close()

    report("上传任务完成")
    return summary


# 停止所有控制
def stop_all_tasks(ip, timeout=10):
    url = f"http://{ip}:8080/api/v3/missionWorks/all/controls/stop"
    return requests.post(url, timeout=timeout)


if __name__ == "__main__":
    # code, text = import_map_data("192.168.16.22", r"map\MS-LH.json")
    # print("status:", code)
    # print("resp:", text)

    # set_mode("192.168.16.22", "manualMode")
    # set_mode("192.168.16.22", "autoMode")
    # set_map("192.168.16.22", "enable")
    # set_map("192.168.16.22", "disable")
    # designated_map("192.168.16.22")
#     result = sync_vehicle_map(
#     ip="192.168.16.22",
#     map_id="1033a265-b2e3-11f0-822a-0242ac110002"
# )
    # result = manual_vehicle_map_relocation(ip="192.168.16.22",init_x=14.7,init_y=25.3,init_angle=0.074)
    # status, data = start_mission(
    #     ip="192.168.16.22",
    #     mission_id="364c49c2-442e-4d95-9acd-730b1c44d772"
    # )
    # print(status)
    # print(data)
    # download_task("192.168.16.22")
    # upload_task("192.168.16.22")
    get_temperature("192.168.16.64")
