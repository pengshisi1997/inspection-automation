"""
优艾智合 YOUICompass AGV 摇杆控制模拟脚本
通过 WebSocket 控制机器人移动

协议分析结果：
  - 通信方式：WebSocket
  - WebSocket 地址：ws://192.168.16.177:8080/agv/manual（手动控制专用通道）
  - 控制指令格式：{"code":"MOVE","data":{"sign":<timestamp>,"vx":0,"vy":0,"vtheta":<角速度>}}
    vx:     前后速度（正=前进，负=后退），范围约 -0.8 ~ 0.8
    vy:     左右速度（一般不用），范围约 -0.8 ~ 0.8  
    vtheta: 旋转角速度（正=左转，负=右转），范围约 -0.8 ~ 0.8
  - 开始控制：{"code":"MOVE","data":{"type":"start","sign":<timestamp>}}
  - 停止控制：{"code":"MOVE","data":{"type":"end","sign":<timestamp>}}
  - 发送频率：约 50ms/次（每秒 20 次）
"""

import asyncio
import websockets
import json
import time
import sys


class AGVController:
    """优艾智合 AGV WebSocket 控制器"""

    # WebSocket 地址（手动控制专用通道）
    WS_URL = "ws://192.168.16.177:8080/agv/manual"

    # 速度范围
    MAX_VX = 0.8       # 前后最大速度
    MAX_VY = 0.8       # 左右最大速度
    MAX_VTHETA = 0.8   # 旋转最大角速度

    # 发送频率（毫秒）
    SEND_INTERVAL = 0.05  # 50ms = 20Hz

    def __init__(self, ws_url=None):
        self.ws_url = ws_url or self.WS_URL
        self.ws = None
        self.sign = int(time.time() * 1000)
        self._running = False

    async def connect(self):
        """连接 WebSocket"""
        print(f"连接 WebSocket: {self.ws_url}")
        try:
            self.ws = await websockets.connect(self.ws_url, ping_interval=None)
            print("WebSocket 连接成功！")

            # 启动接收消息的异步任务
            asyncio.create_task(self._receive_loop())
            return True
        except Exception as e:
            print(f"WebSocket 连接失败: {e}")
            return False

    async def _receive_loop(self):
        """后台接收消息"""
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                code = data.get("code", "")
                # 只打印关键消息，避免刷屏
                if code not in ("AGVSTATUS", "LASERDATA"):
                    print(f"  [收到] {code}: {json.dumps(data.get('data', {}), ensure_ascii=False)[:200]}")
        except websockets.ConnectionClosed:
            print("WebSocket 连接已断开")

    def _move_msg(self, vx=0, vy=0, vtheta=0):
        """构建 MOVE 指令"""
        return json.dumps({
            "code": "MOVE",
            "data": {
                "sign": self.sign,
                "vx": vx,
                "vy": vy,
                "vtheta": vtheta
            }
        })

    async def start_control(self):
        """开始控制（摇杆按下）"""
        self.sign = int(time.time() * 1000)
        msg = json.dumps({"code": "MOVE", "data": {"type": "start", "sign": self.sign}})
        await self.ws.send(msg)
        print(f"[控制开始] sign={self.sign}")

    async def stop_control(self):
        """停止控制（摇杆释放）"""
        msg = json.dumps({"code": "MOVE", "data": {"type": "end", "sign": self.sign}})
        await self.ws.send(msg)
        print(f"[控制停止] sign={self.sign}")

    async def send_move(self, vx=0, vy=0, vtheta=0):
        """发送单次移动指令"""
        msg = self._move_msg(vx, vy, vtheta)
        await self.ws.send(msg)

    async def move_continuous(self, vx=0, vy=0, vtheta=0, duration=2.0):
        """
        持续发送移动指令
        
        参数:
            vx:      前后速度（正=前进，负=后退）
            vy:      左右速度
            vtheta:  旋转角速度（正=左转，负=右转）
            duration: 持续时间（秒）
        """
        self._running = True
        print(f"[移动] vx={vx}, vy={vy}, vtheta={vtheta}, 持续 {duration}s")

        await self.start_control()
        start = time.time()

        while time.time() - start < duration and self._running:
            await self.send_move(vx, vy, vtheta)
            await asyncio.sleep(self.SEND_INTERVAL)

        await self.stop_control()
        # 发送停止指令（速度归零）
        await self.send_move(0, 0, 0)
        print("[停止]")

    async def stop(self):
        """停止持续移动"""
        self._running = False

    async def forward(self, speed=0.8, duration=2.0):
        """前进"""
        print(f"前进 {duration}s，速度 {speed}")
        await self.move_continuous(vx=speed, duration=duration)

    async def backward(self, speed=0.8, duration=2.0):
        """后退"""
        print(f"后退 {duration}s，速度 {speed}")
        await self.move_continuous(vx=-speed, duration=duration)

    async def rotate_left(self, speed=0.8, duration=2.0):
        """左转"""
        print(f"左转 {duration}s，速度 {speed}")
        await self.move_continuous(vtheta=speed, duration=duration)

    async def rotate_right(self, speed=0.8, duration=2.0):
        """右转"""
        print(f"右转 {duration}s，速度 {speed}")
        await self.move_continuous(vtheta=-speed, duration=duration)

    async def disconnect(self):
        """断开连接"""
        if self.ws:
            await self.ws.close()
            print("WebSocket 已断开")


