"""
Batch Processor - 批量条码生成模块

本模块负责批量处理ISBN列表，为每个有效的ISBN生成对应的TIF条码图像。
支持从文件或列表读取ISBN，提供进度回调机制，并能隔离单个ISBN的错误。
"""

import os
from dataclasses import dataclass, field
from typing import Callable, Optional
from pathlib import Path

from .validator import ISBNValidator, ParsedISBN
from .encoder import EAN13Encoder
from .addon_encoder import AddonEncoder
from .renderer import TIFRenderer, RenderConfig, TIFConfig
from .template_manager import TemplateManager


@dataclass
class ParsedInput:
    """ISBN输入解析结果
    
    Attributes:
        isbn_digits: 13位ISBN数字
        addon_digits: 附加码数字（2位或5位），无附加码时为None
        is_valid: 解析是否成功
        error_message: 错误信息（解析失败时）
    """
    isbn_digits: Optional[str]
    addon_digits: Optional[str]
    is_valid: bool
    error_message: Optional[str] = None


def parse_isbn_input(raw_input: str) -> ParsedInput:
    """解析ISBN输入字符串
    
    解析逻辑：
    1. 去除所有非数字字符
    2. 根据数字长度识别ISBN和附加码：
       - 13位: 不带附加码的ISBN
       - 15位: ISBN(前13位) + 2位附加码(后2位)
       - 18位: ISBN(前13位) + 5位附加码(后5位)
       - 其他长度: 返回错误
    
    Args:
        raw_input: 原始输入字符串
        
    Returns:
        ParsedInput: 解析结果
    """
    # 检查空输入
    if not raw_input:
        return ParsedInput(
            isbn_digits=None,
            addon_digits=None,
            is_valid=False,
            error_message="输入为空"
        )
    
    # 去除所有非数字字符
    digits = ''.join(c for c in raw_input if c.isdigit())
    
    # 检查是否有数字
    if not digits:
        return ParsedInput(
            isbn_digits=None,
            addon_digits=None,
            is_valid=False,
            error_message="输入中没有数字"
        )
    
    # 根据长度识别ISBN和附加码
    length = len(digits)
    
    if length == 13:
        # 13位：无附加码的ISBN
        return ParsedInput(
            isbn_digits=digits,
            addon_digits=None,
            is_valid=True
        )
    elif length == 15:
        # 15位：ISBN(前13位) + 2位附加码(后2位)
        return ParsedInput(
            isbn_digits=digits[:13],
            addon_digits=digits[13:],
            is_valid=True
        )
    elif length == 18:
        # 18位：ISBN(前13位) + 5位附加码(后5位)
        return ParsedInput(
            isbn_digits=digits[:13],
            addon_digits=digits[13:],
            is_valid=True
        )
    else:
        # 其他长度：返回错误
        return ParsedInput(
            isbn_digits=None,
            addon_digits=None,
            is_valid=False,
            error_message=f"无效的输入长度：{length}位（应为13、15或18位）"
        )


@dataclass
class BatchError:
    """批量处理错误
    
    Attributes:
        isbn: 导致错误的ISBN字符串
        error_message: 错误描述信息
    """
    isbn: str
    error_message: str


@dataclass
class BatchResult:
    """批量处理结果
    
    Attributes:
        total: 处理的ISBN总数
        success: 成功生成的条码数量
        failed: 失败的数量
        errors: 错误详情列表
    """
    total: int
    success: int
    failed: int
    errors: list[BatchError] = field(default_factory=list)


