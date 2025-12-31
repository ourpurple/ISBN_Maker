"""
Main Window - 主窗口GUI模块

本模块实现ISBN条码生成器的图形用户界面。
使用PyQt6构建现代化界面，支持单个和批量条码生成。
"""

import os
import sys
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox, QFileDialog, QMessageBox, QProgressBar,
    QStatusBar, QMenuBar, QMenu, QScrollArea, QFrame, QSplitter,
    QFontComboBox, QSlider, QRadioButton, QButtonGroup, QInputDialog,
    QApplication, QColorDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage, QAction, QIcon, QFont, QColor

from ..core.validator import ISBNValidator, ParsedISBN
from ..core.encoder import EAN13Encoder
from ..core.addon_encoder import AddonEncoder
from ..core.renderer import TIFRenderer, RenderConfig, TIFConfig, ColorMode, TextAlignment
from ..core.template_manager import TemplateManager
from ..core.batch_processor import BatchProcessor, BatchResult


class BatchWorker(QThread):
    """批量处理工作线程"""
    progress = pyqtSignal(int, int, str)  # current, total, isbn
    finished = pyqtSignal(object)  # BatchResult
    
    def __init__(self, processor: BatchProcessor, isbn_list: list[str], 
                 output_dir: str, config: RenderConfig):
        super().__init__()
        self.processor = processor
        self.isbn_list = isbn_list
        self.output_dir = output_dir
        self.config = config
    
    def run(self):
        def callback(current, total, isbn):
            self.progress.emit(current, total, isbn)
        
        result = self.processor.process_list(
            self.isbn_list, self.output_dir, self.config, callback
        )
        self.finished.emit(result)


