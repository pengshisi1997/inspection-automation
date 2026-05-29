import paramiko
import time

class HSRSSH:
    def __init__(self):
        self.port = 22
        self.username = "youibot"
        self.password = "youibot"
        self.ssh = None
        self.host_ip = None

    def connect(self, host_ip):
        """建立SSH连接"""
        self.host_ip = host_ip
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(host_ip, self.port, self.username, self.password, timeout=10)
            return {'success': True, 'message': 'SSH连接成功'}
        except Exception as e:
            self.ssh = None
            return {'success': False, 'message': f'SSH连接失败: {str(e)}'}

    def execute_command(self, command, sudo=False):
        """执行命令"""
        if self.ssh is None:
            return {'success': False, 'message': 'SSH连接尚未建立'}
        
        try:
            if sudo:
                command = f"echo {self.password} | sudo -S {command}"
            
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            if error and 'password' not in error.lower():
                return {'success': False, 'message': f'命令执行错误: {error}', 'output': output}
            
            return {'success': True, 'message': '命令执行成功', 'output': output}
        except Exception as e:
            return {'success': False, 'message': f'命令执行失败: {str(e)}'}

    def get_pilot_version(self):
        """获取Pilot版本信息"""
        result = self.execute_command('sudo docker ps', sudo=True)
        if result['success']:
            output = result['output']
            youibot_containers = []
            for line in output.split('\n'):
                if 'youibot' in line.lower():
                    youibot_containers.append(line)
            if youibot_containers:
                result['youibot_info'] = youibot_containers
            else:
                result['youibot_info'] = ['未找到youibot相关容器']
        return result

    def close(self):
        """关闭SSH连接"""
        if self.ssh:
            try:
                self.ssh.close()
            except:
                pass
            self.ssh = None

    def test_connection(self, host_ip):
        """测试SSH连接"""
        result = self.connect(host_ip)
        if result['success']:
            version_result = self.get_pilot_version()
            self.close()
            return version_result
        return result

if __name__ == "__main__":
    hsr_ssh = HSRSSH()
    result = hsr_ssh.test_connection("192.168.16.152")
    print(result)