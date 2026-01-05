# Meltwater 自动同步 - 本地定时任务配置

## 配置说明

### 1. 测试阶段 (当前配置)
- **运行频率**: 每天早上10点
- **配置文件**: `com.meltwater.sync.plist`

### 2. 正式阶段 (需要切换时)
- **运行频率**: 每周一早上10点
- **操作步骤**:
  1. 编辑 `com.meltwater.sync.plist`
  2. 注释掉测试阶段的 `StartCalendarInterval` 块
  3. 取消注释正式阶段的 `StartCalendarInterval` 块
  4. 重新加载配置: `./reload_cron.sh`

## 管理命令

### 启动定时任务
```bash
cd /Users/admin/Desktop/meltwater-automation
./start_cron.sh
```

### 停止定时任务
```bash
cd /Users/admin/Desktop/meltwater-automation
./stop_cron.sh
```

### 重新加载配置
```bash
cd /Users/admin/Desktop/meltwater-automation
./reload_cron.sh
```

### 查看任务状态
```bash
launchctl list | grep com.meltwater.sync
```

### 手动测试运行
```bash
cd /Users/admin/Desktop/meltwater-automation
./run_meltwater_sync.sh
```

## 日志文件

- **执行日志**: `cron_output.log`
- **错误日志**: `cron_error.log`
- **下载日志**: `download_log.txt`
- **导入日志**: `import_log.txt`
- **通知日志**: `notification_log.txt`

## 数据流程

1. **下载**: `meltwater_downloader.py` → 从 Meltwater 下载 CSV 文件
2. **导入**: `meltwater_auto_import.py` → 导入到飞书多维表格
3. **通知**: `send_feishu_notification.py` → 发送飞书通知

## 环境变量

所有敏感信息都在 `run_meltwater_sync.sh` 中配置,包括:
- Meltwater 登录凭证
- 飞书应用凭证
- 多维表格信息

## 注意事项

1. macOS 必须授予 Terminal/iTerm 完全磁盘访问权限
2. 确保 Python 3 和 Playwright 已安装
3. 首次运行前需要手动测试一次: `./run_meltwater_sync.sh`
4. 切换到正式阶段后记得修改 plist 文件并重新加载
