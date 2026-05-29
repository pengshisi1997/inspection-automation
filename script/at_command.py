import paramiko
import json
import time
import threading

class Ligit:
    def __init__(self):
        self.port = 22  # SSH默认端口
        self.username = "youibot"
        self.password = "youibot"
        self.serial_port = "/dev/ttyS3"
        self.baudrate = 115200
        self.timeout = 2
        self.remote_path = '/home/youibot/tmp.py'
        self.ssh = None

    def generate_script_content(self, at_command):
        return f'''# -*- coding: utf-8 -*-
        
import serial
import time
import json

def main():
    port = '/dev/ttyS3'  # Change to ttyS3
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
            except Exception as e:
                print(f"连接到远程主机失败: {e}")
                self.ssh = None

    def upload_script(self, at_command):
        if self.ssh is None:
            print("SSH 连接尚未建立")
            return

        try:
            script_content = self.generate_script_content(at_command)
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

            stdin, stdout, stderr = self.ssh.exec_command(f'python {self.remote_path}')
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if output:
                print(output)
            if error:
                print("错误信息:\n", error)
                return None

        except Exception as e:
            print(f"脚本执行失败: {e}")
            return None

    def execute_lighting(self, host_ip, at_command):
        self.connect(host_ip)
        self.upload_script(at_command)
        self.execute_remote_script()

if __name__ == "__main__":
    ssh_robot = Ligit()
    # 举例：调用时传入IP和AT命令
    ssh_robot.execute_lighting("192.168.16.152", "AT+setLampColor=1,1")
    print("全部结束")
