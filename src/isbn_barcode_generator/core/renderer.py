"""
TIF Renderer - TIF图像渲染模块

本模块负责将条码数据渲染为TIF格式图像文件。
支持多种颜色模式、自定义尺寸、文字样式配置等功能。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Tuple, Optional

if TYPE_CHECKING:
    from PIL import Image, ImageDraw

from .validator import ParsedISBN
from .encoder import BarcodePattern


class ColorMode(Enum):
    """颜色模式枚举
    
    支持的颜色模式：
    - BITMAP: 1位黑白二值图像
    - GRAYSCALE: 8位灰度图像
    - RGB: RGB彩色图像
    - CMYK: CMYK印刷色图像
    """
    BITMAP = "1"        # 1位黑白
    GRAYSCALE = "L"     # 8位灰度
    RGB = "RGB"         # RGB彩色
    CMYK = "CMYK"       # CMYK印刷色


class TextAlignment(Enum):
    """文字对齐方式枚举"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class TIFConfig:
    """TIF文件保存配置
    
    Attributes:
        dpi: 图像分辨率（每英寸点数）
        compression: TIF压缩方式，默认使用LZW压缩
    """
    dpi: int = 300
    compression: str = "tiff_lzw"


@dataclass
class RenderConfig:
    """条码渲染配置
    
    包含生成条码图像所需的所有配置参数。
    
    Attributes:
        isbn: 解析后的ISBN数据
        barcode_pattern: EAN-13条码图案
        addon_pattern: 附加码图案（可选）
        addon_digits: 附加码数字（可选）
        dpi: 分辨率（默认300 DPI）
        width_mm: 图像宽度（毫米）
        height_mm: 图像高度（毫米）
        width_px: 图像宽度（像素）
        height_px: 图像高度（像素）
        lock_aspect_ratio: 是否锁定宽高比
        color_mode: 颜色模式
        foreground_color: 前景色（条码颜色）
        background_color: 背景色
        font_family: 字体名称
        font_size: 字号（磅）
        letter_spacing: 字符间距
        isbn_text_offset_y: ISBN文本距条码顶部距离（像素）
        digits_offset_y: 数字距条码底部距离（像素）
        text_alignment: 文字对齐方式
        show_quiet_zone_indicator: 是否显示静区标记（默认开启）
    """
    isbn: ParsedISBN
    barcode_pattern: BarcodePattern
    addon_pattern: Optional[BarcodePattern] = None
    addon_digits: Optional[str] = None
    
    # 图像设置
    dpi: int = 300
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    lock_aspect_ratio: bool = True
    
    # 颜色设置
    color_mode: ColorMode = ColorMode.BITMAP
    foreground_color: Tuple[int, ...] = (0, 0, 0)
    background_color: Tuple[int, ...] = (255, 255, 255)
    
    # 文字设置
    font_family: str = "Arial"
    font_size: int = 10
    letter_spacing: float = 0
    isbn_text_offset_y: int = 5      # ISBN文本距条码顶部距离
    digits_offset_y: int = 2          # 数字距条码底部距离
    text_alignment: TextAlignment = TextAlignment.CENTER
    
    # 静区标记设置
    show_quiet_zone_indicator: bool = True  # 是否显示静区标记


