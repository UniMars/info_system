import hashlib
import re


def generate_id(word: str, record_id: int):
    # 使用哈希函数（如SHA-256）计算word的哈希值
    hash_obj = hashlib.sha256(word.encode())
    hash_value = int(hash_obj.hexdigest(), 16)

    # 取哈希值的低32位
    hash_lower_32_bits = hash_value & 0xFFFFFFFF

    # 将哈希值与record_id组合以生成64位ID
    id_64_bits = (hash_lower_32_bits << 32) | record_id

    # 将最高位设置为0，以确保返回的是63位整数
    id_63_bits = id_64_bits & 0x7FFFFFFFFFFFFFFF

    return id_63_bits


space = re.compile('[\u2002\u2003\u3000\u200b\u200c\u200d\u206c\xa0\x7f]')


def data_cleaning(content):
    content = space.sub(' ', content)
    content = content.replace('\xad', '')
    content = content.strip()
    return content
