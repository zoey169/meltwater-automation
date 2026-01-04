# Meltwater 数据自动导入系统

自动从 Meltwater CSV 文件导入数据到飞书多维表格,具备智能重复检测、定时运行和多渠道通知功能。

## ✨ 核心功能

- ✅ **CSV 数据导入** - 支持 Tab 分隔、UTF-16 编码的 Meltwater 导出文件
- ✅ **智能重复检测** - 基于 Document ID 自动识别并跳过重复记录
- ✅ **批量写入优化** - 每批 15 条记录,避免 API 限制
- ✅ **飞书群消息通知** - 导入完成后发送详细统计卡片到指定群聊
- ✅ **邮件通知** - 同时发送通知到指定邮箱
- ✅ **定时任务调度** - 前 5 次每日运行,之后自动切换为每周运行
- ✅ **日期范围追踪** - 自动统计数据的时间范围

## 📋 系统要求

### 本地运行
- Python 3.7+
- macOS/Linux/Windows

### GitHub Actions 云端运行 (推荐)
- GitHub 账号
- 配置 GitHub Secrets
- CSV 文件上传到可访问的 URL

### 飞书权限
- 飞书开放平台应用权限:
  - `bitable:app` - 多维表格读写
  - `im:message` - 发送消息

## 🚀 快速开始

### 方式一: GitHub Actions 云端运行 (推荐)

#### 1. Fork 或 Clone 本仓库到你的 GitHub 账号

#### 2. 配置 GitHub Secrets

