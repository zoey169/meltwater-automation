# Meltwater 自动化配置指南

## ✅ 已完成

- ✅ Meltwater 自动下载脚本 (`meltwater_downloader.py`)
- ✅ GitHub Actions 工作流更新
- ✅ Playwright 浏览器自动化集成

## 🔐 配置 Meltwater Secrets

需要在 GitHub 仓库中添加以下 3 个 Secrets:

### 方式一: 使用命令行 (推荐)

```bash
# 1. 设置 Meltwater 邮箱
gh secret set MELTWATER_EMAIL --body "your-email@example.com"

# 2. 设置 Meltwater 密码
gh secret set MELTWATER_PASSWORD --body "your-password"

# 3. 设置 Meltwater 登录 URL (可选,默认为 https://app.meltwater.com)
gh secret set MELTWATER_URL --body "https://app.meltwater.com"
```

### 方式二: 使用 GitHub 网页

1. 访问: https://github.com/zoey169/meltwater-automation/settings/secrets/actions
2. 点击 **New repository secret**
3. 添加以下 3 个 secrets:

| Name | Value | 说明 |
|------|-------|------|
| `MELTWATER_EMAIL` | 你的 Meltwater 登录邮箱 | 必填 |
| `MELTWATER_PASSWORD` | 你的 Meltwater 登录密码 | 必填 |
| `MELTWATER_URL` | `https://app.meltwater.com` | 可选,默认值 |

## ⚠️ 重要提示

### 关于 Meltwater 导出逻辑

当前 `meltwater_downloader.py` 包含**通用的浏览器自动化框架**,但具体的导出流程需要根据你的 Meltwater 界面调整。

**需要你确认的信息:**

1. **登录后的界面布局**
   - 是否有验证码?
   - 是否需要 2FA 验证?
   - 登录成功后跳转到哪个页面?

2. **数据导出流程**
   - 如何进入数据导出页面?(点击哪些菜单/按钮?)
   - 如何选择日期范围?
   - 如何选择导出格式(CSV)?
   - 导出按钮的文本或选择器是什么?

### 调试模式

如果自动下载失败,系统会:
- 保存错误截图到 `downloads/error_screenshot.png`
- 输出详细日志
- 将截图和日志上传为 GitHub Actions artifacts

你可以下载这些 artifacts 来查看失败原因。

## 🚀 测试完整流程

### 1. 首次测试建议使用手动模式

在 Meltwater 手动导出一个测试 CSV 文件,上传到一个可访问的 URL,然后:

```bash
gh workflow run meltwater-import.yml -f csv_url="https://your-test-csv-url.com/file.csv"
```

这样可以先验证**导入部分**是否正常工作。

### 2. 配置自动下载后测试

配置好 Meltwater Secrets 后,直接运行:

```bash
gh workflow run meltwater-import.yml
```

不提供 `csv_url` 参数,系统会自动:
1. 登录 Meltwater
2. 下载过去一年的数据
3. 验证重复记录
4. 导入到飞书
5. 发送通知

## 🔍 查看运行结果

```bash
# 查看最近的运行
gh run list --workflow=meltwater-import.yml --limit 5

# 查看详细日志
gh run view <run-id> --log

# 下载 artifacts (包括截图和日志)
gh run download <run-id>
```

## 📝 后续优化建议

根据实际使用情况,可能需要调整:

1. **等待时间**: 如果网络较慢,可能需要增加 `time.sleep()` 的时间
2. **选择器**: 根据实际的 Meltwater 界面更新按钮/输入框的选择器
3. **错误处理**: 增加重试逻辑和更详细的错误信息
4. **验证码处理**: 如果需要验证码,可能需要集成 OCR 或人工介入

## 🆘 需要帮助?

如果遇到问题,请提供:
1. GitHub Actions 运行 ID
2. 错误截图 (从 artifacts 下载)
3. Meltwater 导出界面的截图或描述

我可以根据这些信息调整自动化脚本。
