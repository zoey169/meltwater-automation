#!/usr/bin/env python3
"""
测试新的导出策略 - 先触发导出,然后等待并下载
"""
import os
import sys
import subprocess
import time

# 设置环境变量
os.environ['MELTWATER_EMAIL'] = 'tove.berkhout@anker.com'
os.environ['MELTWATER_PASSWORD'] = 'P3$NwcskGq6!!s3'
os.environ['MELTWATER_URL'] = 'https://app.meltwater.com'
os.environ['DOWNLOAD_PATH'] = './downloads'

print("=" * 80)
print("测试新的导出策略")
print("=" * 80)

# 运行下载脚本,限制最多运行6分钟
start_time = time.time()
max_runtime = 360  # 6分钟

try:
    process = subprocess.Popen(
        [sys.executable, 'meltwater_downloader.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # 实时输出并检查超时
    for line in process.stdout:
        print(line, end='')

        # 检查是否超时
        elapsed = time.time() - start_time
        if elapsed > max_runtime:
            print(f"\n⚠️ 超过最大运行时间 ({max_runtime}秒),终止进程...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            break

    process.wait()
    exit_code = process.returncode

    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ 测试成功!")
    else:
        print(f"❌ 测试失败,退出码: {exit_code}")
    print("=" * 80)

except KeyboardInterrupt:
    print("\n⚠️ 用户中断测试")
    process.terminate()
except Exception as e:
    print(f"\n❌ 测试出错: {e}")
