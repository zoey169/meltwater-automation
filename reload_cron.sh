#!/bin/bash

# 重新加载 Meltwater 定时任务配置

echo "停止旧任务..."
./stop_cron.sh

echo ""
echo "启动新任务..."
./start_cron.sh
