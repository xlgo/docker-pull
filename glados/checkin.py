import hashlib
import json
import os
import random
import sys
import time
from typing import Any, Dict, Optional
import requests


class GLaDOSCheckin:
    """GLaDOS 自动化签到客户端"""

    SALT = "glados-observe-v1"

    def __init__(self, cookie: str, domain: str = "glados.one"):
        self.domain = domain
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Origin": f"https://{self.domain}",
            "Referer": f"https://{self.domain}/console/checkin",
            "Content-Type": "application/json;charset=UTF-8",
            "Cookie": cookie.strip(),
        })

    def get_challenge(self) -> Optional[str]:
        """获取一次性验证挑战 (Nonce)"""
        url = f"https://{self.domain}/api/user/checkin/challenge"
        try:
            resp = self.session.get(url, timeout=15)
            data = resp.json()
            if data.get("code") == 0 and "nonce" in data:
                return data["nonce"]
            print(f"  [!] 获取挑战失败: {data.get('message', '未知错误')}")
            return None
        except Exception as e:
            print(f"  [!] 请求 Challenge 异常: {e}")
            return None

    def calculate_proof(self, nonce: str) -> str:
        """根据 Nonce 与 Salt 计算 SHA-256 证明"""
        raw_text = f"{nonce}.{self.SALT}"
        return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    def submit_checkin(self, nonce: str, proof: str) -> Dict[str, Any]:
        """提交签到载荷"""
        url = f"https://{self.domain}/api/user/checkin"
        payload = {
            "token": self.domain,
            "nonce": nonce,
            "proof": proof,
        }
        try:
            resp = self.session.post(url, json=payload, timeout=15)
            return resp.json()
        except Exception as e:
            return {"code": -999, "message": f"请求异常: {e}"}

    def get_status(self) -> Optional[Dict[str, Any]]:
        """获取账号当前状态与剩余天数"""
        url = f"https://{self.domain}/api/user/status"
        try:
            resp = self.session.get(url, timeout=15)
            return resp.json()
        except Exception:
            return None

    def run(self, account_name: str) -> bool:
        """执行单账号签到"""
        print(f"\n>>>>>> 开始处理账号: [{account_name}] <<<<<<")

        # 1. 获取挑战
        nonce = self.get_challenge()
        if not nonce:
            print("  [-] 获取 Nonce 失败，可能是 Cookie 已失效")
            return False

        print(f"  [+] 成功获取 Nonce: {nonce[:8]}***")

        # 2. 模拟前端 2.6 ~ 3.5 秒随机延时（规避风控）
        internal_wait = round(random.uniform(2.6, 3.5), 2)
        print(f"  [*] 模拟前端行为，随机休眠 {internal_wait} 秒...")
        time.sleep(internal_wait)

        # 3. 计算 Proof
        proof = self.calculate_proof(nonce)

        # 4. 提交签到
        result = self.submit_checkin(nonce, proof)
        print(f"  [*] 签到结果: {result.get('message', '无响应')}")

        # 5. 查询剩余天数
        status_info = self.get_status()
        if status_info and status_info.get("code") == 0:
            user_data = status_info.get("data", {})
            email = user_data.get("email", "未配置邮箱")
            left_days = str(user_data.get("leftDays", "0")).split(".")[0]
            print(f"  [+] 账户邮箱: {email} | 剩余天数: {left_days} 天")

        return result.get("code") in [0, 1]


def extract_cookies() -> Dict[str, str]:
    """
    自动提取并整合所有账号 Cookie：
    1. 优先读取 GitHub Actions 的 SECRETS_CONTEXT
    2. 兼容本地或系统环境变量中的 GLADOS_COOKIE*
    """
    cookies_map = {}

    # 从 GitHub Actions 的全局 Secrets 注入中提取
    secrets_raw = os.environ.get("SECRETS_CONTEXT")
    if secrets_raw:
        try:
            all_secrets = json.loads(secrets_raw)
            for key, val in all_secrets.items():
                if key.upper().startswith("GLADOS_COOKIE") and val.strip():
                    cookies_map[key] = val.strip()
        except Exception:
            pass

    # 从标准环境变量中补全
    for key, val in os.environ.items():
        if key.upper().startswith("GLADOS_COOKIE") and val.strip():
            if key not in cookies_map:
                cookies_map[key] = val.strip()

    # 拆分单个变量内可能存在的多账号（支持换行或 & 拼接）
    final_cookies = {}
    for name, content in cookies_map.items():
        parts = [p.strip() for p in content.replace("\n", "&").split("&") if p.strip()]
        if len(parts) == 1:
            final_cookies[name] = parts[0]
        else:
            for idx, part in enumerate(parts, start=1):
                final_cookies[f"{name}_SUB{idx}"] = part

    return final_cookies


def main():
    accounts = extract_cookies()

    if not accounts:
        print("[!] 错误: 未找到任何有效 Cookie！")
        print("    请在 GitHub 仓库 Settings -> Secrets 中添加以 GLADOS_COOKIE 开头的变量。")
        sys.exit(1)

    print(f"[*] 成功扫描到 {len(accounts)} 个账号，开始依次签到：")

    account_keys = sorted(accounts.keys())
    success_count = 0

    for idx, name in enumerate(account_keys, start=1):
        cookie_val = accounts[name]
        client = GLaDOSCheckin(cookie=cookie_val, domain="glados.one")
        
        if client.run(account_name=name):
            success_count += 1

        # 若还有下一个账号，随机休眠 1.0 ~ 4.0 秒
        if idx < len(account_keys):
            inter_account_wait = round(random.uniform(1.0, 4.0), 2)
            print(f"[*] 账号间安全延时，等待 {inter_account_wait} 秒切换下一账号...")
            time.sleep(inter_account_wait)

    print(f"\n================ 任务完成 ================")
    print(f"共处理账号: {len(accounts)} 个 | 成功: {success_count} | 失败: {len(accounts) - success_count}")


if __name__ == "__main__":
    main()