async def demo():
    """演示：连接 AGV 并执行一系列动作"""
    agv = AGVController()

    # 连接
    if not await agv.connect():
        return

    try:
        # === 示例动作 ===
        
        # 1. 右转 2 秒
        await agv.rotate_right(speed=0.8, duration=2.0)
        await asyncio.sleep(0.5)

        # 2. 左转 2 秒
        await agv.rotate_left(speed=0.8, duration=2.0)
        await asyncio.sleep(0.5)

        # 3. 前进 1 秒
        await agv.forward(speed=0.5, duration=1.0)
        await asyncio.sleep(0.5)

        # 4. 后退 1 秒
        await agv.backward(speed=0.5, duration=1.0)

        print("\n演示完成！")

    except KeyboardInterrupt:
        print("\n用户中断，停止移动...")
        await agv.stop()
    finally:
        await agv.disconnect()


async def interactive():
    """交互模式：键盘控制 AGV"""
    import msvcrt

    agv = AGVController()
    if not await agv.connect():
        return

    print("\n" + "="*50)
    print("  交互式 AGV 控制")
    print("  W/↑ = 前进   S/↓ = 后退")
    print("  A/← = 左转   D/→ = 右转")
    print("  空格 = 停止   Q = 退出")
    print("="*50 + "\n")

    # 后台持续发送移动指令
    current_vx, current_vy, current_vtheta = 0, 0, 0
    moving = False

    async def send_loop():
        nonlocal moving
        while True:
            if moving:
                await agv.send_move(current_vx, current_vy, current_vtheta)
            await asyncio.sleep(agv.SEND_INTERVAL)

    send_task = asyncio.create_task(send_loop())

    try:
        while True:
            # 检查是否有按键
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8', errors='ignore').lower()

                if key in ('w', '\xe0'):  # 上箭头是两个字节
                    if key == '\xe0':
                        msvcrt.getch()  # 读取第二个字节
                    current_vx, current_vy, current_vtheta = 0.5, 0, 0
                    moving = True
                    print("[前进]")

                elif key == 's':
                    current_vx, current_vy, current_vtheta = -0.5, 0, 0
                    moving = True
                    print("[后退]")

                elif key == 'a':
                    current_vx, current_vy, current_vtheta = 0, 0, 0.8
                    moving = True
                    print("[左转]")

                elif key == 'd':
                    current_vx, current_vy, current_vtheta = 0, 0, -0.8
                    moving = True
                    print("[右转]")

                elif key == ' ':
                    moving = False
                    current_vx = current_vy = current_vtheta = 0
                    await agv.send_move(0, 0, 0)
                    print("[停止]")

                elif key == 'q':
                    print("[退出]")
                    break

            await asyncio.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        moving = False
        send_task.cancel()
        await agv.disconnect()


if __name__ == "__main__":
    # 安装依赖：pip install websockets
    import os
    os.system("pip install websockets -q 2>nul")

    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        # 交互模式：python agv_control.py -i
        asyncio.run(interactive())
    else:
        # 演示模式
        asyncio.run(demo())
