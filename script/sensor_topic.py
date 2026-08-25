import paramiko
import time
import re
import multiprocessing
import sys
import os

# 添加脚本所在目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tw_chaosheng import Ligit
from tw_fengshanban import Ligit as FengshanbanLigit
from robot_request import get_environment_data

class RosTopicReader:
    """ROS话题数据读取器"""
    
    def __init__(self, ip, model=None, username='youibot', password='youibot'):
        """初始化读取器
        
        Args:
            ip: 目标设备的IP地址
            model: 机型
            username: SSH用户名
            password: SSH密码
        """
        self.ip = ip
        self.model = model
        self.username = username
        self.password = password
        
        # 根据机型决定话题列表
        if self.model == 'TW':
            # TW机型只包含必要话题
            self.topics = [
                ("/ks114_sensor/ks114_data", "ks114_sensor"),
                ("/imu_data", "imu_data"),
                ("/odom", "odom")
            ]
        else:
            # 其他机型
            self.topics = [
                ("/ks114_sensor/ks114_data", "ks114_sensor"),
                ("/imu_data", "imu_data"),
                ("/sensors/encoder", "encoder"),
                ("/odom", "odom")
            ]
            # 只有当model明确不是MS时才包含tfmini_sensor话题
            if self.model != 'MS':
                self.topics.append(("/tfmini_sensor/tfmini_data", "tfmini_sensor"))
            # MR机型添加噪声传感器和气体传感器
            if self.model == 'MR':
                self.topics.append(("/byz06_sensor/byz06_data", "byz06_sensor"))
                self.topics.append(("/fs00802_sensor/fs00802_data", "fs00802_sensor"))
    
    def _get_single_topic_data(self, topic_info):
        """单个进程获取单个话题的数据"""
        topic, key, ip, username, password = topic_info
        
        # 如果是TW机型且是ks114_sensor话题，从tw_chaosheng.py获取数据
        if self.model == 'TW' and key == 'ks114_sensor':
            try:
                ssh_robot = Ligit()
                result = ssh_robot.get_ultrasonic_data(ip)
                print(f"  {key} 数据获取成功: {result}")
                return (key, result)
            except Exception as e:
                print(f"  {key} 数据获取失败: {e}")
                return (key, None)
        
        # 其他情况使用原有方法
        try:
            # 创建 SSH 客户端
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=username, password=password, timeout=10)
            
            # 打开交互式 shell
            shell = client.invoke_shell()
            time.sleep(0.3)  # 等待 shell 准备就绪
            
            # 发送命令
            shell.send(f'rostopic echo {topic}\n')
            
            # 读取输出，直到获取到足够的数据
            output = ''
            start_time = time.time()
            while time.time() - start_time < 2:
                if shell.recv_ready():
                    output += shell.recv(2048).decode('utf-8', errors='ignore')
                    # 检查是否包含完整的数据块
                    if '---' in output:
                        break
                time.sleep(0.05)
            
            # 发送 Ctrl+C 终止命令
            shell.send('\x03')  # Ctrl+C
            time.sleep(0.5)
            
            # 解析数据
            data = self._parse_topic_data(topic, output)
            
            # 关闭连接
            shell.close()
            client.close()
            
            print(f"  {key} 数据获取成功: {data}")
            return (key, data)
            
        except Exception as e:
            print(f"  {key} 数据获取失败: {e}")
            # 尝试关闭连接
            if 'shell' in locals():
                try:
                    shell.close()
                except:
                    pass
            if 'client' in locals():
                try:
                    client.close()
                except:
                    pass
            return (key, None)
    
    def _read_cpu_hz(self):
        """读取 CPU 频率"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.ip, username=self.username, password=self.password, timeout=10)
            
            # 尝试使用 sysfs 获取实时 CPU 频率（更准确）
            stdin, stdout, stderr = client.exec_command('ls /sys/devices/system/cpu/ | grep "cpu[0-9]"')
            cpu_cores = stdout.read().decode().strip().split('\n')
            
            cpu_hz = []
            for core in cpu_cores:
                if core:
                    cmd = f'cat /sys/devices/system/cpu/{core}/cpufreq/cpuinfo_cur_freq'
                    stdin, stdout, stderr = client.exec_command(cmd)
                    freq = stdout.read().decode().strip()
                    if freq:
                        # 转换为 MHz
                        cpu_hz.append(float(freq) / 1000.0)
            
            # 如果 sysfs 方法失败，回退到 /proc/cpuinfo
            if not cpu_hz:
                stdin, stdout, stderr = client.exec_command('cat /proc/cpuinfo | grep "cpu MHz"')
                text = stdout.read().decode()
                matches = re.findall(r'cpu MHz\s*:\s*([0-9.]+)', text)
                cpu_hz = [float(x) for x in matches]
            
            client.close()
            
            print(f"  CPU 频率获取成功: {cpu_hz}")
            return cpu_hz
            
        except Exception as e:
            print(f"  CPU 频率获取失败: {e}")
            return None
    
    def _check_microphone(self):
        """检测拾音器（仅TW机型）
        通过 lsusb 命令检查是否有 PowerConf 设备
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # TW机型使用22端口，其他机型（EX）使用10022端口
            port = 22 if self.model == 'TW' else 10022
            client.connect(self.ip, port=port, username=self.username, password=self.password, timeout=10)
            
            # 执行 lsusb 命令
            stdin, stdout, stderr = client.exec_command('lsusb')
            output = stdout.read().decode()
            
            client.close()
            
            # 检查是否包含 PowerConf 关键字
            has_microphone = 'PowerConf' in output
            result = '检测到' if has_microphone else '未检测到'
            
            print(f"  拾音器检测结果: {result}")
            return has_microphone
            
        except Exception as e:
            print(f"  拾音器检测失败: {e}")
            return None
    
    def _parse_topic_data(self, topic, output):
        """解析不同话题的数据"""
        if "/ks114_sensor/ks114_data" in topic:
            return self._parse_ks114(output)
        elif "/tfmini_sensor/tfmini_data" in topic:
            return self._parse_tfmini(output)
        elif "/imu_data" in topic:
            return self._parse_imu(output)
        elif "/sensors/encoder" in topic:
            return self._parse_encoder(output)
        elif "/odom" in topic:
            return self._parse_odom(output)
        elif "/byz06_sensor/byz06_data" in topic:
            return self._parse_byz06(output)
        elif "/fs00802_sensor/fs00802_data" in topic:
            return self._parse_fs00802(output)
        return None
    
    def _parse_ks114(self, output):
        """解析 ks114 数据"""
        match = re.search(r'distance:\s*\[([0-9,\s]+)\]', output)
        if not match:
            return None
        nums = match.group(1).split(",")
        return [int(n.strip()) for n in nums]
    
    def _parse_tfmini(self, output):
        """解析 tfmini 数据"""
        match = re.search(r'distance:\s*\[([0-9,\s]+)\]', output)
        if not match:
            return None
        nums = match.group(1).split(",")
        return [int(n.strip()) for n in nums]
    
    def _parse_encoder(self, output):
        """解析 encoder 数据"""
        match = re.search(r'encoder:\s*\[([-0-9,\s]+)\]', output)
        if not match:
            match = re.search(r'data:\s*\[([-0-9,\s]+)\]', output)
        if not match:
            return None
        nums = match.group(1).split(",")
        return [int(n.strip()) for n in nums]
    
    def _parse_imu(self, output):
        """解析 imu 数据"""
        pattern = r'orientation:\s*\n\s*x:\s*([-0-9.e]+)\s*\n\s*y:\s*([-0-9.e]+)\s*\n\s*z:\s*([-0-9.e]+)\s*\n\s*w:\s*([-0-9.e]+)'
        match = re.search(pattern, output)
        if not match:
            return None
        return {
            "x": float(match.group(1)),
            "y": float(match.group(2)),
            "z": float(match.group(3)),
            "w": float(match.group(4))
        }
    
    def _parse_odom(self, output):
        """解析 odom 数据"""
        pattern = r'position:\s*\n\s*x:\s*([-0-9.e]+)\s*\n\s*y:\s*([-0-9.e]+)\s*\n\s*z:\s*([-0-9.e]+)'
        match = re.search(pattern, output)
        if not match:
            return None
        return {
            "x": float(match.group(1)),
            "y": float(match.group(2)),
            "z": float(match.group(3))
        }
    
    def _parse_byz06(self, output):
        """解析 byz06 噪声传感器数据"""
        match = re.search(r'noise_decibel:\s*([-0-9.e]+)', output)
        if not match:
            return None
        return float(match.group(1))
    
    def _parse_fs00802(self, output):
        """解析 fs00802 气体传感器数据，只获取 PM2_5 字段"""
        match = re.search(r'PM2_5:\s*([-0-9.e]+)', output)
        if not match:
            return None
        return float(match.group(1))
    
    def get_all_data(self):
        """获取所有话题的数据
        
        Returns:
            dict: 包含所有话题数据的字典
        """
        print("=== 获取所有话题数据 ===")
        start_time = time.time()
        
        result_dict = {}
        
        # 先尝试单进程方式（更可靠，特别是在Windows上）
        try:
            print("  使用单进程方式获取数据...")
            for topic, key in self.topics:
                print(f"  正在获取 {key} 数据...")
                key_result, data = self._get_single_topic_data((topic, key, self.ip, self.username, self.password))
                result_dict[key_result] = data
        except Exception as e:
            print(f"  单进程方式失败: {e}")
            import traceback
            print(f"  堆栈: {traceback.format_exc()}")
            
            # 如果单进程失败，尝试回退到多进程（仅在非Windows上）
            if sys.platform != 'win32':
                try:
                    print("  尝试使用多进程方式...")
                    # 准备进程参数
                    process_args = [(topic, key, self.ip, self.username, self.password) for topic, key in self.topics]
                    
                    # 创建进程池
                    with multiprocessing.Pool(processes=len(self.topics)) as pool:
                        # 并行执行
                        results = pool.map(self._get_single_topic_data, process_args)
                    
                    # 整理结果
                    result_dict = {key: data for key, data in results}
                except Exception as e2:
                    print(f"  多进程方式也失败: {e2}")
        
        # 读取 CPU 频率
        cpu_hz = self._read_cpu_hz()
        result_dict['cpu_hz'] = cpu_hz
        # TW机型不添加scan_1数据
        if self.model != 'TW':
            result_dict['scan_1'] = "大量数据"
        
        # TW机型添加环境数据
        if self.model == 'TW':
            try:
                env_data = get_environment_data(self.ip)
                if env_data:
                    result_dict.update(env_data)
                    print(f"  环境数据获取成功: {env_data}")
                else:
                    print("  环境数据获取失败")
            except Exception as e:
                print(f"  环境数据获取异常: {e}")
            
            # TW机型添加拾音器检测
            try:
                microphone_data = self._check_microphone()
                result_dict['microphone'] = microphone_data
            except Exception as e:
                print(f"  拾音器检测异常: {e}")
                result_dict['microphone'] = None
            
            # TW机型添加风扇板数据获取
            try:
                fan_robot = FengshanbanLigit()
                fan_data = fan_robot.get_fan_board_temperature(self.ip)
                result_dict['fan_board'] = fan_data
                print(f"  风扇板数据获取成功: {fan_data}")
            except Exception as e:
                print(f"  风扇板数据获取异常: {e}")
                result_dict['fan_board'] = None
        
        end_time = time.time()
        print(f"\n=== 数据获取完成 (耗时: {end_time - start_time:.2f}秒) ===")
        
        return result_dict

if __name__ == "__main__":

    # 使用示例 - TW机型
    print("\n\n=== TW机型测试 ===")
    reader_tw = RosTopicReader('192.168.16.200', model='TW')
    all_data_tw = reader_tw.get_all_data()
    
    print("\n=== 最终结果 (TW机型) ===")
    for key, value in all_data_tw.items():
        print(f"{key}: {value}")
    
    print("\n=== 完整字典 (TW机型) ===")
    print(all_data_tw)