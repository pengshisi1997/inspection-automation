# -*- coding: utf-8 -*-
"""
HSR 车型防撞条检测（串口通信）
通过串口发送AT指令读取防撞条状态
"""

import paramiko
import json
import time

class HSRBumperReader:
    """HSR车型防撞条读取器"""
    
    def __init__(self, ip, username="youibot", password="youibot", timeout=5):
        self.ip = ip
        self.username = username
        self.password = password
        self.timeout = timeout
        self.port = 22
        self.serial_port = "/dev/ttyS3"
        self.remote_path = '/home/youibot/tmp_bumper.py'
        self.ssh = None

    def generate_script_content(self, at_command):
        return f'''# -*- coding: utf-8 -*-
        
import serial
import time
import json

def main():
    port = '/dev/ttyS3'
    baudrate = 115200
    timeout = 2

    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print("打开串行端口 {{}}，波特率 {{}}".format(port, baudrate))
    except serial.SerialException as e:
        print("无法打开串行端口: {{}}".format(e))
        return

    try:
        command = "{at_command}"
        responses = {{}}

        ser.write((command + '\\r\\n').encode('utf-8'))
        print("发送数据: {{}}".format(command))
        time.sleep(1)
        data_received = ser.read(ser.inWaiting()).decode('utf-8', errors='ignore').strip()
        if data_received:
            print("接收到的数据: {{}}".format(data_received))
            responses[command] = data_received
        else:
            print("未接收到数据")
            responses[command] = None

    except KeyboardInterrupt:
        print("程序终止")

    finally:
        ser.close()
        print("关闭串行端口")
        print(json.dumps(responses))

if __name__ == "__main__":
    main()
'''

    def connect(self, host_ip):
        self.host_ip = host_ip
        if self.ssh is None:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                self.ssh.connect(host_ip, self.port, self.username, self.password)
                print(f"SSH连接成功: {host_ip}")
            except Exception as e:
                print(f"连接到远程主机失败: {e}")
                self.ssh = None

    def upload_script(self, at_command):
        if self.ssh is None:
            print("SSH 连接尚未建立")
            return False

        try:
            script_content = self.generate_script_content(at_command)
            sftp = self.ssh.open_sftp()
            with sftp.file(self.remote_path, 'w') as remote_file:
                remote_file.write(script_content)
            sftp.close()
            print("脚本写入成功")
            return True
        except Exception as e:
            print(f"上传脚本失败: {e}")
            return False

    def execute_remote_script(self):
        try:
            if self.ssh is None:
                print("SSH连接尚未建立")
                return None

            stdin, stdout, stderr = self.ssh.exec_command(f'python {self.remote_path}')
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                print("错误信息:\n", error)
                return None
            
            return output

        except Exception as e:
            print(f"脚本执行失败: {e}")
            return None

    def get_emergency_stop_status(self, keyword):
        """
        发送AT+ReadEmgencyStopType指令，查询指定关键字的触发状态
        :param keyword: 关键字，如 'rearBumper', 'leftBumper', 'rightBumper', 'frontBumper'
        :return: True表示触发，False表示未触发
        """
        try:
            self.connect(self.ip)
            if self.ssh is None:
                print(f"SSH连接失败: {self.ip}")
                return False

            self.upload_script("AT+ReadEmgencyStopType")
            output = self.execute_remote_script()
            
            if output is None:
                print("执行脚本失败")
                return False

            print(f"原始输出: [{output}]")

            import re
            try:
                json_data = json.loads(output.strip())
                response = json_data.get("AT+ReadEmgencyStopType", "")
            except:
                response = output

            pattern = rf'(bit[\s:.]*{keyword}[\s:=]+)(\d)'
            match = re.search(pattern, response, re.IGNORECASE)
            
            if match:
                value = int(match.group(2))
                print(f"{keyword} 值为: {value}")
                return value == 1
            
            print(f"未找到 {keyword} 的值")
            return False
            
        except Exception as e:
            print(f"查询失败: {e}")
            return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        ip = sys.argv[1]
        keyword = sys.argv[2]
    else:
        ip = "192.168.16.53"
        keyword = "leftBumper"
    
    reader = HSRBumperReader(ip=ip, timeout=2)
    result = reader.get_emergency_stop_status(keyword)
    print(f"{keyword} 触发状态: {result}")