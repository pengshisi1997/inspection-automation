import paramiko
import json
import time
import threading

class Ligit:
    def __init__(self):
        self.port = 22  # SSH默认端口
        self.username = "youibot"
        self.password = "youibot"
        self.serial_port = "/dev/ttyS0"
        self.baudrate = 115200
        self.timeout = 2
        self.remote_path = '/home/youibot/tmp.py'
        self.ssh = None

    def generate_script_content(self, hex_command):
        return f'''# -*- coding: utf-8 -*-
        
import serial
import time
import json

def hex_to_bytes(hex_str):
    hex_str = hex_str.replace(' ', '')
    return bytes(bytearray.fromhex(hex_str))

def main():
    port = '/dev/ttyS0'  # Change to ttyS0
    baudrate = 115200
    timeout = 2
    responses = {{}}

    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("打开串行端口 {{}}，波特率 {{}}".format(port, baudrate))
    except serial.SerialException as e:
        print("无法打开串行端口: {{}}".format(e))
        print(json.dumps(responses))
        return

    try:
        # 解析hex命令
        hex_data = hex_to_bytes("{hex_command}")

        ser.write(hex_data)
        print("发送数据 (hex): {{}}".format("{hex_command}"))
        
        # 3秒内多次尝试读取数据
        start_time = time.time()
        data_received = b''
        while time.time() - start_time < 3:
            time.sleep(0.1)
            data = ser.read(ser.inWaiting())
            if data:
                data_received += data
        
        if data_received:
            hex_response = ' '.join(['{{:02X}}'.format(ord(b)) for b in data_received])
            print("接收到的数据 (hex): {{}}".format(hex_response))
            responses["{hex_command}"] = hex_response
        else:
            print("未接收到数据")
            responses["{hex_command}"] = None

    except KeyboardInterrupt:
        print("程序终止")

    finally:
        try:
            ser.close()
        except:
            pass
        print("关闭串行端口")
        print(json.dumps(responses))

if __name__ == "__main__":
    main()
'''

    def connect(self, host_ip):
        self.host_ip = host_ip
        print(f"正在连接到主机: {host_ip}")
        if self.ssh is None:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.ssh.connect(host_ip, self.port, self.username, self.password)
                print(f"成功连接到主机: {host_ip}")
            except Exception as e:
                print(f"连接到远程主机失败: {e}")
                self.ssh = None

    def upload_script(self, hex_command):
        if self.ssh is None:
            print("SSH 连接尚未建立")
            return

        try:
            script_content = self.generate_script_content(hex_command)
            sftp = self.ssh.open_sftp()
            with sftp.file(self.remote_path, 'w') as remote_file:
                remote_file.write(script_content)
            sftp.close()
            print("脚本写入成功")
        except Exception as e:
            print(f"上传脚本失败: {e}")

    def execute_remote_script(self):
        try:
            if self.ssh is None:
                self.connect(self.host_ip)

            print(f"正在执行远程脚本: python {self.remote_path}")
            stdin, stdout, stderr = self.ssh.exec_command(f'python {self.remote_path}')
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            print("=== 远程执行输出 ===")
            if output:
                print(output)
            if error:
                print("错误信息:\n", error)
                return None
            print("=== 远程执行结束 ===")
            
            # 解析输出中的JSON数据
            import re
            json_match = re.search(r'\{[^}]*\}', output)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
            return None

        except Exception as e:
            print(f"脚本执行失败: {e}")
            return None

    def execute_lighting(self, host_ip, hex_command):
        self.connect(host_ip)
        self.upload_script(hex_command)
        return self.execute_remote_script()
    
    def get_ultrasonic_data(self, host_ip):
        """获取前后超声波数据"""
        print("开始执行超声波数据采集")
        
        def get_data_with_retry(command, max_retries=2):
            """带重试的数据获取函数"""
            for i in range(max_retries):
                print(f"\n=== 尝试获取数据 (第{i+1}次) ===")
                print(f"正在发送命令: {command}")
                data = self.execute_lighting(host_ip, command)
                
                # 提取值
                if data and isinstance(data, dict):
                    for cmd, value in data.items():
                        if value is not None:
                            return value
                
                if i < max_retries - 1:
                    print(f"数据为null，等待0.5秒后重试...")
                    time.sleep(0.5)
            
            return None
        
        # 获取前超声波数据
        front_value = get_data_with_retry("d0 02 B0")
        
        # 获取后超声波数据
        back_value = get_data_with_retry("d2 02 B0")
        
        # 整理结果
        result = {
            "前超声": front_value,
            "后超声": back_value
        }
        
        print("\n=== 超声波数据采集结果 ===")
        print(f"前超声波数据: {front_value}")
        print(f"后超声波数据: {back_value}")
        print("\n全部结束")
        
        return result

if __name__ == "__main__":
    ssh_robot = Ligit()
    # 只传入IP，获取前后超声波数据
    result = ssh_robot.get_ultrasonic_data("192.168.17.162")
    # 打印返回结果
    print("\n=== 返回结果 ===")
    print(f"完整结果: {result}")
