import paramiko
import json
import time
import threading

class Ligit:
    def __init__(self):
        self.port = 22  # SSH默认端口
        self.username = "youibot"
        self.password = "youibot"
        self.serial_port = "/dev/ttyACM1"
        self.baudrate = 9600
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
    port = '/dev/ttyACM1'
    baudrate = 9600
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

    def execute_serial_command(self, host_ip, hex_command):
        self.connect(host_ip)
        self.upload_script(hex_command)
        return self.execute_remote_script()
    
    def get_fan_board_temperature(self, host_ip):
        """获取风扇板温度"""
        print("开始执行风扇板温度查询")
        
        # 发送01 03 00 00 00 01 84 0A命令查询风扇板温度
        print("\n=== 查询风扇板温度 ===")
        print("正在发送命令: 01 03 00 00 00 01 84 0A")
        result = self.execute_serial_command(host_ip, "01 03 00 00 00 01 84 0A")
        
        print("\n=== 风扇板温度查询结果 ===")
        print(f"返回数据: {result}")
        
        # 解析温度数据
        temperature = None
        if result and isinstance(result, dict):
            for cmd, response in result.items():
                if response:
                    hex_list = response.split()
                    if len(hex_list) >= 3:
                        # 提取倒数第三位
                        target_hex = hex_list[-3]
                        try:
                            # 转换为10进制并减去40
                            temp_decimal = int(target_hex, 16)
                            temperature = temp_decimal - 40
                            print(f"\n=== 温度解析结果 ===")
                            print(f"原始HEX数据: {response}")
                            print(f"提取的HEX值: {target_hex}")
                            print(f"10进制值: {temp_decimal}")
                            print(f"最终温度: {temperature} ℃")
                        except Exception as e:
                            print(f"解析温度失败: {e}")
        
        print("\n全部结束")
        
        return f"{temperature} ℃" if temperature is not None else None

if __name__ == "__main__":
    ssh_robot = Ligit()
    # 传入IP，获取风扇板温度
    temperature = ssh_robot.get_fan_board_temperature("192.168.17.160")
    # 打印返回结果
    print("\n=== 返回结果 ===")
    if temperature is not None:
        print(f"风扇板温度: {temperature} ℃")
    else:
        print("无法获取温度数据")
