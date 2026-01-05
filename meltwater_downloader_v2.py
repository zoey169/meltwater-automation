#!/usr/bin/env python3
"""
Meltwater 自动登录和下载脚本 (v2 - 修复版)
功能:
1. 自动登录 Meltwater 平台
2. 导航到 Monitor 视图并选择正确的时间范围
3. 触发导出并等待生成完成
4. 下载 CSV 文件到本地

修复说明:
- 修复了时间范围不生效的问题(必须在 Monitor 视图中选择)
- 实现了完整的导出工作流程
- 支持通过 days_back 参数控制时间范围
"""

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging
import re

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
SEARCH_ID = os.getenv("SEARCH_ID", "2062364")  # ANZ Coverage 2025 的 Search ID


class MeltwaterDownloader:
    """Meltwater 自动下载器 v2"""

    def __init__(self, email: str, password: str, url: str, download_path: str, search_id: str):
        self.email = email
        self.password = password
        self.url = url
        self.download_path = download_path
        self.search_id = search_id
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
        time.sleep(3)

        # 输入邮箱
        logger.info("输入邮箱...")
        email_selector = 'input[type="email"]'
        self.page.wait_for_selector(email_selector, timeout=30000)
        self.page.fill(email_selector, self.email)

        # 点击 Next 按钮
        logger.info("点击 Next...")
        self.page.click('button:has-text("Next")')
        time.sleep(3)

        # 输入密码
        logger.info("输入密码...")
        password_selector = 'input[type="password"]'
        self.page.wait_for_selector(password_selector, timeout=30000)
        self.page.type(password_selector, self.password, delay=100)
        time.sleep(1)

        # 点击登录按钮
        logger.info("点击登录...")
        self.page.click('button[type="submit"]')

        # 等待登录完成
        logger.info("等待登录完成...")
        self.page.wait_for_load_state('networkidle', timeout=60000)
        time.sleep(2)

        # 处理 passkey 弹窗
        try:
            skip_button = self.page.locator('a:has-text("Continue without passkeys")')
            if skip_button.is_visible(timeout=5000):
                logger.info("跳过 passkey...")
                skip_button.click()
                time.sleep(3)
        except:
            logger.info("无 passkey 弹窗")

        # 等待导航到 Home 页面
        try:
            self.page.wait_for_url("**/home**", timeout=15000)
            logger.info("✅ 登录成功")
        except:
            logger.warning("URL 不包含 home,但继续执行")

    def export_data(self, days_back: int = 365):
        """
        导出数据

        工作流程:
        1. 导航到 Monitor 视图
        2. 选择时间范围(根据 days_back 参数)
        3. 点击 Download 按钮触发导出
        4. 等待导出生成完成
        5. 下载文件

        Args:
            days_back: 导出过去多少天的数据,默认 365 天(一年)
        """
        logger.info(f"开始导出过去 {days_back} 天的数据...")

        # 根据 days_back 确定时间范围选项
        if days_back >= 365:
            time_range = "Last year"
        elif days_back >= 90:
            time_range = "Last 90 days"
        elif days_back >= 30:
            time_range = "Last 30 days"
        elif days_back >= 7:
            time_range = "Last 7 days"
        else:
            time_range = "Last 24 hours"

        logger.info(f"将使用时间范围: {time_range}")

        try:
            # Step 1: 导航到 Monitor 视图
            monitor_url = f"https://app.meltwater.com/a/monitor/view?searches={self.search_id}&type=tag"
            logger.info(f"步骤1: 导航到 Monitor 视图...")
            self.page.goto(monitor_url, wait_until='networkidle', timeout=60000)
            time.sleep(5)

            screenshot_path = os.path.join(self.download_path, "step1_monitor_page.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存 Monitor 页面截图")

            # Step 2: 点击时间范围按钮
            logger.info("步骤2: 点击时间范围按钮...")
            # 查找显示当前时间范围的按钮(如 "Last 30 days" 或 "Last year")
            time_button = self.page.locator('button:has-text("Last")').first
            if time_button.is_visible(timeout=10000):
                current_range = time_button.inner_text()
                logger.info(f"当前时间范围: {current_range}")
                time_button.click()
                time.sleep(2)
                logger.info("✅ 已打开时间范围菜单")
            else:
                raise Exception("未找到时间范围按钮")

            screenshot_path = os.path.join(self.download_path, "step2_time_menu.png")
            self.page.screenshot(path=screenshot_path)

            # Step 3: 选择时间范围
            logger.info(f"步骤3: 选择 '{time_range}'...")
            time_option = self.page.locator(f'button:has-text("{time_range}")').first
            if time_option.is_visible(timeout=5000):
                time_option.click()
                time.sleep(3)  # 等待页面更新
                logger.info(f"✅ 已选择时间范围: {time_range}")
            else:
                raise Exception(f"未找到时间选项: {time_range}")

            screenshot_path = os.path.join(self.download_path, "step3_after_selection.png")
            self.page.screenshot(path=screenshot_path)

            # 验证结果数量
            try:
                results_text = self.page.locator('text=/\\d+ results/').first.inner_text()
                results_count = re.search(r'(\d+)', results_text).group(1)
                logger.info(f"当前显示结果数: {results_count}")
            except:
                logger.warning("无法获取结果数量")

            # Step 4: 点击 Download 按钮
            logger.info("步骤4: 点击 Download 按钮...")
            download_button = self.page.locator('button:has-text("Download")').first
            if download_button.is_visible(timeout=10000):
                download_button.click()
                time.sleep(2)
                logger.info("✅ 已点击 Download 按钮")
            else:
                raise Exception("未找到 Download 按钮")

            screenshot_path = os.path.join(self.download_path, "step4_download_dialog.png")
            self.page.screenshot(path=screenshot_path)

            # Step 5: 在对话框中点击 Download
            logger.info("步骤5: 在对话框中确认下载...")
            # 对话框中的 Download 按钮
            dialog_download_button = self.page.locator('[role="dialog"] button:has-text("Download")').first
            if dialog_download_button.is_visible(timeout=5000):
                dialog_download_button.click()
                logger.info("✅ 已触发导出生成")
            else:
                # 可能没有对话框,直接触发了
                logger.warning("未检测到对话框,可能直接触发导出")

            time.sleep(3)
            screenshot_path = os.path.join(self.download_path, "step5_export_triggered.png")
            self.page.screenshot(path=screenshot_path)

            # Step 6: 等待导出完成通知
            logger.info("步骤6: 等待导出生成完成...")
            logger.info("将监控通知区域...")

            max_wait_time = 300  # 最多等待 5 分钟
            check_interval = 5   # 每 5 秒检查一次
            elapsed_time = 0
            export_ready = False
            download_link_ref = None

            while elapsed_time < max_wait_time and not export_ready:
                logger.info(f"⏳ 等待中... ({elapsed_time}/{max_wait_time}秒)")
                time.sleep(check_interval)
                elapsed_time += check_interval

                # 查找通知:"Your CSV file is ready"
                try:
                    ready_notification = self.page.locator('text=Your CSV file is ready')
                    if ready_notification.count() > 0:
                        logger.info("✅ 检测到导出完成通知!")
                        export_ready = True

                        # 查找通知中的 Download 链接
                        # 通知通常在右上角的浮动窗口中
                        download_links = self.page.locator('text=Your CSV file is ready >> .. >> a:has-text("Download")')
                        if download_links.count() > 0:
                            logger.info(f"找到 {download_links.count()} 个 Download 链接")
                            download_link_ref = download_links.last  # 使用最新的一个
                        else:
                            # 尝试更宽松的选择器
                            download_links = self.page.locator('a:has-text("Download")').filter(has_text="Your CSV file is ready")
                            if download_links.count() > 0:
                                logger.info(f"找到 {download_links.count()} 个 Download 链接(宽松匹配)")
                                download_link_ref = download_links.last

                        break
                except Exception as e:
                    logger.debug(f"检查通知失败: {e}")
                    continue

            if not export_ready:
                raise Exception("导出生成超时")

            # Step 7: 点击 Download 链接下载文件
            logger.info("步骤7: 下载文件...")

            # 如果找到了明确的 Download 链接,点击它
            if download_link_ref:
                with self.page.expect_download(timeout=30000) as download_info:
                    download_link_ref.click()
                    logger.info("✅ 已点击 Download 链接")

                download = download_info.value
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"meltwater_export_{timestamp}.csv"
                filepath = os.path.join(self.download_path, filename)
                download.save_as(filepath)
                logger.info(f"✅ 文件已保存: {filepath}")

                return filepath
            else:
                # 如果没有找到链接,尝试从通知中提取 URL
                logger.warning("未找到 Download 链接,尝试提取下载 URL...")

                # 查找所有 a 标签,找到包含 .csv 的链接
                csv_links = self.page.locator('a[href*=".csv"]')
                if csv_links.count() > 0:
                    logger.info(f"找到 {csv_links.count()} 个 CSV 链接")
                    # 使用最后一个(最新的)
                    with self.page.expect_download(timeout=30000) as download_info:
                        csv_links.last.click()
                        logger.info("✅ 已点击 CSV 链接")

                    download = download_info.value
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"meltwater_export_{timestamp}.csv"
                    filepath = os.path.join(self.download_path, filename)
                    download.save_as(filepath)
                    logger.info(f"✅ 文件已保存: {filepath}")

                    return filepath
                else:
                    raise Exception("未找到下载链接")

        except Exception as e:
            logger.error(f"导出数据时出错: {str(e)}")
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
    logger.info("Meltwater 自动下载开始 (v2)")
    logger.info("=" * 50)

    # 创建下载器实例
    downloader = MeltwaterDownloader(
        email=MELTWATER_EMAIL,
        password=MELTWATER_PASSWORD,
        url=MELTWATER_URL,
        download_path=DOWNLOAD_PATH,
        search_id=SEARCH_ID
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
