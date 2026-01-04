#!/usr/bin/env python3
"""
验证飞书多维表格访问权限
"""
import requests
import os
import json

FEISHU_APP_ID = "cli_a702c225665e100d"
FEISHU_APP_SECRET = "5D7PoQaMtb8Er1qqfUnGpfcYiFekaX2b"

def get_tenant_access_token():
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    
    response = requests.post(url, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        print(f"✅ 成功获取 access_token")
        return result["tenant_access_token"]
    else:
        print(f"❌ 获取 token 失败: {result}")
        return None

def test_bitable_access(token, app_token):
    """测试 Bitable 访问权限"""
    # 尝试列出 app 中的所有表
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 测试 App Token: {app_token}")
    print(f"📍 请求 URL: {url}")
    
    response = requests.get(url, headers=headers)
    print(f"📡 响应状态码: {response.status_code}")
    
    result = response.json()
    print(f"📄 响应内容:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == 0:
        tables = result.get("data", {}).get("items", [])
        print(f"\n✅ 成功访问! 找到 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table.get('name')} (ID: {table.get('table_id')})")
        return True
    else:
        print(f"\n❌ 访问失败: {result.get('msg')}")
        return False

def main():
    print("=" * 60)
    print("飞书多维表格访问权限验证")
    print("=" * 60)
    
    # 获取 token
    token = get_tenant_access_token()
    if not token:
        return
    
    # 测试当前配置的 app_token
    current_app_token = "WBWLbcH7ba2oCDsZqNScxVF2nzc"
    test_bitable_access(token, current_app_token)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
