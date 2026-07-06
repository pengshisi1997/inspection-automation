import socket
import json
import time
import os
import sys

# 引入全局路径配置
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.model_config import IMAGE_YUNTAI_DIR, TEST_RECORD_DIR, get_image_yuntai_dir, get_result_file_path


class MosPTZController:
    """
    MOS云台控制器类
    用于通过TCP协议与MOS云台通信
    """
    
    def __init__(self, host, port=18211):
        """
        初始化控制器
        
        Args:
            host: MOS服务器IP地址
            port: MOS服务器端口，默认为18211
        """
        self.host = host
        self.port = port
        self.STX = b'\x02'
        self.ETX = b'\x03'
        self.cmd = "11051".encode('ascii')
        self.status_cmd = "11053".encode('ascii')
        self.mos_status_cmd = "11056".encode('ascii')
        self.tail = "0000".encode('ascii')
    
    def build_data(self, operation_detail, target="visible", action_type="111"):
        """
        构建请求数据
        
        Args:
            operation_detail: 操作详情（任务名）
            target: 目标，默认为"visible"
            action_type: 动作类型，默认为"111"
        
        Returns:
            构建好的JSON数据
        """
        data = {
            "id": "1",
            "operation_type": "PTZCONTROL",
            "target": target,
            "operation_detail": operation_detail,
            "action_type": action_type,
            "PTZcontrol_params": {
                "channel_1": {
                    "camera_name": "visible",
                    "channel_type": 1,
                    "photo_action": False,
                    "video_action": False,
                    "temp_action": False,
                    "expert_temp_action": False,
                    "param_type": 1,
                    "setting_action": False,
                    "preset_action": False,
                    "params": {
                        "P": 150,
                        "T": 80,
                        "Z": 8,
                        "focus": 10000,
                        "iris": 200,
                        "brightness": 0,
                        "contrast": 0,
                        "saturation": 0,
                        "sharpness": 0,
                        "light_inhibit_switch": 0,
                        "focus_mode": 2,
                        "noise_mode": 0,
                        "noise_level": 0,
                        "spectral_level": 0,
                        "temporal_level": 0,
                        "defog_mode": 0,
                        "light_switch": 0,
                        "wiper_switch": 0,
                        "record_time": 0,
                        "preset_id": 1,
                        "waiting_time": 0
                    }
                },
                "channel_2": {
                    "camera_name": "visible",
                    "channel_type": 1,
                    "photo_action": True,
                    "video_action": False,
                    "temp_action": False,
                    "expert_temp_action": False,
                    "param_type": 1,
                    "setting_action": False,
                    "preset_action": False,
                    "params": {
                        "P": 0,
                        "T": 0,
                        "Z": 7,
                        "focus": 0,
                        "iris": 0,
                        "brightness": 0,
                        "contrast": 0,
                        "saturation": 0,
                        "sharpness": 0,
                        "light_inhibit_switch": 0,
                        "focus_mode": 0,
                        "noise_mode": 0,
                        "noise_level": 0,
                        "spectral_level": 0,
                        "temporal_level": 0,
                        "defog_mode": 0,
                        "light_switch": 0,
                        "wiper_switch": 0,
                        "record_time": 0,
                        "preset_id": 0,
                        "waiting_time": 0
                    }
                }
            }
        }
        return data
    
    def build_packet(self, json_str="", cmd=None):
        """
        按协议封包
        
        Args:
            json_str: JSON字符串，默认为空
            cmd: 命令编号，默认为None使用self.cmd
        
        Returns:
            封装好的数据包
        """
        cmd_to_use = cmd if cmd is not None else self.cmd
        packet = self.STX + cmd_to_use + json_str.encode('utf-8') + self.tail + self.ETX
        return packet
    
    def parse_response(self, resp):
        """
        解析返回数据
        
        Args:
            resp: 原始响应数据
        
        Returns:
            解析后的结果
        """
        if resp[0] == 0x02 and resp[-1] == 0x03:
            body = resp[1:-1]
            body = body[6:]  # 去掉前6位（命令编号）
            body = body[:-4]  # 去掉最后4位（0000）
            if body:
                try:
                    body_str = body.decode()
                    if not body_str.startswith('{'):
                        body_str = '{' + body_str
                    return json.loads(body_str)
                except:
                    return body.decode()
            return None
        return resp
    
    def send_request(self, operation_detail, timeout=10):
        """
        发送请求并获取响应
        
        Args:
            operation_detail: 操作详情（任务名）
            timeout: 超时时间，默认为10秒
        
        Returns:
            解析后的响应结果
        """
        data = self.build_data(operation_detail)
        json_str = json.dumps(data, separators=(',', ':'))
        packet = self.build_packet(json_str)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((self.host, self.port))
            s.sendall(packet)
            response = s.recv(4096)
            return self.parse_response(response)
    
    def query_task_status(self, timeout=10):
        """
        查询任务状态
        
        Args:
            timeout: 超时时间，默认为10秒
        
        Returns:
            解析后的任务状态
        """
        packet = self.build_packet(cmd=self.status_cmd)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((self.host, self.port))
            s.sendall(packet)
            response = s.recv(4096)
            return self.parse_response(response)
    
    def query_mos_status(self, timeout=10):
        """
        查询MOS集成状态（11056）
        
        Args:
            timeout: 超时时间，默认为10秒
        
        Returns:
            解析后的MOS状态
        """
        packet = self.build_packet(cmd=self.mos_status_cmd)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((self.host, self.port))
            s.sendall(packet)
            response = s.recv(4096)
            return self.parse_response(response)
    
    def save_temperature_data(self, max_temp, min_temp):
        """
        保存温度数据到 image_yuntai/SN_cewen.json
        
        Args:
            max_temp: 最高温度
            min_temp: 最低温度
        
        Returns:
            保存成功返回文件路径，失败返回 None
        """
        try:
            # 获取 SN 号
            sn_name = "UNKNOWN_SN"
            try:
                result_file = get_result_file_path(self.host)
                if os.path.exists(result_file):
                    with open(result_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sn = data.get("robot_info", {}).get("sn") or "UNKNOWN_SN"
                    sn = str(sn).strip()
                    for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                        sn = sn.replace(ch, "_")
                    sn_name = sn if sn else "UNKNOWN_SN"
            except Exception:
                pass
            
            # 创建 image_yuntai 目录（按IP分组）
            local_dir = get_image_yuntai_dir(self.host)
            
            # 构建文件路径
            temp_file = os.path.join(local_dir, f"{sn_name}_cewen.json")
            
            # 保存数据
            temp_data = {
                "max_temp": max_temp,
                "min_temp": min_temp
            }
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2)
            
            return temp_file
        except Exception as e:
            print(f"保存温度数据失败: {e}")
            return None
    
    def execute_and_poll_status(self, operation_detail, poll_interval=2, timeout=120, query_timeout=10):
        """
        执行任务并循环查询状态
        
        Args:
            operation_detail: 操作详情（任务名）
            poll_interval: 轮询间隔（秒），默认为2秒
            timeout: 总超时时间（秒），默认为30秒
            query_timeout: 单次查询超时时间（秒），默认为10秒
        
        Returns:
            识别到的路径（photo_path或video_path）或状态字典
        """
        # 特定任务名称列表，这些任务通过MOS状态查询来判断完成
        mos_status_tasks = ['light_PTZ', 'light_point', 'thermal_point', 'Manual_focusing', 'Auto_focusing']
        # 需要检查路径的任务列表
        path_check_tasks = ['light_video', 'thermal_photo', 'thermal_video', 'light_photo', 'thermal_Temperature']


        
        result = self.send_request(operation_detail, timeout=query_timeout)
        print("任务已发送:", result)
        
        start_time = time.time()
        path_found = False
        result_path = ""
        mos_ready = False
        temp_data = None  # 用于存储温度数据
        
        while time.time() - start_time < timeout:
            try:
                # 判断是否是需要检查路径的任务
                if operation_detail in path_check_tasks:
                    # 同时查询任务状态和MOS状态
                    task_status = self.query_task_status(timeout=query_timeout)
                    print("当前任务状态:", task_status)
                    
                    mos_status = self.query_mos_status(timeout=query_timeout)
                    print("当前MOS状态:", mos_status)
                    
                    # 检查数据是否已获取
                    if not path_found and isinstance(task_status, dict):
                        data = task_status.get("data", {})
                        ptz_control = data.get("PTZControl", {})
                        channel_1 = ptz_control.get("channel_1", {})
                        channel_2 = ptz_control.get("channel_2", {})
                        
                        if operation_detail == "light_video":
                            video_path = channel_1.get("video_path", "")
                            if video_path:
                                path_found = True
                                result_path = video_path
                                print("路径已获取:", result_path)
                        elif operation_detail == "thermal_photo":
                            photo_path = channel_2.get("photo_path", "")
                            if photo_path:
                                path_found = True
                                result_path = photo_path
                                print("路径已获取:", result_path)
                        elif operation_detail == "thermal_video":
                            video_path = channel_2.get("video_path", "")
                            if video_path:
                                path_found = True
                                result_path = video_path
                                print("路径已获取:", result_path)
                        elif operation_detail == "light_photo":
                            photo_path = channel_1.get("photo_path", "")
                            if photo_path:
                                path_found = True
                                result_path = photo_path
                                print("路径已获取:", result_path)
                        elif operation_detail == "thermal_Temperature":
                            # 处理温度测量任务
                            max_temp = None
                            min_temp = None
                            
                            # 检查 channel_2 的温度数据（根据示例响应）
                            if channel_2:
                                max_temp = channel_2.get("max_temp")
                                min_temp = channel_2.get("min_temp")
                            
                            # 也检查 HIK_Camera_TypeC 的数据（根据示例响应）
                            hik_type_c = ptz_control.get("HIK_Camera_TypeC", {})
                            if hik_type_c:
                                ch1 = hik_type_c.get("channel_1", {})
                                if ch1:
                                    if max_temp is None:
                                        max_temp = ch1.get("max_temp")
                                    if min_temp is None:
                                        min_temp = ch1.get("min_temp")
                            
                            # 如果获取到了温度数据
                            if max_temp is not None and min_temp is not None:
                                temp_data = (max_temp, min_temp)
                                path_found = True  # 用 path_found 表示数据已获取
                                print(f"温度数据已获取: 最高={max_temp}, 最低={min_temp}")
                    
                    # 检查MOS状态
                    if isinstance(mos_status, dict):
                        mos_data = mos_status.get("data", {})
                        mos_status_val = mos_data.get("status")
                        if mos_status_val == 2:
                            mos_ready = True
                            print("MOS已就绪")
                    
                    # 只有当数据已获取且MOS已就绪时，才认为任务完成
                    if path_found and mos_ready:
                        if operation_detail == "thermal_Temperature":
                            # 保存温度数据
                            if temp_data:
                                saved_file = self.save_temperature_data(temp_data[0], temp_data[1])
                                if saved_file:
                                    print(f"温度数据已保存到: {saved_file}")
                                    return saved_file
                            return temp_data
                        else:
                            print("路径已获取且MOS已就绪，任务完成")
                            return result_path
                
                # 判断是否是需要查询MOS状态的任务
                elif operation_detail in mos_status_tasks:
                    status = self.query_mos_status(timeout=query_timeout)
                    print("当前MOS状态:", status)
                    
                    if isinstance(status, dict):
                        data = status.get("data", {})
                        mos_status_val = data.get("status")
                        
                        # READY状态（值为2）表示任务结束
                        if mos_status_val == 2:
                            print("MOS已就绪，任务完成")
                            return status
                
                time.sleep(poll_interval)
            except Exception as e:
                print(f"查询状态时出错: {e}")
                time.sleep(poll_interval)
        
        print("查询超时")
        return None


if __name__ == "__main__":
    # 测试代码
    controller = MosPTZController("192.168.17.52")
    final_status = controller.execute_and_poll_status("thermal_photo")
    print("最终任务状态:", final_status)
