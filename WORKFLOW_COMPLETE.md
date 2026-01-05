# Meltwater 完整自动化工作流程

## 📋 流程概述

完整的自动化流程包含以下步骤:

1. **登录 Meltwater** → 自动登录到 Meltwater 平台
2. **下载数据** → 从 ANZ Coverage 2025 下载 CSV 数据文件
3. **数据去重** → 基于 Document ID 进行去重处理
4. **导入多维表格** → 将新数据批量导入飞书多维表格
5. **发送飞书通知** → 通知相关人员数据同步完成

## ✅ 已验证的完整流程

### 最近一次成功运行 (2026-01-04)

**运行1** - 测试流程 (18:33-18:35)
- 下载: 18 条记录 (部分数据)
- 导入: 18/18 成功 (100%)
- 通知: 2/2 发送成功

**运行2** - 完整数据导入 (18:36)
- 使用完整文件: `meltwater_export_20260104_173903.csv`
- CSV 总记录: 214 条
- 去重: 12 条重复
- 新增导入: **202 条** ✅
- 导入成功率: 100% (202/202)
- 通知: 2/2 发送成功 ✅

**当前数据状态:**
- 多维表格总记录数: **220 条** (18 + 202)
- 目标表格: `ExoBbLPZoajFihsvegNcDvUsnce/tblqmDCzRUdDMI3x`

## 🚀 如何运行完整流程

### 方式1: 使用主脚本 (推荐)

```bash
cd /Users/admin/Desktop/meltwater-automation
./run_meltwater_sync.sh
```

该脚本会自动执行:
1. 从 Meltwater 下载数据
2. 导入到飞书多维表格 (自动去重)
3. 发送飞书通知

### 方式2: 手动分步执行

#### 步骤1: 下载数据
```bash
export MELTWATER_EMAIL="tove.berkhout@anker.com"
export MELTWATER_PASSWORD='P3$NwcskGq6!!s3'
python3 meltwater_downloader.py
```

#### 步骤2: 导入数据
```bash
export CSV_FILE_PATH="./downloads/meltwater_export_XXXXXX.csv"
export FEISHU_APP_ID="cli_a702c225665e100d"
export FEISHU_APP_SECRET="5D7PoQaMtb8Er1qqfUnGpfcYiFekaX2b"
export BITABLE_APP_TOKEN="ExoBbLPZoajFihsvegNcDvUsnce"
export BITABLE_TABLE_ID="tblqmDCzRUdDMI3x"
python3 meltwater_auto_import.py
```

#### 步骤3: 发送通知
```bash
export WORKFLOW_STATUS="success"
export DOWNLOAD_FILE="./downloads/meltwater_export_XXXXXX.csv"
export IMPORT_SUCCESS="202"
export IMPORT_TOTAL="202"
export FEISHU_RECIPIENTS="email:zoey.yuan@anker.com,chat_id:oc_8a3dc5b72d6ed10d57582b925d138223"
python3 send_feishu_notification.py
```

## 📅 定时任务配置

### 当前配置
- **工具**: launchd (macOS)
- **频率**: 每天早上 10:00 (测试阶段)
- **配置文件**: `com.meltwater.sync.plist`

### 管理命令

**启动定时任务:**
```bash
./start_cron.sh
```

**停止定时任务:**
```bash
./stop_cron.sh
```

**重新加载配置:**
```bash
./reload_cron.sh
```

**查看运行状态:**
```bash
launchctl list | grep com.meltwater.sync
```

### 切换到正式运行 (每周一)

编辑 `com.meltwater.sync.plist`:
1. 注释掉当前的 `StartCalendarInterval` (每天)
2. 取消注释正式的 `StartCalendarInterval` (每周一)
3. 运行: `./reload_cron.sh`

## 📊 核心脚本说明

### 1. `meltwater_downloader.py`
**功能**: 自动登录 Meltwater 并下载数据

**工作流程**:
1. 启动浏览器 (headless 模式)
2. 访问 Meltwater 登录页面
3. 输入邮箱 → 点击 Next
4. 输入密码 → 点击登录
5. 跳过 passkey 设置
6. 等待进入 Home 页面
7. 在 Alerts 区域查找 "ANZ_Coverage_2025"
8. 点击下载按钮
9. 等待文件下载完成
10. 返回文件路径

**输出**: `./downloads/meltwater_export_YYYYMMDD_HHMMSS.csv`

**⚠️ 当前限制**:
- 只下载 Meltwater 已准备好的 "ANZ_Coverage_2025" 文件
- 不会主动创建新的导出任务
- `days_back` 参数暂未使用

### 2. `meltwater_auto_import.py`
**功能**: 导入 CSV 到飞书多维表格,自动去重

**工作流程**:
1. 获取飞书 access_token
2. 读取现有表格中的所有 Document ID
3. 读取 CSV 文件 (自动检测编码)
4. 基于 Document ID 进行去重
5. 将新记录分批导入 (每批15条)
6. 输出导入统计

**去重逻辑**:
- 比对字段: `Document ID`
- 只导入表格中不存在的记录

**批量导入**:
- 批次大小: 15 条/批
- 自动处理重试

### 3. `send_feishu_notification.py`
**功能**: 发送飞书卡片通知

