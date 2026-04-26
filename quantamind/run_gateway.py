#!/usr/bin/env python3
"""启动 QuantaMind Gateway（服务端）。默认端口 18789。"""

from quantamind.server.gateway import run_gateway

if __name__ == "__main__":
    run_gateway()
