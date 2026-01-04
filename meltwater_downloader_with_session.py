#!/usr/bin/env python3
"""
Meltwater 自动下载脚本 - 支持会话复用
功能:
1. 支持使用已有的浏览器登录状态
2. 导出过去一年的数据为 CSV
3. 下载 CSV 文件到本地
"""

import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 从环境变量读取配置
MELTWATER_URL = os.getenv("MELTWATER_URL", "https://app.meltwater.com")
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "./downloads")
USER_DATA_DIR = os.getenv("USER_DATA_DIR", "./browser_data")  # 浏览器数据目录


class MeltwaterDownloaderWithSession:
    """Meltwater 自动下载器 - 支持会话复用"""

    def __init__(self, url: str, download_path: str, user_data_dir: str):
        self.url = url
        self.download_path = download_path
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # 确保目录存在
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.user_data_dir, exist_ok=True)

    def start_browser(self):
        """启动浏览器并使用持久化上下文"""
        logger.info("启动浏览器(使用持久化会话)...")
        self.playwright = sync_playwright().start()

        # 使用持久化上下文,这样可以保存登录状态
        self.context = self.playwright.chromium.launch_persistent_context(
            self.user_data_dir,
            headless=False,  # 首次运行时使用非 headless 模式方便手动登录
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        logger.info("浏览器启动成功")

    def check_login_status(self):
        """检查是否已登录"""
        logger.info("检查登录状态...")

        try:
            self.page.goto(self.url, wait_until='networkidle', timeout=60000)
            time.sleep(3)
        except Exception as e:
            logger.warning(f"页面加载出现问题,但继续检查: {str(e)}")

        # 保存当前页面截图
        try:
            screenshot_path = os.path.join(self.download_path, "session_check.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存页面截图: {screenshot_path}")
        except Exception as e:
            logger.warning(f"截图失败: {str(e)}")

        # 检查是否在登录页面
        try:
            page_content = self.page.content().lower()
            is_login_page = 'password' in page_content and 'email' in page_content
        except Exception as e:
            logger.warning(f"无法读取页面内容,假设需要登录: {str(e)}")
            is_login_page = True

        if is_login_page:
            logger.warning("⚠️  检测到登录页面,需要手动登录")
            logger.info("请在打开的浏览器窗口中手动登录...")
            logger.info("等待登录完成... (最长等待 180 秒)")
            logger.info("浏览器窗口将保持打开状态,直到登录完成或超时")

            # 轮询检测登录状态,最多等待 3 分钟
            max_wait_seconds = 180
            check_interval = 5
            elapsed = 0

            while elapsed < max_wait_seconds:
                time.sleep(check_interval)
                elapsed += check_interval

                # 检查当前页面是否还在登录页
                try:
                    # 等待页面稳定
                    self.page.wait_for_load_state('domcontentloaded', timeout=3000)
                    current_content = self.page.content().lower()

                    # 检查是否还在登录页
                    still_on_login = 'password' in current_content and 'email' in current_content

                    if not still_on_login:
                        logger.info(f"✅ 检测到登录完成 (耗时 {elapsed} 秒)")
                        # 额外等待确保登录完全完成
                        time.sleep(5)
                        return True

                except PlaywrightTimeout:
                    # 页面加载超时,可能是在导航,继续等待
                    if elapsed % 15 == 0:
                        logger.info(f"页面正在加载... 已等待 {elapsed}/{max_wait_seconds} 秒")
                    continue
                except Exception as e:
                    # 其他异常,记录但继续等待
                    if elapsed % 30 == 0:  # 每30秒记录一次
                        logger.warning(f"页面检查遇到问题: {str(e)[:100]}")
                    continue

                if elapsed % 15 == 0:  # 每 15 秒输出一次状态
                    logger.info(f"等待中... 已等待 {elapsed}/{max_wait_seconds} 秒")

            # 超时
            logger.error(f"❌ 登录超时 (等待了 {max_wait_seconds} 秒)")
            raise Exception("手动登录超时")
        else:
            logger.info("✅ 已检测到登录状态")
            return True

    def export_data(self):
        """导出过去365天的数据"""
        logger.info("开始导出过去 365 天的数据...")

        # 等待页面完全加载
        logger.info("等待页面完全加载...")
        time.sleep(5)

        # 等待网络空闲
        logger.info("等待网络空闲...")
        self.page.wait_for_load_state('networkidle', timeout=30000)
        logger.info("✅ 网络已空闲")

        # 额外等待确保动态内容渲染
        logger.info("额外等待 10 秒以确保动态内容完全渲染...")
        time.sleep(10)

        # 保存主页截图
        try:
            screenshot_path = os.path.join(self.download_path, "home_page.png")
            self.page.screenshot(path=screenshot_path)
            logger.info(f"已保存 Home 页面截图: {screenshot_path}")
        except:
            pass

        # 策略: 直接在当前页面查找下载按钮
        logger.info("查找 ANZ Coverage 2025 下载按钮...")

        # 使用之前成功的选择器
        download_button_selectors = [
            # 父元素导航 - 这是之前成功的方法
            'text=ANZ_Coverage_2025 >> .. >> .. >> .. >> a',
            'text=ANZ_Coverage_2025 >> .. >> .. >> .. >> button',
            'text=ANZ Coverage 2025 >> .. >> .. >> .. >> a',
            'text=ANZ Coverage 2025 >> .. >> .. >> .. >> button',

            # 直接查找下载链接
            'a:has-text("Download")',
            '[aria-label="Download"]',
            'button:has-text("Download")',
        ]

        downloaded_file = None
        for selector in download_button_selectors:
            try:
                logger.info(f"尝试选择器: {selector}")
                if self.page.locator(selector).count() > 0:
                    logger.info(f"✅ 找到匹配元素: {selector}")

                    # 设置下载监听
                    with self.page.expect_download(timeout=60000) as download_info:
                        self.page.locator(selector).first.click()
                        logger.info("已点击下载按钮,等待下载...")

                    download = download_info.value

                    # 保存文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"meltwater_export_{timestamp}.csv"
                    save_path = os.path.join(self.download_path, filename)
                    download.save_as(save_path)

                    logger.info(f"✅ 文件下载成功: {save_path}")
                    downloaded_file = save_path
                    break

            except PlaywrightTimeout:
                logger.warning(f"选择器超时: {selector}")
                continue
            except Exception as e:
                logger.warning(f"选择器失败 {selector}: {str(e)}")
                continue

        if not downloaded_file:
            logger.error("❌ 所有选择器都失败了")
            # 保存错误截图
            try:
                screenshot_path = os.path.join(self.download_path, "error_no_button.png")
                self.page.screenshot(path=screenshot_path)
                logger.info(f"已保存错误截图: {screenshot_path}")
            except:
                pass
            raise Exception("无法找到下载按钮")

        return downloaded_file

    def close_browser(self):
        """关闭浏览器"""
        logger.info("关闭浏览器...")
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("浏览器已关闭")

    def run(self):
        """执行完整的下载流程"""
        csv_file = None
        try:
            self.start_browser()
            self.check_login_status()
            csv_file = self.export_data()
            return csv_file
        except Exception as e:
            logger.error(f"❌ 下载失败: {str(e)}")
            # 保存错误截图
            try:
                if self.page:
                    screenshot_path = os.path.join(self.download_path, "error_screenshot.png")
                    self.page.screenshot(path=screenshot_path)
                    logger.info(f"已保存错误截图: {screenshot_path}")
            except:
                pass
            raise
        finally:
            self.close_browser()


def main():
    logger.info("=" * 50)
    logger.info("Meltwater 自动下载开始(会话复用模式)")
    logger.info("=" * 50)

    downloader = MeltwaterDownloaderWithSession(
        url=MELTWATER_URL,
        download_path=DOWNLOAD_PATH,
        user_data_dir=USER_DATA_DIR
    )

    try:
        csv_file = downloader.run()
        logger.info("=" * 50)
        logger.info("✅ 下载完成!")
        logger.info(f"文件路径: {csv_file}")
        logger.info("=" * 50)
        print(f"SUCCESS:{csv_file}")  # 输出成功标记供其他脚本使用
        return 0
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
