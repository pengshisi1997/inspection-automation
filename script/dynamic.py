import sys
import os
import time
import json
from datetime import datetime

import requests

# 添加脚本目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import compass_request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL = "MS"

# 引入全局路径配置
sys.path.insert(0, BASE_DIR)
from config.model_config import (
    DYNAMIC_TASK_EXECUTION,
    TEST_RECORD_DIR,
    get_image_yuntai_dir,
    get_result_file_path,
)


class InspectionAutomation:
    def __init__(self, ip, jixing, auto_initialize=True):
        self.ip = ip
        self.jixing = (jixing or DEFAULT_MODEL).strip()
        self.tasks = DYNAMIC_TASK_EXECUTION
        # 非定义机型回退使用MS动态任务配置
        if self.jixing not in self.tasks:
            self.jixing = DEFAULT_MODEL
        if auto_initialize:
            self.initialize()

    def _get_result_file_path(self):
        return get_result_file_path(self.ip)

    def _load_result_data(self):
        result_file = self._get_result_file_path()
        legacy_file = os.path.join(TEST_RECORD_DIR, f"{self.ip}.json")
        for file_path in (result_file, legacy_file):
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
        return {}

    def _resolve_model_file(self, base_dir, filename):
        model_path = os.path.join(BASE_DIR, base_dir, self.jixing, filename)
        if os.path.exists(model_path):
            return model_path
        return os.path.join(BASE_DIR, base_dir, filename)

    def _resolve_mission_dir(self):
        model_dir = os.path.join(BASE_DIR, "mission", self.jixing)
        if os.path.isdir(model_dir):
            return model_dir
        return os.path.join(BASE_DIR, "mission")

    def initialize(self, stop_event=None):
        """初始化操作，执行用户指定的代码"""
        map_file = self._resolve_model_file("map", "自动化测试.json")
        mission_dir = self._resolve_mission_dir()
        map_params = {
            "MS": "6e53131d-15fa-11f1-98fd-0242ac110002",
            "MR": "91b7a2a8-4f61-11f1-8ba3-0242ac110003",
            "HSR": "7640a72f-53e5-11f1-9b5e-0242ac110002"
        }
        map_id = map_params.get(self.jixing, map_params["MS"])
        relocation_params = {
            "MS": (22.08, 5.83, 1.51),
            "MR": (5.9, 15.3, 6.5),
            "HSR": (34.4, 14.9, 3.1)
        }
        init_x, init_y, init_angle = relocation_params.get(self.jixing, relocation_params["MS"])

        def report_task_upload_progress(message):
            self.save_task_status(
                None,
                current_step=message,
                step_status="running",
                init_steps=init_steps,
                error="",
            )

        steps = [
            ("切换手动模式", lambda: compass_request.set_mode(self.ip, "manualMode")),
            ("导入地图", lambda: compass_request.import_map_data(self.ip, map_file, model=self.jixing)),
            (
                "上传任务",
                lambda: compass_request.upload_task(
                    self.ip,
                    mission_dir=mission_dir,
                    progress_callback=report_task_upload_progress,
                ),
            ),
            ("启用地图", lambda: compass_request.set_map(self.ip, "enable", map_id)),
            ("同步车辆地图", lambda: compass_request.sync_vehicle_map(self.ip, map_id)),
            ("手动重定位", lambda: compass_request.manual_relocation(ip=self.ip, init_x=init_x, init_y=init_y, init_angle=init_angle)),
            ("切换自动模式", lambda: compass_request.set_mode(self.ip, "autoMode"))
        ]
        init_steps = []
        for step_name, action in steps:
            if stop_event and stop_event.is_set():
                raise RuntimeError("动态测试已停止")
            self.save_task_status(None, current_step=step_name, step_status="running", init_steps=init_steps, error="")
            max_attempts = 2 if step_name == "手动重定位" else 1
            step_error = None
            for attempt in range(1, max_attempts + 1):
                if attempt > 1:
                    if stop_event and stop_event.is_set():
                        step_error = RuntimeError("动态测试已停止")
                        break
                    self.save_task_status(
                        None,
                        current_step="手动重定位失败，正在重试（2/2）",
                        step_status="running",
                        init_steps=init_steps,
                        error="",
                    )
                try:
                    action()
                    step_error = None
                    break
                except Exception as e:
                    step_error = e

            if step_error is None:
                init_steps.append({"name": step_name, "status": "success"})
                self.save_task_status(None, current_step=step_name, step_status="success", init_steps=init_steps, error="")
            else:
                init_steps.append({"name": step_name, "status": "failed"})
                retry_text = "重试后仍失败" if max_attempts > 1 else "失败"
                error_msg = f"{step_name}{retry_text}: {step_error}"
                self.save_task_status(None, current_step=step_name, step_status="failed", init_steps=init_steps, error=error_msg, result="failed")
                raise RuntimeError(error_msg) from step_error
        self.save_task_status(None, current_step="初始化完成", step_status="success", init_steps=init_steps, error="")

    def _build_status_by_index(self, task_names, current_idx, current_running=True):
        """
        根据当前任务索引构建状态：
        - 前面的元素：success
        - 当前元素：pending（执行中）/ success（执行完成）
        - 后面的元素：failed
        """
        status = {}
        for idx, name in enumerate(task_names):
            if idx < current_idx:
                status[name] = "success"
            elif idx == current_idx:
                status[name] = "pending" if current_running else "success"
            else:
                status[name] = "failed"
        return status



    def _execute_hsr_yuntai(self):
        """执行HSR云台任务：调用HSR云台接口进行可见光拍照、热成像拍照和测温"""
        from script.hsr_yuntai import AGVClient, BASE_URL, CLIENT_ID, API_SECRET
        
        # 获取SN号
        def get_sn():
            try:
                data = self._load_result_data()
                sn = data.get("robot_info", {}).get("sn") or "UNKNOWN_SN"
                sn = str(sn).strip()
                for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                    sn = sn.replace(ch, "_")
                return sn if sn else "UNKNOWN_SN"
            except Exception:
                return "UNKNOWN_SN"
        
        sn = get_sn()
        image_yuntai_dir = get_image_yuntai_dir(self.ip)
        os.makedirs(image_yuntai_dir, exist_ok=True)
        
        # 直接调用HSR云台接口，指定保存目录和SN前缀
        client = AGVClient(CLIENT_ID, API_SECRET, BASE_URL)
        result = client.execute(self.ip, save_dir=image_yuntai_dir, sn_prefix=sn)
        
        # 保存温度数据
        temperature = result.get("temperature")
        if temperature:
            temp_data = {
                "max_temp": temperature.get("max_temp", temperature.get("maxTemp")),
                "min_temp": temperature.get("min_temp", temperature.get("minTemp"))
            }
            temp_file = os.path.join(image_yuntai_dir, f"{sn}_cewen.json")
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2)
            print(f"温度数据已保存到: {temp_file}")
        
        return len(result.get("photos", [])) > 0 or temperature is not None

    def run_tasks(self, stop_event=None):
        """遍历执行所有任务"""
        results = {}

        if self.jixing not in self.tasks:
            results["time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_task_status(results, result="failed")
            return results

        task_names = list(self.tasks[self.jixing].keys())

        # 初始状态：全部 failed
        results = {task_name: "failed" for task_name in task_names}
        self.save_task_status(results, current_step="准备执行动态任务", step_status="running", error="")

        for i, task_name in enumerate(task_names):
            if stop_event and stop_event.is_set():
                interrupted_status = {name: ("success" if idx < i else "failed") for idx, name in enumerate(task_names)}
                self.save_task_status(
                    interrupted_status,
                    current_step="动态测试已停止",
                    step_status="stopped",
                    error="",
                    result="pending",
                )
                return interrupted_status

            # 进入当前任务时：前 success，当前 pending，后 failed
            results = self._build_status_by_index(task_names, i, current_running=True)
            self.save_task_status(results, current_step=f"执行任务: {task_name}", step_status="running", error="")

            print(f"开始执行任务: {task_name}")
            task_id = self.tasks[self.jixing][task_name]

            # 所有机型的云台任务执行前，都确保机器人图片目录已经存在。
            if task_name == "云台":
                self.save_task_status(
                    results,
                    current_step="检查云台图片目录",
                    step_status="running",
                    error="",
                )
                try:
                    compass_request.ensure_remote_image_directory(self.ip)
                except Exception as e:
                    failed_status = self._build_status_by_index(task_names, i, current_running=False)
                    failed_status[task_name] = "failed"
                    error_msg = f"云台图片目录检查失败: {e}"
                    self.save_task_status(
                        failed_status,
                        current_step="云台图片目录检查失败",
                        step_status="failed",
                        error=error_msg,
                        result="failed",
                    )
                    failed_status["error"] = error_msg
                    return failed_status

                self.save_task_status(
                    results,
                    current_step="云台图片目录已就绪",
                    step_status="success",
                    error="",
                )

            # HSR云台任务特殊处理
            if self.jixing == "HSR" and task_name == "云台" and task_id == "hsr_yuntai":
                try:
                    success = self._execute_hsr_yuntai()
                    if not success:
                        raise RuntimeError("HSR云台任务执行失败")
                    print(f"任务 {task_name} 执行完成")
                    results = self._build_status_by_index(task_names, i, current_running=False)
                    self.save_task_status(results, current_step=f"任务完成: {task_name}", step_status="success", error="")
                    continue
                except Exception as e:
                    failed_status = self._build_status_by_index(task_names, i, current_running=False)
                    failed_status[task_name] = "failed"
                    error_msg = f"{task_name}执行失败: {e}"
                    self.save_task_status(failed_status, current_step=f"任务失败: {task_name}", step_status="failed", error=error_msg, result="failed")
                    failed_status["error"] = error_msg
                    return failed_status
            
            try:
                status_code, mission_resp = compass_request.start_mission(self.ip, task_id)
                if status_code >= 400:
                    raise RuntimeError(f"启动任务接口异常: {status_code}, {mission_resp}")
            except Exception as e:
                failed_status = self._build_status_by_index(task_names, i, current_running=False)
                failed_status[task_name] = "failed"
                error_msg = f"{task_name}执行失败: {e}"
                self.save_task_status(failed_status, current_step=f"任务失败: {task_name}", step_status="failed", error=error_msg, result="failed")
                failed_status["error"] = error_msg
                return failed_status

            # 等待任务完成：保持当前状态分布
            while self.is_task_running(task_name):
                if stop_event and stop_event.is_set():
                    interrupted_status = {name: ("success" if idx < i else "failed") for idx, name in enumerate(task_names)}
                    self.save_task_status(
                        interrupted_status,
                        current_step="动态测试已停止",
                        step_status="stopped",
                        error="",
                        result="pending",
                    )
                    return interrupted_status

                print(f"任务 {task_name} 正在执行中...")
                
                results = self._build_status_by_index(task_names, i, current_running=True)
                self.save_task_status(results, current_step=f"执行任务: {task_name}", step_status="running", error="")
                time.sleep(5)

            print(f"任务 {task_name} 执行完成")
            
            # 任务正常完成
            results = self._build_status_by_index(task_names, i, current_running=False)
            
            self.save_task_status(results, current_step=f"任务完成: {task_name}", step_status="success", error="")

        results['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save_task_status(results, current_step="动态测试完成", step_status="success", error="", result="success")
        return results

    def save_task_status(self, status, current_step=None, step_status=None, init_steps=None, error=None, result=None):
        """保存任务状态到文件"""
        status_file = self._get_result_file_path()
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        
        existing_data = self._load_result_data()

        existing_dynamic = existing_data.get('dynamic', {})
        if not isinstance(existing_dynamic, dict):
            existing_dynamic = {}

        latest_status = status if status is not None else existing_dynamic.get('data', {})
        if not isinstance(latest_status, dict):
            latest_status = {}
        task_statuses = {k: v for k, v in latest_status.items() if k != 'time'}
        inferred_result = existing_dynamic.get('result', 'running')
        if task_statuses:
            inferred_result = 'success' if all(s == 'success' for s in task_statuses.values()) else 'running'
        if result is not None:
            inferred_result = result

        dynamic_payload = {
            'data': latest_status,
            'result': inferred_result,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_step': current_step if current_step is not None else existing_dynamic.get('current_step', ''),
            'step_status': step_status if step_status is not None else existing_dynamic.get('step_status', ''),
            'init_steps': init_steps if init_steps is not None else existing_dynamic.get('init_steps', []),
            'error': error if error is not None else existing_dynamic.get('error', '')
        }

        existing_data['dynamic'] = dynamic_payload
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    def is_task_running(self, task_name):
        """查询任务是否结束"""
        url = (
            f"http://{self.ip}:8080/api/v3/missionWorks/listByStatus"
            "?statusList=CREATE,START,WAIT,RUNNING,FAULT,PAUSE,BEING_PAUSE,BEING_RESUME,WAITINPUT"
        )

        try:
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return False

            data = response.json()
            mission_list = data.get("missionWorkList", [])

            for task in mission_list:
                if task_name in task.get("name", ""):
                    return True

            return False
        except Exception as e:
            print(f"查询任务状态时出错: {e}")
            return False

    def get_all_task_status(self):
        """查询所有任务的状态"""
        status = {}
        if self.jixing in self.tasks:
            for task_name in self.tasks[self.jixing].keys():
                is_running = self.is_task_running(task_name)
                status[task_name] = "pending" if is_running else "failed"
        return status


# 示例用法
if __name__ == "__main__":
    ip = "192.168.16.25"
    jixing = "MS"

    # 初始化类并执行初始化操作
    inspector = InspectionAutomation(ip, jixing)

    # 执行所有任务
    results = inspector.run_tasks()
    print(f"所有任务执行结果: {results}")

    # 查询所有任务状态
    all_status = inspector.get_all_task_status()
    print(f"所有任务状态: {all_status}")
