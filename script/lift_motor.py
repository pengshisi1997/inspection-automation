import requests
import json
import time


class LiftingPlatformController:
    """
    升降平台控制类
    初始化只需要传入机器人 IP
    调用 run() 即可完成：上升到100% → 下降到0%
    """

    def __init__(self, ip, rpm=500):
        self.ip = ip
        self.rpm = rpm
        self.url = f"http://{ip}:8080/api/v3/vehicles/devices/liftingPlatform/control"
        self.headers = {"Content-Type": "application/json"}

    def _move_to_height(self, height_percent):
        """
        内部方法：控制升降平台到指定高度
        """
        target_ticks = int(height_percent * 10)
        data = {
            "rpm": self.rpm,
            "target_ticks": target_ticks
        }

        try:
            response = requests.put(
                self.url,
                headers=self.headers,
                data=json.dumps(data),
                timeout=50
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "height_percent": height_percent,
                    "target_ticks": target_ticks,
                    "response": response.text,
                    "timestamp": time.time()
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "response": response.text,
                    "timestamp": time.time()
                }

        except requests.exceptions.Timeout:
            return {"status": "error", "message": "连接超时"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "连接失败"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
        except Exception as e:
            return {"status": "error", "message": f"未知错误: {str(e)}"}

    def run(self):
        """
        执行完整流程：
        1. 上升到 100%
        2. 等待
        3. 下降到 0%
        """
        print(f"[{self.ip}] 升降平台上升到 100%")
        result_up = self._move_to_height(100)
        print(result_up)

        time.sleep(2)  # 根据实际机械响应时间可调整

        print(f"[{self.ip}] 升降平台下降到 0%")
        result_down = self._move_to_height(0)
        print(result_down)

        print(f"[{self.ip}] 升降流程结束")

if __name__ == "__main__":
    controller = LiftingPlatformController("192.168.16.134")
    controller.run()