# CSV 文件上传指南

GitHub Actions 无法直接访问本地文件,需要通过以下方式之一提供 CSV 文件:

## 方式 1: 手动触发并提供 CSV URL (推荐)

### 步骤:
1. 将 CSV 文件上传到可访问的地址(如网盘、对象存储等)
2. 获取文件的直接下载 URL
3. 在 GitHub 仓库页面:
   - 点击 **Actions** 标签
   - 选择 **Meltwater Data Import** 工作流
   - 点击 **Run workflow** 按钮
   - 在 `csv_url` 输入框中填入 CSV 文件的 URL
   - 点击 **Run workflow** 开始执行

### 支持的 URL 示例:
- Google Drive: `https://drive.google.com/uc?export=download&id=FILE_ID`
- Dropbox: `https://www.dropbox.com/s/xxxxx/file.csv?dl=1`
- 对象存储 (S3/OSS): `https://bucket.s3.amazonaws.com/path/to/file.csv`

## 方式 2: GitHub Release Artifacts

### 步骤:
1. 创建一个 GitHub Release
2. 将 CSV 文件作为 Asset 上传
3. 修改工作流配置,从 Release 下载文件

## 方式 3: 定期 API 拉取 (需要 Meltwater API)

如果 Meltwater 提供 API 接口,可以修改工作流直接从 API 获取数据。

## 当前配置

当前工作流需要通过 **手动触发 + CSV URL** 的方式运行。

### 如何测试:
```bash
# 使用 gh CLI 手动触发
gh workflow run meltwater-import.yml -f csv_url="https://your-csv-url.com/file.csv"
```

## 自动化建议

### 选项 A: 使用云存储
1. 每次导出 CSV 后上传到固定的云存储路径
2. 修改工作流使用固定 URL 自动获取

### 选项 B: 集成 Meltwater API
如果 Meltwater 支持 API 导出,可以完全自动化。

### 选项 C: 邮件附件自动处理
配置邮件服务,自动提取 CSV 附件并上传到可访问位置。

## 注意事项

- CSV 文件必须是 **Tab 分隔**、**UTF-16 编码**
- 下载 URL 必须是**直接下载链接**,不能是预览页面
- 确保 URL 可以被 GitHub Actions 服务器访问(公开或有访问令牌)
