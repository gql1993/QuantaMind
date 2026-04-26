# QuantaMind CLI 客户端 — 命令行入口

import asyncio
import json
import sys
from typing import Optional

from quantamind import config

GATEWAY_URL = f"http://{config.GATEWAY_HOST}:{config.GATEWAY_PORT}"


async def chat_stream(session_id: Optional[str], message: str) -> None:
    import aiohttp
    url = f"{GATEWAY_URL}/api/v1/chat"
    payload = {"message": message, "stream": True}
    if session_id:
        payload["session_id"] = session_id
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                print(f"Error: {resp.status}", file=sys.stderr)
                return
            async for line in resp.content:
                if line.startswith(b"data: "):
                    try:
                        obj = json.loads(line[6:].decode())
                        if obj.get("type") == "content" and obj.get("data"):
                            print(obj["data"], end="", flush=True)
                        if obj.get("type") == "done" and obj.get("session_id"):
                            print()  # newline after reply
                            return
                    except (json.JSONDecodeError, KeyError):
                        continue


async def main_loop() -> None:
    import aiohttp
    # 创建会话
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{GATEWAY_URL}/api/v1/sessions", json={}) as resp:
            if resp.status != 200:
                print("Failed to create session. Is the gateway running?", file=sys.stderr)
                print("  Start with: python -m quantamind.server.gateway", file=sys.stderr)
                return
            data = await resp.json()
            session_id = data.get("session_id", "")

    print("QuantaMind CLI — 输入消息与 AI 对话，Ctrl+C 或输入 exit 退出。")
    print(f"Gateway: {GATEWAY_URL} | Session: {session_id[:8]}...")
    print("-" * 50)
    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break
        await chat_stream(session_id, user_input)


def run_cli() -> None:
    asyncio.run(main_loop())


if __name__ == "__main__":
    run_cli()
