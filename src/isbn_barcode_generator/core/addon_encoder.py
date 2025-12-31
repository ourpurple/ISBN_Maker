"""
Addon Encoder - EAN-2/EAN-5附加码编码模块

EAN-2附加码结构（共20个模块）：
- 起始符：4个模块 (1011)
- 第1位数字：7个模块
- 分隔符：2个模块 (01)
- 第2位数字：7个模块

EAN-5附加码结构（共47个模块）：
- 起始符：4个模块 (1011)
- 第1位数字：7个模块
- 分隔符：2个模块 (01)
- 第2位数字：7个模块
- 分隔符：2个模块 (01)
- 第3位数字：7个模块
- 分隔符：2个模块 (01)
- 第4位数字：7个模块
- 分隔符：2个模块 (01)
- 第5位数字：7个模块
"""

from .encoder import BarcodePattern


class AddonEncoder:
    """EAN-2/EAN-5附加码编码器
    
    将2位或5位数字编码为符合GS1标准的附加码条码图案。
    附加码用于在主条码右侧显示额外信息（如价格）。
    """
    
    # 起始符
    START_GUARD = "1011"
    
    # 数字间分隔符
    SEPARATOR = "01"
    
    # 附加码左侧编码 (与EAN-13的L/G编码相同)
    L_CODES: dict[str, str] = {
        "0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101",
        "4": "0100011", "5": "0110001", "6": "0101111", "7": "0111011",
        "8": "0110111", "9": "0001011"
    }
    
    G_CODES: dict[str, str] = {
        "0": "0100111", "1": "0110011", "2": "0011011", "3": "0100001",
        "4": "0011101", "5": "0111001", "6": "0000101", "7": "0010001",
        "8": "0001001", "9": "0010111"
    }
    
    # EAN-2奇偶模式 (根据校验和决定)
    EAN2_PARITY: dict[int, str] = {
        0: "LL", 1: "LG", 2: "GL", 3: "GG"
    }
    
    # EAN-5奇偶模式 (根据校验和决定)
    EAN5_PARITY: dict[int, str] = {
        0: "GGLLL", 1: "GLGLL", 2: "GLLGL", 3: "GLLLG", 4: "LGGLL",
        5: "LLGGL", 6: "LLLGG", 7: "LGLGL", 8: "LGLLG", 9: "LLGLG"
    }
    
    def encode_2(self, digits: str) -> BarcodePattern:
        """编码2位附加码
        
        EAN-2附加码结构（共20个模块）：
        - 起始符：4个模块 (1011)
        - 第1位数字：7个模块
        - 分隔符：2个模块 (01)
        - 第2位数字：7个模块
        
        Args:
            digits: 2位数字字符串
            
        Returns:
            BarcodePattern: 包含条码图案的数据对象
            
        Raises:
            ValueError: 如果输入不是2位数字
        """
        # 验证输入
        if len(digits) != 2:
            raise ValueError(f"EAN-2需要2位数字，当前为{len(digits)}位")
        if not digits.isdigit():
            raise ValueError("输入必须全部为数字")
        
        # 计算校验和以确定奇偶模式
        checksum = self._calculate_checksum_2(digits)
        parity_pattern = self.EAN2_PARITY[checksum]
        
        # 构建条码图案
        bars_str = ""
        guard_positions: list[int] = []
        
        # 1. 起始符 (4个模块)
        bars_str += self.START_GUARD
        guard_positions.extend([0, 1, 2, 3])
        
        # 2. 编码数字
        for i, digit in enumerate(digits):
            # 选择L或G编码
            if parity_pattern[i] == 'L':
                bars_str += self.L_CODES[digit]
            else:  # 'G'
                bars_str += self.G_CODES[digit]
            
            # 在数字之间添加分隔符（最后一位后不加）
            if i < len(digits) - 1:
                bars_str += self.SEPARATOR
        
        # 转换为整数列表
        bars = [int(b) for b in bars_str]
        
        return BarcodePattern(
            bars=bars,
            module_count=len(bars),
            guard_positions=guard_positions
        )
    
    def encode_5(self, digits: str) -> BarcodePattern:
        """编码5位附加码
        
        EAN-5附加码结构（共47个模块）：
        - 起始符：4个模块 (1011)
        - 5位数字，每位7个模块，数字间有2个模块的分隔符
        - 总计：4 + 7*5 + 2*4 = 4 + 35 + 8 = 47个模块
        
        Args:
            digits: 5位数字字符串
            
        Returns:
            BarcodePattern: 包含条码图案的数据对象
            
        Raises:
            ValueError: 如果输入不是5位数字
        """
        # 验证输入
        if len(digits) != 5:
            raise ValueError(f"EAN-5需要5位数字，当前为{len(digits)}位")
        if not digits.isdigit():
            raise ValueError("输入必须全部为数字")
        
        # 计算校验和以确定奇偶模式
        checksum = self._calculate_checksum_5(digits)
        parity_pattern = self.EAN5_PARITY[checksum]
        
        # 构建条码图案
        bars_str = ""
        guard_positions: list[int] = []
        
        # 1. 起始符 (4个模块)
        bars_str += self.START_GUARD
        guard_positions.extend([0, 1, 2, 3])
        
        # 2. 编码数字
        for i, digit in enumerate(digits):
            # 选择L或G编码
            if parity_pattern[i] == 'L':
                bars_str += self.L_CODES[digit]
            else:  # 'G'
                bars_str += self.G_CODES[digit]
            
            # 在数字之间添加分隔符（最后一位后不加）
            if i < len(digits) - 1:
                bars_str += self.SEPARATOR
        
        # 转换为整数列表
        bars = [int(b) for b in bars_str]
        
        return BarcodePattern(
            bars=bars,
            module_count=len(bars),
            guard_positions=guard_positions
        )
    
    def _calculate_checksum_2(self, digits: str) -> int:
        """计算2位附加码校验和
        
        EAN-2校验和计算：将2位数字作为整数，对4取模
        
        Args:
            digits: 2位数字字符串
            
        Returns:
            int: 校验和 (0-3)
        """
        value = int(digits)
        return value % 4
    
    def _calculate_checksum_5(self, digits: str) -> int:
        """计算5位附加码校验和
        
        EAN-5校验和计算：
        - 奇数位（1,3,5）乘以3
        - 偶数位（2,4）乘以9
        - 求和后对10取模
        
        Args:
            digits: 5位数字字符串
            
        Returns:
            int: 校验和 (0-9)
        """
        total = 0
        for i, digit in enumerate(digits):
            d = int(digit)
            if i % 2 == 0:  # 奇数位 (索引0,2,4 对应位置1,3,5)
                total += d * 3
            else:  # 偶数位 (索引1,3 对应位置2,4)
                total += d * 9
        return total % 10
