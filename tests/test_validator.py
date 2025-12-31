"""
ISBN Validator Tests - ISBN验证器测试
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from src.isbn_barcode_generator.core.validator import ISBNValidator, ParsedISBN, ValidationResult


class TestISBNChecksumValidation:
    """Property 1: ISBN校验位验证
    
    **Feature: isbn-barcode-generator, Property 1: ISBN校验位验证**
    **Validates: Requirements 1.1, 1.2**
    
    *For any* 12位数字字符串（978或979开头），计算校验位后附加到末尾形成的13位ISBN，
    验证器应返回有效；而附加错误校验位的ISBN，验证器应返回无效。
    """
    
    @given(st.text(alphabet="0123456789", min_size=9, max_size=9))
    @settings(max_examples=100)
    def test_valid_isbn_with_correct_checksum_passes(self, suffix_9: str):
        """正确校验位的ISBN应通过验证"""
        # 使用978前缀构建12位ISBN
        isbn_12 = "978" + suffix_9
        
        validator = ISBNValidator()
        correct_check = validator.calculate_check_digit(isbn_12)
        valid_isbn = isbn_12 + correct_check
        
        result = validator.validate(valid_isbn)
        assert result.is_valid, f"Valid ISBN {valid_isbn} should pass validation"
    
    @given(st.text(alphabet="0123456789", min_size=9, max_size=9))
    @settings(max_examples=100)
    def test_invalid_isbn_with_wrong_checksum_fails(self, suffix_9: str):
        """错误校验位的ISBN应验证失败"""
        isbn_12 = "978" + suffix_9
        
        validator = ISBNValidator()
        correct_check = validator.calculate_check_digit(isbn_12)
        # 生成错误的校验位
        wrong_check = str((int(correct_check) + 1) % 10)
        invalid_isbn = isbn_12 + wrong_check
        
        result = validator.validate(invalid_isbn)
        assert not result.is_valid, f"Invalid ISBN {invalid_isbn} should fail validation"
        assert result.error_message is not None
    
    @given(st.text(alphabet="0123456789", min_size=9, max_size=9))
    @settings(max_examples=100)
    def test_979_prefix_isbn_validation(self, suffix_9: str):
        """979前缀的ISBN也应正确验证"""
        isbn_12 = "979" + suffix_9
        
        validator = ISBNValidator()
        correct_check = validator.calculate_check_digit(isbn_12)
        valid_isbn = isbn_12 + correct_check
        
        result = validator.validate(valid_isbn)
        assert result.is_valid, f"Valid ISBN {valid_isbn} with 979 prefix should pass"


class TestISBNParseRoundTrip:
    """Property 2: ISBN解析Round-Trip
    
    **Feature: isbn-barcode-generator, Property 2: ISBN解析Round-Trip**
    **Validates: Requirements 1.3, 1.4**
    
    *For any* 有效的ISBN-13（无论带连字符还是不带），解析后提取的数字部分应为13位纯数字，
    且格式化后的显示应符合标准格式（ISBN XXX-X-XXXX-XXXX-X）。
    """
    
    @given(st.text(alphabet="0123456789", min_size=9, max_size=9))
    @settings(max_examples=100)
    def test_parse_extracts_13_digits(self, suffix_9: str):
        """解析后的数字部分应为13位纯数字"""
        isbn_12 = "978" + suffix_9
        
        validator = ISBNValidator()
        correct_check = validator.calculate_check_digit(isbn_12)
        valid_isbn = isbn_12 + correct_check
        
        parsed = validator.parse(valid_isbn)
        
        assert parsed.is_valid
        assert len(parsed.digits) == 13
        assert parsed.digits.isdigit()
        assert parsed.digits == valid_isbn
    
    @given(st.text(alphabet="0123456789", min_size=9, max_size=9))
    @settings(max_examples=100)
    def test_parse_with_hyphens_extracts_same_digits(self, suffix_9: str):
        """带连字符的ISBN解析后应提取相同的数字部分"""
        isbn_12 = "978" + suffix_9
        
        validator = ISBNValidator()
        correct_check = validator.calculate_check_digit(isbn_12)
        valid_isbn = isbn_12 + correct_check
        
        # 创建带连字符的版本
        hyphenated = f"{valid_isbn[0:3]}-{valid_isbn[3]}-{valid_isbn[4:8]}-{valid_isbn[8:12]}-{valid_isbn[12]}"
        
        parsed_plain = validator.parse(valid_isbn)
        parsed_hyphen = validator.parse(hyphenated)
        
        assert parsed_plain.digits == parsed_hyphen.digits
        assert parsed_plain.is_valid == parsed_hyphen.is_valid
    
    @given(st.text(alphabet="0123456789", min_size=9, max_size=9))
    @settings(max_examples=100)
    def test_formatted_output_follows_standard(self, suffix_9: str):
        """格式化输出应符合标准格式 ISBN XXX-X-XXXX-XXXX-X"""
        isbn_12 = "978" + suffix_9
        
        validator = ISBNValidator()
        correct_check = validator.calculate_check_digit(isbn_12)
        valid_isbn = isbn_12 + correct_check
        
        parsed = validator.parse(valid_isbn)
        
        assert parsed.is_valid
        assert parsed.formatted.startswith("ISBN ")
        # 验证格式：ISBN XXX-X-XXXX-XXXX-X
        parts = parsed.formatted.replace("ISBN ", "").split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 3  # 前缀
        assert len(parts[1]) == 1  # 注册组
        assert len(parts[2]) == 4  # 出版者
        assert len(parts[3]) == 4  # 书名
        assert len(parts[4]) == 1  # 校验位
