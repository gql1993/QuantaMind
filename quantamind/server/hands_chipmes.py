# Hands 适配器：CHIPMES（真实半导体制造执行系统）
# 通过 REST API 对接 E:\work\MES 的 CHIPMES 系统（Spring Boot，端口 8082）
# 模块：cm（芯片管理）、fm（制造管理）、pm（计划管理）

import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

_log = logging.getLogger("quantamind.hands.chipmes")


def _chipmes_base() -> str:
    from quantamind import config as app_config
    return app_config.get_database_config("mes_chipmes").get("base_url", "http://127.0.0.1:8082").rstrip("/")


def _urlopen_no_proxy(req: urllib.request.Request, timeout: int = 2):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(req, timeout=timeout)


def _probe(path: str, timeout: int = 2) -> Optional[int]:
    try:
        req = urllib.request.Request(f"{_chipmes_base()}{path}", method="GET")
        with _urlopen_no_proxy(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def _is_connected():
    """动态检测 CHIPMES 是否在线"""
    # 真实 Java 版常见表现：
    # - "/" 返回 401（已启动但未登录）
    # - "/doc.html" 或 "/swagger-ui.html" 返回 200
    # - "/actuator/health" 返回 200
    for path in ("/actuator/info", "/actuator/health", "/doc.html", "/swagger-ui.html", "/"):
        status = _probe(path, timeout=2)
        if status is not None and status < 500:
            return True
    return False

MES_DIR = "E:\\work\\MES"


def _api(method: str, path: str, body: Optional[dict] = None) -> Optional[dict]:
    if not _is_connected():
        return None
    try:
        url = f"{_chipmes_base()}{path}"
        data = json.dumps(body).encode() if body else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with _urlopen_no_proxy(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        _log.warning("CHIPMES API 调用失败 %s %s: %s", method, path, e)
        return None


def get_system_info() -> Dict[str, Any]:
    """获取 CHIPMES 系统信息"""
    data = _api("GET", "/actuator/info")
    if data:
        return {"system": "CHIPMES", "info": data, "connected": True, "base_url": _chipmes_base()}
    connected = _is_connected()
    if connected:
        health = _api("GET", "/actuator/health")
        return {
            "system": "CHIPMES 半导体制造执行系统",
            "version": "9.0",
            "framework": "Spring Boot + MyBatis-Plus",
            "port": 8082,
            "mode": "real",
            "health": health,
            "connected": True,
            "base_url": _chipmes_base(),
            "doc_url": f"{_chipmes_base()}/doc.html",
            "swagger_url": f"{_chipmes_base()}/swagger-ui.html",
        }
    return {
        "system": "CHIPMES 半导体制造执行系统",
        "version": "9.0",
        "framework": "Spring Boot + MyBatis-Plus",
        "port": 8082,
        "modules": {
            "cm": "芯片管理（Chip Management）— 芯片型号、批次、晶圆管理",
            "fm": "制造管理（Fabrication Management）— 工艺路线、工序、设备、良率",
            "pm": "计划管理（Plan Management）— 生产计划、排产、工单",
        },
        "features": ["主订单/子订单管理", "工艺路线管理", "批次跟踪", "设备管理",
                     "良率统计", "SPC 过程监控", "审计日志", "Swagger API 文档"],
        "connected": connected,
        "base_url": _chipmes_base(),
        "install_path": MES_DIR,
        "start_command": f"cd {MES_DIR}\\CHIPMES-service && start.bat",
        "ui_url": f"打开 {MES_DIR}\\CHIPMES-ui\\index.html",
    }


def get_api_docs() -> Dict[str, Any]:
    """获取 CHIPMES Swagger API 文档地址"""
    data = _api("GET", "/v3/api-docs")
    if data:
        paths = list(data.get("paths", {}).keys())[:30]
        return {"swagger_url": f"{_chipmes_base()}/swagger-ui.html",
                "api_count": len(data.get("paths", {})),
                "sample_paths": paths, "connected": True}
    return {
        "swagger_url": f"{_chipmes_base()}/swagger-ui.html",
        "note": "CHIPMES 未运行。启动方式：cd E:\\work\\MES\\CHIPMES-service && start.bat",
        "expected_apis": [
            "/api/plan/ordermain — 主订单管理",
            "/api/plan/childmaindetail — 子订单管理",
            "/api/base/craft — 工艺路线",
            "/api/base/equipment — 设备管理",
            "/api/info/* — 基础信息",
            "/api/wms/* — 仓储管理",
            "/api/iqc/* — 来料检验",
            "/api/eqi/* — 设备检验",
        ],
        "connected": False,
    }


def query_orders(status: Optional[str] = None) -> Dict[str, Any]:
    """查询生产订单"""
    data = _api("GET", "/api/plan/ordermain" + (f"?status={status}" if status else ""))
    if data:
        return {"orders": data, "connected": True}
    mock = [
        {"order_id": "WO-2026-001", "product": "20bit-Transmon", "qty": 24, "status": "生产中", "priority": "高"},
        {"order_id": "WO-2026-002", "product": "105bit-Transmon", "qty": 12, "status": "待排产", "priority": "中"},
        {"order_id": "WO-2026-003", "product": "JJ-Test", "qty": 48, "status": "已完成", "priority": "低"},
    ]
    if status:
        mock = [o for o in mock if o["status"] == status]
    return {"orders": mock, "count": len(mock), "connected": False}


def query_craft_routes() -> Dict[str, Any]:
    """查询工艺路线"""
    data = _api("GET", "/api/base/craft")
    if data:
        return {"routes": data, "connected": True}
    mock = [
        {"route_id": "CR-001", "name": "超导量子芯片全流程", "steps": ["衬底清洗", "Nb/Ta 溅射", "光刻", "RIE 刻蚀", "JJ 制备(Dolan)", "空气桥", "布线", "封装测试"], "products": ["20bit-Transmon", "105bit-Transmon"]},
        {"route_id": "CR-002", "name": "JJ 单步测试", "steps": ["清洗", "EBL 曝光", "双角蒸镀", "Lift-off", "电学测试"], "products": ["JJ-Test"]},
    ]
    return {"routes": mock, "count": len(mock), "connected": False}


def query_equipment() -> Dict[str, Any]:
    """查询设备列表"""
    data = _api("GET", "/api/base/equipment")
    if data:
        return {"equipment": data, "connected": True}
    mock = [
        {"eq_id": "SPUTTER-01", "name": "磁控溅射台", "type": "薄膜沉积", "status": "运行"},
        {"eq_id": "LITHO-01", "name": "激光直写机", "type": "光刻", "status": "运行"},
        {"eq_id": "EBL-01", "name": "电子束曝光机", "type": "EBL", "status": "运行"},
        {"eq_id": "ETCH-01", "name": "RIE 刻蚀机", "type": "刻蚀", "status": "维护中"},
        {"eq_id": "EVAP-01", "name": "双角蒸镀台", "type": "JJ 制备", "status": "运行"},
        {"eq_id": "CRYO-01", "name": "稀释制冷机", "type": "测控", "status": "运行"},
    ]
    return {"equipment": mock, "count": len(mock), "connected": False}


def query_yield_stats(product: Optional[str] = None) -> Dict[str, Any]:
    """查询良率统计"""
    data = _api("GET", "/api/report/yield" + (f"?product={product}" if product else ""))
    if data:
        return {"yield": data, "connected": True}
    mock = [
        {"lot": "LOT-2026-0301", "product": "20bit-Transmon", "yield_pct": 91.7, "defects": 2, "total": 24},
        {"lot": "LOT-2026-0285", "product": "20bit-Transmon", "yield_pct": 95.8, "defects": 1, "total": 24},
        {"lot": "LOT-2026-0302", "product": "105bit-Transmon", "yield_pct": 87.5, "defects": 3, "total": 24},
    ]
    import random
    random.seed(42)
    avg = round(sum(m["yield_pct"] for m in mock) / len(mock), 1)
    return {"yield_data": mock, "average_yield_pct": avg, "connected": False}


def start_chipmes() -> Dict[str, Any]:
    """启动 CHIPMES 系统（提供启动命令）"""
    return {
        "command": f"cd /d {MES_DIR}\\CHIPMES-service && start.bat",
        "ui": f"{MES_DIR}\\CHIPMES-ui\\index.html",
        "port": 8082,
        "swagger": f"{_chipmes_base()}/swagger-ui.html",
        "note": "请在命令行执行上述命令启动 CHIPMES 后端，然后用浏览器打开 UI",
    }


def get_capabilities() -> Dict[str, Any]:
    return {
        "source": "CHIPMES 半导体制造执行系统",
        "version": "9.0",
        "connected": _is_connected(),
        "base_url": _chipmes_base(),
        "modules": ["cm（芯片管理）", "fm（制造管理）", "pm（计划管理）"],
        "features": ["订单管理", "工艺路线", "设备管理", "批次跟踪", "良率统计", "SPC", "审计日志"],
        "install_path": MES_DIR,
    }


# ── 数据库表结构元数据（基于 chipmesdb.sql 401张表） ──

CHIPMES_DB_SCHEMA = {
    "database": "chipmesdb",
    "total_tables": 401,
    "categories": {
        "base": {
            "count": 138, "desc": "基础数据（设备/工艺/产品/物料/晶圆/车间/产线）",
            "key_tables": {
                "base_equimentmanage": {"cols": 64, "desc": "设备管理", "key_fields": ["equino", "equiname", "equispec", "equifunction", "assetno", "factname", "equistatus"]},
                "base_craftdetail": {"cols": 35, "desc": "工艺明细", "key_fields": ["craftno", "craftid", "nodecode", "nodename", "aliasnodename"]},
                "base_crafttemp": {"cols": 37, "desc": "工艺模板", "key_fields": ["craftno", "materialstype", "modelno", "materialsno", "stagenm"]},
                "base_product": {"cols": 33, "desc": "产品信息", "key_fields": ["productno", "productname", "productspec", "bitnum", "couplingdegree", "quantumerrorcorr"]},
                "base_productmain": {"cols": 38, "desc": "产品BOM主表", "key_fields": ["bomver", "productno", "productname", "rawmaterialsno"]},
                "base_materials": {"cols": 83, "desc": "物料信息", "key_fields": ["materialsno", "materialsname", "materialsspec", "materialsmodel", "materialsbarcode"]},
                "base_waferinfo": {"cols": 28, "desc": "晶圆信息", "key_fields": ["waferno", "wafername", "fdiameter", "fthickness", "farea"]},
                "base_wafertype": {"cols": 19, "desc": "晶圆类型", "key_fields": ["typeno", "typename", "fstatus"]},
                "base_station": {"cols": 23, "desc": "工站信息", "key_fields": ["stationno", "stationname", "prolineno", "workshopno"]},
                "base_workshop": {"cols": 22, "desc": "车间信息", "key_fields": ["workshopno", "workshopname", "workshoppos"]},
                "base_productionline": {"cols": 22, "desc": "产线信息", "key_fields": ["prolineno", "prolinename", "workshopno"]},
                "base_devicealarm": {"cols": 31, "desc": "设备告警", "key_fields": ["equino", "ipaddr", "taskno", "taskbatchno", "interfacetype"]},
                "base_devicerecipe": {"cols": 29, "desc": "设备配方", "key_fields": ["equino", "ipaddr", "taskno", "interfacetype"]},
                "base_deviceevent": {"cols": 31, "desc": "设备事件", "key_fields": ["equino", "ipaddr", "taskno"]},
                "base_devicevaribale": {"cols": 28, "desc": "设备变量", "key_fields": ["equino", "ipaddr", "taskno"]},
            },
        },
        "plan": {
            "count": 4, "desc": "生产计划（订单/排产）",
            "key_tables": {
                "plan_ordermanage": {"cols": 50, "desc": "生产订单管理", "key_fields": ["orderno", "productno", "productname", "bitnum", "couplingdegree", "orderstatus", "orderqty"]},
                "plan_scheduling": {"cols": 41, "desc": "排产计划", "key_fields": ["orderno", "productno", "productname", "bitnum", "schedulingstatus"]},
                "plan_schedulingequi": {"cols": 41, "desc": "排产设备", "key_fields": ["orderno", "equino"]},
                "plan_schedulingtask": {"cols": 50, "desc": "排产任务", "key_fields": ["orderno", "taskno", "taskstatus"]},
            },
        },
        "info": {
            "count": 46, "desc": "生产执行信息（批次/追溯/在制品）",
            "key_tables": {
                "info_batchmanage": {"cols": 52, "desc": "批次管理", "key_fields": ["orderno", "taskno", "taskbatchno", "batchstatus", "batchtype"]},
                "info_batchtracein": {"cols": 33, "desc": "批次进站", "key_fields": ["traceorderno", "orderno", "taskbatchno", "trackindatetime", "equino"]},
                "info_batchtrackout": {"cols": 34, "desc": "批次出站", "key_fields": ["traceorderno", "orderno", "taskbatchno", "trackoutdatetime", "equino"]},
                "info_wipinfo": {"cols": 41, "desc": "在制品信息", "key_fields": ["traceorderno", "orderno", "taskbatchno", "inputdatetime", "cabinetno"]},
                "info_batchrework": {"cols": 52, "desc": "批次返工", "key_fields": ["orderno", "taskbatchno", "reworkreason"]},
                "info_batchcheckdata": {"cols": 33, "desc": "批次检验数据", "key_fields": ["orderno", "taskbatchno", "checkresult"]},
                "info_batchmaterialsuse": {"cols": 33, "desc": "批次物料使用", "key_fields": ["orderno", "taskbatchno", "materialsno"]},
                "info_batcwaferlist": {"cols": 44, "desc": "批次晶圆清单", "key_fields": ["orderno", "taskbatchno", "waferno"]},
            },
        },
        "iq": {
            "count": 12, "desc": "来料检验/质量检验",
            "key_tables": {
                "iq_checkresult": {"cols": 44, "desc": "检验结果", "key_fields": ["requestno", "materialsno", "materialsname", "checkresult"]},
                "iq_checkrquest": {"cols": 44, "desc": "检验请求", "key_fields": ["requestno", "materialsno", "materialsname", "requesdate"]},
                "iq_checkproject": {"cols": 28, "desc": "检验项目", "key_fields": ["projectno", "projectname", "pointnum"]},
            },
        },
        "spc": {
            "count": 7, "desc": "统计过程控制",
            "key_tables": {
                "spc_controlchartset": {"cols": 46, "desc": "控制图设置", "key_fields": ["controlchartsetno", "controlchartsetname", "controltype", "subgroupnum"]},
                "spc_project": {"cols": 21, "desc": "SPC 项目", "key_fields": ["projectno", "projectdesc", "cdatatype", "samplenum"]},
                "spc_projectstatihead": {"cols": 26, "desc": "SPC 统计表头"},
                "spc_projectstatidetail": {"cols": 24, "desc": "SPC 统计明细"},
            },
        },
        "wms": {
            "count": 69, "desc": "仓储管理（出入库/库存/盘点）",
            "key_tables": {
                "wms_accessroystockinfo1": {"desc": "入库单"},
                "wms_accessroystockinfo2": {"desc": "出库单"},
                "wms_accessroystockinfo6": {"desc": "盘点单"},
            },
        },
        "act": {"count": 58, "desc": "工作流引擎 (Flowable)"},
        "sys": {"count": 21, "desc": "系统管理（用户/角色/权限/配置）"},
        "plugin": {"count": 18, "desc": "插件（数据大屏/邮件/报表/数据源）"},
        "qrtz": {"count": 11, "desc": "Quartz 调度器"},
        "flw": {"count": 8, "desc": "Flowable 事件引擎"},
        "device": {"count": 2, "desc": "设备通信配置"},
    },
    "quantum_specific_fields": {
        "base_product.bitnum": "比特数量",
        "base_product.couplingdegree": "耦合度",
        "base_product.quantumerrorcorr": "量子纠错",
        "plan_ordermanage.bitnum": "比特数量",
        "plan_ordermanage.couplingdegree": "耦合度",
        "base_waferinfo.fdiameter": "晶圆直径",
        "base_waferinfo.fthickness": "晶圆厚度",
    },
}


def get_db_schema() -> Dict[str, Any]:
    """获取 CHIPMES 完整数据库表结构（401张表）"""
    return CHIPMES_DB_SCHEMA


def query_table_structure(table_name: str) -> Dict[str, Any]:
    """查询指定表的详细结构"""
    for cat_name, cat_info in CHIPMES_DB_SCHEMA["categories"].items():
        if "key_tables" in cat_info:
            for tbl, tbl_info in cat_info["key_tables"].items():
                if tbl == table_name or table_name in tbl:
                    return {"table": tbl, "category": cat_name, **tbl_info}
    return {"error": f"表 {table_name} 未在关键表列表中，数据库共 401 张表",
            "hint": "调用 get_db_schema() 查看完整分类"}
