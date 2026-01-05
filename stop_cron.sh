#!/bin/bash

# 停止 Meltwater 定时任务

TARGET_PLIST="$HOME/Library/LaunchAgents/com.meltwater.sync.plist"

if [ ! -f "$TARGET_PLIST" ]; then
    echo "⚠️ 定时任务未安装"
    exit 0
fi

if launchctl unload "$TARGET_PLIST" 2>/dev/null; then
    echo "✅ 定时任务已停止"
else
    echo "⚠️ 定时任务可能未运行"
fi

# 删除 plist 文件
rm -f "$TARGET_PLIST"
echo "✅ 已删除配置文件"
