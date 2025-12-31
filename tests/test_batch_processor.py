"""
Batch Processor Tests - 批量处理器测试
"""

import os
import tempfile
import shutil
import pytest
from hypothesis import given, strategies as st, settings, assume

from src.isbn_barcode_generator.core.validator import ISBNValidator
from src.isbn_barcode_generator.core.encoder import EAN13Encoder
from src.isbn_barcode_generator.core.addon_encoder import AddonEncoder
from src.isbn_barcode_generator.core.renderer import TIFRenderer, RenderConfig, ColorMode
from src.isbn_barcode_generator.core.batch_processor import BatchProcessor, BatchResult, BatchError, parse_isbn_input


def create_valid_isbn(suffix_9: str) -> str:
    """从9位后缀创建有效的ISBN-13"""
    isbn_12 = "978" + suffix_9
    validator = ISBNValidator()
    check_digit = validator.calculate_check_digit(isbn_12)
    return isbn_12 + check_digit


def create_batch_processor() -> BatchProcessor:
    """创建BatchProcessor实例"""
    return BatchProcessor(
        validator=ISBNValidator(),
        encoder=EAN13Encoder(),
        addon_encoder=AddonEncoder(),
        renderer=TIFRenderer()
    )


def create_dummy_render_config() -> RenderConfig:
    """创建用于测试的渲染配置"""
    validator = ISBNValidator()
    encoder = EAN13Encoder()
    # 使用一个有效的ISBN作为占位符
    dummy_isbn = create_valid_isbn("123456789")
    parsed = validator.parse(dummy_isbn)
    pattern = encoder.encode(parsed.digits)
    
    return RenderConfig(
        isbn=parsed,
        barcode_pattern=pattern,
        dpi=300,
        color_mode=ColorMode.BITMAP
    )


class TestBatchProcessingCompleteness:
    """Property 12: 批量处理完整性
    
    **Feature: isbn-barcode-generator, Property 12: 批量处理完整性**
    **Validates: Requirements 5.1, 5.2**
    
    *For any* 包含N个有效ISBN的列表，批量处理后应生成N个对应的TIF文件，
    每个文件名应包含对应的ISBN号。
    """
    
    @given(st.lists(
        st.text(alphabet="0123456789", min_size=9, max_size=9),
        min_size=1,
        max_size=5,
        unique=True
    ))
    @settings(max_examples=100)
    def test_batch_generates_correct_number_of_files(self, suffixes: list[str]):
        """批量处理N个有效ISBN应生成N个TIF文件"""
        # 创建有效的ISBN列表
        isbn_list = [create_valid_isbn(suffix) for suffix in suffixes]
        
        # 创建临时输出目录
        output_dir = tempfile.mkdtemp()
        try:
            processor = create_batch_processor()
            config = create_dummy_render_config()
            
            result = processor.process_list(isbn_list, output_dir, config)
            
            # 验证结果
            assert result.total == len(isbn_list), f"Total should be {len(isbn_list)}"
            assert result.success == len(isbn_list), f"Success should be {len(isbn_list)}"
            assert result.failed == 0, "Failed should be 0 for all valid ISBNs"
            assert len(result.errors) == 0, "Errors should be empty"
            
            # 验证生成的文件数量
            generated_files = [f for f in os.listdir(output_dir) if f.endswith('.tif')]
            assert len(generated_files) == len(isbn_list), \
                f"Should generate {len(isbn_list)} TIF files, got {len(generated_files)}"
        finally:
            shutil.rmtree(output_dir)
    
    @given(st.lists(
        st.text(alphabet="0123456789", min_size=9, max_size=9),
        min_size=1,
        max_size=5,
        unique=True
    ))
    @settings(max_examples=100)
    def test_batch_filenames_contain_isbn(self, suffixes: list[str]):
        """生成的文件名应包含对应的ISBN号"""
        isbn_list = [create_valid_isbn(suffix) for suffix in suffixes]
        
        output_dir = tempfile.mkdtemp()
        try:
            processor = create_batch_processor()
            config = create_dummy_render_config()
            
            processor.process_list(isbn_list, output_dir, config)
            
            # 验证每个ISBN都有对应的文件
            for isbn in isbn_list:
                expected_filename = f"{isbn}.tif"
                file_path = os.path.join(output_dir, expected_filename)
                assert os.path.exists(file_path), \
                    f"File {expected_filename} should exist for ISBN {isbn}"
        finally:
            shutil.rmtree(output_dir)
    
    @given(st.lists(
        st.text(alphabet="0123456789", min_size=9, max_size=9),
        min_size=1,
        max_size=3,
        unique=True
    ))
    @settings(max_examples=100)
    def test_batch_result_counts_match(self, suffixes: list[str]):
        """批量处理结果的计数应一致：total = success + failed"""
        isbn_list = [create_valid_isbn(suffix) for suffix in suffixes]
        
        output_dir = tempfile.mkdtemp()
        try:
            processor = create_batch_processor()
            config = create_dummy_render_config()
            
            result = processor.process_list(isbn_list, output_dir, config)
            
            # 验证计数一致性
            assert result.total == result.success + result.failed, \
                "total should equal success + failed"
        finally:
            shutil.rmtree(output_dir)



