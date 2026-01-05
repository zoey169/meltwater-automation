#!/usr/bin/env python3
"""
测试 meltwater_downloader_v2.py 的关键功能
使用现有浏览器会话进行测试
"""

import os
import sys
from datetime import datetime

# 导入 v2 版本的类
from meltwater_downloader_v2 import MeltwaterDownloader

def test_download():
    """测试完整下载流程"""
    print("=" * 60)
    print("测试 meltwater_downloader_v2.py")
    print("=" * 60)

    # 从环境变量读取配置
    email = os.getenv("MELTWATER_EMAIL")
    password = os.getenv("MELTWATER_PASSWORD")
    url = os.getenv("MELTWATER_URL", "https://app.meltwater.com")
    download_path = os.getenv("DOWNLOAD_PATH", "./downloads")
    search_id = os.getenv("SEARCH_ID", "2062364")

    if not email or not password:
        print("❌ 错误: 缺少 MELTWATER_EMAIL 或 MELTWATER_PASSWORD 环境变量")
        return False

    print(f"\n配置:")
    print(f"  Email: {email}")
    print(f"  URL: {url}")
    print(f"  Download Path: {download_path}")
    print(f"  Search ID: {search_id}")
    print()

    # 创建下载器实例
    downloader = MeltwaterDownloader(
        email=email,
        password=password,
        url=url,
        download_path=download_path,
        search_id=search_id
    )

    try:
        # 测试下载过去一年的数据
        print("开始测试下载...")
        filepath = downloader.download(days_back=365)

        if filepath and os.path.exists(filepath):
            # 检查文件大小和行数
            file_size = os.path.getsize(filepath)
            with open(filepath, 'r', encoding='utf-16') as f:
                line_count = sum(1 for _ in f)

            print(f"\n✅ 测试成功!")
            print(f"  文件路径: {filepath}")
            print(f"  文件大小: {file_size / 1024:.2f} KB")
            print(f"  行数: {line_count} ({line_count - 1} 条记录 + 1 个表头)")

            # 验证数据完整性
            expected_records = 222
            actual_records = line_count - 1

            if actual_records >= expected_records - 10:  # 允许 ±10 条误差
                print(f"  ✅ 数据完整性检查通过 (预期 ~{expected_records} 条)")
                return True
            else:
                print(f"  ⚠️ 警告: 记录数({actual_records})少于预期({expected_records})")
                return False
        else:
            print("❌ 测试失败: 文件未下载")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_download()
    sys.exit(0 if success else 1)
