"""
EAN-13 Encoder Tests - EAN-13编码器测试
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from src.isbn_barcode_generator.core.encoder import EAN13Encoder, BarcodePattern
from src.isbn_barcode_generator.core.validator import ISBNValidator


# 生成有效ISBN-12前缀的策略（978或979开头）
isbn_prefix_strategy = st.sampled_from(["978", "979"])
isbn_suffix_strategy = st.text(alphabet="0123456789", min_size=9, max_size=9)


@st.composite
def valid_isbn_12(draw):
    """生成有效的ISBN-12前缀（不含校验位）"""
    prefix = draw(isbn_prefix_strategy)
    suffix = draw(isbn_suffix_strategy)
    return prefix + suffix


class TestEAN13EncoderStructure:
    """Property 3: EAN-13编码结构完整性
    
    Feature: isbn-barcode-generator, Property 3: EAN-13编码结构完整性
    Validates: Requirements 2.1, 2.2
    
    *For any* 有效的13位ISBN数字，编码后的条码图案应包含：
    - 3个模块的起始符
    - 42个模块的左侧数据
    - 5个模块的中间分隔符
    - 42个模块的右侧数据
    - 3个模块的终止符
    - 总计95个模块
    """
    
    @given(valid_isbn_12())
    @settings(max_examples=100)
    def test_ean13_structure_completeness(self, isbn_12: str):
        """
        Feature: isbn-barcode-generator, Property 3: EAN-13编码结构完整性
        Validates: Requirements 2.1, 2.2
        """
        # 计算正确的校验位生成有效的ISBN-13
        validator = ISBNValidator()
        check_digit = validator.calculate_check_digit(isbn_12)
        isbn_13 = isbn_12 + check_digit
        
        # 编码
        encoder = EAN13Encoder()
        pattern = encoder.encode(isbn_13)
        
        # 验证总模块数为95
        assert pattern.module_count == 95, f"Expected 95 modules, got {pattern.module_count}"
        assert len(pattern.bars) == 95, f"Expected 95 bars, got {len(pattern.bars)}"
        
        # 验证起始符 (101) - 位置0-2
        start_guard = pattern.bars[0:3]
        assert start_guard == [1, 0, 1], f"Start guard should be [1,0,1], got {start_guard}"
        
        # 验证左侧数据区域 - 位置3-44 (42个模块)
        left_data = pattern.bars[3:45]
        assert len(left_data) == 42, f"Left data should be 42 modules, got {len(left_data)}"
        
        # 验证中间分隔符 (01010) - 位置45-49
        center_guard = pattern.bars[45:50]
        assert center_guard == [0, 1, 0, 1, 0], f"Center guard should be [0,1,0,1,0], got {center_guard}"
        
        # 验证右侧数据区域 - 位置50-91 (42个模块)
        right_data = pattern.bars[50:92]
        assert len(right_data) == 42, f"Right data should be 42 modules, got {len(right_data)}"
        
        # 验证终止符 (101) - 位置92-94
        end_guard = pattern.bars[92:95]
        assert end_guard == [1, 0, 1], f"End guard should be [1,0,1], got {end_guard}"
        
        # 验证所有条码值只能是0或1
        for bar in pattern.bars:
            assert bar in [0, 1], f"Bar value should be 0 or 1, got {bar}"



class TestEAN13ParityEncoding:
    """Property 4: EAN-13奇偶编码模式正确性
    
    Feature: isbn-barcode-generator, Property 4: EAN-13奇偶编码模式正确性
    Validates: Requirements 2.3
    
    *For any* 有效的ISBN-13，第一位数字决定的奇偶编码模式应正确应用于左侧6位数字的编码。
    """
    
    @given(valid_isbn_12())
    @settings(max_examples=100)
    def test_ean13_parity_encoding_correctness(self, isbn_12: str):
        """
        Feature: isbn-barcode-generator, Property 4: EAN-13奇偶编码模式正确性
        Validates: Requirements 2.3
        """
        # 计算正确的校验位生成有效的ISBN-13
        validator = ISBNValidator()
        check_digit = validator.calculate_check_digit(isbn_12)
        isbn_13 = isbn_12 + check_digit
        
        encoder = EAN13Encoder()
        pattern = encoder.encode(isbn_13)
        
        # 获取第一位数字决定的奇偶模式
        first_digit = isbn_13[0]
        parity_pattern = encoder._get_parity_pattern(first_digit)
        
        # 验证奇偶模式长度为6
        assert len(parity_pattern) == 6, f"Parity pattern should be 6 chars, got {len(parity_pattern)}"
        
        # 验证奇偶模式只包含L和G
        for char in parity_pattern:
            assert char in ['L', 'G'], f"Parity pattern should only contain L or G, got {char}"
        
        # 验证左侧6位数字的编码是否符合奇偶模式
        # 左侧数据从位置3开始，每位数字7个模块
        left_data = pattern.bars[3:45]
        
        for i in range(6):
            digit = isbn_13[i + 1]  # 左侧6位是isbn_13[1:7]
            digit_encoding = left_data[i * 7:(i + 1) * 7]
            digit_encoding_str = ''.join(str(b) for b in digit_encoding)
            
            if parity_pattern[i] == 'L':
                expected_encoding = encoder.L_CODES[digit]
                assert digit_encoding_str == expected_encoding, \
                    f"Digit {digit} at position {i} should use L-code {expected_encoding}, got {digit_encoding_str}"
            else:  # 'G'
                expected_encoding = encoder.G_CODES[digit]
                assert digit_encoding_str == expected_encoding, \
                    f"Digit {digit} at position {i} should use G-code {expected_encoding}, got {digit_encoding_str}"
    
    @given(st.sampled_from(list("0123456789")))
    @settings(max_examples=10)
    def test_parity_pattern_lookup(self, first_digit: str):
        """验证奇偶模式查找表的正确性"""
        encoder = EAN13Encoder()
        parity = encoder._get_parity_pattern(first_digit)
        
        # 验证返回的模式在预定义表中
        assert parity == encoder.PARITY_PATTERNS[first_digit]
        
        # 验证模式长度为6
        assert len(parity) == 6
        
        # 验证模式只包含L和G
        assert all(c in ['L', 'G'] for c in parity)


class TestEAN13RightSideEncoding:
    """验证右侧数据使用R编码"""
    
    @given(valid_isbn_12())
    @settings(max_examples=100)
    def test_right_side_uses_r_codes(self, isbn_12: str):
        """验证右侧6位数字全部使用R编码"""
        validator = ISBNValidator()
        check_digit = validator.calculate_check_digit(isbn_12)
        isbn_13 = isbn_12 + check_digit
        
        encoder = EAN13Encoder()
        pattern = encoder.encode(isbn_13)
        
        # 右侧数据从位置50开始，每位数字7个模块
        right_data = pattern.bars[50:92]
        
        for i in range(6):
            digit = isbn_13[i + 7]  # 右侧6位是isbn_13[7:13]
            digit_encoding = right_data[i * 7:(i + 1) * 7]
            digit_encoding_str = ''.join(str(b) for b in digit_encoding)
            
            expected_encoding = encoder.R_CODES[digit]
            assert digit_encoding_str == expected_encoding, \
                f"Digit {digit} at right position {i} should use R-code {expected_encoding}, got {digit_encoding_str}"