class MainWindow(QMainWindow):
    """主窗口
    
    ISBN条码生成器的主界面，包含：
    - ISBN输入面板
    - 设置面板（分辨率、颜色模式、尺寸等）
    - 文字样式面板
    - 预览面板
    - 模板管理面板
    - 生成和批量生成功能
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化核心组件
        self.validator = ISBNValidator()
        self.encoder = EAN13Encoder()
        self.addon_encoder = AddonEncoder()
        self.renderer = TIFRenderer()
        
        # 模板管理器（使用用户目录下的templates文件夹）
        templates_dir = os.path.join(os.path.expanduser("~"), ".isbn_barcode_generator", "templates")
        self.template_manager = TemplateManager(templates_dir)
        
        # 批量处理器
        self.batch_processor = BatchProcessor(
            self.validator, self.encoder, self.addon_encoder, self.renderer,
            self.template_manager
        )
        
        # 当前配置
        self.current_config = self.template_manager.get_default_template()
        
        # 颜色值
        self.foreground_color = (0, 0, 0)
        self.background_color = (255, 255, 255)
        
        # 批量ISBN列表
        self.batch_isbn_list: list[str] = []
        
        # 工作线程
        self.batch_worker: Optional[BatchWorker] = None
        
        # 设置UI
        self._setup_ui()
        
        # 应用现代化样式
        self._apply_modern_style()
        
        # 加载默认配置
        self._load_default_config()

    
    def _set_window_icon(self) -> None:
        """设置窗口图标"""
        # 尝试多个可能的图标路径
        icon_paths = [
            # 相对于模块的路径
            os.path.join(os.path.dirname(__file__), "..", "resources", "icon.ico"),
            os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png"),
            # 相对于工作目录的路径
            os.path.join("src", "isbn_barcode_generator", "resources", "icon.ico"),
            os.path.join("src", "isbn_barcode_generator", "resources", "icon.png"),
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                # 同时设置应用程序图标（用于任务栏）
                QApplication.instance().setWindowIcon(QIcon(icon_path))
                break

    def _apply_modern_style(self) -> None:
        """应用现代化视觉样式"""
        self.setStyleSheet("""
            /* 主窗口背景 */
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            /* 分组框样式 */
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                color: #333;
            }
            
            /* 按钮样式 */
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
                min-height: 24px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #ccc;
                color: #888;
            }
            
            /* 输入框样式 */
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 10px;
                background-color: white;
                font-size: 12px;
            }
            
            QLineEdit:focus {
                border-color: #0078d4;
            }
            
            QLineEdit:disabled {
                background-color: #f0f0f0;
            }
            
            /* 下拉框样式 */
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
                background-color: white;
                font-size: 12px;
                min-height: 24px;
            }
            
            QComboBox:focus {
                border-color: #0078d4;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            
            /* 数值输入框样式 - 使用系统默认样式显示箭头 */
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #0078d4;
            }
            
            /* 复选框样式 */
            QCheckBox {
                font-size: 12px;
                spacing: 8px;
            }
            
            /* 标签样式 */
            QLabel {
                font-size: 12px;
                color: #333;
            }
            
            /* 进度条样式 */
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
            
            /* 状态栏样式 */
            QStatusBar {
                background-color: #f0f0f0;
                border-top: 1px solid #ddd;
                font-size: 11px;
            }
            
            /* 菜单栏样式 */
            QMenuBar {
                background-color: white;
                border-bottom: 1px solid #ddd;
                padding: 2px;
            }
            
            QMenuBar::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            
            QMenuBar::item:selected {
                background-color: #e5e5e5;
            }
            
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
            }
            
            QMenu::item {
                padding: 6px 30px 6px 20px;
                border-radius: 3px;
            }
            
            QMenu::item:selected {
                background-color: #0078d4;
                color: white;
            }
            
            /* 滚动区域样式 */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            /* 分割器样式 */
            QSplitter::handle {
                background-color: #ddd;
                width: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #0078d4;
            }
            
            /* 字体选择框样式 - 使用系统默认样式 */
            QFontComboBox:focus {
                border-color: #0078d4;
            }
        """)

    
    def _setup_ui(self) -> None:
        """初始化UI组件"""
        # 设置窗口属性
        self.setWindowTitle("ISBN条码生成器")
        self.setMinimumSize(1000, 770)
        self.resize(1200, 880)
        
        # 设置窗口图标
        self._set_window_icon()
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 左侧面板（设置区域）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 添加各个面板
        left_layout.addWidget(self._create_input_panel())
        left_layout.addWidget(self._create_settings_panel())
        left_layout.addWidget(self._create_text_style_panel())
        left_layout.addWidget(self._create_template_panel())
        left_layout.addWidget(self._create_generate_panel())
        left_layout.addStretch()
        
        # 右侧面板（预览区域）
        right_panel = self._create_preview_panel()
        
        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧滚动区域
        left_scroll = QScrollArea()
        left_scroll.setWidget(left_panel)
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(480)
        left_scroll.setMaximumWidth(600)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        splitter.addWidget(left_scroll)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)

    
    def _create_menu_bar(self) -> None:
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打开ISBN列表(&O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_isbn_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 模板菜单
        template_menu = menubar.addMenu("模板(&T)")
        
        save_template_action = QAction("保存模板(&S)...", self)
        save_template_action.triggered.connect(self._save_template)
        template_menu.addAction(save_template_action)
        
        load_template_action = QAction("加载模板(&L)...", self)
        load_template_action.triggered.connect(self._load_template_dialog)
        template_menu.addAction(load_template_action)
        
        template_menu.addSeparator()
        
        reset_action = QAction("重置为默认(&R)", self)
        reset_action.triggered.connect(self._reset_to_default)
        template_menu.addAction(reset_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)


    def _create_input_panel(self) -> QWidget:
        """创建ISBN输入面板"""
        group = QGroupBox("ISBN输入")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # 单个ISBN输入
        isbn_layout = QHBoxLayout()
        isbn_label = QLabel("ISBN:")
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("输入ISBN-13 (如: 978-7-5649-2235-1)")
        self.isbn_input.textChanged.connect(self._on_isbn_changed)
        isbn_layout.addWidget(isbn_label)
        isbn_layout.addWidget(self.isbn_input)
        layout.addLayout(isbn_layout)
        
        # 附加码选项（移到批量导入上面）
        addon_layout = QHBoxLayout()
        addon_label = QLabel("附加码:")
        self.addon_type_combo = QComboBox()
        self.addon_type_combo.addItems(["无", "2位附加码", "5位附加码"])
        self.addon_type_combo.currentIndexChanged.connect(self._on_addon_type_changed)
        
        self.addon_input = QLineEdit()
        self.addon_input.setPlaceholderText("附加码数字")
        self.addon_input.setMaxLength(5)
        self.addon_input.setEnabled(False)
        self.addon_input.textChanged.connect(self._update_preview)
        
        addon_layout.addWidget(addon_label)
        addon_layout.addWidget(self.addon_type_combo)
        addon_layout.addWidget(self.addon_input)
        layout.addLayout(addon_layout)
        
        # 批量导入
        batch_layout = QHBoxLayout()
        self.batch_btn = QPushButton("批量导入...")
        self.batch_btn.clicked.connect(self._open_isbn_file)
        self.batch_count_label = QLabel("已导入: 0 个ISBN")
        batch_layout.addWidget(self.batch_btn)
        batch_layout.addWidget(self.batch_count_label)
        batch_layout.addStretch()
        layout.addLayout(batch_layout)
        
        return group

    
    def _create_settings_panel(self) -> QWidget:
        """创建设置面板"""
        group = QGroupBox("图像设置")
        layout = QGridLayout(group)
        layout.setSpacing(8)
        layout.setHorizontalSpacing(10)
        # 设置列宽：标签 | 控件 | 间隔 | 标签 | 控件（两列控件等宽）
        layout.setColumnStretch(0, 0)  # 左列标签
        layout.setColumnStretch(1, 1)  # 左列控件
        layout.setColumnStretch(2, 0)  # 中间间隔
        layout.setColumnMinimumWidth(2, 15)  # 中间留空
        layout.setColumnStretch(3, 0)  # 右列标签
        layout.setColumnStretch(4, 1)  # 右列控件（与左列控件相同stretch）
        
        row = 0
        
        # 第一行：分辨率 | 颜色模式
        layout.addWidget(QLabel("分辨率(DPI):"), row, 0)
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["150", "300", "600", "1200"])
        self.dpi_combo.setCurrentText("300")
        self.dpi_combo.setEditable(True)
        self.dpi_combo.currentTextChanged.connect(self._update_preview)
        layout.addWidget(self.dpi_combo, row, 1)
        
        layout.addWidget(QLabel("颜色模式:"), row, 3)
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["1位黑白", "8位灰度", "RGB", "CMYK"])
        self.color_mode_combo.currentIndexChanged.connect(self._update_preview)
        layout.addWidget(self.color_mode_combo, row, 4)
        row += 1
        
        # 第二行：宽度 | 高度
        layout.addWidget(QLabel("宽度(mm):"), row, 0)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(10, 200)
        self.width_spin.setValue(37.29)
        self.width_spin.setDecimals(2)
        self.width_spin.setFixedHeight(40)  # 统一高度
        self.width_spin.valueChanged.connect(self._on_width_changed)
        layout.addWidget(self.width_spin, row, 1)
        
        layout.addWidget(QLabel("高度(mm):"), row, 3)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(10, 200)
        self.height_spin.setValue(25.93)
        self.height_spin.setDecimals(2)
        self.height_spin.setFixedHeight(40)  # 统一高度
        self.height_spin.valueChanged.connect(self._on_height_changed)
        layout.addWidget(self.height_spin, row, 4)
        row += 1
        
        # 锁定宽高比 和 显示静区标记 在同一行
        self.lock_ratio_check = QCheckBox("锁定宽高比")
        self.lock_ratio_check.setChecked(True)
        layout.addWidget(self.lock_ratio_check, row, 0, 1, 2)
        
        self.quiet_zone_check = QCheckBox("显示静区标记")
        self.quiet_zone_check.setChecked(True)  # 默认开启
        self.quiet_zone_check.stateChanged.connect(self._update_preview)
        layout.addWidget(self.quiet_zone_check, row, 3, 1, 2)
        row += 1
        
        # 前景色 和 背景色 在同一行
        layout.addWidget(QLabel("前景色:"), row, 0)
        self.fg_color_btn = QPushButton()
        self.fg_color_btn.setFixedSize(60, 25)
        self.fg_color_btn.setStyleSheet("background-color: black;")
        self.fg_color_btn.clicked.connect(self._choose_foreground_color)
        layout.addWidget(self.fg_color_btn, row, 1)
        
        layout.addWidget(QLabel("背景色:"), row, 3)
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(60, 25)
        self.bg_color_btn.setStyleSheet("background-color: white; border: 1px solid gray;")
        self.bg_color_btn.clicked.connect(self._choose_background_color)
        layout.addWidget(self.bg_color_btn, row, 4)
        
        return group

    
    def _create_text_style_panel(self) -> QWidget:
        """创建文字样式面板"""
        group = QGroupBox("文字样式")
        layout = QGridLayout(group)
        layout.setSpacing(8)
        layout.setHorizontalSpacing(10)
        # 设置列宽：标签 | 控件 | 间隔 | 标签 | 控件（两列控件等宽）
        layout.setColumnStretch(0, 0)  # 左列标签
        layout.setColumnStretch(1, 1)  # 左列控件
        layout.setColumnStretch(2, 0)  # 中间间隔
        layout.setColumnMinimumWidth(2, 15)  # 中间留空
        layout.setColumnStretch(3, 0)  # 右列标签
        layout.setColumnStretch(4, 1)  # 右列控件（与左列控件相同stretch）
        # 设置两列控件的最小宽度一致
        layout.setColumnMinimumWidth(1, 120)
        layout.setColumnMinimumWidth(4, 120)
        
        row = 0
        
        # 第一行：字体 | 字号
        layout.addWidget(QLabel("字体:"), row, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.setMaximumWidth(150)  # 限制字体选择框最大宽度
        self.font_combo.setFixedHeight(40)  # 固定高度
        self.font_combo.currentFontChanged.connect(self._update_preview)
        layout.addWidget(self.font_combo, row, 1)
        
        layout.addWidget(QLabel("字号:"), row, 3)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 999)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setFixedHeight(40)  # 与字体选择框高度一致
        self.font_size_spin.valueChanged.connect(self._update_preview)
        layout.addWidget(self.font_size_spin, row, 4)
        row += 1
        
        # 第二行：字间距 | 对齐方式
        layout.addWidget(QLabel("字间距:"), row, 0)
        self.letter_spacing_spin = QDoubleSpinBox()
        self.letter_spacing_spin.setRange(-5, 20)
        self.letter_spacing_spin.setValue(0)
        self.letter_spacing_spin.setDecimals(1)
        self.letter_spacing_spin.setFixedHeight(40)  # 统一高度
        self.letter_spacing_spin.valueChanged.connect(self._update_preview)
        layout.addWidget(self.letter_spacing_spin, row, 1)
        
        layout.addWidget(QLabel("对齐方式:"), row, 3)
        self.align_combo = QComboBox()
        self.align_combo.addItems(["居中", "左对齐", "右对齐"])
        self.align_combo.setFixedHeight(40)  # 统一高度
        self.align_combo.currentIndexChanged.connect(self._update_preview)
        layout.addWidget(self.align_combo, row, 4)
        row += 1
        
        # 第三行：ISBN文本偏移 | 数字偏移
        layout.addWidget(QLabel("ISBN偏移:"), row, 0)
        self.isbn_offset_spin = QSpinBox()
        self.isbn_offset_spin.setRange(0, 50)
        self.isbn_offset_spin.setValue(5)
        self.isbn_offset_spin.setFixedHeight(40)  # 统一高度
        self.isbn_offset_spin.valueChanged.connect(self._update_preview)
        layout.addWidget(self.isbn_offset_spin, row, 1)
        
        layout.addWidget(QLabel("数字偏移:"), row, 3)
        self.digits_offset_spin = QSpinBox()
        self.digits_offset_spin.setRange(0, 50)
        self.digits_offset_spin.setValue(2)
        self.digits_offset_spin.setFixedHeight(40)  # 统一高度
        self.digits_offset_spin.valueChanged.connect(self._update_preview)
        layout.addWidget(self.digits_offset_spin, row, 4)
        
        return group


    def _create_preview_panel(self) -> QWidget:
        """创建预览面板"""
        group = QGroupBox("条码预览")
        layout = QVBoxLayout(group)
        
        # 预览图像标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        self.preview_label.setText("输入ISBN后显示预览")
        
        layout.addWidget(self.preview_label, 1)
        
        # 预览信息
        self.preview_info_label = QLabel()
        self.preview_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_info_label)
        
        return group
    
    def _create_template_panel(self) -> QWidget:
        """创建模板管理面板"""
        group = QGroupBox("模板管理")
        layout = QHBoxLayout(group)
        layout.setSpacing(8)
        
        # 模板选择下拉框
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(150)
        self._refresh_template_list()
        layout.addWidget(self.template_combo)
        
        # 加载按钮
        load_btn = QPushButton("加载")
        load_btn.clicked.connect(self._load_selected_template)
        layout.addWidget(load_btn)
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_template)
        layout.addWidget(save_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self._delete_template)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        return group
    
    def _create_generate_panel(self) -> QWidget:
        """创建生成面板"""
        group = QGroupBox("生成")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # 输出目录
        dir_layout = QHBoxLayout()
        dir_label = QLabel("输出目录:")
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("选择输出目录...")
        self.output_dir_input.setText(os.path.expanduser("~/Desktop/ISBN"))
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_output_dir)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.output_dir_input)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)
        
        # 生成按钮
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成条码")
        self.generate_btn.setMinimumHeight(35)
        self.generate_btn.clicked.connect(self._generate_barcode)
        
        self.batch_generate_btn = QPushButton("批量生成")
        self.batch_generate_btn.setMinimumHeight(35)
        self.batch_generate_btn.clicked.connect(self._batch_generate)
        
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.batch_generate_btn)
        layout.addLayout(btn_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 进度信息
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        return group

    
    def _update_preview(self) -> None:
        """更新预览图像"""
        isbn_text = self.isbn_input.text().strip()
        
        if not isbn_text:
            self.preview_label.setText("输入ISBN后显示预览")
            self.preview_info_label.setText("")
            return
        
        # 验证ISBN
        parsed = self.validator.parse(isbn_text)
        if not parsed.is_valid:
            self.preview_label.setText(f"无效的ISBN: {parsed.error_message}")
            self.preview_info_label.setText("")
            return
        
        try:
            # 获取当前配置
            config = self._get_current_config(parsed)
            
            # 渲染图像
            image = self.renderer.render(config)
            
            # 转换为QPixmap显示
            pixmap = self._pil_to_pixmap(image)
            
            # 缩放以适应预览区域
            scaled_pixmap = pixmap.scaled(
                self.preview_label.size() - QSize(20, 20),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled_pixmap)
            
            # 显示图像信息
            dpi = int(self.dpi_combo.currentText() or "300")
            width_mm = self.width_spin.value()
            height_mm = self.height_spin.value()
            self.preview_info_label.setText(
                f"尺寸: {width_mm:.2f}mm × {height_mm:.2f}mm | "
                f"分辨率: {dpi} DPI | "
                f"像素: {image.width} × {image.height}"
            )
            
        except Exception as e:
            self.preview_label.setText(f"预览错误: {str(e)}")
            self.preview_info_label.setText("")

    
    def _get_current_config(self, parsed: ParsedISBN) -> RenderConfig:
        """获取当前配置"""
        # 编码条码
        barcode_pattern = self.encoder.encode(parsed.digits)
        
        # 处理附加码
        addon_pattern = None
        addon_digits = None
        addon_type = self.addon_type_combo.currentIndex()
        
        if addon_type > 0:
            addon_text = self.addon_input.text().strip()
            if addon_type == 1 and len(addon_text) == 2 and addon_text.isdigit():
                addon_pattern = self.addon_encoder.encode_2(addon_text)
                addon_digits = addon_text
            elif addon_type == 2 and len(addon_text) == 5 and addon_text.isdigit():
                addon_pattern = self.addon_encoder.encode_5(addon_text)
                addon_digits = addon_text
        
        # 获取颜色模式
        color_mode_map = {
            0: ColorMode.BITMAP,
            1: ColorMode.GRAYSCALE,
            2: ColorMode.RGB,
            3: ColorMode.CMYK
        }
        color_mode = color_mode_map.get(self.color_mode_combo.currentIndex(), ColorMode.BITMAP)
        
        # 获取对齐方式
        align_map = {
            0: TextAlignment.CENTER,
            1: TextAlignment.LEFT,
            2: TextAlignment.RIGHT
        }
        text_alignment = align_map.get(self.align_combo.currentIndex(), TextAlignment.CENTER)
        
        # 获取DPI
        try:
            dpi = int(self.dpi_combo.currentText())
        except ValueError:
            dpi = 300
        
        return RenderConfig(
            isbn=parsed,
            barcode_pattern=barcode_pattern,
            addon_pattern=addon_pattern,
            addon_digits=addon_digits,
            dpi=dpi,
            width_mm=self.width_spin.value(),
            height_mm=self.height_spin.value(),
            lock_aspect_ratio=self.lock_ratio_check.isChecked(),
            color_mode=color_mode,
            foreground_color=self.foreground_color,
            background_color=self.background_color,
            font_family=self.font_combo.currentFont().family(),
            font_size=self.font_size_spin.value(),
            letter_spacing=self.letter_spacing_spin.value(),
            isbn_text_offset_y=self.isbn_offset_spin.value(),
            digits_offset_y=self.digits_offset_spin.value(),
            text_alignment=text_alignment,
            show_quiet_zone_indicator=self.quiet_zone_check.isChecked()
        )
    
    def _pil_to_pixmap(self, pil_image) -> QPixmap:
        """将PIL图像转换为QPixmap"""
        # 转换为RGB模式（如果需要）
        if pil_image.mode == "1":
            pil_image = pil_image.convert("L")
        if pil_image.mode == "CMYK":
            pil_image = pil_image.convert("RGB")
        if pil_image.mode == "L":
            pil_image = pil_image.convert("RGB")
        
        # 转换为QImage
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(data, pil_image.width, pil_image.height, 
                       pil_image.width * 3, QImage.Format.Format_RGB888)
        
        return QPixmap.fromImage(qimage)


    def _generate_barcode(self) -> None:
        """生成条码"""
        isbn_text = self.isbn_input.text().strip()
        
        if not isbn_text:
            QMessageBox.warning(self, "警告", "请输入ISBN号")
            return
        
        # 验证ISBN
        parsed = self.validator.parse(isbn_text)
        if not parsed.is_valid:
            QMessageBox.warning(self, "验证失败", f"无效的ISBN: {parsed.error_message}")
            return
        
        # 获取输出目录
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 获取配置
            config = self._get_current_config(parsed)
            
            # 渲染图像
            image = self.renderer.render(config)
            
            # 保存文件
            output_path = os.path.join(output_dir, f"{parsed.digits}.tif")
            tif_config = TIFConfig(dpi=config.dpi)
            self.renderer.save_tif(image, output_path, tif_config)
            
            self.status_bar.showMessage(f"条码已保存: {output_path}")
            QMessageBox.information(self, "成功", f"条码已保存到:\n{output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成条码失败: {str(e)}")
    
    def _batch_generate(self) -> None:
        """批量生成条码"""
        if not self.batch_isbn_list:
            QMessageBox.warning(self, "警告", "请先导入ISBN列表")
            return
        
        # 获取输出目录
        output_dir = self.output_dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取当前配置（使用第一个有效ISBN作为模板）
        for isbn in self.batch_isbn_list:
            parsed = self.validator.parse(isbn)
            if parsed.is_valid:
                config = self._get_current_config(parsed)
                break
        else:
            QMessageBox.warning(self, "警告", "没有有效的ISBN")
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.batch_isbn_list))
        
        # 禁用按钮
        self.generate_btn.setEnabled(False)
        self.batch_generate_btn.setEnabled(False)
        
        # 创建工作线程
        self.batch_worker = BatchWorker(
            self.batch_processor, self.batch_isbn_list, output_dir, config
        )
        self.batch_worker.progress.connect(self._on_batch_progress)
        self.batch_worker.finished.connect(self._on_batch_finished)
        self.batch_worker.start()
    
    def _on_batch_progress(self, current: int, total: int, isbn: str) -> None:
        """批量处理进度更新"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"正在处理: {isbn} ({current}/{total})")
    
    def _on_batch_finished(self, result: BatchResult) -> None:
        """批量处理完成"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # 启用按钮
        self.generate_btn.setEnabled(True)
        self.batch_generate_btn.setEnabled(True)
        
        # 显示结果
        message = f"批量生成完成!\n\n成功: {result.success}\n失败: {result.failed}"
        if result.errors:
            message += "\n\n失败列表:\n"
            for error in result.errors[:10]:  # 最多显示10个
                message += f"  {error.isbn}: {error.error_message}\n"
            if len(result.errors) > 10:
                message += f"  ... 还有 {len(result.errors) - 10} 个失败"
        
        self.status_bar.showMessage(f"批量生成完成: 成功 {result.success}, 失败 {result.failed}")
        QMessageBox.information(self, "批量生成完成", message)

    
    def _on_isbn_changed(self, text: str) -> None:
        """ISBN输入变化"""
        self._update_preview()
    
    def _on_addon_type_changed(self, index: int) -> None:
        """附加码类型变化"""
        if index == 0:
            self.addon_input.setEnabled(False)
            self.addon_input.clear()
            # 选择无附加码时，加载默认配置
            config = self.template_manager.get_default_template()
            self._apply_config(config)
            self.status_bar.showMessage("已加载无附加码默认配置")
        elif index == 1:
            self.addon_input.setEnabled(True)
            self.addon_input.setMaxLength(2)
            self.addon_input.setPlaceholderText("2位数字")
            # 选择2位附加码时，加载2位附加码内置配置
            config = self.template_manager.get_addon_2_template()
            self._apply_config(config)
            self.status_bar.showMessage("已加载2位附加码默认配置")
        else:
            self.addon_input.setEnabled(True)
            self.addon_input.setMaxLength(5)
            self.addon_input.setPlaceholderText("5位数字")
            # 选择5位附加码时，尝试加载"5位附加码"模板
            self._try_load_template("5位附加码")
        
        self._update_preview()
    
    def _try_load_template(self, name: str) -> None:
        """尝试加载指定模板，如果不存在则静默忽略"""
        try:
            if self.template_manager.template_exists(name):
                config = self.template_manager.load_template(name)
                self._apply_config(config)
                self.status_bar.showMessage(f"已自动加载模板 '{name}'")
        except Exception:
            pass  # 静默忽略错误
    
    def _on_width_changed(self, value: float) -> None:
        """宽度变化时处理宽高比锁定"""
        if self.lock_ratio_check.isChecked():
            # 计算新高度
            aspect_ratio = 37.29 / 25.93  # 标准宽高比
            new_height = value / aspect_ratio
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(new_height)
            self.height_spin.blockSignals(False)
        
        self._update_preview()
    
    def _on_height_changed(self, value: float) -> None:
        """高度变化时处理宽高比锁定"""
        if self.lock_ratio_check.isChecked():
            # 计算新宽度
            aspect_ratio = 37.29 / 25.93  # 标准宽高比
            new_width = value * aspect_ratio
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(new_width)
            self.width_spin.blockSignals(False)
        
        self._update_preview()
    
    def _choose_foreground_color(self) -> None:
        """选择前景色"""
        color = QColorDialog.getColor(QColor(*self.foreground_color), self, "选择前景色")
        if color.isValid():
            self.foreground_color = (color.red(), color.green(), color.blue())
            self.fg_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self._update_preview()
    
    def _choose_background_color(self) -> None:
        """选择背景色"""
        color = QColorDialog.getColor(QColor(*self.background_color), self, "选择背景色")
        if color.isValid():
            self.background_color = (color.red(), color.green(), color.blue())
            self.bg_color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            self._update_preview()
    
    def _browse_output_dir(self) -> None:
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_dir_input.text()
        )
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def _open_isbn_file(self) -> None:
        """打开ISBN文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开ISBN列表", "",
            "文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 解析ISBN列表
                self.batch_isbn_list = []
                for line in lines:
                    isbn = line.strip()
                    if isbn and not isbn.startswith('#'):
                        # 处理CSV格式（取第一列）
                        if ',' in isbn:
                            isbn = isbn.split(',')[0].strip()
                        self.batch_isbn_list.append(isbn)
                
                self.batch_count_label.setText(f"已导入: {len(self.batch_isbn_list)} 个ISBN")
                self.status_bar.showMessage(f"已导入 {len(self.batch_isbn_list)} 个ISBN")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")

    
    def _save_template(self) -> None:
        """保存当前配置为模板"""
        name, ok = QInputDialog.getText(self, "保存模板", "模板名称:")
        
        if ok and name:
            try:
                config = {
                    "dpi": int(self.dpi_combo.currentText() or "300"),
                    "width_mm": self.width_spin.value(),
                    "height_mm": self.height_spin.value(),
                    "width_px": None,
                    "height_px": None,
                    "lock_aspect_ratio": self.lock_ratio_check.isChecked(),
                    "color_mode": ["BITMAP", "GRAYSCALE", "RGB", "CMYK"][self.color_mode_combo.currentIndex()],
                    "foreground_color": list(self.foreground_color),
                    "background_color": list(self.background_color),
                    "font_family": self.font_combo.currentFont().family(),
                    "font_size": self.font_size_spin.value(),
                    "letter_spacing": self.letter_spacing_spin.value(),
                    "isbn_text_offset_y": self.isbn_offset_spin.value(),
                    "digits_offset_y": self.digits_offset_spin.value(),
                    "text_alignment": ["center", "left", "right"][self.align_combo.currentIndex()],
                    "show_quiet_zone_indicator": self.quiet_zone_check.isChecked()
                }
                
                self.template_manager.save_template(name, config)
                self._refresh_template_list()
                self.status_bar.showMessage(f"模板 '{name}' 已保存")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存模板失败: {str(e)}")
    
    def _load_selected_template(self) -> None:
        """加载选中的模板"""
        name = self.template_combo.currentText()
        if not name:
            return
        
        try:
            config = self.template_manager.load_template(name)
            self._apply_config(config)
            self.status_bar.showMessage(f"模板 '{name}' 已加载")
        except FileNotFoundError:
            QMessageBox.warning(self, "警告", f"模板 '{name}' 不存在")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败: {str(e)}")
    
    def _load_template_dialog(self) -> None:
        """显示加载模板对话框"""
        templates = self.template_manager.list_templates()
        if not templates:
            QMessageBox.information(self, "提示", "没有已保存的模板")
            return
        
        name, ok = QInputDialog.getItem(
            self, "加载模板", "选择模板:", templates, 0, False
        )
        
        if ok and name:
            try:
                config = self.template_manager.load_template(name)
                self._apply_config(config)
                self.status_bar.showMessage(f"模板 '{name}' 已加载")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载模板失败: {str(e)}")
    
    def _delete_template(self) -> None:
        """删除选中的模板"""
        name = self.template_combo.currentText()
        if not name:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除模板 '{name}' 吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.template_manager.delete_template(name)
                self._refresh_template_list()
                self.status_bar.showMessage(f"模板 '{name}' 已删除")
            except FileNotFoundError:
                QMessageBox.warning(self, "警告", f"模板 '{name}' 不存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除模板失败: {str(e)}")
    
    def _refresh_template_list(self) -> None:
        """刷新模板列表"""
        self.template_combo.clear()
        templates = self.template_manager.list_templates()
        self.template_combo.addItems(templates)
    
    def _reset_to_default(self) -> None:
        """重置为默认配置"""
        config = self.template_manager.get_default_template()
        self._apply_config(config)
        self.status_bar.showMessage("已重置为默认配置")

    
    def _apply_config(self, config: dict) -> None:
        """应用配置到UI"""
        # 阻止信号触发
        self.dpi_combo.blockSignals(True)
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.color_mode_combo.blockSignals(True)
        self.font_combo.blockSignals(True)
        self.font_size_spin.blockSignals(True)
        self.letter_spacing_spin.blockSignals(True)
        self.isbn_offset_spin.blockSignals(True)
        self.digits_offset_spin.blockSignals(True)
        self.align_combo.blockSignals(True)
        self.quiet_zone_check.blockSignals(True)
        
        try:
            # 应用配置
            if "dpi" in config:
                self.dpi_combo.setCurrentText(str(config["dpi"]))
            
            if "width_mm" in config:
                self.width_spin.setValue(config["width_mm"])
            
            if "height_mm" in config:
                self.height_spin.setValue(config["height_mm"])
            
            if "lock_aspect_ratio" in config:
                self.lock_ratio_check.setChecked(config["lock_aspect_ratio"])
            
            if "color_mode" in config:
                mode_map = {"BITMAP": 0, "GRAYSCALE": 1, "RGB": 2, "CMYK": 3}
                self.color_mode_combo.setCurrentIndex(mode_map.get(config["color_mode"], 0))
            
            if "foreground_color" in config:
                self.foreground_color = tuple(config["foreground_color"])
                color = QColor(*self.foreground_color)
                self.fg_color_btn.setStyleSheet(f"background-color: {color.name()};")
            
            if "background_color" in config:
                self.background_color = tuple(config["background_color"])
                color = QColor(*self.background_color)
                self.bg_color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
            
            if "font_family" in config:
                self.font_combo.setCurrentFont(QFont(config["font_family"]))
            
            if "font_size" in config:
                self.font_size_spin.setValue(config["font_size"])
            
            if "letter_spacing" in config:
                self.letter_spacing_spin.setValue(config["letter_spacing"])
            
            if "isbn_text_offset_y" in config:
                self.isbn_offset_spin.setValue(config["isbn_text_offset_y"])
            
            if "digits_offset_y" in config:
                self.digits_offset_spin.setValue(config["digits_offset_y"])
            
            if "text_alignment" in config:
                align_map = {"center": 0, "left": 1, "right": 2}
                self.align_combo.setCurrentIndex(align_map.get(config["text_alignment"], 0))
            
            if "show_quiet_zone_indicator" in config:
                self.quiet_zone_check.setChecked(config["show_quiet_zone_indicator"])
                
        finally:
            # 恢复信号
            self.dpi_combo.blockSignals(False)
            self.width_spin.blockSignals(False)
            self.height_spin.blockSignals(False)
            self.color_mode_combo.blockSignals(False)
            self.font_combo.blockSignals(False)
            self.font_size_spin.blockSignals(False)
            self.letter_spacing_spin.blockSignals(False)
            self.isbn_offset_spin.blockSignals(False)
            self.digits_offset_spin.blockSignals(False)
            self.align_combo.blockSignals(False)
            self.quiet_zone_check.blockSignals(False)
        
        # 更新预览
        self._update_preview()
    
    def _load_default_config(self) -> None:
        """加载默认配置"""
        config = self.template_manager.get_default_template()
        self._apply_config(config)
    
    def _show_about(self) -> None:
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 ISBN条码生成器",
            "ISBN条码生成器 v1.0\n\n"
            "一个专业的ISBN-13条码生成工具，支持：\n"
            "• EAN-13条码生成\n"
            "• 2位和5位附加码\n"
            "• 多种颜色模式\n"
            "• 自定义尺寸和样式\n"
            "• 批量生成\n"
            "• 模板管理\n\n"
            "符合GS1国际标准"
        )


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("ISBN条码生成器")
    app.setOrganizationName("ISBN Barcode Generator")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
