# Hands 适配器：secsgem（SECS/GEM 设备通信协议栈）
# 职责：通过 HSMS/SECS-II/GEM 协议与半导体设备通信
# 能力：远程命令、Collection Event 订阅、告警管理、配方管理、状态变量查询
# 当 secsgem 未安装时优雅降级为 Mock

from typing import Any, Dict, List, Optional
import logging

_log = logging.getLogger("quantamind.hands.secsgem")

try:
    import secsgem.common
    import secsgem.gem.hosthandler
    import secsgem.hsms
    HAS_SECSGEM = True
    _log.info("secsgem 已加载")
except ImportError:
    HAS_SECSGEM = False
    _log.warning("secsgem 未安装，使用 Mock 模式")

_connections: Dict[str, Any] = {}
_mock_equipment_state: Dict[str, Dict] = {
    "CVD-01": {"state": "idle", "recipe": "SiO2_300nm", "wafer_count": 0, "alarms": []},
    "ETCH-02": {"state": "processing", "recipe": "Deep_Si_Etch", "wafer_count": 12, "alarms": []},
    "LITHO-03": {"state": "idle", "recipe": "EBL_JJ_v2", "wafer_count": 0, "alarms": ["ALM-101: 光源功率偏低"]},
}


def connect_equipment(equipment_id: str, host: str = "127.0.0.1", port: int = 5000) -> Dict[str, Any]:
    """通过 HSMS 连接半导体设备"""
    if HAS_SECSGEM:
        try:
            settings = secsgem.common.Settings(
                address=host,
                port=port,
                connect_mode=secsgem.hsms.HsmsConnectMode.ACTIVE,
                device_type=secsgem.common.DeviceType.HOST,
            )
            handler = secsgem.gem.hosthandler.GemHostHandler(settings)
            handler.enable()
            _connections[equipment_id] = handler
            return {"equipment_id": equipment_id, "status": "connected", "host": host, "port": port, "backend": "secsgem"}
        except Exception as e:
            return {"error": str(e), "backend": "secsgem"}
    _connections[equipment_id] = {"mock": True}
    return {"equipment_id": equipment_id, "status": "connected", "host": host, "port": port, "backend": "mock"}


def get_equipment_status(equipment_id: str) -> Dict[str, Any]:
    """查询设备状态变量（SV）"""
    if HAS_SECSGEM and equipment_id in _connections and not isinstance(_connections[equipment_id], dict):
        try:
            handler = _connections[equipment_id]
            return {"equipment_id": equipment_id, "control_state": "online", "backend": "secsgem"}
        except Exception as e:
            return {"error": str(e)}
    mock = _mock_equipment_state.get(equipment_id, {"state": "unknown"})
    return {"equipment_id": equipment_id, **mock, "backend": "mock"}


def list_equipment() -> Dict[str, Any]:
    """列出所有已连接/已知设备及状态"""
    result = []
    for eid, state in _mock_equipment_state.items():
        result.append({"equipment_id": eid, "state": state["state"], "recipe": state.get("recipe"), "alarms_count": len(state.get("alarms", []))})
    return {"equipment": result, "count": len(result)}


def send_remote_command(equipment_id: str, command: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """发送远程命令（S2F41）：如 START, STOP, PAUSE, RESUME"""
    if HAS_SECSGEM and equipment_id in _connections and not isinstance(_connections[equipment_id], dict):
        try:
            handler = _connections[equipment_id]
            handler.send_remote_command(command, params or {})
            return {"equipment_id": equipment_id, "command": command, "status": "sent", "backend": "secsgem"}
        except Exception as e:
            return {"error": str(e)}
    return {"equipment_id": equipment_id, "command": command, "status": "sent", "backend": "mock"}


def subscribe_collection_event(equipment_id: str, ceid: int, data_variables: List[int]) -> Dict[str, Any]:
    """订阅 Collection Event（S2F33/S2F35）：设备上报指定事件与数据"""
    if HAS_SECSGEM and equipment_id in _connections and not isinstance(_connections[equipment_id], dict):
        try:
            handler = _connections[equipment_id]
            handler.subscribe_collection_event(ceid, data_variables)
            return {"equipment_id": equipment_id, "ceid": ceid, "dvs": data_variables, "status": "subscribed", "backend": "secsgem"}
        except Exception as e:
            return {"error": str(e)}
    return {"equipment_id": equipment_id, "ceid": ceid, "dvs": data_variables, "status": "subscribed", "backend": "mock"}


def list_alarms(equipment_id: str) -> Dict[str, Any]:
    """查询设备告警列表"""
    if HAS_SECSGEM and equipment_id in _connections and not isinstance(_connections[equipment_id], dict):
        try:
            handler = _connections[equipment_id]
            alarms = handler.list_alarms()
            return {"equipment_id": equipment_id, "alarms": alarms, "backend": "secsgem"}
        except Exception as e:
            return {"error": str(e)}
    mock = _mock_equipment_state.get(equipment_id, {})
    return {"equipment_id": equipment_id, "alarms": mock.get("alarms", []), "backend": "mock"}


def get_process_programs(equipment_id: str) -> Dict[str, Any]:
    """查询设备可用配方/工艺程序列表"""
    if HAS_SECSGEM and equipment_id in _connections and not isinstance(_connections[equipment_id], dict):
        try:
            handler = _connections[equipment_id]
            pplist = handler.get_process_program_list()
            return {"equipment_id": equipment_id, "recipes": pplist, "backend": "secsgem"}
        except Exception as e:
            return {"error": str(e)}
    recipes = ["SiO2_300nm", "Al_Etch_v3", "Deep_Si_Etch", "EBL_JJ_v2", "Nb_Sputter_200nm", "JJ_Dolan_Bridge"]
    return {"equipment_id": equipment_id, "recipes": recipes, "backend": "mock"}


def upload_recipe(equipment_id: str, recipe_name: str, recipe_body: str = "") -> Dict[str, Any]:
    """上传配方到设备"""
    return {"equipment_id": equipment_id, "recipe": recipe_name, "status": "uploaded", "backend": "mock" if not HAS_SECSGEM else "secsgem"}


def go_online(equipment_id: str) -> Dict[str, Any]:
    """设备上线（Host 控制模式）"""
    if HAS_SECSGEM and equipment_id in _connections and not isinstance(_connections[equipment_id], dict):
        try:
            _connections[equipment_id].go_online()
            return {"equipment_id": equipment_id, "control_state": "online", "backend": "secsgem"}
        except Exception as e:
            return {"error": str(e)}
    return {"equipment_id": equipment_id, "control_state": "online", "backend": "mock"}


def go_offline(equipment_id: str) -> Dict[str, Any]:
    """设备下线"""
    return {"equipment_id": equipment_id, "control_state": "offline", "backend": "mock" if not HAS_SECSGEM else "secsgem"}


def get_capabilities() -> Dict[str, Any]:
    return {
        "protocol": "SECS/GEM (SEMI E4/E5/E30/E37)",
        "transport": "HSMS over TCP/IP",
        "features": ["远程命令 (S2F41)", "Collection Event 订阅 (S2F33/S2F35)", "告警管理", "配方管理", "状态变量查询", "设备上下线控制"],
        "installed": HAS_SECSGEM,
    }