class TIFRenderer:
    """条码图像渲染器
    
    负责将条码数据渲染为TIF格式图像文件。
    支持多种颜色模式、自定义尺寸、文字样式配置等功能。
    
    GS1标准EAN-13条码尺寸（100%放大率）：
    - 标准宽度：37.29mm（包含静区）
    - 标准高度：25.93mm（包含文字）
    - 模块宽度：0.33mm
    - 条码高度：22.85mm
    """
    
    # GS1标准尺寸常量（毫米）
    STANDARD_MODULE_WIDTH_MM = 0.33  # 标准模块宽度
    STANDARD_BARCODE_HEIGHT_MM = 22.85  # 标准条码高度
    STANDARD_TOTAL_WIDTH_MM = 37.29  # 标准总宽度（含静区）
    STANDARD_TOTAL_HEIGHT_MM = 25.93  # 标准总高度（含文字）
    
    # EAN-13条码模块数
    EAN13_MODULES = 95  # 主条码模块数
    LEFT_QUIET_ZONE_MODULES = 11  # 左侧静区模块数
    RIGHT_QUIET_ZONE_MODULES = 7  # 右侧静区模块数
    
    # 附加码间距
    ADDON_GAP_MODULES = 7  # 主条码与附加码之间的间距模块数
    
    def __init__(self):
        """初始化渲染器"""
        self._pil_available = True
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            self._pil_available = False
    
    def render(self, config: RenderConfig) -> "Image.Image":
        """渲染条码图像
        
        Args:
            config: 渲染配置对象
            
        Returns:
            PIL.Image.Image: 渲染后的图像对象
            
        Raises:
            ImportError: 如果PIL库未安装
            ValueError: 如果配置参数无效
        """
        from PIL import Image, ImageDraw
        
        # 计算图像尺寸
        width_px, height_px = self._calculate_image_size(config)
        
        # 计算模块宽度（像素）
        module_width_px = self._calculate_module_width(config, width_px)
        
        # 创建图像
        pil_mode = self._get_pil_mode(config.color_mode)
        bg_color = self._convert_color(config.background_color, config.color_mode)
        image = Image.new(pil_mode, (width_px, height_px), bg_color)
        draw = ImageDraw.Draw(image)
        
        # 计算条码绘制区域
        barcode_area = self._calculate_barcode_area(config, width_px, height_px, module_width_px)
        
        # 绘制主条码
        self._draw_barcode(draw, config.barcode_pattern, config, barcode_area, module_width_px)
        
        # 绘制附加码（如果有）
        if config.addon_pattern and config.addon_digits:
            addon_area = self._calculate_addon_area(barcode_area, config, module_width_px)
            self._draw_addon(draw, config.addon_pattern, config, addon_area, module_width_px)
        
        # 绘制文字
        self._draw_text(draw, config, barcode_area, module_width_px)
        
        # 绘制静区标记（如果启用）
        if config.show_quiet_zone_indicator:
            self._draw_quiet_zone_indicators(draw, config, barcode_area, module_width_px, width_px)
        
        return image
    
    def save_tif(self, image: "Image.Image", path: str, config: TIFConfig) -> None:
        """保存为TIF文件
        
        Args:
            image: PIL图像对象
            path: 输出文件路径
            config: TIF配置对象
        """
        # 设置DPI信息
        dpi = (config.dpi, config.dpi)
        
        # 保存TIF文件
        image.save(
            path,
            format='TIFF',
            dpi=dpi,
            compression=config.compression
        )
    
    def _calculate_image_size(self, config: RenderConfig) -> Tuple[int, int]:
        """计算图像尺寸（像素）
        
        根据配置计算最终图像的宽度和高度。
        支持毫米和像素两种单位，以及宽高比锁定。
        
        Args:
            config: 渲染配置
            
        Returns:
            Tuple[int, int]: (宽度像素, 高度像素)
        """
        # 计算默认尺寸（基于标准尺寸）
        default_width_px = self._mm_to_px(self.STANDARD_TOTAL_WIDTH_MM, config.dpi)
        default_height_px = self._mm_to_px(self.STANDARD_TOTAL_HEIGHT_MM, config.dpi)
        
        # 如果有附加码，增加宽度（包含附加码右侧边距）
        if config.addon_pattern:
            addon_width_modules = config.addon_pattern.module_count + self.ADDON_GAP_MODULES + 5  # 右侧留5个模块空白
            addon_width_mm = addon_width_modules * self.STANDARD_MODULE_WIDTH_MM
            default_width_px += self._mm_to_px(addon_width_mm, config.dpi)
        
        # 确定最终尺寸
        width_px = None
        height_px = None
        
        # 优先使用像素值
        if config.width_px is not None:
            width_px = config.width_px
        elif config.width_mm is not None:
            width_px = self._mm_to_px(config.width_mm, config.dpi)
        
        if config.height_px is not None:
            height_px = config.height_px
        elif config.height_mm is not None:
            height_px = self._mm_to_px(config.height_mm, config.dpi)
        
        # 处理宽高比锁定
        if config.lock_aspect_ratio:
            aspect_ratio = default_width_px / default_height_px
            
            if width_px is not None and height_px is None:
                height_px = int(width_px / aspect_ratio)
            elif height_px is not None and width_px is None:
                width_px = int(height_px * aspect_ratio)
            elif width_px is None and height_px is None:
                width_px = default_width_px
                height_px = default_height_px
        else:
            # 不锁定宽高比时，使用默认值填充未指定的维度
            if width_px is None:
                width_px = default_width_px
            if height_px is None:
                height_px = default_height_px
        
        return (int(width_px), int(height_px))
    
    def _calculate_module_width(self, config: RenderConfig, image_width_px: int) -> float:
        """计算模块宽度（像素）
        
        Args:
            config: 渲染配置
            image_width_px: 图像宽度（像素）
            
        Returns:
            float: 模块宽度（像素）
        """
        # 计算总模块数（包含静区）
        total_modules = self.LEFT_QUIET_ZONE_MODULES + self.EAN13_MODULES + self.RIGHT_QUIET_ZONE_MODULES
        
        if config.addon_pattern:
            # 附加码模块数 + 间距 + 右侧边距
            total_modules += self.ADDON_GAP_MODULES + config.addon_pattern.module_count + 5
        
        return image_width_px / total_modules
    
    def _calculate_barcode_area(self, config: RenderConfig, width_px: int, height_px: int, 
                                 module_width_px: float) -> dict:
        """计算条码绘制区域
        
        Args:
            config: 渲染配置
            width_px: 图像宽度
            height_px: 图像高度
            module_width_px: 模块宽度
            
        Returns:
            dict: 包含条码区域坐标的字典
        """
        # 计算文字区域高度
        isbn_text_height = config.font_size + config.isbn_text_offset_y
        digits_height = config.font_size + config.digits_offset_y
        
        # 条码起始X坐标（左侧静区之后）
        barcode_x = int(self.LEFT_QUIET_ZONE_MODULES * module_width_px)
        
        # 无附加码时，整体左移0.5mm
        if not config.addon_pattern:
            offset_mm_px = self._mm_to_px(0.5, config.dpi)
            barcode_x -= offset_mm_px
        
        # 条码宽度
        barcode_width = int(self.EAN13_MODULES * module_width_px)
        
        # 条码Y坐标和高度
        barcode_y = isbn_text_height + 5  # 顶部留出ISBN文本空间
        barcode_height = height_px - barcode_y - digits_height - 5
        
        return {
            'x': barcode_x,
            'y': barcode_y,
            'width': barcode_width,
            'height': barcode_height,
            'module_width': module_width_px
        }
    
    def _calculate_addon_area(self, main_area: dict, config: RenderConfig, 
                               module_width_px: float) -> dict:
        """计算附加码绘制区域
        
        Args:
            main_area: 主条码区域
            config: 渲染配置
            module_width_px: 模块宽度
            
        Returns:
            dict: 包含附加码区域坐标的字典
        """
        # 附加码起始X坐标（主条码右侧 + 静区 + 间距）
        addon_x = main_area['x'] + main_area['width'] + int(
            (self.RIGHT_QUIET_ZONE_MODULES + self.ADDON_GAP_MODULES) * module_width_px
        )
        
        # 附加码高度比主条码短，底部与主条码底部数字顶部对齐
        addon_height = int(main_area['height'] * 0.85)
        # 附加码顶部Y坐标：主条码底部 - 附加码高度
        addon_y = main_area['y'] + main_area['height'] - addon_height
        
        addon_width = int(config.addon_pattern.module_count * module_width_px)
        
        return {
            'x': addon_x,
            'y': addon_y,
            'width': addon_width,
            'height': addon_height,
            'module_width': module_width_px
        }
    
    def _draw_barcode(self, draw: "ImageDraw.ImageDraw", pattern: BarcodePattern,
                      config: RenderConfig, area: dict, module_width_px: float) -> None:
        """绘制条码图案
        
        Args:
            draw: PIL ImageDraw对象
            pattern: 条码图案数据
            config: 渲染配置
            area: 绘制区域
            module_width_px: 模块宽度
        """
        fg_color = self._convert_color(config.foreground_color, config.color_mode)
        
        x = area['x']
        y = area['y']
        height = area['height']
        
        # 保护条延长高度
        guard_extension = int(height * 0.1)
        
        for i, bar in enumerate(pattern.bars):
            bar_width = module_width_px
            bar_x = x + int(i * module_width_px)
            
            if bar == 1:  # 黑条
                # 检查是否是保护条（需要延长）
                bar_height = height
                if i in pattern.guard_positions:
                    bar_height = height + guard_extension
                
                draw.rectangle(
                    [bar_x, y, bar_x + int(bar_width), y + bar_height],
                    fill=fg_color
                )
    
    def _draw_addon(self, draw: "ImageDraw.ImageDraw", pattern: BarcodePattern,
                    config: RenderConfig, area: dict, module_width_px: float) -> None:
        """绘制附加码
        
        Args:
            draw: PIL ImageDraw对象
            pattern: 附加码图案数据
            config: 渲染配置
            area: 绘制区域
            module_width_px: 模块宽度
        """
        fg_color = self._convert_color(config.foreground_color, config.color_mode)
        
        x = area['x']
        y = area['y']
        height = area['height']
        
        for i, bar in enumerate(pattern.bars):
            bar_width = module_width_px
            bar_x = x + int(i * module_width_px)
            
            if bar == 1:  # 黑条
                draw.rectangle(
                    [bar_x, y, bar_x + int(bar_width), y + height],
                    fill=fg_color
                )
    
    def _draw_text(self, draw: "ImageDraw.ImageDraw", config: RenderConfig,
                   barcode_area: dict, module_width_px: float) -> None:
        """绘制文字（ISBN文本和数字）
        
        Args:
            draw: PIL ImageDraw对象
            config: 渲染配置
            barcode_area: 条码区域
            module_width_px: 模块宽度
        """
        from PIL import ImageFont
        
        fg_color = self._convert_color(config.foreground_color, config.color_mode)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype(config.font_family, config.font_size)
        except (OSError, IOError):
            # 如果找不到指定字体，使用默认字体
            try:
                font = ImageFont.truetype("arial.ttf", config.font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()
        
        # 绘制ISBN文本（条码上方）- 应用字间距
        isbn_text = config.isbn.formatted
        isbn_y = config.isbn_text_offset_y
        
        # 如果有字间距，逐字符绘制ISBN文本
        if config.letter_spacing != 0:
            # 计算带字间距的总宽度
            total_width = 0
            char_widths = []
            for char in isbn_text:
                bbox = draw.textbbox((0, 0), char, font=font)
                char_width = bbox[2] - bbox[0]
                char_widths.append(char_width)
                total_width += char_width
            total_width += config.letter_spacing * (len(isbn_text) - 1)
            
            # 计算起始X坐标（根据对齐方式）
            if config.text_alignment == TextAlignment.CENTER:
                isbn_x = barcode_area['x'] + (barcode_area['width'] - total_width) // 2
            elif config.text_alignment == TextAlignment.LEFT:
                isbn_x = barcode_area['x']
            else:  # RIGHT
                isbn_x = barcode_area['x'] + barcode_area['width'] - total_width
            
            # 逐字符绘制
            current_x = isbn_x
            for i, char in enumerate(isbn_text):
                draw.text((current_x, isbn_y), char, font=font, fill=fg_color)
                current_x += char_widths[i] + config.letter_spacing
        else:
            # 无字间距，直接绘制
            text_bbox = draw.textbbox((0, 0), isbn_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            
            if config.text_alignment == TextAlignment.CENTER:
                isbn_x = barcode_area['x'] + (barcode_area['width'] - text_width) // 2
            elif config.text_alignment == TextAlignment.LEFT:
                isbn_x = barcode_area['x']
            else:  # RIGHT
                isbn_x = barcode_area['x'] + barcode_area['width'] - text_width
            
            draw.text((isbn_x, isbn_y), isbn_text, font=font, fill=fg_color)
        
        # 绘制EAN-13数字（条码下方）- 不应用字间距，固定间距
        digits = config.isbn.digits
        digits_y = barcode_area['y'] + barcode_area['height'] + config.digits_offset_y
        
        # 绘制第一位数字（在条码左侧）
        first_digit = digits[0]
        # 计算第一位数字宽度
        first_digit_bbox = draw.textbbox((0, 0), first_digit, font=font)
        first_digit_width = first_digit_bbox[2] - first_digit_bbox[0]
        # 向右移动半个字符宽度
        first_digit_x = barcode_area['x'] - int(2 * module_width_px) - config.font_size + int(0.5 * first_digit_width)
        draw.text((first_digit_x, digits_y), first_digit, font=font, fill=fg_color)
        
        # 绘制左侧6位数字（起始符之后，中间分隔符之前）- 固定间距
        left_digits = digits[1:7]
        left_start_x = barcode_area['x'] + int(3 * module_width_px)  # 起始符后
        left_width = int(42 * module_width_px)  # 左侧数据区宽度
        self._draw_digit_group(draw, left_digits, left_start_x, digits_y, 
                               left_width, font, fg_color, 0)  # 固定间距为0
        
        # 绘制右侧6位数字（中间分隔符之后，终止符之前）- 固定间距
        right_digits = digits[7:13]
        right_start_x = barcode_area['x'] + int(50 * module_width_px)  # 中间分隔符后
        right_width = int(42 * module_width_px)  # 右侧数据区宽度
        self._draw_digit_group(draw, right_digits, right_start_x, digits_y,
                               right_width, font, fg_color, 0)  # 固定间距为0
        
        # 绘制附加码数字（如果有）
        if config.addon_digits:
            # 计算附加码条码的右边缘位置
            addon_x = barcode_area['x'] + barcode_area['width'] + int(
                (self.RIGHT_QUIET_ZONE_MODULES + self.ADDON_GAP_MODULES) * module_width_px
            )
            addon_width = int(config.addon_pattern.module_count * module_width_px)
            addon_right_x = addon_x + addon_width
            
            # 计算附加码数字宽度
            addon_digits_bbox = draw.textbbox((0, 0), config.addon_digits, font=font)
            addon_digits_width = addon_digits_bbox[2] - addon_digits_bbox[0]
            
            # 附加码数字右对齐到附加码条码右边缘，再向左移动1个字符宽度
            char_width = addon_digits_width / len(config.addon_digits) if config.addon_digits else 0
            addon_digits_x = addon_right_x - addon_digits_width - int(1 * char_width)
            
            # 附加码数字在附加码条码上方
            addon_height = int(barcode_area['height'] * 0.85)
            addon_top_y = barcode_area['y'] + barcode_area['height'] - addon_height
            addon_digits_y = addon_top_y - config.font_size - 2
            draw.text((addon_digits_x, addon_digits_y), config.addon_digits, font=font, fill=fg_color)
    
    def _draw_digit_group(self, draw: "ImageDraw.ImageDraw", digits: str,
                          start_x: int, y: int, width: int, font, 
                          color, letter_spacing: float) -> None:
        """绘制一组数字
        
        Args:
            draw: PIL ImageDraw对象
            digits: 数字字符串
            start_x: 起始X坐标
            y: Y坐标
            width: 可用宽度
            font: 字体对象
            color: 颜色
            letter_spacing: 字符间距
        """
        if not digits:
            return
        
        # 计算每个字符的宽度和间距
        total_spacing = letter_spacing * (len(digits) - 1)
        char_width = (width - total_spacing) / len(digits)
        
        for i, digit in enumerate(digits):
            x = start_x + int(i * (char_width + letter_spacing))
            # 居中绘制每个数字
            bbox = draw.textbbox((0, 0), digit, font=font)
            digit_width = bbox[2] - bbox[0]
            centered_x = x + (char_width - digit_width) / 2
            draw.text((centered_x, y), digit, font=font, fill=color)
    
    def _draw_quiet_zone_indicators(self, draw: "ImageDraw.ImageDraw", config: RenderConfig,
                                     barcode_area: dict, module_width_px: float, 
                                     image_width_px: int) -> None:
        """绘制静区标记
        
        在条码右侧静区边界绘制">"符号，用于标识静区的范围，符合GS1标准要求。
        - 无附加码时：标记在主条码右下方（与底部数字同一行）
        - 有附加码时：标记紧挨着附加码数字右侧
        
        Args:
            draw: PIL ImageDraw对象
            config: 渲染配置
            barcode_area: 条码区域
            module_width_px: 模块宽度
            image_width_px: 图像宽度
        """
        from PIL import ImageFont
        
        fg_color = self._convert_color(config.foreground_color, config.color_mode)
        
        # 使用与条码数字相同的字体大小
        try:
            font = ImageFont.truetype(config.font_family, config.font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("arial.ttf", config.font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()
        
        # 右侧静区标记 ">"
        right_indicator = ">"
        right_bbox = draw.textbbox((0, 0), right_indicator, font=font)
        right_indicator_width = right_bbox[2] - right_bbox[0]
        
        if config.addon_pattern and config.addon_digits:
            # 有附加码时，静区标记紧挨着附加码数字右侧
            # 计算附加码数字的位置（与_draw_text中的计算保持一致）
            addon_x = barcode_area['x'] + barcode_area['width'] + int(
                (self.RIGHT_QUIET_ZONE_MODULES + self.ADDON_GAP_MODULES) * module_width_px
            )
            addon_width = int(config.addon_pattern.module_count * module_width_px)
            addon_right_x = addon_x + addon_width
            
            # 计算附加码数字宽度
            addon_digits_bbox = draw.textbbox((0, 0), config.addon_digits, font=font)
            addon_digits_width = addon_digits_bbox[2] - addon_digits_bbox[0]
            
            # 附加码数字位置（与_draw_text中一致）
            char_width = addon_digits_width / len(config.addon_digits) if config.addon_digits else 0
            addon_digits_x = addon_right_x - addon_digits_width - int(0.5 * char_width)
            
            # 静区标记紧挨着附加码数字右侧
            right_x = addon_digits_x + addon_digits_width
            
            # Y坐标：与附加码数字同一行
            addon_height = int(barcode_area['height'] * 0.85)
            addon_y = barcode_area['y'] + barcode_area['height'] - addon_height
            indicator_y = addon_y - config.font_size - 2
        else:
            # 无附加码时，标记在主条码右侧静区末端（与底部数字同一行）
            right_x = barcode_area['x'] + barcode_area['width'] + int(
                self.RIGHT_QUIET_ZONE_MODULES * module_width_px
            )
            # Y坐标：与底部数字同一行
            indicator_y = barcode_area['y'] + barcode_area['height'] + config.digits_offset_y
        
        # 确保不超出图像边界
        if right_x + right_indicator_width > image_width_px:
            right_x = image_width_px - right_indicator_width - 2
        
        draw.text((right_x, indicator_y), right_indicator, font=font, fill=fg_color)
    
    def _mm_to_px(self, mm: float, dpi: int) -> int:
        """毫米转像素
        
        Args:
            mm: 毫米值
            dpi: 分辨率
            
        Returns:
            int: 像素值
        """
        return int(mm * dpi / 25.4)
    
    def _px_to_mm(self, px: int, dpi: int) -> float:
        """像素转毫米
        
        Args:
            px: 像素值
            dpi: 分辨率
            
        Returns:
            float: 毫米值
        """
        return px * 25.4 / dpi
    
    def get_default_size_mm(self, has_addon: bool = False, addon_modules: int = 0) -> Tuple[float, float]:
        """获取默认尺寸（毫米）
        
        根据GS1标准返回默认的条码图像尺寸。
        
        Args:
            has_addon: 是否包含附加码
            addon_modules: 附加码模块数
            
        Returns:
            Tuple[float, float]: (宽度毫米, 高度毫米)
        """
        width_mm = self.STANDARD_TOTAL_WIDTH_MM
        if has_addon:
            addon_width_mm = (addon_modules + self.ADDON_GAP_MODULES) * self.STANDARD_MODULE_WIDTH_MM
            width_mm += addon_width_mm
        return (width_mm, self.STANDARD_TOTAL_HEIGHT_MM)
    
    def get_default_size_px(self, dpi: int, has_addon: bool = False, 
                            addon_modules: int = 0) -> Tuple[int, int]:
        """获取默认尺寸（像素）
        
        Args:
            dpi: 分辨率
            has_addon: 是否包含附加码
            addon_modules: 附加码模块数
            
        Returns:
            Tuple[int, int]: (宽度像素, 高度像素)
        """
        width_mm, height_mm = self.get_default_size_mm(has_addon, addon_modules)
        return (self._mm_to_px(width_mm, dpi), self._mm_to_px(height_mm, dpi))
    
    def calculate_size_with_aspect_ratio(self, width: Optional[float] = None,
                                          height: Optional[float] = None,
                                          dpi: int = 300,
                                          has_addon: bool = False,
                                          addon_modules: int = 0) -> Tuple[float, float]:
        """根据宽高比锁定计算尺寸（毫米）
        
        当只指定宽度或高度时，根据标准宽高比计算另一个维度。
        
        Args:
            width: 宽度（毫米），可选
            height: 高度（毫米），可选
            dpi: 分辨率
            has_addon: 是否包含附加码
            addon_modules: 附加码模块数
            
        Returns:
            Tuple[float, float]: (宽度毫米, 高度毫米)
        """
        default_width, default_height = self.get_default_size_mm(has_addon, addon_modules)
        aspect_ratio = default_width / default_height
        
        if width is not None and height is None:
            return (width, width / aspect_ratio)
        elif height is not None and width is None:
            return (height * aspect_ratio, height)
        elif width is not None and height is not None:
            return (width, height)
        else:
            return (default_width, default_height)
    
    def get_minimum_scannable_size_mm(self) -> Tuple[float, float]:
        """获取最小可扫描尺寸（毫米）
        
        根据GS1标准，EAN-13条码的最小放大率为80%。
        
        Returns:
            Tuple[float, float]: (最小宽度毫米, 最小高度毫米)
        """
        min_scale = 0.8  # 80%放大率
        return (
            self.STANDARD_TOTAL_WIDTH_MM * min_scale,
            self.STANDARD_TOTAL_HEIGHT_MM * min_scale
        )
    
    def _get_pil_mode(self, color_mode: ColorMode) -> str:
        """获取PIL图像模式
        
        Args:
            color_mode: 颜色模式枚举
            
        Returns:
            str: PIL图像模式字符串
        """
        return color_mode.value
    
    def _convert_color(self, color: Tuple[int, ...], color_mode: ColorMode) -> any:
        """转换颜色值到指定颜色模式
        
        Args:
            color: RGB颜色元组
            color_mode: 目标颜色模式
            
        Returns:
            适合目标颜色模式的颜色值
        """
        if color_mode == ColorMode.BITMAP:
            # 1位模式：0=黑，1=白
            # 判断颜色亮度
            if len(color) >= 3:
                brightness = (color[0] + color[1] + color[2]) / 3
            else:
                brightness = color[0]
            return 0 if brightness < 128 else 1
        
        elif color_mode == ColorMode.GRAYSCALE:
            # 灰度模式：0-255
            if len(color) >= 3:
                return int((color[0] + color[1] + color[2]) / 3)
            return color[0]
        
        elif color_mode == ColorMode.RGB:
            # RGB模式：直接返回RGB元组
            if len(color) >= 3:
                return (color[0], color[1], color[2])
            return (color[0], color[0], color[0])
        
        elif color_mode == ColorMode.CMYK:
            # CMYK模式：从RGB转换
            if len(color) >= 3:
                r, g, b = color[0], color[1], color[2]
            else:
                r = g = b = color[0]
            
            # RGB到CMYK转换
            if r == 0 and g == 0 and b == 0:
                return (0, 0, 0, 255)  # 纯黑
            
            c = 1 - r / 255
            m = 1 - g / 255
            y = 1 - b / 255
            k = min(c, m, y)
            
            if k < 1:
                c = (c - k) / (1 - k)
                m = (m - k) / (1 - k)
                y = (y - k) / (1 - k)
            else:
                c = m = y = 0
            
            return (int(c * 255), int(m * 255), int(y * 255), int(k * 255))
        
        return color
