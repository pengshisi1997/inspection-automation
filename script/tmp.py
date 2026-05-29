def check_obstacle_avoidance_success(self):
    """检查避障任务是否成功
    成功条件：线速度为0，x坐标17到18之间，y坐标9-10之间
    """
    url = f"http://{self.ip}:8080/api/v3/vehicles"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # 提取速度和位置信息
            speed_vx = data.get("defaultVehicleStatus", {}).get("speed", {}).get("speed_vx", 0)
            pos_x = data.get("defaultVehicleStatus", {}).get("position", {}).get("pos_x", 0)
            pos_y = data.get("defaultVehicleStatus", {}).get("position", {}).get("pos_y", 0)
            
            print(f"当前状态 - 线速度: {speed_vx}, x坐标: {pos_x}, y坐标: {pos_y}")
            
            # 检查成功条件
            if abs(speed_vx) < 0.01 and 16.5 <= pos_x <= 18.5 and 9 <= pos_y <= 11:
                compass_request.stop_all_tasks(self.ip)
                print("避障任务成功！")
                return True
        return False
    except Exception as e:
        print(f"检查避障状态时出错: {e}")
        return False