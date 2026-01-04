# GitHub Actions 快速启动指南

## ✅ 配置完成状态

您的 GitHub Actions 已经配置完成!

### 已完成的配置:
- ✅ GitHub Secrets 已设置
- ✅ 工作流配置已推送
- ✅ 定时任务已激活

### Secrets 列表:
- `FEISHU_APP_ID` ✓
- `FEISHU_APP_SECRET` ✓
- `BITABLE_APP_TOKEN` ✓
- `BITABLE_TABLE_ID` ✓
- `TARGET_CHAT_ID` ✓
- `NOTIFICATION_EMAIL` ✓

## 🚀 如何使用

### 方式一: 手动触发测试

1. 准备 CSV 文件并上传到可访问的 URL
   - 可以使用 Google Drive, Dropbox 等
   - 确保 URL 是直接下载链接

2. 在 GitHub 仓库页面手动触发:
   ```bash
   # 使用命令行
   gh workflow run meltwater-import.yml -f csv_url="https://your-csv-url.com/file.csv"

   # 或者在网页上操作
   # 访问: https://github.com/zoey169/meltwater-automation/actions
   # 选择 "Meltwater Data Import"
   # 点击 "Run workflow"
   # 输入 CSV URL
   ```

3. 查看运行结果:
   ```bash
   # 查看最近的运行
   gh run list --workflow=meltwater-import.yml

   # 查看具体运行详情
   gh run view <run-id>
   ```

### 方式二: 自动定时执行

工作流会在**每天早上 9:00 (北京时间)**自动运行。

**注意**:
- 当前定时运行需要 CSV URL,如果没有提供会失败
- 建议修改工作流配置,添加固定的 CSV 下载逻辑
- 或者使用手动触发 + 定期上传 CSV 的方式

## 📝 CSV 文件准备

### 方式 A: 使用 Google Drive

1. 上传 CSV 到 Google Drive
2. 右键点击文件 → 共享 → 获取链接 → 设为"知道链接的人都可以查看"
3. 获取文件 ID (在 URL 中)
4. 使用此格式: `https://drive.google.com/uc?export=download&id=FILE_ID`

### 方式 B: 使用 Dropbox

1. 上传 CSV 到 Dropbox
2. 获取分享链接
3. 将 URL 末尾的 `?dl=0` 改为 `?dl=1`

### 方式 C: 使用对象存储 (S3/OSS)

上传到云存储并设置公开访问,或使用临时访问 URL。

## 🔍 查看执行日志

### 网页查看:
访问: https://github.com/zoey169/meltwater-automation/actions

### 命令行查看:
```bash
# 列出最近的运行
gh run list --workflow=meltwater-import.yml --limit 5

# 查看运行日志
gh run view <run-id> --log

# 下载日志文件
gh run download <run-id>
```

## ⏰ 修改定时时间

如需修改定时执行时间,编辑 `.github/workflows/meltwater-import.yml`:

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 1:00 = 北京时间 9:00
```

Cron 格式: `分钟 小时 日 月 星期`

示例:
- `0 1 * * *` - 每天 UTC 1:00 (北京时间 9:00)
- `0 1 * * 1` - 每周一 UTC 1:00
- `0 1,13 * * *` - 每天 UTC 1:00 和 13:00 (北京时间 9:00 和 21:00)

## 📊 通知确认

执行成功后,你会收到:
1. 飞书群消息卡片 (群 ID: oc_8a3dc5b72d6ed10d57582b925d138223)
2. 邮件通知 (zoey.yuan@anker.com)

## ❓ 常见问题

### Q: 定时任务不运行?
A: 检查:
1. 工作流是否启用 (Actions 页面)
2. 是否提供了 CSV URL
3. 仓库是否有 GitHub Actions 权限

### Q: CSV 下载失败?
A: 确认:
1. URL 是直接下载链接,不是预览页面
2. URL 可以公开访问
3. 文件格式正确 (Tab 分隔, UTF-16 编码)

### Q: 如何暂停定时任务?
A: 两种方式:
1. 在 Actions 页面禁用工作流
2. 删除工作流文件中的 `schedule` 配置

## 🎉 下一步

1. 准备第一个 CSV 文件
2. 手动触发测试运行
3. 检查飞书通知
4. 设置 CSV 自动上传流程
5. 验证定时任务运行

## 🔗 相关文档

- [完整 README](README.md)
- [CSV 上传指南](CSV_UPLOAD_GUIDE.md)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
