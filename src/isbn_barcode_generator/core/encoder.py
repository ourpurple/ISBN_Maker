"""
EAN-13 Encoder - EAN-13条码编码模块
"""

from dataclasses import dataclass


@dataclass
class BarcodePattern:
    """条码图案数据
    
    Attributes:
        bars: 条码图案列表 (1=黑条, 0=白条)
        module_count: 模块总数
        guard_positions: 保护条位置列表（用于延长显示）
    """
    bars: list[int]             # 条码图案 (1=黑条, 0=白条)
    module_count: int           # 模块总数
    guard_positions: list[int]  # 保护条位置（用于延长显示）


class EAN13Encoder:
    """EAN-13条码编码器
    
    将13位ISBN/EAN数字编码为符合GS1标准的EAN-13条码图案。
    
    EAN-13条码结构（共95个模块）：
    - 起始符：3个模块 (101)
    - 左侧数据：42个模块 (6位数字 × 7模块)
    - 中间分隔符：5个模块 (01010)
    - 右侧数据：42个模块 (6位数字 × 7模块)
    - 终止符：3个模块 (101)
    """
    
    # 起始符和终止符
    START_GUARD = "101"
    CENTER_GUARD = "01010"
    END_GUARD = "101"
    
    # 左侧奇数编码 (L-codes)
    L_CODES: dict[str, str] = {
        "0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101",
        "4": "0100011", "5": "0110001", "6": "0101111", "7": "0111011",
        "8": "0110111", "9": "0001011"
    }
    
    # 左侧偶数编码 (G-codes)
    G_CODES: dict[str, str] = {
        "0": "0100111", "1": "0110011", "2": "0011011", "3": "0100001",
        "4": "0011101", "5": "0111001", "6": "0000101", "7": "0010001",
        "8": "0001001", "9": "0010111"
    }
    
    # 右侧编码 (R-codes)
    R_CODES: dict[str, str] = {
        "0": "1110010", "1": "1100110", "2": "1101100", "3": "1000010",
        "4": "1011100", "5": "1001110", "6": "1010000", "7": "1000100",
        "8": "1001000", "9": "1110100"
    }
    
    # 奇偶校验模式 (根据第一位数字决定左侧6位的编码方式)
    # L = 使用L_CODES (奇数编码)
    # G = 使用G_CODES (偶数编码)
    PARITY_PATTERNS: dict[str, str] = {
        "0": "LLLLLL", "1": "LLGLGG", "2": "LLGGLG", "3": "LLGGGL",
        "4": "LGLLGG", "5": "LGGLLG", "6": "LGGGLL", "7": "LGLGLG",
        "8": "LGLGGL", "9": "LGGLGL"
    }
    
    def encode(self, digits: str) -> BarcodePattern:
        """将13位数字编码为条码图案
        
        Args:
            digits: 13位纯数字字符串
            
        Returns:
            BarcodePattern: 包含条码图案、模块数和保护条位置的数据对象
            
        Raises:
            ValueError: 如果输入不是13位数字
        """
        # 验证输入
        if len(digits) != 13:
            raise ValueError(f"EAN-13需要13位数字，当前为{len(digits)}位")
        if not digits.isdigit():
            raise ValueError("输入必须全部为数字")
        
        # 获取奇偶编码模式
        parity_pattern = self._get_parity_pattern(digits[0])
        
        # 构建条码图案
        bars_str = ""
        guard_positions: list[int] = []
        
        # 1. 起始符 (3个模块)
        start_pos = 0
        bars_str += self.START_GUARD
        guard_positions.extend([start_pos, start_pos + 1, start_pos + 2])
        
        # 2. 左侧数据 (6位数字，每位7个模块，共42个模块)
        # 使用digits[1:7]，根据parity_pattern选择L或G编码
        for i, digit in enumerate(digits[1:7]):
            if parity_pattern[i] == 'L':
                bars_str += self.L_CODES[digit]
            else:  # 'G'
                bars_str += self.G_CODES[digit]
        
        # 3. 中间分隔符 (5个模块)
        center_start = len(bars_str)
        bars_str += self.CENTER_GUARD
        guard_positions.extend([center_start, center_start + 1, center_start + 2,
                               center_start + 3, center_start + 4])
        
        # 4. 右侧数据 (6位数字，每位7个模块，共42个模块)
        # 使用digits[7:13]，全部使用R编码
        for digit in digits[7:13]:
            bars_str += self.R_CODES[digit]
        
        # 5. 终止符 (3个模块)
        end_start = len(bars_str)
        bars_str += self.END_GUARD
        guard_positions.extend([end_start, end_start + 1, end_start + 2])
        
        # 转换为整数列表
        bars = [int(b) for b in bars_str]
        
        return BarcodePattern(
            bars=bars,
            module_count=len(bars),
            guard_positions=guard_positions
        )
    
    def _get_parity_pattern(self, first_digit: str) -> str:
        """根据第一位数字获取奇偶编码模式
        
        第一位数字决定了左侧6位数字使用L编码还是G编码的模式。
        
        Args:
            first_digit: 第一位数字字符
            
        Returns:
            str: 6字符的奇偶模式字符串，如"LLGLGG"
            
        Raises:
            ValueError: 如果输入不是单个数字
        """
        if len(first_digit) != 1 or not first_digit.isdigit():
            raise ValueError("first_digit必须是单个数字字符")
        
        return self.PARITY_PATTERNS[first_digit]
