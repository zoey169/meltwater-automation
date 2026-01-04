#!/usr/bin/env python3
"""
测试导出触发策略 - 模拟 GitHub Actions 环境(没有预先存在的文件)
通过修改下载脚本,强制跳过 Home Alerts 检查,直接测试导出触发逻辑
"""
import os
import sys

# 读取原始脚本
with open('meltwater_downloader.py', 'r') as f:
    original_code = f.read()

# 修改代码,强制跳过 Home Alerts 检查
# 将 "if anz_file_exists:" 改为 "if False:" 来强制进入 else 分支
modified_code = original_code.replace(
    'if anz_file_exists:',
    'if False:  # 强制跳过 Home Alerts 检查以测试导出触发策略'
)

# 写入临时测试文件
test_file = 'meltwater_downloader_test_trigger.py'
with open(test_file, 'w') as f:
    f.write(modified_code)

print("=" * 80)
print("创建了测试文件:", test_file)
print("该文件强制跳过 Home Alerts 检查,直接测试导出触发和等待逻辑")
print("=" * 80)
print()
print("要运行测试,请执行:")
print(f"python3 {test_file}")
print()
print("注意:这个测试可能需要等待 5+ 分钟,因为需要触发导出并等待完成")