class BatchProcessor:
    """批量条码生成器
    
    负责批量处理ISBN列表，为每个有效的ISBN生成对应的TIF条码图像。
    单个ISBN的错误不会影响其他ISBN的处理。
    
    Attributes:
        validator: ISBN验证器
        encoder: EAN-13编码器
        addon_encoder: 附加码编码器
        renderer: TIF渲染器
        template_manager: 模板管理器（可选）
    """
    
    def __init__(self, validator: ISBNValidator, 
                 encoder: EAN13Encoder,
                 addon_encoder: AddonEncoder,
                 renderer: TIFRenderer,
                 template_manager: Optional[TemplateManager] = None):
        """初始化批量处理器
        
        Args:
            validator: ISBN验证器
            encoder: EAN-13编码器
            addon_encoder: 附加码编码器
            renderer: TIF渲染器
            template_manager: 模板管理器（可选，用于获取附加码模板配置）
        """
        self.validator = validator
        self.encoder = encoder
        self.addon_encoder = addon_encoder
        self.renderer = renderer
        self.template_manager = template_manager
    
    def process_file(self, input_file: str, output_dir: str,
                     config: RenderConfig,
                     progress_callback: Optional[Callable[[int, int, str], None]] = None
                     ) -> BatchResult:
        """处理ISBN列表文件
        
        从文件中读取ISBN列表（每行一个ISBN），为每个有效的ISBN生成条码图像。
        
        Args:
            input_file: 输入文件路径，每行包含一个ISBN
            output_dir: 输出目录路径
            config: 渲染配置（isbn字段将被每个ISBN覆盖）
            progress_callback: 进度回调函数，参数为(当前索引, 总数, 当前ISBN)
            
        Returns:
            BatchResult: 处理结果摘要
            
        Raises:
            FileNotFoundError: 如果输入文件不存在
            IOError: 如果文件读取失败
        """
        # 读取文件内容
        isbn_list = self._read_isbn_file(input_file)
        
        # 调用process_list处理
        return self.process_list(isbn_list, output_dir, config, progress_callback)
    
    def process_list(self, isbn_list: list[str], output_dir: str,
                     config: RenderConfig,
                     progress_callback: Optional[Callable[[int, int, str], None]] = None
                     ) -> BatchResult:
        """处理ISBN列表
        
        为列表中的每个有效ISBN生成条码图像。单个ISBN的错误不会影响其他ISBN的处理。
        
        Args:
            isbn_list: ISBN字符串列表
            output_dir: 输出目录路径
            config: 渲染配置（isbn字段将被每个ISBN覆盖）
            progress_callback: 进度回调函数，参数为(当前索引, 总数, 当前ISBN)
            
        Returns:
            BatchResult: 处理结果摘要
        """
        # 确保输出目录存在
        self._ensure_output_dir(output_dir)
        
        total = len(isbn_list)
        success = 0
        failed = 0
        errors: list[BatchError] = []
        
        for index, isbn_raw in enumerate(isbn_list):
            # 调用进度回调
            if progress_callback:
                progress_callback(index, total, isbn_raw)
            
            # 处理单个ISBN
            try:
                error = self._process_single_isbn(isbn_raw, output_dir, config)
                if error:
                    failed += 1
                    errors.append(error)
                else:
                    success += 1
            except Exception as e:
                # 捕获所有异常，确保错误隔离
                failed += 1
                errors.append(BatchError(isbn=isbn_raw, error_message=str(e)))
        
        return BatchResult(
            total=total,
            success=success,
            failed=failed,
            errors=errors
        )
    
    def _process_single_isbn(self, isbn_raw: str, output_dir: str, 
                              config: RenderConfig) -> Optional[BatchError]:
        """处理单个ISBN
        
        使用新的parse_isbn_input函数解析输入，支持：
        - 自动去除非数字字符
        - 根据长度自动识别附加码
        - 根据是否有附加码自动选择合适的模板配置
        
        Args:
            isbn_raw: 原始ISBN字符串，支持格式：
                     - 纯ISBN: 978-7-5649-6151-0
                     - 带附加码: 978756492235102 (15位) 或 978756492235112345 (18位)
                     - 带斜杠分隔附加码: 978-7-5492-2320/02
            output_dir: 输出目录
            config: 渲染配置
            
        Returns:
            BatchError: 如果处理失败返回错误对象，成功返回None
        """
        # 清理ISBN字符串（去除首尾空白）
        isbn_clean = isbn_raw.strip()
        
        # 跳过空行
        if not isbn_clean:
            return None
        
        # 使用新的解析函数解析ISBN和附加码
        parsed_input = parse_isbn_input(isbn_clean)
        
        if not parsed_input.is_valid:
            return BatchError(isbn=isbn_raw, error_message=parsed_input.error_message or "无效的ISBN")
        
        # 使用解析出的附加码（如果有），否则使用配置中的附加码
        addon_digits = parsed_input.addon_digits if parsed_input.addon_digits else config.addon_digits
        
        # 验证ISBN（使用解析出的ISBN数字）
        parsed = self.validator.parse(parsed_input.isbn_digits)
        if not parsed.is_valid:
            return BatchError(isbn=isbn_raw, error_message=parsed.error_message or "无效的ISBN")
        
        # 编码条码
        barcode_pattern = self.encoder.encode(parsed.digits)
        
        # 处理附加码
        addon_pattern = None
        if addon_digits:
            if len(addon_digits) == 2:
                addon_pattern = self.addon_encoder.encode_2(addon_digits)
            elif len(addon_digits) == 5:
                addon_pattern = self.addon_encoder.encode_5(addon_digits)
        
        # 根据是否有附加码选择合适的模板配置
        if addon_digits and self.template_manager:
            # 有附加码时，使用附加码模板的配置
            if len(addon_digits) == 2:
                addon_template = self.template_manager.get_addon_2_template()
            else:
                # 5位附加码也使用2位附加码模板（或可以添加专门的5位模板）
                addon_template = self.template_manager.get_addon_2_template()
            
            # 创建新的渲染配置（使用附加码模板的参数）
            render_config = RenderConfig(
                isbn=parsed,
                barcode_pattern=barcode_pattern,
                addon_pattern=addon_pattern,
                addon_digits=addon_digits,
                dpi=addon_template.get('dpi', config.dpi),
                width_mm=addon_template.get('width_mm', config.width_mm),
                height_mm=addon_template.get('height_mm', config.height_mm),
                width_px=addon_template.get('width_px', config.width_px),
                height_px=addon_template.get('height_px', config.height_px),
                lock_aspect_ratio=addon_template.get('lock_aspect_ratio', config.lock_aspect_ratio),
                color_mode=config.color_mode,  # 保持原配置的颜色模式
                foreground_color=config.foreground_color,  # 保持原配置的前景色
                background_color=config.background_color,  # 保持原配置的背景色
                font_family=addon_template.get('font_family', config.font_family),
                font_size=addon_template.get('font_size', config.font_size),
                letter_spacing=addon_template.get('letter_spacing', config.letter_spacing),
                isbn_text_offset_y=addon_template.get('isbn_text_offset_y', config.isbn_text_offset_y),
                digits_offset_y=addon_template.get('digits_offset_y', config.digits_offset_y),
                text_alignment=config.text_alignment
            )
        else:
            # 无附加码或无模板管理器时，使用原配置
            render_config = RenderConfig(
                isbn=parsed,
                barcode_pattern=barcode_pattern,
                addon_pattern=addon_pattern,
                addon_digits=addon_digits,
                dpi=config.dpi,
                width_mm=config.width_mm,
                height_mm=config.height_mm,
                width_px=config.width_px,
                height_px=config.height_px,
                lock_aspect_ratio=config.lock_aspect_ratio,
                color_mode=config.color_mode,
                foreground_color=config.foreground_color,
                background_color=config.background_color,
                font_family=config.font_family,
                font_size=config.font_size,
                letter_spacing=config.letter_spacing,
                isbn_text_offset_y=config.isbn_text_offset_y,
                digits_offset_y=config.digits_offset_y,
                text_alignment=config.text_alignment
            )
        
        # 渲染图像
        image = self.renderer.render(render_config)
        
        # 生成输出文件名（使用ISBN数字作为文件名）
        output_filename = f"{parsed.digits}.tif"
        output_path = os.path.join(output_dir, output_filename)
        
        # 保存TIF文件
        tif_config = TIFConfig(dpi=config.dpi)
        self.renderer.save_tif(image, output_path, tif_config)
        
        return None
    
    def _read_isbn_file(self, input_file: str) -> list[str]:
        """读取ISBN列表文件
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            list[str]: ISBN字符串列表
            
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        path = Path(input_file)
        if not path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 返回所有行（包括空行，由process_list处理）
        return [line.strip() for line in lines]
    
    def _ensure_output_dir(self, output_dir: str) -> None:
        """确保输出目录存在
        
        Args:
            output_dir: 输出目录路径
        """
        path = Path(output_dir)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
