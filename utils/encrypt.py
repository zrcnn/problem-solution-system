#!/usr/bin/env python3
"""
ID加密工具
将简单的数字ID加密为复杂的字符串，避免在URL中暴露真实ID
"""

import base64
import hashlib
import random
import string
from typing import Optional


class IDCrypt:
    """ID加密解密工具类"""
    
    # 默认密钥，生产环境应该从配置中读取
    DEFAULT_KEY = "dunYuan_2024_SecureKey_X9k2m"
    
    def __init__(self, key: str = None):
        """
        初始化工具类
        
        Args:
            key: 加密密钥，如果为None则使用默认密钥
        """
        self.key = key or self.DEFAULT_KEY
        # 生成密钥的哈希，用于加密
        self.key_hash = hashlib.sha256(self.key.encode()).digest()
    
    def _generate_salt(self) -> str:
        """生成随机盐值（8位字母数字）"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    def _xor_with_key(self, data: bytes) -> bytes:
        """使用密钥对数据进行XOR操作"""
        key_len = len(self.key_hash)
        return bytes(b ^ self.key_hash[i % key_len] for i, b in enumerate(data))
    
    def encrypt(self, id_value: int, prefix: str = "") -> str:
        """
        加密ID
        
        Args:
            id_value: 要加密的数字ID
            prefix: 前缀标识（可选），用于区分不同类型的ID
            
        Returns:
            加密后的字符串（8位以上）
        """
        # 1. 将ID转换为4字节
        id_bytes = id_value.to_bytes(4, byteorder='big')
        
        # 2. 生成随机盐值
        salt = self._generate_salt().encode()
        
        # 3. 组合数据：盐值 + ID
        data = salt + id_bytes
        
        # 4. XOR加密
        encrypted = self._xor_with_key(data)
        
        # 5. Base64编码
        encoded = base64.urlsafe_b64encode(encrypted).decode()
        
        # 6. 添加前缀（如果有）
        if prefix:
            return f"{prefix}_{encoded}"
        
        return encoded
    
    def decrypt(self, encrypted_str: str, prefix: str = "") -> Optional[int]:
        """
        解密ID
        
        Args:
            encrypted_str: 加密后的字符串
            prefix: 前缀标识（可选）
            
        Returns:
            解密后的数字ID，如果解密失败返回None
        """
        try:
            # 1. 移除前缀
            if prefix and encrypted_str.startswith(f"{prefix}_"):
                encrypted_str = encrypted_str[len(prefix) + 1:]
            
            # 2. Base64解码
            decoded = base64.urlsafe_b64decode(encrypted_str.encode())
            
            # 3. XOR解密
            decrypted = self._xor_with_key(decoded)
            
            # 4. 提取ID（最后4字节）
            id_bytes = decrypted[-4:]
            id_value = int.from_bytes(id_bytes, byteorder='big')
            
            return id_value
            
        except Exception as e:
            # 解密失败
            print(f"ID解密失败: {e}")
            return None
    
    def encrypt_product_id(self, product_id: int) -> str:
        """加密产品ID"""
        return self.encrypt(product_id, prefix="p")
    
    def decrypt_product_id(self, encrypted_str: str) -> Optional[int]:
        """解密产品ID"""
        return self.decrypt(encrypted_str, prefix="p")
    
    def encrypt_card_id(self, card_id: int) -> str:
        """加密卡片ID"""
        return self.encrypt(card_id, prefix="c")
    
    def decrypt_card_id(self, encrypted_str: str) -> Optional[int]:
        """解密卡片ID"""
        return self.decrypt(encrypted_str, prefix="c")
    
    def encrypt_problem_id(self, problem_id: int) -> str:
        """加密问题ID"""
        return self.encrypt(problem_id, prefix="q")
    
    def decrypt_problem_id(self, encrypted_str: str) -> Optional[int]:
        """解密问题ID"""
        return self.decrypt(encrypted_str, prefix="q")


# 全局加密工具实例
id_crypt = IDCrypt()


def encrypt_product_id(product_id: int) -> str:
    """加密产品ID"""
    return id_crypt.encrypt_product_id(product_id)


def decrypt_product_id(encrypted_str: str) -> Optional[int]:
    """解密产品ID"""
    return id_crypt.decrypt_product_id(encrypted_str)


def encrypt_card_id(card_id: int) -> str:
    """加密卡片ID"""
    return id_crypt.encrypt_card_id(card_id)


def decrypt_card_id(encrypted_str: str) -> Optional[int]:
    """解密卡片ID"""
    return id_crypt.decrypt_card_id(encrypted_str)


def encrypt_problem_id(problem_id: int) -> str:
    """加密问题ID"""
    return id_crypt.encrypt_problem_id(problem_id)


def decrypt_problem_id(encrypted_str: str) -> Optional[int]:
    """解密问题ID"""
    return id_crypt.decrypt_problem_id(encrypted_str)


if __name__ == "__main__":
    # 测试加密解密功能
    print("=== ID加密工具测试 ===")
    
    # 测试产品ID
    product_id = 1
    encrypted = encrypt_product_id(product_id)
    decrypted = decrypt_product_id(encrypted)
    print(f"产品ID: {product_id} -> 加密: {encrypted} -> 解密: {decrypted}")
    assert decrypted == product_id, "产品ID解密失败"
    
    # 测试卡片ID
    card_id = 123
    encrypted = encrypt_card_id(card_id)
    decrypted = decrypt_card_id(encrypted)
    print(f"卡片ID: {card_id} -> 加密: {encrypted} -> 解密: {decrypted}")
    assert decrypted == card_id, "卡片ID解密失败"
    
    # 测试问题ID
    problem_id = 616
    encrypted = encrypt_problem_id(problem_id)
    decrypted = decrypt_problem_id(encrypted)
    print(f"问题ID: {problem_id} -> 加密: {encrypted} -> 解密: {decrypted}")
    assert decrypted == problem_id, "问题ID解密失败"
    
    # 测试多次加密产生不同结果（因为盐值随机）
    encrypted1 = encrypt_product_id(1)
    encrypted2 = encrypt_product_id(1)
    print(f"\n同一ID多次加密结果不同: {encrypted1} != {encrypted2}: {encrypted1 != encrypted2}")
    assert encrypted1 != encrypted2, "同一ID多次加密应该产生不同结果"
    
    print("\n✅ 所有测试通过！")