运行配置脚本(需要先安装 [GitHub CLI](https://cli.github.com/)):

```bash
./setup_github_secrets.sh
```

或者手动在 GitHub 仓库设置中添加以下 Secrets:
- `FEISHU_APP_ID` - 飞书应用 ID
- `FEISHU_APP_SECRET` - 飞书应用密钥
- `BITABLE_APP_TOKEN` - 多维表格 App Token
- `BITABLE_TABLE_ID` - 多维表格 Table ID
- `TARGET_CHAT_ID` - 飞书群聊 ID
- `NOTIFICATION_EMAIL` - 通知邮箱

#### 3. 准备 CSV 文件

将 CSV 文件上传到可访问的 URL,详见 [CSV_UPLOAD_GUIDE.md](CSV_UPLOAD_GUIDE.md)

#### 4. 手动触发工作流

在 GitHub 仓库页面:
1. 点击 **Actions** 标签
2. 选择 **Meltwater Data Import** 工作流
3. 点击 **Run workflow**
4. 输入 CSV 文件的 URL
5. 点击 **Run workflow** 开始执行

#### 5. 自动定时执行

工作流会在每天早上 9:00 (北京时间) 自动运行。

**注意**: 自动运行需要提供固定的 CSV URL 或修改工作流配置。

---

### 方式二: 本地运行

#### 1. 克隆仓库

```bash
git clone https://github.com/zoey169/meltwater-automation.git
cd meltwater-automation
```

#### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件,填写以下信息:

```env
# 飞书应用配置
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

# 多维表格配置
BITABLE_APP_TOKEN=your_app_token
BITABLE_TABLE_ID=your_table_id

# 通知配置
TARGET_CHAT_ID=your_chat_id
NOTIFICATION_EMAIL=your.email@example.com

# CSV 文件路径
CSV_FILE_PATH=/path/to/meltwater/export.csv
```

#### 如何获取配置参数?

- **飞书应用凭证**: 在 [飞书开放平台](https://open.feishu.cn/) 创建应用后获取
- **多维表格 Token**: 从表格 URL 获取,格式为 `https://xxx.feishu.cn/base/{APP_TOKEN}?table={TABLE_ID}`
- **群聊 ID**: 在飞书群聊中,点击群设置 → 群机器人 → 添加机器人后获取

#### 4. 手动测试运行

```bash
python3 meltwater_auto_import.py
```

成功运行后会:
- 从 CSV 读取数据
- 检测并跳过重复记录
- 批量写入新记录到飞书表格
- 发送通知到群聊和邮箱

---

## ⚙️ 设置本地定时任务 (macOS)

**注意**: 如果已使用 GitHub Actions,无需配置本地定时任务。

### 创建 LaunchAgent 配置

创建文件 `~/Library/LaunchAgents/com.meltwater.import.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.meltwater.import</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/meltwater-automation/meltwater_auto_import.py</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/path/to/meltwater_import.log</string>

    <key>StandardErrorPath</key>
    <string>/path/to/meltwater_import_error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

**注意**: 请替换以下路径:
- Python 解释器路径 (使用 `which python3` 查看)
- 脚本路径 (替换为实际的项目路径)
- 日志文件路径

### 加载定时任务

```bash
# 加载任务
launchctl load ~/Library/LaunchAgents/com.meltwater.import.plist

# 查看状态
launchctl list | grep meltwater

# 卸载任务
launchctl unload ~/Library/LaunchAgents/com.meltwater.import.plist
```

## 📊 数据字段映射

| CSV 字段 | 飞书表格字段 | 类型 | 说明 |
|----------|-------------|------|------|
| Title | Title/Coverage | 文本 | 标题 |
| Document ID | Document ID | 文本 | 唯一标识 |
| Reach | Reach | 数字 | 触达数 |
| AVE | AVE | 数字 | 广告等值 |
| Source Name | Source Name | 文本 | 来源名称 |
| Author Name | Author Name | 文本 | 作者(可选) |
| Date | Date | 日期 | 毫秒时间戳 |
| URL | URL/Link | 超链接 | 链接(可选) |

## 🔄 调度模式

系统支持自动调度频率切换:

### 初始模式 (前 5 次)
- **频率**: 每天早上 9:00
- **目的**: 快速验证系统稳定性

### 自动切换 (第 6 次起)
- **频率**: 每周一早上 9:00
- **触发**: 运行 5 次后自动切换

### 管理调度状态

```bash
# 查看当前状态
python3 manage_meltwater_schedule.py status

# 重置运行计数(重新开始每日模式)
python3 manage_meltwater_schedule.py reset

# 手动增加运行次数
python3 manage_meltwater_schedule.py increment
```

## 📈 通知示例

导入完成后会发送包含以下信息的消息卡片:

- 📅 导入时间
- 📊 数据时间范围
- 📝 CSV 总记录数
- 🔄 重复记录数
- ✨ 新增记录数
- ✅ 成功导入数
- ❌ 失败记录数
- ⏱️ 总耗时

## 🔧 工作流程

1. **获取现有数据** - 从飞书表格读取所有 Document ID (分页处理)
2. **读取 CSV** - 解析 Tab 分隔的 UTF-16 编码文件
3. **重复检测** - 对比 CSV 与现有记录,跳过重复
4. **批量写入** - 分批写入新记录 (15 条/批,间隔 1 秒)
5. **发送通知** - 发送消息卡片到群聊和邮箱
6. **更新状态** - 记录运行次数,自动调整调度模式

## 📝 注意事项

### CSV 文件要求
- 格式: Tab 分隔
- 编码: UTF-16
- 必须包含 Document ID 列用于去重

### API 限制
- 每批最多 15 条记录
- 批次间延迟 1 秒避免限流

### 重复检测
- 基于 Document ID 精确匹配
- 已存在记录不会重复导入

### 时区设置
- 使用系统本地时区
- launchd 会自动处理时区转换

## 🔍 故障排查

### 导入失败

1. **检查环境变量**
   ```bash
   cat .env
   ```

2. **验证飞书应用权限**
   - 确认应用已添加到目标群聊
   - 检查应用是否有多维表格读写权限

3. **查看错误日志**
   ```bash
   tail -f meltwater_import_error.log
   ```

### 定时任务未运行

1. **检查任务状态**
   ```bash
   launchctl list | grep meltwater
   ```

2. **验证 Python 路径**
   ```bash
   which python3
   ```

3. **手动测试**
   ```bash
   python3 meltwater_auto_import.py
   ```

### 通知发送失败

- **群消息**: 确认机器人已添加到目标群聊
- **邮件通知**: 检查邮箱地址格式是否正确

## 📁 项目结构

```
meltwater-automation/
├── .github/
│   └── workflows/
│       └── meltwater-import.yml    # GitHub Actions 工作流配置
├── meltwater_auto_import.py        # 主导入脚本
├── manage_meltwater_schedule.py    # 调度管理脚本(本地使用)
├── setup_github_secrets.sh         # GitHub Secrets 配置脚本
├── requirements.txt                # Python 依赖
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略规则
├── CSV_UPLOAD_GUIDE.md            # CSV 文件上传指南
├── com.meltwater.import.plist.example  # macOS 定时任务示例
└── README.md                       # 本文档
```

## 🔐 安全说明

- 所有敏感信息通过环境变量或 GitHub Secrets 配置
- `.env` 文件已加入 `.gitignore`,不会提交到版本库
- GitHub Secrets 加密存储,不会在日志中显示
- 建议定期更换飞书应用凭证
- CSV 文件不会提交到仓库(已加入 `.gitignore`)

## 📅 更新日志

### 2026-01-04

#### v1.1 - GitHub Actions 支持
- ✨ 添加 GitHub Actions 云端定时执行
- ✅ 支持手动触发和定时触发
- ✅ GitHub Secrets 自动配置脚本
- ✅ CSV 文件 URL 下载支持
- 📝 完善文档和使用指南

#### v1.0 - 初始版本
- ✨ 实现 CSV 自动导入功能
- ✅ 添加智能重复检测
- ✅ 实现定时任务调度
- ✅ 支持自动频率切换
- ✅ 添加飞书群消息通知
- ✅ 添加邮件通知功能

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request!

## 📧 联系方式

如有问题或建议,请通过 GitHub Issues 联系。
