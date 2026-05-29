import requests
from requests.auth import HTTPDigestAuth
import tkinter as tk
from PIL import Image, ImageTk
import io

# 配置（拆分IP和端口，更清晰且避免拼接错误）
DEVICE_IP = "192.168.16.64"  # 仅IP地址，不含端口
DEVICE_PORT = 8083           # 单独指定端口
USER = "admin"
PWD = "robot2020"
CHANNEL = "101"  # 主码流（子码流用102，按需调整）
REFRESH_INTERVAL = 1000  # 刷新间隔（毫秒）

# 拼接URL（重点：端口要放在IP后，格式为 http://IP:端口/...）
URL = f"http://{DEVICE_IP}:{DEVICE_PORT}/ISAPI/Streaming/channels/{CHANNEL}/picture"

class CameraViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("海康相机实时图像")
        self.root.geometry("800x600")
        
        # 创建标签用于显示图像
        self.label = tk.Label(root)
        self.label.pack(fill=tk.BOTH, expand=True)
        
        # 创建状态标签
        self.status_var = tk.StringVar()
        self.status_var.set("初始化中...")
        self.status_label = tk.Label(root, textvariable=self.status_var, bg="lightgray")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 开始刷新图像
        self.update_image()
    
    def update_image(self):
        try:
            # 抓图（添加verify=False，解决部分设备证书问题）
            resp = requests.get(
                URL,
                auth=HTTPDigestAuth(USER, PWD),
                timeout=10,
                verify=False  # 海康设备常需关闭SSL验证，否则可能报错
            )

            # 处理响应
            if resp.status_code == 200:
                # 将响应内容转换为图像
                image_data = io.BytesIO(resp.content)
                image = Image.open(image_data)
                
                # 调整图像大小以适应窗口
                window_width = self.root.winfo_width()
                window_height = self.root.winfo_height() - 30  # 减去状态栏高度
                
                if window_width > 0 and window_height > 0:
                    # 保持宽高比
                    image.thumbnail((window_width, window_height), Image.Resampling.LANCZOS)
                
                # 转换为Tkinter可用的图像格式
                photo = ImageTk.PhotoImage(image)
                
                # 更新标签显示
                self.label.config(image=photo)
                self.label.image = photo  # 保持引用，防止垃圾回收
                
                # 更新状态
                self.status_var.set("✅ 图像获取成功")
            else:
                self.status_var.set(f"❌ 抓图失败：状态码 {resp.status_code}")

        except requests.exceptions.ConnectTimeout:
            self.status_var.set("❌ 连接超时：请检查设备IP/端口是否正确，或网络是否通")
        except requests.exceptions.ConnectionError:
            self.status_var.set("❌ 连接失败：请确认设备在线，且8083端口已开放")
        except Exception as e:
            self.status_var.set(f"❌ 未知错误：{str(e)}")
        finally:
            # 定时刷新
            self.root.after(REFRESH_INTERVAL, self.update_image)

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraViewer(root)
    root.mainloop()