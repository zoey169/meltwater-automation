import os
import sys
import time
from playwright.sync_api import sync_playwright

def debug_download_button():
    download_path = "./downloads"
    os.makedirs(download_path, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Login
            page.goto("https://app.meltwater.com")
            time.sleep(3)
            
            page.fill('input[type="email"]', "tove.berkhout@anker.com")
            page.click('button:has-text("Next")')
            time.sleep(3)
            
            page.fill('input[type="password"]', 'P3$NwcskGq6!!s3')
            page.click('button[type="submit"]')
            time.sleep(5)
            
            try:
                page.click('button:has-text("Continue without passkeys")', timeout=5000)
                time.sleep(2)
            except:
                pass
            
            # Wait for page to load
            print("等待页面加载...")
            try:
                page.wait_for_selector('text=Hello', timeout=10000)
            except:
                pass
            
            try:
                page.wait_for_load_state('networkidle', timeout=15000)
            except:
                pass
            
            time.sleep(10)
            
            # Find the ANZ Coverage row
            print("\n查找 ANZ Coverage 行...")
            row = page.locator('text=ANZ_Coverage_2025').locator('..')
            print(f"找到行: {row}")
            
            # Get all buttons in this row
            print("\n获取该行中的所有按钮...")
            buttons = row.locator('button').all()
            print(f"找到 {len(buttons)} 个按钮")
            
            for i, btn in enumerate(buttons):
                try:
                    aria_label = btn.get_attribute('aria-label')
                    title = btn.get_attribute('title')
                    text = btn.inner_text()
                    print(f"\n按钮 {i}:")
                    print(f"  aria-label: {aria_label}")
                    print(f"  title: {title}")
                    print(f"  text: {text}")
                except Exception as e:
                    print(f"  Error: {e}")
            
            # Try to find download button by various selectors
            print("\n\n尝试各种选择器...")
            selectors = [
                'button[aria-label*="Download"]',
                'button[title*="Download"]',
                'button:has-text("Download")',
                '[data-testid*="download"]',
                'button svg[data-icon="download"]',
            ]
            
            for selector in selectors:
                try:
                    count = row.locator(selector).count()
                    print(f"{selector}: {count} 个匹配")
                    if count > 0:
                        print(f"  ✅ 找到!")
                except Exception as e:
                    print(f"{selector}: Error - {e}")
            
            # Take screenshot
            page.screenshot(path=f"{download_path}/debug_button_structure.png", full_page=True)
            print(f"\n已保存截图: {download_path}/debug_button_structure.png")
            
            input("\n按 Enter 关闭浏览器...")
            
        finally:
            browser.close()

if __name__ == "__main__":
    debug_download_button()
