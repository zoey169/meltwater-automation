#!/usr/bin/env python3
"""
Complete workflow test - Download from Meltwater with session + Import to Bitable
使用会话复用模式
"""

import os
import sys
import logging
import subprocess
import re
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_download():
    """Step 1: 从 Meltwater 下载数据 (使用会话模式)"""
    logger.info("=" * 60)
    logger.info("Step 1: 从 Meltwater 下载数据 (会话复用模式)")
    logger.info("=" * 60)

    # 从环境变量读取配置
    env = os.environ.copy()
    env['MELTWATER_URL'] = os.getenv('MELTWATER_URL', 'https://app.meltwater.com')
    env['DOWNLOAD_PATH'] = os.getenv('DOWNLOAD_PATH', './downloads')
    env['USER_DATA_DIR'] = os.getenv('USER_DATA_DIR', './browser_data')

    # 运行下载脚本
    start_time = time.time()
    try:
        result = subprocess.run(
            ['python3', 'meltwater_downloader_with_session.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )

        duration = int(time.time() - start_time)

        logger.info("下载脚本输出:")
        logger.info(result.stdout)

        if result.returncode != 0:
            logger.error(f"下载失败! 错误输出:")
            logger.error(result.stderr)
            return None, None, None

        # 从输出中提取文件路径和记录数
        csv_file = None
        records = None

        for line in result.stdout.split('\n'):
            if line.startswith('SUCCESS:'):
                csv_file = line.split('SUCCESS:')[1].strip()
                logger.info(f"✅ 下载成功: {csv_file}")
            # 尝试从输出中提取记录数
            if 'CSV 总记录数:' in line or '总记录数:' in line:
                match = re.search(r'(\d+)', line)
                if match:
                    records = match.group(1)

        if not csv_file:
            logger.error("未找到下载成功标记")
            return None, None, None

        # 如果没有从输出提取到记录数,尝试读取文件统计
        if not records:
            try:
                import csv as csv_module
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv_module.reader(f)
                    records = str(sum(1 for row in reader) - 1)  # 减去表头
            except:
                records = "N/A"

        return csv_file, records, duration

    except subprocess.TimeoutExpired:
        logger.error("下载超时 (300秒)")
        return None, None, None
    except Exception as e:
        logger.error(f"下载出错: {str(e)}")
        return None, None, None

def run_import(csv_file):
    """Step 2: 导入数据到飞书 Bitable"""
    logger.info("=" * 60)
    logger.info("Step 2: 导入数据到飞书 Bitable")
    logger.info("=" * 60)

    if not csv_file or not os.path.exists(csv_file):
        logger.error(f"CSV 文件不存在: {csv_file}")
        return None

    # 从环境变量读取配置
    env = os.environ.copy()
    env['CSV_FILE_PATH'] = csv_file
    env['FEISHU_APP_ID'] = os.getenv('FEISHU_APP_ID')
    env['FEISHU_APP_SECRET'] = os.getenv('FEISHU_APP_SECRET')
    env['BITABLE_APP_TOKEN'] = os.getenv('BITABLE_APP_TOKEN')
    env['BITABLE_TABLE_ID'] = os.getenv('BITABLE_TABLE_ID')

    # 检查必需的环境变量
    required_vars = ['FEISHU_APP_ID', 'FEISHU_APP_SECRET', 'BITABLE_APP_TOKEN', 'BITABLE_TABLE_ID']
    missing = [var for var in required_vars if not env.get(var)]
    if missing:
        logger.error(f"缺少必需的环境变量: {', '.join(missing)}")
        return None

    # 运行导入脚本
    start_time = time.time()
    try:
        result = subprocess.run(
            ['python3', 'meltwater_auto_import.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )

        duration = int(time.time() - start_time)

        logger.info("导入脚本输出:")
        logger.info(result.stdout)

        if result.returncode != 0:
            logger.error(f"导入失败! 错误输出:")
            logger.error(result.stderr)
            return None

        # 从输出中提取统计信息
        stats = {
            'success': 0,
            'failed': 0,
            'total': 0,
            'success_rate': '0',
            'duration': duration,
            'duplicates': 0
        }

        for line in result.stdout.split('\n'):
            # 成功条数: "成功: 214 条"
            if match := re.search(r'成功[:\s]+(\d+)\s*条', line):
                stats['success'] = int(match.group(1))
            # 失败条数: "失败: 0 条"
            elif match := re.search(r'失败[:\s]+(\d+)\s*条', line):
                stats['failed'] = int(match.group(1))
            # 总计条数: "总计: 214 条"
            elif match := re.search(r'总计[:\s]+(\d+)\s*条', line):
                stats['total'] = int(match.group(1))
            # 成功率: "成功率: 100.0%"
            elif match := re.search(r'成功率[:\s]+([\d.]+)%', line):
                stats['success_rate'] = match.group(1)
            # 重复记录: "重复记录数: 0"
            elif match := re.search(r'重复记录数[:\s]+(\d+)', line):
                stats['duplicates'] = int(match.group(1))

        # 判断是否成功(即使没有SUCCESS标记,也可以根据成功率判断)
        if 'SUCCESS' in result.stdout or (stats['total'] > 0 and stats['success'] == stats['total']):
            logger.info("✅ 导入成功!")
            return stats
        else:
            logger.error("导入脚本未返回成功标记")
            return stats  # 仍然返回统计数据,便于通知

    except subprocess.TimeoutExpired:
        logger.error("导入超时 (300秒)")
        return None
    except Exception as e:
        logger.error(f"导入出错: {str(e)}")
        return None

def run_notification(csv_file, download_records, download_duration, import_stats):
    """Step 3: 发送飞书卡片消息通知"""
    logger.info("=" * 60)
    logger.info("Step 3: 发送飞书卡片消息通知")
    logger.info("=" * 60)

    # 准备环境变量
    env = os.environ.copy()
    env['WORKFLOW_STATUS'] = 'success' if import_stats else 'failure'
    env['DOWNLOAD_RECORDS'] = str(download_records)
    env['DOWNLOAD_DURATION'] = str(download_duration)
    env['DOWNLOAD_FILE'] = csv_file

    if import_stats:
        env['IMPORT_SUCCESS'] = str(import_stats['success'])
        env['IMPORT_FAILED'] = str(import_stats['failed'])
        env['IMPORT_TOTAL'] = str(import_stats['total'])
        env['IMPORT_SUCCESS_RATE'] = str(import_stats['success_rate'])
        env['IMPORT_DURATION'] = str(import_stats['duration'])
        env['IMPORT_DUPLICATES'] = str(import_stats['duplicates'])
    else:
        # 导入失败时的默认值
        env['IMPORT_SUCCESS'] = '0'
        env['IMPORT_FAILED'] = '0'
        env['IMPORT_TOTAL'] = '0'
        env['IMPORT_SUCCESS_RATE'] = '0'
        env['IMPORT_DURATION'] = 'N/A'
        env['IMPORT_DUPLICATES'] = '0'

    # 如果环境变量中没有设置接收者,使用默认值
    # 优先使用 FEISHU_RECIPIENTS (支持多个接收者)
    # 其次使用 FEISHU_CHAT_ID (兼容旧版本)
    if 'FEISHU_RECIPIENTS' not in env and 'FEISHU_CHAT_ID' in env:
        # 兼容旧版本:将 FEISHU_CHAT_ID 转换为 FEISHU_RECIPIENTS 格式
        env['FEISHU_RECIPIENTS'] = f"chat_id:{env['FEISHU_CHAT_ID']}"

    # 运行通知脚本
    try:
        result = subprocess.run(
            ['python3', 'send_feishu_notification.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )

        logger.info("通知脚本输出:")
        logger.info(result.stdout)

        if result.returncode == 0 and 'SUCCESS' in result.stdout:
            logger.info("✅ 通知发送成功!")
            return True
        else:
            logger.warning("⚠️ 通知发送失败,但不影响工作流")
            if result.stderr:
                logger.warning(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        logger.warning("⚠️ 通知发送超时 (60秒),但不影响工作流")
        return False
    except Exception as e:
        logger.warning(f"⚠️ 通知发送出错: {str(e)},但不影响工作流")
        return False

def main():
    logger.info("=" * 60)
    logger.info("完整工作流测试开始 (会话复用模式)")
    logger.info("=" * 60)

    # Step 1: 下载
    csv_file, download_records, download_duration = run_download()
    if not csv_file:
        logger.error("❌ 工作流失败: 下载步骤失败")
        return 1

    # Step 2: 导入
    import_stats = run_import(csv_file)
    if not import_stats:
        logger.error("❌ 工作流失败: 导入步骤失败")

        # 即使导入失败,也尝试发送通知
        run_notification(csv_file, download_records, download_duration, None)
        return 1

    # Step 3: 发送通知
    run_notification(csv_file, download_records, download_duration, import_stats)

    logger.info("=" * 60)
    logger.info("✅ 完整工作流测试成功!")
    logger.info("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