**通知内容**:
- 工作流状态 (成功/失败)
- 下载文件名
- 导入统计 (成功/失败/总计)
- 执行时间

**接收者**:
- 个人: zoey.yuan@anker.com
- 群组: oc_8a3dc5b72d6ed10d57582b925d138223

## 📁 项目结构

```
meltwater-automation/
├── run_meltwater_sync.sh          # 主执行脚本
├── meltwater_downloader.py        # 下载脚本
├── meltwater_auto_import.py       # 导入脚本
├── send_feishu_notification.py    # 通知脚本
├── com.meltwater.sync.plist       # launchd 配置
├── downloads/                     # 下载文件目录
├── download_log.txt              # 下载日志
├── import_log.txt                # 导入日志
├── notification_log.txt          # 通知日志
└── README.md                     # 项目文档
```

## 🔍 日志文件

### 查看最近的运行日志

**下载日志:**
```bash
cat download_log.txt
```

**导入日志:**
```bash
cat import_log.txt
```

**通知日志:**
```bash
cat notification_log.txt
```

**定时任务日志:**
```bash
cat cron_output.log  # 标准输出
cat cron_error.log   # 错误输出
```

## ⚙️ 环境变量配置

所有敏感信息都在 `run_meltwater_sync.sh` 中配置:

### Meltwater 凭证
- `MELTWATER_EMAIL`: tove.berkhout@anker.com
- `MELTWATER_PASSWORD`: (已配置)
- `MELTWATER_URL`: https://app.meltwater.com

### 飞书应用凭证
- `FEISHU_APP_ID`: cli_a702c225665e100d
- `FEISHU_APP_SECRET`: (已配置)

### 多维表格信息
- `BITABLE_APP_TOKEN`: ExoBbLPZoajFihsvegNcDvUsnce
- `BITABLE_TABLE_ID`: tblqmDCzRUdDMI3x

## ✨ 成功标准

一个完整的成功流程应该:
1. ✅ 登录 Meltwater 成功
2. ✅ 下载 CSV 文件 (文件大小 > 0)
3. ✅ 读取 CSV 成功 (正确的编码)
4. ✅ 去重检查完成
5. ✅ 数据导入成功 (成功率 = 100%)
6. ✅ 飞书通知发送成功 (2/2)

## 🎯 数据质量保证

### 去重机制
- **去重字段**: Document ID (唯一标识符)
- **去重时机**: 导入前
- **去重方式**: 查询现有表格中所有 Document ID,只导入新记录

### 数据完整性
- CSV 编码自动检测 (utf-8, utf-16, latin-1)
- 批量导入失败自动重试
- 导入统计详细记录

### 错误处理
- 下载失败 → 流程终止,发送失败通知
- 导入失败 → 记录失败数量,继续执行
- 通知失败 → 记录日志,不影响数据导入

## 📈 性能指标

### 最近执行时间
- **完整流程**: ~70 秒
  - 下载: ~60 秒
  - 导入(202条): ~6 秒
  - 通知: ~2 秒

### 吞吐量
- 批量导入速度: ~30 条/秒
- 单批处理: 15 条
- 批次间隔: 0.5 秒

## 🔧 故障排查

### 问题1: 下载失败
**症状**: 未找到 CSV 文件或文件为空

**可能原因**:
- Meltwater 登录失败
- Passkey 弹窗未跳过
- ANZ_Coverage_2025 文件未准备好

**解决方案**:
1. 检查登录凭证
2. 查看 `downloads/debug_*.png` 截图
3. 手动登录 Meltwater 检查文件状态

### 问题2: 导入失败
**症状**: 导入成功率 < 100%

**可能原因**:
- 网络问题
- 飞书 API 限流
- 数据格式错误

**解决方案**:
1. 查看 `import_log.txt` 错误详情
2. 重试导入
3. 检查多维表格字段配置

### 问题3: 通知失败
**症状**: 未收到飞书通知

**可能原因**:
- 飞书 token 过期
- 接收者 ID 错误
- 网络问题

**解决方案**:
1. 查看 `notification_log.txt`
2. 验证 FEISHU_APP_ID 和 SECRET
3. 确认接收者 ID 正确

## 📝 维护建议

### 每周检查
- [ ] 查看定时任务执行日志
- [ ] 确认数据导入成功率
- [ ] 验证飞书通知送达

### 每月检查
- [ ] 清理旧的 CSV 文件 (downloads/)
- [ ] 归档日志文件
- [ ] 检查磁盘空间

### 配置更新
如需修改配置:
1. 编辑 `run_meltwater_sync.sh`
2. 测试运行: `./run_meltwater_sync.sh`
3. 确认成功后更新定时任务

## 🎉 项目状态

- ✅ **登录 Meltwater** - 已实现并验证
- ✅ **下载 CSV** - 已实现并验证
- ✅ **数据去重** - 已实现并验证
- ✅ **导入多维表格** - 已实现并验证
- ✅ **发送飞书通知** - 已实现并验证
- ✅ **定时任务** - 已配置 (测试阶段)
- ✅ **完整流程闭环** - 已验证成功 ✨

---

**最后验证时间**: 2026-01-04 18:36
**验证结果**: ✅ 所有流程正常运行
**当前数据**: 220 条记录
