"""
Addon Encoder Tests - 附加码编码器测试

Property 5: 附加码编码长度正确性
Validates: Requirements 3.1, 3.2
"""

import pytest
from hypothesis import given, strategies as st, settings

from src.isbn_barcode_generator.core.addon_encoder import AddonEncoder


class TestAddonEncoderProperties:
    """附加码编码器属性测试"""
    
    @given(st.text(alphabet="0123456789", min_size=2, max_size=2))
    @settings(max_examples=100)
    def test_ean2_encoding_length(self, digits: str):
        """
        Feature: isbn-barcode-generator, Property 5: 附加码编码长度正确性
        
        *For any* 2位数字字符串，EAN-2编码后应产生20个模块的条码图案。
        
        EAN-2结构：
        - 起始符：4个模块 (1011)
        - 第1位数字：7个模块
        - 分隔符：2个模块 (01)
        - 第2位数字：7个模块
        - 总计：4 + 7 + 2 + 7 = 20个模块
        
        **Validates: Requirements 3.1**
        """
        encoder = AddonEncoder()
        pattern = encoder.encode_2(digits)
        
        # EAN-2应产生20个模块
        assert pattern.module_count == 20, \
            f"EAN-2编码应产生20个模块，实际为{pattern.module_count}个"
        
        # 验证bars列表长度与module_count一致
        assert len(pattern.bars) == pattern.module_count, \
            f"bars长度({len(pattern.bars)})应与module_count({pattern.module_count})一致"
        
        # 验证所有元素都是0或1
        assert all(b in (0, 1) for b in pattern.bars), \
            "条码图案应只包含0和1"
    
    @given(st.text(alphabet="0123456789", min_size=5, max_size=5))
    @settings(max_examples=100)
    def test_ean5_encoding_length(self, digits: str):
        """
        Feature: isbn-barcode-generator, Property 5: 附加码编码长度正确性
        
        *For any* 5位数字字符串，EAN-5编码后应产生47个模块的条码图案。
        
        EAN-5结构：
        - 起始符：4个模块 (1011)
        - 5位数字，每位7个模块：35个模块
        - 4个分隔符，每个2个模块：8个模块
        - 总计：4 + 35 + 8 = 47个模块
        
        **Validates: Requirements 3.2**
        """
        encoder = AddonEncoder()
        pattern = encoder.encode_5(digits)
        
        # EAN-5应产生47个模块
        assert pattern.module_count == 47, \
            f"EAN-5编码应产生47个模块，实际为{pattern.module_count}个"
        
        # 验证bars列表长度与module_count一致
        assert len(pattern.bars) == pattern.module_count, \
            f"bars长度({len(pattern.bars)})应与module_count({pattern.module_count})一致"
        
        # 验证所有元素都是0或1
        assert all(b in (0, 1) for b in pattern.bars), \
            "条码图案应只包含0和1"


class TestAddonEncoderUnit:
    """附加码编码器单元测试"""
    
    def test_encode_2_valid_input(self):
        """测试有效的2位附加码编码"""
        encoder = AddonEncoder()
        pattern = encoder.encode_2("12")
        
        assert pattern.module_count == 20
        assert len(pattern.bars) == 20
        # 验证起始符 (1011)
        assert pattern.bars[:4] == [1, 0, 1, 1]
    
    def test_encode_5_valid_input(self):
        """测试有效的5位附加码编码"""
        encoder = AddonEncoder()
        pattern = encoder.encode_5("12345")
        
        assert pattern.module_count == 47
        assert len(pattern.bars) == 47
        # 验证起始符 (1011)
        assert pattern.bars[:4] == [1, 0, 1, 1]
    
    def test_encode_2_invalid_length(self):
        """测试无效长度的2位附加码"""
        encoder = AddonEncoder()
        
        with pytest.raises(ValueError, match="EAN-2需要2位数字"):
            encoder.encode_2("1")
        
        with pytest.raises(ValueError, match="EAN-2需要2位数字"):
            encoder.encode_2("123")
    
    def test_encode_5_invalid_length(self):
        """测试无效长度的5位附加码"""
        encoder = AddonEncoder()
        
        with pytest.raises(ValueError, match="EAN-5需要5位数字"):
            encoder.encode_5("1234")
        
        with pytest.raises(ValueError, match="EAN-5需要5位数字"):
            encoder.encode_5("123456")
    
    def test_encode_2_non_digit(self):
        """测试非数字输入的2位附加码"""
        encoder = AddonEncoder()
        
        with pytest.raises(ValueError, match="输入必须全部为数字"):
            encoder.encode_2("ab")
    
    def test_encode_5_non_digit(self):
        """测试非数字输入的5位附加码"""
        encoder = AddonEncoder()
        
        with pytest.raises(ValueError, match="输入必须全部为数字"):
            encoder.encode_5("abcde")
    
    def test_checksum_2_calculation(self):
        """测试2位附加码校验和计算"""
        encoder = AddonEncoder()
        
        # 校验和 = 数值 % 4
        assert encoder._calculate_checksum_2("00") == 0
        assert encoder._calculate_checksum_2("04") == 0
        assert encoder._calculate_checksum_2("01") == 1
        assert encoder._calculate_checksum_2("05") == 1
        assert encoder._calculate_checksum_2("02") == 2
        assert encoder._calculate_checksum_2("03") == 3
    
    def test_checksum_5_calculation(self):
        """测试5位附加码校验和计算"""
        encoder = AddonEncoder()
        
        # 校验和 = (d1*3 + d2*9 + d3*3 + d4*9 + d5*3) % 10
        # "12345": 1*3 + 2*9 + 3*3 + 4*9 + 5*3 = 3 + 18 + 9 + 36 + 15 = 81 % 10 = 1
        assert encoder._calculate_checksum_5("12345") == 1
        
        # "00000": 0*3 + 0*9 + 0*3 + 0*9 + 0*3 = 0 % 10 = 0
        assert encoder._calculate_checksum_5("00000") == 0
