import sys
import subprocess

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.lib import colors
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.lib import colors

from datetime import datetime
from config.model_config import INTEGRATED_TASK_DESCRIPTIONS, MODEL_CONFIG

# 动态测试子任务描述
dynamic_task_descriptions = {
    '直线': '0.4速度，0.8速度，1.2速度 ，任务能正常执行完成',
    '曲线': '0.4速度，0.8速度，1.2速度，任务能正常执行完成',
    '云台': 'ptz拍照，预置点拍照，普通测温，专家测温，照片生成在/server/data/image文件夹',
    '沟壑': '任务能正常执行完成',
    '切区': '静止-1区，低速（≈0.4 m/s）-2区，中速（≈0.7 m/s）-3区，高速（≈1.2 m/s）-4区，旋转-5区',
    '横移': '横向移动测试，任务能正常执行完成',
    '45°夹角': '45度夹角测试，任务能正常执行完成',
    '精定位': '精确定位测试，任务能正常执行完成',
    '上集成': '上集成功能测试，任务能正常执行完成'
}

# 集成测试子任务描述
integrated_task_descriptions = INTEGRATED_TASK_DESCRIPTIONS


class RobotTestReport:

    def __init__(self, data: dict):
        self.data = data
        self.model_config = MODEL_CONFIG
        self.current_model = self.data.get('robot_info', {}).get('model', 'MS')
        # 获取当前机型的配置
        self.current_config = self.model_config.get(self.current_model, self.model_config['MS'])
        # 优先使用后端传入的筛选配置，确保PDF和前端展示一致
        report_filters = self.data.get('report_filters', {})
        if isinstance(report_filters, dict):
            filter_model = report_filters.get('model')
            if filter_model:
                self.current_model = filter_model
            merged_config = dict(self.current_config)
            for key in ['test_items', 'version', 'sensor', 'ping', 'button', 'light', 'anti_collision', 'integrated']:
                value = report_filters.get(key)
                if isinstance(value, list):
                    merged_config[key] = value
            self.current_config = merged_config
        # 读取manual_tests.json文件（优先按机型目录）
        import json
        import os
        base_dir = os.path.dirname(os.path.dirname(__file__))
        model_manual_tests_path = os.path.join(base_dir, 'config', self.current_model, 'manual_tests.json')
        legacy_manual_tests_path = os.path.join(base_dir, 'config', 'manual_tests.json')
        manual_tests_path = model_manual_tests_path if os.path.exists(model_manual_tests_path) else legacy_manual_tests_path
        self.manual_tests = []
        if os.path.exists(manual_tests_path):
            with open(manual_tests_path, 'r', encoding='utf-8') as f:
                self.manual_tests = json.load(f).get('manual_tests', [])

        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

        styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            name='ReportTitle',
            parent=styles['Title'],
            fontName='STSong-Light',
            fontSize=24,
            leading=30,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30
        )

        self.header_style = ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontName='STSong-Light',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=20,
            spaceAfter=10,
            borderWidth=0,
            borderPadding=0,
            borderRadius=0,
            backColor=None
        )

        self.text_style = styles["Normal"]
        self.text_style.fontName = "STSong-Light"
        self.text_style.fontSize = 12

    def generate(self, filename: str):

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )

        elements = []

        # 标题
        elements.append(Paragraph("机器人巡检自动化测试报告", self.title_style))
        
        # 机器人信息头部 (单独拉出来)
        elements.append(self._header_info())
        elements.append(Spacer(1, 20))
        
        # 根据机型配置筛选测试项
        test_items = self.current_config.get('test_items', [])
        
        section_idx = 1
        
        if 'version' in test_items:
            elements += self._version_info(section_idx)
            section_idx += 1
        
        if 'sensor' in test_items:
            elements += self._sensor_info(section_idx)
            section_idx += 1
            
        if 'ping' in test_items:
            elements += self._ping_info(section_idx)
            section_idx += 1
            
        if 'button' in test_items:
            elements += self._button_info(section_idx)
            section_idx += 1
            
        if 'anti_collision' in test_items:
            elements += self._anti_collision_info(section_idx)
            section_idx += 1
            
        if 'light' in test_items and self.current_config.get('light', []):
            elements += self._light_info(section_idx)
            section_idx += 1
            
        if 'dynamic' in test_items:
            elements += self._dynamic_info(section_idx)
            section_idx += 1
        
        if 'integrated' in test_items:
            elements += self._integrated_info(section_idx)
            section_idx += 1
        
        if 'manual' in test_items:
            elements += self._manual_info(section_idx)
            section_idx += 1

        # 添加云台照片（仅当有有效SN且照片存在时添加
        robot_sn = self.data.get('robot_info', {}).get('sn', '')
        
        if robot_sn and robot_sn.strip():
            # 构建照片路径
            import os
            image_yuntai_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image_yuntai')
            
            # 仅尝试使用机器人SN的照片，不使用UNKNOWN_SN的照片
            ptz1_path = os.path.join(image_yuntai_path, f'{robot_sn}_ptz1.jpg')
            ptz2_path = os.path.join(image_yuntai_path, f'{robot_sn}_ptz2.jpg')
            # 尝试使用预置点1照片作为备选
            preset1_path = os.path.join(image_yuntai_path, f'{robot_sn}_预置点1.jpg')
            # 新增：可见光拍照和热成像拍照
            light_photo_path = os.path.join(image_yuntai_path, f'{robot_sn}_可见光拍照.jpg')
            thermal_photo_path = os.path.join(image_yuntai_path, f'{robot_sn}_热成像拍照.jpg')
            
            # 辅助函数：安全地检查图片是否有效
            def is_image_valid(img_path):
                if os.path.exists(img_path):
                    try:
                        from PIL import Image as PILImage
                        # 尝试打开图片验证
                        with PILImage.open(img_path):
                            pass
                        return True
                    except Exception as e:
                        print(f"跳过损坏的图片文件 {img_path}: {str(e)}")
                return False
            
            # 辅助函数：安全地添加图片
            def add_image_safely(img_path):
                img = Image(img_path, width=200*mm, height=150*mm)
                elements.append(img)
                elements.append(Spacer(1, 10))
            
            # 检查是否有任意一张照片可用
            has_valid_light = is_image_valid(light_photo_path)
            has_valid_thermal = is_image_valid(thermal_photo_path)
            has_valid_ptz1 = is_image_valid(ptz1_path)
            has_valid_ptz2 = is_image_valid(ptz2_path)
            has_valid_preset = is_image_valid(preset1_path)
            
            has_any_valid = has_valid_light or has_valid_thermal or has_valid_ptz1 or has_valid_ptz2 or has_valid_preset
            
            if has_any_valid:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("云台照片", self.header_style))
                elements.append(Spacer(1, 10))
            
                # 优先添加可见光和热成像拍照
                if has_valid_light:
                    add_image_safely(light_photo_path)
            
                if has_valid_thermal:
                    add_image_safely(thermal_photo_path)
            
                # 添加ptz和预置点照片
                if has_valid_ptz1:
                    add_image_safely(ptz1_path)
            
                if has_valid_ptz2:
                    add_image_safely(ptz2_path)
                elif not has_valid_ptz1 and not has_valid_ptz2 and has_valid_preset:
                    add_image_safely(preset1_path)

        doc.build(elements)


    def _header_info(self):
        info = self.data.get("robot_info", {})
        
        # 创建更美观的头部信息表
        data = [
            ["机器型号", info.get("model", ""), "SN序列号", info.get("sn", "")],
            ["测试人员", info.get("tester", ""), "测试日期", datetime.now().strftime('%Y-%m-%d')],
            ["机器IP", info.get("ip", ""), "", ""]
        ]
        
        # 样式优化
        table = Table(data, colWidths=[80, 160, 80, 160])
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            
            # 背景色
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor('#e8f4f8')), # 标签列背景
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor('#e8f4f8')), # 标签列背景
            
            # 边框
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor('#2980b9')),
            
            # 对齐
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("padding", (0, 0), (-1, -1), 6),
        ]))
        
        return table

    def _manual_info(self, idx):
        from reportlab.platypus import Paragraph
        manual = self.data.get("manual", {})
        data = manual.get("data", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、人工测试", self.header_style))
        elements.append(Spacer(1, 5))

        table_data = [["测试项目", "测试步骤", "结果", "备注", "测试时间"]]
        
        # 直接使用manual_tests.json中的内容，不再进行过滤
        for test_item in self.manual_tests:
            test_name = test_item.get('name', '')
            test_description = test_item.get('description', '')
            # 处理description可能是数组的情况，将其连接成字符串
            if isinstance(test_description, list):
                test_description = '\n'.join(test_description)
            test_result = data.get(test_name, '')
            test_time = ''
            test_note = ''
            if isinstance(test_result, dict):
                test_time = test_result.get('time', '')
                test_note = test_result.get('note', '')
                test_result = test_result.get('result', '')
            # 使用Paragraph对象包装所有文本，确保自动换行
            test_name_paragraph = Paragraph(test_name, self.text_style)
            test_description_paragraph = Paragraph(test_description, self.text_style)
            test_result_paragraph = Paragraph(self._status(test_result), self.text_style)
            test_note_paragraph = Paragraph(test_note, self.text_style)
            test_time_paragraph = Paragraph(test_time, self.text_style)
            table_data.append([test_name_paragraph, test_description_paragraph, test_result_paragraph, test_note_paragraph, test_time_paragraph])

        # 使用Paragraph对象包装总体结果和测试时间行的文本
        total_result_paragraph = Paragraph("总体结果", self.text_style)
        total_result_value_paragraph = Paragraph(self._status(manual.get("result")), self.text_style)
        test_time_paragraph = Paragraph("测试时间", self.text_style)
        test_time_value_paragraph = Paragraph(manual.get("time", ""), self.text_style)
        empty_paragraph = Paragraph("", self.text_style)
        
        table_data.append([total_result_paragraph, empty_paragraph, total_result_value_paragraph, empty_paragraph, empty_paragraph])
        table_data.append([test_time_paragraph, empty_paragraph, test_time_value_paragraph, empty_paragraph, empty_paragraph])

        # 更新表格样式以适应5列，调整列宽度分配
        table = Table(table_data, colWidths=[90, 250, 60, 80, 100])
        
        # 使用自定义样式
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),  # 其他列的测试内容字体保持正常大小
            ("FONTSIZE", (1, 1), (1, -1), 6),  # 测试步骤列的字体缩小
            
            # 表头样式
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),  # 表头字体保持正常大小
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            
            # 内容样式
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),  # 测试项目左对齐
            ("ALIGN", (1, 0), (1, -1), "LEFT"),  # 测试步骤左对齐
            ("ALIGN", (2, 0), (2, -1), "CENTER"),  # 测试结果居中对齐
            ("ALIGN", (3, 0), (3, -1), "LEFT"),  # 备注左对齐
            ("ALIGN", (4, 0), (4, -1), "CENTER"),  # 测试时间居中对齐
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # 垂直对齐改为顶部
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))
        
        return elements

    # ------------------------------
    # 表格工具
    # ------------------------------

    def _table(self, data):
        table = Table(data, colWidths=[150, 320])
        
        # 更加美观的表格样式
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            
            # 表头样式
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            
            # 内容样式
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))

        return table

    def _status(self, value):
        if isinstance(value, dict):
            value = value.get("result") or value.get("status") or value.get("value")
        if value == "success":
            return "通过"
        elif value == "failed":
            return "失败"
        else:
            return "未测试" if not value else str(value)

    # ------------------------------
    # 版本信息
    # ------------------------------

    def _version_info(self, idx):
        ver = self.data.get("version", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、版本信息检测", self.header_style))
        elements.append(Spacer(1, 5))

        data = [["项目", "版本"]]
        
        # 根据机型配置筛选版本信息子项
        version_items = self.current_config.get('version', [])
        if 'pilot_version' in version_items:
            data.append(["Pilot版本", ver.get("pilot_version", "")])
        if 'compass_version' in version_items:
            data.append(["Compass版本", ver.get("compass_version", "")])
        if 'mirror_system' in version_items:
            data.append(["镜像系统", ver.get("mirror_system", "")])
        if 'rcc_base_version' in version_items:
            data.append(["RCC基础版本", ver.get("rcc_base_version", "")])
        if 'robot_version' in version_items:
            data.append(["Robot版本", ver.get("robot_version", "")])
        if 'rws_version' in version_items:
            data.append(["RWS版本", ver.get("rws_version", "")])
        if 'youiscript_version' in version_items:
            data.append(["YouiScript版本", ver.get("youiscript_version", "")])
        if 'mos_version' in version_items:
            data.append(["MOS版本", ver.get("mos_version", "")])
        if 'mos_version_hsr' in version_items:
            data.append(["上集成MOS版本", ver.get("mos_version_hsr", "")])
        if 'mirror_system_hsr' in version_items:
            data.append(["上集成工控机镜像", ver.get("mirror_system_hsr", "")])
        
        data.append(["测试结果", self._status(ver.get("result"))])
        data.append(["测试时间", ver.get("time", "")])

        elements.append(self._table(data))
        elements.append(Spacer(1, 15))

        return elements

    # ------------------------------
    # 传感器检测
    # ------------------------------

    def _sensor_info(self, idx):
        sensor = self.data.get("sensor", {})
        sensor_data = sensor.get("data", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、传感器检测", self.header_style))
        elements.append(Spacer(1, 5))

        data = [["检测项", "原始数据"]]
        
        # 根据机型配置筛选传感器子项
        sensor_items = self.current_config.get('sensor', [])
        if 'ks114_sensor' in sensor_items:
            data.append(["超声波传感器", str(sensor_data.get("ks114_sensor", "无数据"))])
        if 'odom' in sensor_items:
            data.append(["里程计", str(sensor_data.get("odom", "无数据"))])
        if 'imu_data' in sensor_items:
            data.append(["IMU数据", str(sensor_data.get("imu_data", "无数据"))])
        if 'encoder' in sensor_items:
            data.append(["编码器", str(sensor_data.get("encoder", "无数据"))])
        if 'tfmini_sensor' in sensor_items:
            data.append(["防跌落传感器", str(sensor_data.get("tfmini_sensor", "无数据"))])
        if 'scan_1' in sensor_items:
            data.append(["激光雷达", str(sensor_data.get("scan_1", "无数据"))])
        if 'cpu_hz' in sensor_items:
            data.append(["CPU频率(需大于2400hz)", str(sensor_data.get("cpu_hz", "无数据"))])
        if 'temperature' in sensor_items:
            data.append(["温度", str(sensor_data.get("temperature", "无数据"))])
        if 'humidity' in sensor_items:
            data.append(["湿度", str(sensor_data.get("humidity", "无数据"))])
        if 'pm10' in sensor_items:
            data.append(["PM10", str(sensor_data.get("pm10", "无数据"))])
        if 'pm2_5' in sensor_items:
            data.append(["PM2.5", str(sensor_data.get("pm2_5", "无数据"))])
        if 'o2' in sensor_items:
            data.append(["O2", str(sensor_data.get("o2", "无数据"))])
        if 'co' in sensor_items:
            data.append(["CO", str(sensor_data.get("co", "无数据"))])
        if 'microphone' in sensor_items:
            data.append(["麦克风", str(sensor_data.get("microphone", "无数据"))])
        if 'fan_board' in sensor_items:
            data.append(["风扇板", str(sensor_data.get("fan_board", "无数据"))])
        if 'byz06_sensor' in sensor_items:
            data.append(["气体传感器(氧气)", str(sensor_data.get("byz06_sensor", "无数据"))])
        if 'fs00802_sensor' in sensor_items:
            data.append(["噪声传感器", str(sensor_data.get("fs00802_sensor", "无数据"))])
        
        data.append(["整体测试结果", self._status(sensor.get("result"))])
        data.append(["检测时间", sensor.get("time", "")])

        elements.append(self._table(data))
        elements.append(Spacer(1, 15))

        return elements

    # ------------------------------
    # 网络检测
    # ------------------------------

    def _ping_info(self, idx):
        ping = self.data.get("ping", {})
        data_ping = ping.get("data", {})

        # IP地址到设备名称的映射
        ip_map = {
            '192.168.0.8': '4g运维',
            '192.168.2.63': '云台',
            '192.168.2.250': '路由器',
            '192.168.0.100': '内网口',
            '192.168.2.2': '外网口',
            '192.168.0.100:8081': 'Compass接口',
            '192.168.2.100': '算力板',
            '192.168.0.50': 'PLC'
        }

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、网络连通性检测(标准<10ms)", self.header_style))
        elements.append(Spacer(1, 5))

        table_data = [["设备", "延迟"]]
        ping_items = self.current_config.get('ping', [])
        if ping_items:
            for ip in ping_items:
                delay = data_ping.get(ip)
                # 如果有映射名称，显示 "名称 (IP)"，否则直接显示 IP
                if ip in ip_map:
                    device_name = f"{ip_map[ip]} ({ip})"
                else:
                    device_name = ip
                table_data.append([device_name, delay if delay else "未检测"])
        else:
            for ip, delay in data_ping.items():
                if ip in ip_map:
                    device_name = f"{ip_map[ip]} ({ip})"
                else:
                    device_name = ip
                table_data.append([device_name, delay])

        table_data.append(["测试结果", self._status(ping.get("result"))])
        table_data.append(["测试时间", ping.get("time", "")])

        elements.append(self._table(table_data))
        elements.append(Spacer(1, 15))

        return elements

    # ------------------------------
    # 按键检测
    # ------------------------------

    def _button_info(self, idx):
        button = self.data.get("button", {})
        data_button = button.get("data", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、按键功能检测", self.header_style))
        elements.append(Spacer(1, 5))

        table_data = [["检测项", "结果"]]
        
        # 根据机型配置筛选按钮子项
        button_items = self.current_config.get('button', [])
        if 'emergency_stop' in button_items:
            table_data.append(["急停按钮", self._status(data_button.get("emergency_stop"))])
        if 'left_emergency_stop' in button_items:
            table_data.append(["左急停按钮", self._status(data_button.get("left_emergency_stop"))])
        if 'right_emergency_stop' in button_items:
            table_data.append(["右急停按钮", self._status(data_button.get("right_emergency_stop"))])
        if 'voice' in button_items:
            table_data.append(["语音按钮", "未检测" if data_button.get("voice") is None else self._status(data_button.get("voice"))])
        if 'unlock_brake' in button_items:
            table_data.append(["解抱闸按钮", "未检测" if data_button.get("unlock_brake") is None else self._status(data_button.get("unlock_brake"))])
        if 'chassis_left_stop' in button_items:
            table_data.append(["底盘左急停按钮", "未检测" if data_button.get("chassis_left_stop") is None else self._status(data_button.get("chassis_left_stop"))])
        if 'chassis_right_stop' in button_items:
            table_data.append(["底盘右急停按钮", "未检测" if data_button.get("chassis_right_stop") is None else self._status(data_button.get("chassis_right_stop"))])
        if 'integrated_left_stop' in button_items:
            table_data.append(["上集成左急停按钮", "未检测" if data_button.get("integrated_left_stop") is None else self._status(data_button.get("integrated_left_stop"))])
        if 'integrated_right_stop' in button_items:
            table_data.append(["上集成右急停按钮", "未检测" if data_button.get("integrated_right_stop") is None else self._status(data_button.get("integrated_right_stop"))])
        
        table_data.append(["总体结果", self._status(button.get("result"))])
        table_data.append(["测试时间", button.get("time", "")])

        elements.append(self._table(table_data))
        elements.append(Spacer(1, 15))

        return elements

    # ------------------------------
    # 防撞检测
    # ------------------------------

    def _anti_collision_info(self, idx):
        anti = self.data.get("anti_collision", {})
        data = anti.get("data", {})
        newton = anti.get("newton", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、防撞检测", self.header_style))
        elements.append(Spacer(1, 5))

        table_data = [
            ["方向", "检测结果", "拉力记录(N)"]
        ]
        anti_collision_items = self.current_config.get('anti_collision', [])
        label_map = {
            "front": "前方",
            "back": "后方",
            "left": "左方",
            "right": "右方"
        }
        for strip in anti_collision_items:
            strip_status = "未检测" if data.get(strip) is None else self._status(data.get(strip))
            strip_newton = str(newton.get(strip, ""))
            table_data.append([label_map.get(strip, str(strip)), strip_status, strip_newton])
        
        table_data.append(["总体结果", self._status(anti.get("result")), ""])
        table_data.append(["测试时间", anti.get("time", ""), ""])

        # 更新表格样式以适应3列
        table = Table(table_data, colWidths=[100, 150, 220])
        
        # 使用自定义样式
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            
            # 表头
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            
            # 内容
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        return elements

    # ------------------------------
    # 灯光检测
    # ------------------------------

    def _light_info(self, idx):
        light = self.data.get("light", {})
        data = light.get("data", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、灯光检测", self.header_style))
        elements.append(Spacer(1, 5))

        table_data = [["灯光类型", "检测结果"]]
        
        # 根据机型配置筛选灯光子项
        light_items = self.current_config.get('light', [])
        if 'red' in light_items:
            table_data.append(["红色指示灯", self._status(data.get("red"))])
        if 'blue' in light_items:
            table_data.append(["蓝色指示灯", self._status(data.get("blue"))])
        if 'green' in light_items:
            table_data.append(["绿色指示灯", self._status(data.get("green"))])
        if 'front_light' in light_items:
            table_data.append(["前灯", self._status(data.get("front_light"))])
        if 'back_light' in light_items:
            table_data.append(["后灯", self._status(data.get("back_light"))])
        if 'charge_relay' in light_items:
            table_data.append(["充电继电器", self._status(data.get("charge_relay"))])
        
        table_data.append(["总体结果", self._status(light.get("result"))])
        table_data.append(["测试时间", light.get("time", "")])

        elements.append(self._table(table_data))
        elements.append(Spacer(1, 15))

        return elements

    # ------------------------------
    # 动态测试
    # ------------------------------

    def _dynamic_info(self, idx):
        dynamic = self.data.get("dynamic", {})
        data = dynamic.get("data", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、动态功能测试", self.header_style))
        elements.append(Spacer(1, 5))


        table_data = [["测试项目", "测试描述", "结果"]]
        # 根据机型获取动态测试任务列表
        dynamic_items = self.current_config.get('dynamic', ['直线', '切区', '曲线', '沟壑', '云台'])
        for task_name in dynamic_items:
            description = dynamic_task_descriptions.get(task_name, "")
            task_value = data.get(task_name)
            # 使用Paragraph对象包装文本，确保自动换行
            test_name_paragraph = Paragraph(task_name, self.text_style)
            description_paragraph = Paragraph(description, self.text_style)
            result_paragraph = Paragraph(self._status(task_value), self.text_style)
            table_data.append([test_name_paragraph, description_paragraph, result_paragraph])

        # 使用Paragraph对象包装总体结果和测试时间行的文本
        total_result_paragraph = Paragraph("总体结果", self.text_style)
        total_result_value_paragraph = Paragraph(self._status(dynamic.get("result")), self.text_style)
        test_time_paragraph = Paragraph("测试时间", self.text_style)
        test_time_value_paragraph = Paragraph(dynamic.get("time", ""), self.text_style)
        empty_paragraph = Paragraph("", self.text_style)
        
        table_data.append([total_result_paragraph, empty_paragraph, total_result_value_paragraph])
        table_data.append([test_time_paragraph, empty_paragraph, test_time_value_paragraph])

        # 更新表格样式以适应3列
        table = Table(table_data, colWidths=[100, 300, 100])
        
        # 使用自定义样式
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            
            # 表头样式
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            
            # 内容样式
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # 垂直对齐改为顶部
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        return elements

    # ------------------------------
    # 集成测试
    # ------------------------------

    def _integrated_info(self, idx):
        integrated = self.data.get("integrated", {})
        data = integrated.get("data", {})

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、集成功能测试", self.header_style))
        elements.append(Spacer(1, 5))

        table_data = [["测试项目", "测试描述", "结果"]]
        integrated_items = self.current_config.get('integrated', [])
        for task_name in integrated_items:
            description = integrated_task_descriptions.get(task_name, "")
            task_value = data.get(task_name)
            # 使用Paragraph对象包装文本，确保自动换行
            test_name_paragraph = Paragraph(description, self.text_style)
            description_paragraph = Paragraph(description, self.text_style)
            result_paragraph = Paragraph(self._status(task_value), self.text_style)
            table_data.append([test_name_paragraph, description_paragraph, result_paragraph])

        # 使用Paragraph对象包装总体结果和测试时间行的文本
        total_result_paragraph = Paragraph("总体结果", self.text_style)
        total_result_value_paragraph = Paragraph(self._status(integrated.get("result")), self.text_style)
        test_time_paragraph = Paragraph("测试时间", self.text_style)
        test_time_value_paragraph = Paragraph(integrated.get("time", ""), self.text_style)
        empty_paragraph = Paragraph("", self.text_style)
        
        table_data.append([total_result_paragraph, empty_paragraph, total_result_value_paragraph])
        table_data.append([test_time_paragraph, empty_paragraph, test_time_value_paragraph])

        # 更新表格样式以适应3列
        table = Table(table_data, colWidths=[100, 300, 100])
        
        # 使用自定义样式
        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            
            # 表头样式
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            
            # 内容样式
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),  # 垂直对齐改为顶部
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        return elements


# ===========================
# 使用示例
# ===========================

if __name__ == "__main__":

    import json
    import os

    # 确保有测试数据
    test_file = "test_record/192.168.16.67.json"
    if os.path.exists(test_file):
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = RobotTestReport(data)
        report.generate("机器人测试报告_with_time.pdf")
        print("PDF生成完成")
    else:
        print(f"未找到测试文件: {test_file}")
