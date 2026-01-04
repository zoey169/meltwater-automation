#!/usr/bin/env python3
"""
完整流程测试脚本
步骤:
1. 使用 meltwater_downloader 登录并下载 CSV
2. 使用 meltwater_auto_import 导入数据到多维表格
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def log(msg):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def run_command(cmd, description):
    """执行命令并返回结果"""
    log(f"开始: {description}")
    log(f"命令: {cmd}")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log(f"✅ 成功: {description}")
        return True, result.stdout
    else:
        log(f"❌ 失败: {description}")
        log(f"错误输出:\n{result.stderr}")
        return False, result.stderr

def main():
    log("=" * 60)
    log("Meltwater 完整流程测试开始")
    log("=" * 60)

    # 检查环境变量
    required_env_vars = {
        "MELTWATER_EMAIL": os.getenv("MELTWATER_EMAIL"),
        "MELTWATER_PASSWORD": os.getenv("MELTWATER_PASSWORD"),
        "MELTWATER_URL": os.getenv("MELTWATER_URL"),
        "FEISHU_APP_ID": os.getenv("FEISHU_APP_ID"),
        "FEISHU_APP_SECRET": os.getenv("FEISHU_APP_SECRET"),
        "BITABLE_APP_TOKEN": os.getenv("BITABLE_APP_TOKEN"),
        "BITABLE_TABLE_ID": os.getenv("BITABLE_TABLE_ID"),
    }

    log("\n步骤 0: 检查环境变量")
    missing_vars = [k for k, v in required_env_vars.items() if not v]
    if missing_vars:
        log(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        return False

    log("✅ 所有必需的环境变量已设置")

    # 步骤 1: 下载 CSV
    log("\n" + "=" * 60)
    log("步骤 1: 从 Meltwater 下载 CSV 文件")
    log("=" * 60)

    download_cmd = f"""export MELTWATER_EMAIL="{os.getenv('MELTWATER_EMAIL')}" && \
export MELTWATER_PASSWORD='{os.getenv('MELTWATER_PASSWORD')}' && \
export MELTWATER_URL="{os.getenv('MELTWATER_URL')}" && \
export DOWNLOAD_PATH="./downloads" && \
python3 meltwater_downloader.py"""

    success, output = run_command(download_cmd, "Meltwater CSV 下载")

    if not success:
        log("❌ 下载步骤失败,终止流程")
        return False

    # 从输出中提取 CSV 文件路径
    csv_file = None
    for line in output.split('\n'):
        if 'SUCCESS:' in line:
            csv_file = line.split('SUCCESS:')[1].strip()
            break
        elif '✅ 下载完成:' in line or '✅ 文件下载成功:' in line:
            csv_file = line.split(':')[-1].strip()
            break

    if not csv_file or not os.path.exists(csv_file):
        log(f"❌ 找不到下载的 CSV 文件: {csv_file}")
        return False

    log(f"✅ CSV 文件下载成功: {csv_file}")

    # 步骤 2: 导入到多维表格
    log("\n" + "=" * 60)
    log("步骤 2: 导入数据到飞书多维表格")
    log("=" * 60)

    import_cmd = f"""export FEISHU_APP_ID="{os.getenv('FEISHU_APP_ID')}" && \
export FEISHU_APP_SECRET="{os.getenv('FEISHU_APP_SECRET')}" && \
export BITABLE_APP_TOKEN="{os.getenv('BITABLE_APP_TOKEN')}" && \
export BITABLE_TABLE_ID="{os.getenv('BITABLE_TABLE_ID')}" && \
export CSV_FILE_PATH="{csv_file}" && \
python3 meltwater_auto_import.py"""

    success, output = run_command(import_cmd, "导入数据到多维表格")

    if not success:
        log("❌ 导入步骤失败")
        log(f"输出:\n{output}")
        return False

    log("✅ 数据导入成功")
    log(f"输出:\n{output}")

    # 总结
    log("\n" + "=" * 60)
    log("🎉 完整流程测试成功!")
    log("=" * 60)
    log(f"下载文件: {csv_file}")
    log(f"导入完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log(f"❌ 发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
