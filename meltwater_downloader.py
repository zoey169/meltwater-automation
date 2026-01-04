#!/usr/bin/env python3
"""
Meltwater 自动登录和下载脚本
功能:
1. 自动登录 Meltwater 平台
2. 导出过去一年的数据为 CSV
3. 下载 CSV 文件到本地
"""

import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 从环境变量读取 Meltwater 登录信息
MELTWATER_EMAIL = os.getenv("MELTWATER_EMAIL")
MELTWATER_PASSWORD = os.getenv("MELTWATER_PASSWORD")
MELTWATER_URL = os.getenv("MELTWATER_URL", "https://app.meltwater.com")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "./downloads")


class MeltwaterDownloader:
    """Meltwater 自动下载器"""

    def __init__(self, email: str, password: str, url: str, download_path: str):
        self.email = email
        self.password = password
        self.url = url
        self.download_path = download_path
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # 确保下载目录存在
        os.makedirs(self.download_path, exist_ok=True)

    def start_browser(self):
        """启动浏览器"""
        logger.info("启动浏览器...")
        self.playwright = sync_playwright().start()

        # 启动 Chromium 浏览器
        self.browser = self.playwright.chromium.launch(
            headless=True,  # GitHub Actions 中使用 headless 模式
            args=['--no-sandbox', '--disable-dev-shm-usage']  # 云环境优化
        )

        # 创建浏览器上下文,设置下载路径
        self.context = self.browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )

        self.page = self.context.new_page()
        logger.info("浏览器启动成功")

    def login(self):
        """登录 Meltwater"""
        logger.info(f"访问 Meltwater: {self.url}")
        self.page.goto(self.url, wait_until='networkidle', timeout=60000)

        # 等待登录页面加载
        time.sleep(3)

        # 输入邮箱
        logger.info("输入登录凭证...")
        email_selector = 'input[type="email"], input[name="email"], input[id="email"]'
        self.page.wait_for_selector(email_selector, timeout=30000)
        self.page.fill(email_selector, self.email)

        # 输入密码
        password_selector = 'input[type="password"], input[name="password"], input[id="password"]'
        self.page.wait_for_selector(password_selector, timeout=30000)
        self.page.fill(password_selector, self.password)

        # 点击登录按钮
        login_button_selector = 'button[type="submit"], button:has-text("Sign In"), button:has-text("Log In")'
        self.page.click(login_button_selector)

        logger.info("等待登录完成...")
        # 等待页面跳转,检查是否成功登录
        try:
            # 等待仪表板或主页元素出现
            self.page.wait_for_load_state('networkidle', timeout=60000)
            time.sleep(5)
            logger.info("登录成功!")
        except PlaywrightTimeout:
            logger.error("登录超时,可能需要验证码或凭证错误")
            raise

    def export_data(self, days_back: int = 365):
        """
        导出数据

        Args:
            days_back: 导出过去多少天的数据,默认 365 天(一年)
        """
        logger.info(f"开始导出过去 {days_back} 天的数据...")

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

        # 注意: 以下是通用导出逻辑示例,实际需要根据 Meltwater 界面调整
        # 你需要提供具体的 Meltwater 导出流程

        try:
            # 1. 导航到导出页面
            logger.info("导航到导出页面...")
            # 示例: 查找并点击 Export/Download 按钮
            export_selectors = [
                'button:has-text("Export")',
                'a:has-text("Export")',
                'button:has-text("Download")',
                '[data-testid="export-button"]'
            ]

            for selector in export_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    logger.info(f"找到导出按钮: {selector}")
                    break
                except:
                    continue
            else:
                logger.warning("未找到导出按钮,可能需要手动配置选择器")

            time.sleep(2)

            # 2. 选择日期范围
            logger.info("设置日期范围...")
            # 这里需要根据实际界面填写日期选择逻辑

            # 3. 选择导出格式(CSV)
            logger.info("选择 CSV 格式...")
            # 查找 CSV 选项

            # 4. 触发下载
            logger.info("触发下载...")
            # 监听下载事件
            with self.page.expect_download(timeout=120000) as download_info:
                # 点击最终下载/确认按钮
                download_button_selectors = [
                    'button:has-text("Download")',
                    'button:has-text("Export")',
                    'button:has-text("Confirm")',
                    'button[type="submit"]'
                ]

                for selector in download_button_selectors:
                    try:
                        self.page.click(selector, timeout=5000)
                        break
                    except:
                        continue

            # 保存下载的文件
            download = download_info.value
            filename = f"meltwater_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.download_path, filename)
            download.save_as(filepath)

            logger.info(f"文件下载成功: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"导出数据时出错: {str(e)}")
            # 保存截图用于调试
            screenshot_path = os.path.join(self.download_path, "error_screenshot.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存错误截图: {screenshot_path}")
            raise

    def close(self):
        """关闭浏览器"""
        logger.info("关闭浏览器...")
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("浏览器已关闭")

    def download(self, days_back: int = 365) -> str:
        """
        完整的下载流程

        Args:
            days_back: 导出过去多少天的数据

        Returns:
            下载的文件路径
        """
        try:
            self.start_browser()
            self.login()
            filepath = self.export_data(days_back)
            return filepath
        finally:
            self.close()


def main():
    """主函数"""
    # 检查必要的环境变量
    if not MELTWATER_EMAIL or not MELTWATER_PASSWORD:
        logger.error("错误: 缺少 MELTWATER_EMAIL 或 MELTWATER_PASSWORD 环境变量")
        return None

    logger.info("=" * 50)
    logger.info("Meltwater 自动下载开始")
    logger.info("=" * 50)

    # 创建下载器实例
    downloader = MeltwaterDownloader(
        email=MELTWATER_EMAIL,
        password=MELTWATER_PASSWORD,
        url=MELTWATER_URL,
        download_path=DOWNLOAD_PATH
    )

    try:
        # 下载过去一年的数据
        filepath = downloader.download(days_back=365)
        logger.info(f"✅ 下载完成: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"❌ 下载失败: {str(e)}")
        return None


if __name__ == "__main__":
    result = main()
    if result:
        print(f"SUCCESS:{result}")
    else:
        print("FAILED")
        exit(1)
