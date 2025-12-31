"""
ISBN Validator - ISBN-13格式验证和解析模块
"""

import re
from dataclasses import dataclass


@dataclass
class ParsedISBN:
    """解析后的ISBN数据"""
    raw: str                    # 原始输入
    digits: str                 # 13位纯数字
    formatted: str              # 格式化显示 (ISBN 978-7-5649-2235-1)
    is_valid: bool
    error_message: str | None = None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    error_message: str | None = None


class ISBNValidator:
    """ISBN-13格式验证和解析"""
    
    def validate(self, isbn: str) -> ValidationResult:
        """验证ISBN格式和校验位
        
        验证ISBN-13格式（978或979开头的13位数字）和校验位正确性。
        支持带连字符和不带连字符的输入格式。
        """
        # 提取纯数字部分
        digits = self._extract_digits(isbn)
        
        # 检查长度
        if len(digits) != 13:
            return ValidationResult(
                is_valid=False,
                error_message=f"ISBN必须是13位数字，当前为{len(digits)}位"
            )
        
        # 检查前缀（必须是978或979）
        if not (digits.startswith("978") or digits.startswith("979")):
            return ValidationResult(
                is_valid=False,
                error_message="ISBN-13必须以978或979开头"
            )
        
        # 验证校验位
        expected_check = self.calculate_check_digit(digits[:12])
        actual_check = digits[12]
        
        if expected_check != actual_check:
            return ValidationResult(
                is_valid=False,
                error_message=f"校验位错误：期望{expected_check}，实际为{actual_check}"
            )
        
        return ValidationResult(is_valid=True, error_message=None)
    
    def parse(self, isbn: str) -> ParsedISBN:
        """解析ISBN，提取数字部分和格式化显示
        
        支持带连字符（如978-7-5649-2235-1）和不带连字符（如9787564922351）的输入。
        返回包含原始输入、纯数字、格式化显示和验证状态的ParsedISBN对象。
        """
        raw = isbn
        digits = self._extract_digits(isbn)
        
        # 先验证
        validation = self.validate(isbn)
        
        if not validation.is_valid:
            return ParsedISBN(
                raw=raw,
                digits=digits,
                formatted="",
                is_valid=False,
                error_message=validation.error_message
            )
        
        # 格式化显示：ISBN XXX-X-XXXX-XXXX-X
        formatted = self._format_isbn(digits)
        
        return ParsedISBN(
            raw=raw,
            digits=digits,
            formatted=formatted,
            is_valid=True,
            error_message=None
        )
    
    def calculate_check_digit(self, isbn_12: str) -> str:
        """计算ISBN-13校验位
        
        使用ISBN-13校验位算法：
        1. 从左到右，奇数位乘1，偶数位乘3
        2. 求和后对10取模
        3. 用10减去模值，如果结果为10则校验位为0
        """
        if len(isbn_12) != 12:
            raise ValueError(f"计算校验位需要12位数字，当前为{len(isbn_12)}位")
        
        if not isbn_12.isdigit():
            raise ValueError("ISBN必须全部为数字")
        
        total = 0
        for i, digit in enumerate(isbn_12):
            weight = 1 if i % 2 == 0 else 3
            total += int(digit) * weight
        
        check = (10 - (total % 10)) % 10
        return str(check)
    
    def _extract_digits(self, isbn: str) -> str:
        """从ISBN字符串中提取纯数字部分"""
        return re.sub(r'[^0-9]', '', isbn)
    
    def _format_isbn(self, digits: str) -> str:
        """将13位数字格式化为标准ISBN显示格式
        
        格式：ISBN XXX-X-XXXX-XXXX-X
        """
        if len(digits) != 13:
            return ""
        
        # 标准格式：ISBN 978-X-XXXX-XXXX-X
        # 分组：前缀(3) - 注册组(1) - 出版者(4) - 书名(4) - 校验位(1)
        return f"ISBN {digits[0:3]}-{digits[3]}-{digits[4:8]}-{digits[8:12]}-{digits[12]}"
