# _*_ coding :utf-8 _*_
# @Time : 2023/4/15 19:35
# @Author ：李文杰
# @Project : data_visualization
from django.core.cache import cache


def read_file_to_dataframe(file_path, page_number=0):
    import pandas as pd

    """
    读取xlsx、xls、csv格式的文件，并返回dataframe格式的数据
    """
    file_path = str(file_path)
    cache_key = f"report.utils.read_file_to_dataframe_{file_path}_{page_number}"
    df = cache.get(cache_key)

    if df is not None:
        cache.set(cache_key, df, 7200)
        return df
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        df = pd.read_excel(file_path, sheet_name=page_number)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format, only xlsx, xls, and csv are supported.")
    cache.set(cache_key, df, 7200)
    return df
