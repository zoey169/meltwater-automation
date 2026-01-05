#!/bin/bash

# Meltwater 数据同步定时任务执行脚本
# 此脚本会依次执行:下载、导入、通知

set -e  # 遇到错误立即退出

# 切换到项目目录
cd /Users/admin/Desktop/meltwater-automation

# 记录开始时间
echo "=========================================="
echo "Meltwater 数据同步开始: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 设置环境变量
export MELTWATER_EMAIL="tove.berkhout@anker.com"
export MELTWATER_PASSWORD='P3$NwcskGq6!!s3'
export MELTWATER_URL="https://app.meltwater.com"
export DOWNLOAD_PATH="./downloads"

export FEISHU_APP_ID="cli_a702c225665e100d"
export FEISHU_APP_SECRET="5D7PoQaMtb8Er1qqfUnGpfcYiFekaX2b"
export BITABLE_APP_TOKEN="ExoBbLPZoajFihsvegNcDvUsnce"
export BITABLE_TABLE_ID="tblqmDCzRUdDMI3x"

# 步骤1: 下载数据
echo ""
echo "步骤1: 从 Meltwater 下载数据..."
python3 meltwater_downloader.py 2>&1 | tee download_log.txt

# 提取下载的文件路径
CSV_FILE=$(grep "SUCCESS:" download_log.txt | tail -1 | cut -d':' -f2)

if [ -z "$CSV_FILE" ]; then
    echo "❌ 下载失败 - 未找到CSV文件"
    exit 1
fi

echo "✅ 已下载: $CSV_FILE"

# 步骤2: 导入到飞书多维表格
echo ""
echo "步骤2: 导入数据到飞书多维表格..."
export CSV_FILE_PATH="$CSV_FILE"
python3 meltwater_auto_import.py 2>&1 | tee import_log.txt

# 提取导入统计 (兼容 macOS grep)
IMPORT_SUCCESS=$(grep '成功:' import_log.txt | tail -1 | sed 's/.*成功:[[:space:]]*\([0-9]*\).*/\1/')
IMPORT_FAILED=$(grep '失败:' import_log.txt | tail -1 | sed 's/.*失败:[[:space:]]*\([0-9]*\).*/\1/')
IMPORT_TOTAL=$(grep '总计:' import_log.txt | tail -1 | sed 's/.*总计:[[:space:]]*\([0-9]*\).*/\1/')

# 确保变量不为空
IMPORT_SUCCESS=${IMPORT_SUCCESS:-0}
IMPORT_FAILED=${IMPORT_FAILED:-0}
IMPORT_TOTAL=${IMPORT_TOTAL:-0}

echo "✅ 导入完成: $IMPORT_SUCCESS/$IMPORT_TOTAL 条成功"

# 步骤3: 发送飞书通知
echo ""
echo "步骤3: 发送飞书通知..."
export WORKFLOW_STATUS="success"
export DOWNLOAD_FILE="$CSV_FILE"
export IMPORT_SUCCESS="$IMPORT_SUCCESS"
export IMPORT_FAILED="$IMPORT_FAILED"
export IMPORT_TOTAL="$IMPORT_TOTAL"
export FEISHU_RECIPIENTS="email:zoey.yuan@anker.com,chat_id:oc_8a3dc5b72d6ed10d57582b925d138223"

python3 send_feishu_notification.py 2>&1 | tee notification_log.txt || echo "⚠️ 通知发送失败,但继续执行"

# 记录结束时间
echo ""
echo "=========================================="
echo "Meltwater 数据同步完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
