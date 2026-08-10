import sys
import subprocess
import os

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

import re

from datetime import datetime
from config.model_config import (
    MODEL_CONFIG,
    SUBTASK_CATALOG,
    IMAGE_YUNTAI_DIR,
    TEST_RECORD_DIR,
    get_image_yuntai_dir,
    get_manual_upload_dir,
    _safe_ip,
)


def _safe_filename(name):
    if not name:
        return '_'
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', str(name))
    cleaned = re.sub(r'\s+', '_', cleaned).strip('_')
    if not cleaned:
        cleaned = '_'
    return cleaned[:120]

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

        # 辅助函数：安全地检查图片是否有效
            def is_image_valid(img_path):
                if os.path.exists(img_path):
                    try:
                        from PIL import Image as PILImage
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
            
            # 辅助函数：按优先级查找图片路径
            def find_image_path(filename, ip_dir, fallback_dir):
                # 1) 优先在IP目录下查找
                ip_path = os.path.join(ip_dir, filename)
                if os.path.exists(ip_path):
                    return ip_path
                # 2) 回退到全局目录
                fallback_path = os.path.join(fallback_dir, filename)
                if os.path.exists(fallback_path):
                    return fallback_path
                return None
            
            # 添加云台照片（仅当有有效SN且照片存在时添加）
            robot_sn = self.data.get('robot_info', {}).get('sn', '')
            robot_ip = self.data.get('robot_info', {}).get('ip', '')
            
            if robot_sn and robot_sn.strip():
                # 获取按IP分组的目录和回退目录
                image_yuntai_ip_dir = get_image_yuntai_dir(robot_ip)
                image_yuntai_fallback_dir = IMAGE_YUNTAI_DIR
                
                # 仅尝试使用机器人SN的照片，不使用UNKNOWN_SN的照片
                ptz1_path = find_image_path(f'{robot_sn}_ptz1.jpg', image_yuntai_ip_dir, image_yuntai_fallback_dir)
                ptz2_path = find_image_path(f'{robot_sn}_ptz2.jpg', image_yuntai_ip_dir, image_yuntai_fallback_dir)
                preset1_path = find_image_path(f'{robot_sn}_预置点1.jpg', image_yuntai_ip_dir, image_yuntai_fallback_dir)
                light_photo_path = find_image_path(f'{robot_sn}_可见光拍照.jpg', image_yuntai_ip_dir, image_yuntai_fallback_dir)
                thermal_photo_path = find_image_path(f'{robot_sn}_热成像拍照.jpg', image_yuntai_ip_dir, image_yuntai_fallback_dir)
                
                # 检查是否有任意一张照片可用
                has_valid_light = is_image_valid(light_photo_path) if light_photo_path else False
                has_valid_thermal = is_image_valid(thermal_photo_path) if thermal_photo_path else False
                has_valid_ptz1 = is_image_valid(ptz1_path) if ptz1_path else False
                has_valid_ptz2 = is_image_valid(ptz2_path) if ptz2_path else False
                has_valid_preset = is_image_valid(preset1_path) if preset1_path else False
                
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
            
            # 添加手动上传照片
            if robot_ip:
                # 与app.py保持一致：先对IP做_safe_filename处理，再传给get_manual_upload_dir
                safe_robot_ip = _safe_filename(robot_ip)
                manual_upload_ip_dir = get_manual_upload_dir(safe_robot_ip)
                manual_upload_fallback_dir = get_manual_upload_dir(None)
                
                # 获取所有手动测试项
                manual_test_names = [item.get('name', '') for item in self.manual_tests]
                all_manual_images = []
                added_paths = set()
                
                # 收集测试项对应的目录名（含安全文件名）
                test_dir_names = {}
                for test_name in manual_test_names:
                    if test_name:
                        safe_test_name = _safe_filename(test_name)
                        test_dir_names[safe_test_name] = test_name
                
                # 扫描IP目录下的所有子目录（包含未在manual_tests.json中定义的目录）
                # 注意：不能直接扫描全局回退目录 static/manual_upload/ 的外层，
                # 因为该目录下可能存在不归属任何机器的共享/孤立测试项子目录
                # （例如 static/manual_upload/外观检查/xxx.jpg），
                # 直接扫描会导致所有机器的报告都混入同一张照片。
                # 这里仅扫描：
                #   1) 新结构：test_record/<ip>/manual_upload/<测试项>/
                #   2) 旧结构回退：static/manual_upload/<当前机器IP>/<测试项>/  （按IP归属）
                scan_dirs = [manual_upload_ip_dir]
                if os.path.isdir(manual_upload_fallback_dir):
                    old_ip_dir = os.path.join(manual_upload_fallback_dir, safe_robot_ip)
                    if os.path.isdir(old_ip_dir) and os.path.abspath(old_ip_dir) != os.path.abspath(manual_upload_ip_dir):
                        scan_dirs.append(old_ip_dir)
                for scan_dir in scan_dirs:
                    if os.path.isdir(scan_dir):
                        for dir_name in os.listdir(scan_dir):
                            dir_path = os.path.join(scan_dir, dir_name)
                            if os.path.isdir(dir_path):
                                # 获取显示名称（优先使用原始测试项名，否则使用目录名）
                                display_name = test_dir_names.get(dir_name, dir_name)
                                for filename in os.listdir(dir_path):
                                    lower = filename.lower()
                                    if lower.endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')):
                                        img_path = os.path.join(dir_path, filename)
                                        # 使用set去重
                                        if img_path not in added_paths and is_image_valid(img_path):
                                            added_paths.add(img_path)
                                            all_manual_images.append((display_name, img_path))
                
                # 按测试项名称排序
                all_manual_images.sort(key=lambda x: x[0])
                
                if all_manual_images:
                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("手动上传照片", self.header_style))
                    elements.append(Spacer(1, 10))
                    
                    for test_name, img_path in all_manual_images:
                        elements.append(Paragraph(f"【{test_name}】", self.text_style))
                        add_image_safely(img_path)

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
        
        version_catalog = SUBTASK_CATALOG.get('version', {})
        for item_id in self.current_config.get('version', []):
            label = version_catalog.get(item_id, {}).get('label', item_id)
            data.append([label, ver.get(item_id, "")])
        
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
        
        sensor_catalog = SUBTASK_CATALOG.get('sensor', {})
        for item_id in self.current_config.get('sensor', []):
            label = sensor_catalog.get(item_id, {}).get('label', item_id)
            data.append([label, str(sensor_data.get(item_id, "无数据"))])
        
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

        elements = []
        section_title = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"][idx-1]
        elements.append(Paragraph(f"{section_title}、网络连通性检测(标准<10ms)", self.header_style))
        elements.append(Spacer(1, 5))

        table_data = [["设备", "延迟"]]
        ping_items = self.current_config.get('ping', [])
        ping_catalog = SUBTASK_CATALOG.get('ping', {})
        if ping_items:
            for ip in ping_items:
                delay = data_ping.get(ip)
                device_name = ping_catalog.get(ip, {}).get('label', ip)
                table_data.append([device_name, delay if delay else "未检测"])
        else:
            for ip, delay in data_ping.items():
                device_name = ping_catalog.get(ip, {}).get('label', ip)
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
        
        button_catalog = SUBTASK_CATALOG.get('button', {})
        for item_id in self.current_config.get('button', []):
            label = button_catalog.get(item_id, {}).get('label', item_id)
            value = data_button.get(item_id)
            table_data.append([label, "未检测" if value is None else self._status(value)])
        
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
        collision_catalog = SUBTASK_CATALOG.get('anti_collision', {})
        for strip in anti_collision_items:
            strip_status = "未检测" if data.get(strip) is None else self._status(data.get(strip))
            strip_newton = str(newton.get(strip, ""))
            meta = collision_catalog.get(strip, {})
            label = meta.get('report_label', meta.get('label', str(strip)))
            table_data.append([label, strip_status, strip_newton])
        
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
        
        light_catalog = SUBTASK_CATALOG.get('light', {})
        for item_id in self.current_config.get('light', []):
            label = light_catalog.get(item_id, {}).get('label', item_id)
            table_data.append([label, self._status(data.get(item_id))])
        
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
        dynamic_catalog = SUBTASK_CATALOG.get('dynamic', {})
        for task_name in dynamic_items:
            meta = dynamic_catalog.get(task_name, {})
            label = meta.get('label', task_name)
            description = meta.get('description', "")
            task_value = data.get(task_name)
            # 使用Paragraph对象包装文本，确保自动换行
            test_name_paragraph = Paragraph(label, self.text_style)
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
        integrated_catalog = SUBTASK_CATALOG.get('integrated', {})
        for task_name in integrated_items:
            meta = integrated_catalog.get(task_name, {})
            label = meta.get('label', task_name)
            description = meta.get('description', "")
            task_value = data.get(task_name)
            # 使用Paragraph对象包装文本，确保自动换行
            test_name_paragraph = Paragraph(label, self.text_style)
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
    test_file = os.path.join(TEST_RECORD_DIR, "192.168.16.67.json")
    if os.path.exists(test_file):
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = RobotTestReport(data)
        report.generate("机器人测试报告_with_time.pdf")
        print("PDF生成完成")
    else:
        print(f"未找到测试文件: {test_file}")
