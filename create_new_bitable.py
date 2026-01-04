#!/usr/bin/env python3
"""
创建新的飞书多维表格用于 Meltwater 数据导入
"""
import requests
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

def create_bitable():
    """创建新的多维表格"""
    token = get_tenant_access_token()
    if not token:
        return
    
    url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 创建多维表格的配置
    data = {
        "name": "Meltwater ANZ Coverage 2025"
    }
    
    print(f"\n📝 创建多维表格: {data['name']}")
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    print(f"📄 响应:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == 0:
        app_token = result["data"]["app"]["app_token"]
        app_url = result["data"]["app"]["url"]
        
        print(f"\n✅ 多维表格创建成功!")
        print(f"📌 App Token: {app_token}")
        print(f"🔗 访问链接: {app_url}")
        
        return app_token
    else:
        print(f"\n❌ 创建失败: {result.get('msg')}")
        return None

def create_table_with_fields(app_token):
    """在多维表格中创建数据表和字段"""
    token = get_tenant_access_token()
    if not token:
        return
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 定义表结构
    table_config = {
        "table": {
            "name": "Meltwater Data",
            "default_view_name": "全部数据",
            "fields": [
                {
                    "field_name": "Document ID",
                    "type": 1,  # 文本
                    "ui_type": "Text"
                },
                {
                    "field_name": "Title/Coverage",
                    "type": 1,
                    "ui_type": "Text"
                },
                {
                    "field_name": "Date",
                    "type": 5,  # 日期
                    "ui_type": "DateTime",
                    "property": {
                        "date_formatter": "yyyy/MM/dd"
                    }
                },
                {
                    "field_name": "Source Name",
                    "type": 1,
                    "ui_type": "Text"
                },
                {
                    "field_name": "Author Name",
                    "type": 1,
                    "ui_type": "Text"
                },
                {
                    "field_name": "Reach",
                    "type": 1,
                    "ui_type": "Text"
                },
                {
                    "field_name": "AVE",
                    "type": 1,
                    "ui_type": "Text"
                },
                {
                    "field_name": "URL/Link",
                    "type": 15,  # 超链接
                    "ui_type": "Url"
                }
            ]
        }
    }
    
    print(f"\n📝 创建数据表...")
    
    response = requests.post(url, headers=headers, json=table_config)
    result = response.json()
    
    print(f"📄 响应:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == 0:
        table_id = result["data"]["table_id"]
        print(f"\n✅ 数据表创建成功!")
        print(f"📌 Table ID: {table_id}")
        
        return table_id
    else:
        print(f"\n❌ 创建数据表失败: {result.get('msg')}")
        return None

def main():
    print("=" * 80)
    print("创建新的飞书多维表格用于 Meltwater 数据")
    print("=" * 80)
    
    # Step 1: 创建多维表格
    app_token = create_bitable()
    if not app_token:
        return
    
    # Step 2: 创建数据表和字段
    table_id = create_table_with_fields(app_token)
    if not table_id:
        return
    
    print("\n" + "=" * 80)
    print("✅ 全部完成! 请将以下配置添加到环境变量:")
    print("=" * 80)
    print(f"export BITABLE_APP_TOKEN=\"{app_token}\"")
    print(f"export BITABLE_TABLE_ID=\"{table_id}\"")
    print("=" * 80)

if __name__ == "__main__":
    main()
