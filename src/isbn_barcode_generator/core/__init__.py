"""
Core module - 核心业务逻辑模块

包含ISBN验证、EAN-13编码、附加码编码、TIF渲染、模板管理和批量处理功能。
"""

from .validator import ISBNValidator, ParsedISBN, ValidationResult
from .encoder import EAN13Encoder, BarcodePattern
from .addon_encoder import AddonEncoder
from .renderer import TIFRenderer, RenderConfig, ColorMode, TextAlignment, TIFConfig
from .template_manager import TemplateManager, Template
from .batch_processor import BatchProcessor, BatchResult, BatchError

__all__ = [
    "ISBNValidator",
    "ParsedISBN",
    "ValidationResult",
    "EAN13Encoder",
    "BarcodePattern",
    "AddonEncoder",
    "TIFRenderer",
    "RenderConfig",
    "ColorMode",
    "TextAlignment",
    "TIFConfig",
    "TemplateManager",
    "Template",
    "BatchProcessor",
    "BatchResult",
    "BatchError",
]
