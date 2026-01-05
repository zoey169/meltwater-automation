#!/bin/bash

# 启动 Meltwater 定时任务

PLIST_FILE="$HOME/Desktop/meltwater-automation/com.meltwater.sync.plist"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$LAUNCHD_DIR/com.meltwater.sync.plist"

# 创建 LaunchAgents 目录(如果不存在)
mkdir -p "$LAUNCHD_DIR"

# 复制 plist 文件
cp "$PLIST_FILE" "$TARGET_PLIST"

# 验证 plist 文件格式
if ! plutil -lint "$TARGET_PLIST" > /dev/null 2>&1; then
    echo "❌ plist 文件格式错误,请检查"
    exit 1
fi

echo "✅ plist 文件格式正确"

# 卸载旧任务(如果存在)
launchctl unload "$TARGET_PLIST" 2>/dev/null

# 加载新任务
if launchctl load "$TARGET_PLIST"; then
    echo "✅ 定时任务已启动"
    echo ""
    echo "任务配置:"
    echo "  - 运行频率: 每天早上10点"
    echo "  - 日志文件: cron_output.log"
    echo "  - 错误日志: cron_error.log"
    echo ""
    echo "查看任务状态:"
    echo "  launchctl list | grep com.meltwater.sync"
else
    echo "❌ 定时任务启动失败"
    exit 1
fi
