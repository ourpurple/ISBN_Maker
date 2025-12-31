"""
ISBN Barcode Generator - 批量ISBN条码生成器

生成符合GS1标准的TIF格式条码图片，支持EAN-13编码、附加码、
多种颜色模式、自定义文字样式和模板管理功能。
"""

__version__ = "1.0.0"
__author__ = "ISBN Barcode Generator Team"

from .core.validator import ISBNValidator, ParsedISBN, ValidationResult
from .core.encoder import EAN13Encoder, BarcodePattern
from .core.addon_encoder import AddonEncoder
from .core.renderer import TIFRenderer, RenderConfig, ColorMode, TextAlignment, TIFConfig
from .core.template_manager import TemplateManager, Template
from .core.batch_processor import BatchProcessor, BatchResult, BatchError

__all__ = [
    # Validator
    "ISBNValidator",
    "ParsedISBN", 
    "ValidationResult",
    # Encoder
    "EAN13Encoder",
    "BarcodePattern",
    # Addon Encoder
    "AddonEncoder",
    # Renderer
    "TIFRenderer",
    "RenderConfig",
    "ColorMode",
    "TextAlignment",
    "TIFConfig",
    # Template Manager
    "TemplateManager",
    "Template",
    # Batch Processor
    "BatchProcessor",
    "BatchResult",
    "BatchError",
]