class TestBatchProcessingErrorIsolation:
    """Property 13: 批量处理错误隔离
    
    **Feature: isbn-barcode-generator, Property 13: 批量处理错误隔离**
    **Validates: Requirements 5.3, 5.4**
    
    *For any* 包含有效和无效ISBN混合的列表，批量处理应为所有有效ISBN生成文件，
    无效ISBN不应阻止其他ISBN的处理，且结果摘要应正确报告成功和失败数量。
    """
    
    @given(
        st.lists(
            st.text(alphabet="0123456789", min_size=9, max_size=9),
            min_size=1,
            max_size=3,
            unique=True
        ),
        st.lists(
            st.text(alphabet="0123456789", min_size=9, max_size=9),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_invalid_isbn_does_not_block_valid_ones(self, valid_suffixes: list[str], invalid_suffixes: list[str]):
        """无效ISBN不应阻止有效ISBN的处理"""
        # 确保两组后缀不重叠
        assume(set(valid_suffixes).isdisjoint(set(invalid_suffixes)))
        
        # 创建有效ISBN列表
        valid_isbns = [create_valid_isbn(suffix) for suffix in valid_suffixes]
        
        # 创建无效ISBN列表（使用错误的校验位）
        invalid_isbns = []
        for suffix in invalid_suffixes:
            isbn_12 = "978" + suffix
            validator = ISBNValidator()
            correct_check = validator.calculate_check_digit(isbn_12)
            wrong_check = str((int(correct_check) + 1) % 10)
            invalid_isbns.append(isbn_12 + wrong_check)
        
        # 混合有效和无效ISBN
        mixed_list = valid_isbns + invalid_isbns
        
        output_dir = tempfile.mkdtemp()
        try:
            processor = create_batch_processor()
            config = create_dummy_render_config()
            
            result = processor.process_list(mixed_list, output_dir, config)
            
            # 验证所有有效ISBN都成功生成了文件
            for isbn in valid_isbns:
                expected_filename = f"{isbn}.tif"
                file_path = os.path.join(output_dir, expected_filename)
                assert os.path.exists(file_path), \
                    f"Valid ISBN {isbn} should have generated file despite invalid ISBNs in list"
            
            # 验证成功数量等于有效ISBN数量
            assert result.success == len(valid_isbns), \
                f"Success count should be {len(valid_isbns)}, got {result.success}"
        finally:
            shutil.rmtree(output_dir)
    
    @given(
        st.lists(
            st.text(alphabet="0123456789", min_size=9, max_size=9),
            min_size=1,
            max_size=3,
            unique=True
        ),
        st.lists(
            st.text(alphabet="0123456789", min_size=9, max_size=9),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_result_summary_reports_correct_counts(self, valid_suffixes: list[str], invalid_suffixes: list[str]):
        """结果摘要应正确报告成功和失败数量"""
        assume(set(valid_suffixes).isdisjoint(set(invalid_suffixes)))
        
        valid_isbns = [create_valid_isbn(suffix) for suffix in valid_suffixes]
        
        invalid_isbns = []
        for suffix in invalid_suffixes:
            isbn_12 = "978" + suffix
            validator = ISBNValidator()
            correct_check = validator.calculate_check_digit(isbn_12)
            wrong_check = str((int(correct_check) + 1) % 10)
            invalid_isbns.append(isbn_12 + wrong_check)
        
        mixed_list = valid_isbns + invalid_isbns
        
        output_dir = tempfile.mkdtemp()
        try:
            processor = create_batch_processor()
            config = create_dummy_render_config()
            
            result = processor.process_list(mixed_list, output_dir, config)
            
            # 验证总数
            assert result.total == len(mixed_list), \
                f"Total should be {len(mixed_list)}, got {result.total}"
            
            # 验证成功数量
            assert result.success == len(valid_isbns), \
                f"Success should be {len(valid_isbns)}, got {result.success}"
            
            # 验证失败数量
            assert result.failed == len(invalid_isbns), \
                f"Failed should be {len(invalid_isbns)}, got {result.failed}"
            
            # 验证错误列表长度
            assert len(result.errors) == len(invalid_isbns), \
                f"Errors list should have {len(invalid_isbns)} items, got {len(result.errors)}"
        finally:
            shutil.rmtree(output_dir)
    
    @given(
        st.lists(
            st.text(alphabet="0123456789", min_size=9, max_size=9),
            min_size=1,
            max_size=3,
            unique=True
        ),
        st.lists(
            st.text(alphabet="0123456789", min_size=9, max_size=9),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=100)
    def test_errors_contain_invalid_isbn_info(self, valid_suffixes: list[str], invalid_suffixes: list[str]):
        """错误列表应包含无效ISBN的信息"""
        assume(set(valid_suffixes).isdisjoint(set(invalid_suffixes)))
        
        valid_isbns = [create_valid_isbn(suffix) for suffix in valid_suffixes]
        
        invalid_isbns = []
        for suffix in invalid_suffixes:
            isbn_12 = "978" + suffix
            validator = ISBNValidator()
            correct_check = validator.calculate_check_digit(isbn_12)
            wrong_check = str((int(correct_check) + 1) % 10)
            invalid_isbns.append(isbn_12 + wrong_check)
        
        mixed_list = valid_isbns + invalid_isbns
        
        output_dir = tempfile.mkdtemp()
        try:
            processor = create_batch_processor()
            config = create_dummy_render_config()
            
            result = processor.process_list(mixed_list, output_dir, config)
            
            # 验证每个无效ISBN都在错误列表中
            error_isbns = {error.isbn for error in result.errors}
            for invalid_isbn in invalid_isbns:
                assert invalid_isbn in error_isbns, \
                    f"Invalid ISBN {invalid_isbn} should be in errors list"
            
            # 验证每个错误都有错误信息
            for error in result.errors:
                assert error.error_message is not None, \
                    f"Error for ISBN {error.isbn} should have error message"
                assert len(error.error_message) > 0, \
                    f"Error message for ISBN {error.isbn} should not be empty"
        finally:
            shutil.rmtree(output_dir)


class TestNonDigitCharacterCleaning:
    """Property 1: 非数字字符清理
    
    **Feature: isbn-batch-import-optimization, Property 1: 非数字字符清理**
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    *For any* 包含数字和非数字字符混合的输入字符串，解析后提取的数字部分应仅包含原输入中的所有数字字符，且顺序保持不变。
    """
    
    @given(
        st.text(alphabet="0123456789", min_size=13, max_size=18).filter(
            lambda s: len(s) in (13, 15, 18)
        ),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-/ ", min_size=0, max_size=10)
    )
    @settings(max_examples=100)
    def test_non_digit_characters_removed_preserving_digit_order(self, digits: str, non_digits: str):
        """非数字字符应被去除，数字顺序保持不变
        
        测试策略：
        1. 生成有效长度的数字字符串（13、15或18位）
        2. 在数字之间随机插入非数字字符
        3. 验证解析后提取的数字与原始数字相同
        """
        # 在数字之间随机插入非数字字符
        mixed_input = ""
        for i, d in enumerate(digits):
            # 在每个数字前可能插入一些非数字字符
            if non_digits and i < len(non_digits):
                mixed_input += non_digits[i]
            mixed_input += d
        
        # 解析输入
        result = parse_isbn_input(mixed_input)
        
        # 验证解析成功
        assert result.is_valid, f"Should be valid for input with {len(digits)} digits"
        
        # 验证提取的数字与原始数字相同（顺序保持不变）
        extracted_digits = result.isbn_digits
        if result.addon_digits:
            extracted_digits += result.addon_digits
        
        assert extracted_digits == digits, \
            f"Extracted digits '{extracted_digits}' should equal original digits '{digits}'"
    
    @given(st.text(alphabet="0123456789", min_size=13, max_size=13))
    @settings(max_examples=100)
    def test_hyphen_separated_isbn_cleaned(self, digits: str):
        """带连字符的ISBN应正确清理
        
        测试格式如：978-7-5649-2235-1
        """
        # 构造带连字符的ISBN格式
        hyphenated = f"{digits[:3]}-{digits[3]}-{digits[4:8]}-{digits[8:12]}-{digits[12]}"
        
        result = parse_isbn_input(hyphenated)
        
        assert result.is_valid
        assert result.isbn_digits == digits
        assert result.addon_digits is None
    
    @given(st.text(alphabet="0123456789", min_size=13, max_size=13))
    @settings(max_examples=100)
    def test_isbn_prefix_ignored(self, digits: str):
        """ISBN字母前缀应被忽略
        
        测试格式如：ISBN 978-7-5649-2235-1
        """
        # 构造带ISBN前缀的格式
        prefixed = f"ISBN {digits}"
        
        result = parse_isbn_input(prefixed)
        
        assert result.is_valid
        assert result.isbn_digits == digits
        assert result.addon_digits is None
    
    @given(st.text(alphabet="0123456789", min_size=13, max_size=13))
    @settings(max_examples=100)
    def test_space_separated_isbn_cleaned(self, digits: str):
        """带空格的ISBN应正确清理"""
        # 构造带空格的ISBN格式
        spaced = f"{digits[:3]} {digits[3:6]} {digits[6:9]} {digits[9:]}"
        
        result = parse_isbn_input(spaced)
        
        assert result.is_valid
        assert result.isbn_digits == digits
        assert result.addon_digits is None


class Test13DigitRecognitionNoAddon:
    """Property 2: 13位数字识别为无附加码ISBN
    
    **Feature: isbn-batch-import-optimization, Property 2: 13位数字识别为无附加码ISBN**
    **Validates: Requirements 2.1, 3.3**
    
    *For any* 清理后长度为13位的数字字符串，解析结果应将全部13位识别为ISBN，附加码应为None。
    """
    
    @given(st.text(alphabet="0123456789", min_size=13, max_size=13))
    @settings(max_examples=100)
    def test_13_digit_recognized_as_isbn_no_addon(self, digits: str):
        """13位数字应被识别为无附加码的ISBN
        
        测试策略：
        1. 生成任意13位数字字符串
        2. 验证解析结果is_valid为True
        3. 验证isbn_digits等于输入的13位数字
        4. 验证addon_digits为None
        """
        result = parse_isbn_input(digits)
        
        assert result.is_valid, f"13-digit input '{digits}' should be valid"
        assert result.isbn_digits == digits, \
            f"ISBN digits should be '{digits}', got '{result.isbn_digits}'"
        assert result.addon_digits is None, \
            f"Addon digits should be None for 13-digit input, got '{result.addon_digits}'"
    
    @given(
        st.text(alphabet="0123456789", min_size=13, max_size=13),
        st.text(alphabet="-/ ", min_size=1, max_size=5)
    )
    @settings(max_examples=100)
    def test_13_digit_with_separators_recognized_as_isbn_no_addon(self, digits: str, separators: str):
        """带分隔符的13位数字应被识别为无附加码的ISBN
        
        测试策略：
        1. 生成13位数字字符串
        2. 在数字之间插入分隔符（连字符、斜杠、空格）
        3. 验证解析后仍然识别为13位ISBN，无附加码
        """
        # 在数字之间插入分隔符
        mixed_input = ""
        sep_index = 0
        for i, d in enumerate(digits):
            mixed_input += d
            # 在某些位置插入分隔符
            if i in (2, 3, 7, 11) and sep_index < len(separators):
                mixed_input += separators[sep_index]
                sep_index += 1
        
        result = parse_isbn_input(mixed_input)
        
        assert result.is_valid, f"Input '{mixed_input}' with 13 digits should be valid"
        assert result.isbn_digits == digits, \
            f"ISBN digits should be '{digits}', got '{result.isbn_digits}'"
        assert result.addon_digits is None, \
            f"Addon digits should be None for 13-digit input, got '{result.addon_digits}'"
    
    @given(st.text(alphabet="0123456789", min_size=13, max_size=13))
    @settings(max_examples=100)
    def test_13_digit_with_isbn_prefix_recognized_as_isbn_no_addon(self, digits: str):
        """带ISBN前缀的13位数字应被识别为无附加码的ISBN
        
        测试策略：
        1. 生成13位数字字符串
        2. 添加"ISBN "前缀
        3. 验证解析后仍然识别为13位ISBN，无附加码
        """
        prefixed_input = f"ISBN {digits}"
        
        result = parse_isbn_input(prefixed_input)
        
        assert result.is_valid, f"Input '{prefixed_input}' should be valid"
        assert result.isbn_digits == digits, \
            f"ISBN digits should be '{digits}', got '{result.isbn_digits}'"
        assert result.addon_digits is None, \
            f"Addon digits should be None for 13-digit input, got '{result.addon_digits}'"
