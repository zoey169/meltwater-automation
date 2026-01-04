#!/usr/bin/env python3
"""
从飞书多维表格 URL 提取 app_token 和 table_id
"""
import re

url = "https://anker-in.feishu.cn/base/ExoBbLPZoajFihsvegNcDvUsnce?table=tblqmDCzRUdDMI3x&view=vewxycGIAm"

# 提取 app_token (base/ 后面的部分)
app_token_match = re.search(r'/base/([a-zA-Z0-9]+)', url)
app_token = app_token_match.group(1) if app_token_match else None

# 提取 table_id (table= 后面的部分)
table_id_match = re.search(r'table=([a-zA-Z0-9]+)', url)
table_id = table_id_match.group(1) if table_id_match else None

print("=" * 60)
print("从 URL 提取的多维表格信息:")
print("=" * 60)
print(f"App Token:  {app_token}")
print(f"Table ID:   {table_id}")
print("=" * 60)
print("\n环境变量配置:")
print(f"export BITABLE_APP_TOKEN=\"{app_token}\"")
print(f"export BITABLE_TABLE_ID=\"{table_id}\"")
print("=" * 60)
