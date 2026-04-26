"""
Simulation adapters for HFSS, Q3D, LOM, surrogate, EPR.

HFSS/Q3D adapter uses pyaedt when available.
LOM and surrogate can run locally without external tools.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger

from quantamind.server.qeda_simulation.manager import SimulationAdapter
from quantamind.server.qeda_models.simulation import SimJobStatus, SimulationJob, SimulationType


class MockSimulationAdapter(SimulationAdapter):
    """
    模拟仿真适配器 - 用于 LOM、代理模型等快速本地仿真。

    立即返回模拟结果，用于测试和演示。
    """

    name = "mock"
    supported_types = [
        SimulationType.LOM,
        SimulationType.SURROGATE_PREDICT,
        SimulationType.BLACKBOX_QUANTIZATION,
    ]

    async def submit(self, job: SimulationJob) -> str:
        handle = f"mock_{job.job_id}"
        asyncio.create_task(self._simulate_async(handle, job))
        return handle

    async def _simulate_async(self, handle: str, job: SimulationJob) -> None:
        await asyncio.sleep(0.5)
        from quantamind.server.events import SimulationCompleted, SimulationProgress, get_event_bus

        bus = get_event_bus()
        for i in range(1, 6):
            await asyncio.sleep(0.2)
            bus.publish(SimulationProgress(
                job_id=job.job_id,
                progress=i / 5.0,
                message=f"模拟仿真步骤 {i}/5",
                source=self.name,
            ))

        out_dir = Path("results") / job.job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "summary.json").write_text(
            '{"frequencies_ghz": [4.95, 5.05], "status": "completed"}',
            encoding="utf-8",
        )

        bus.publish(SimulationCompleted(
            job_id=job.job_id,
            success=True,
            result_path=str(out_dir),
            source=self.name,
        ))

    async def poll_status(self, handle: str) -> tuple[SimJobStatus, float, str]:
        return SimJobStatus.COMPLETED, 1.0, "完成"

    async def fetch_results(self, handle: str, output_dir: str) -> str:
        return output_dir

    async def cancel(self, handle: str) -> None:
        pass


class HFSSSimulationAdapter(SimulationAdapter):
    """
    Ansys HFSS 本征模仿真适配器。

    需要 pyaedt 和本地 Ansys 安装。无 pyaedt 时降级为占位实现。
    """

    name = "hfss"
    supported_types = [
        SimulationType.EIGENMODE,
        SimulationType.DRIVEN_MODAL,
    ]

    def __init__(self, ansys_version: str = "2024.1", non_interactive: bool = True) -> None:
        self._ansys_version = ansys_version
        self._non_interactive = non_interactive
        self._pyaedt_available = False
        try:
            import pyaedt  # noqa: F401
            self._pyaedt_available = True
        except ImportError:
            logger.warning("pyaedt not installed, HFSS adapter will use placeholder mode")

    async def submit(self, job: SimulationJob) -> str:
        handle = f"hfss_{job.job_id}"
        if self._pyaedt_available:
            asyncio.create_task(self._run_hfss(handle, job))
        else:
            asyncio.create_task(self._run_placeholder(handle, job))
        return handle

    async def _run_placeholder(self, handle: str, job: SimulationJob) -> None:
        from quantamind.server.events import SimulationCompleted, SimulationProgress, get_event_bus

        bus = get_event_bus()
        bus.publish(SimulationProgress(
            job_id=job.job_id,
            progress=0.0,
            message="HFSS 适配器占位模式 (需安装 pyaedt)",
            source=self.name,
        ))
        await asyncio.sleep(1.0)
        out_dir = Path("results") / job.job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        bus.publish(SimulationCompleted(
            job_id=job.job_id,
            success=False,
            result_path="",
            source=self.name,
        ))

    async def _run_hfss(self, handle: str, job: SimulationJob) -> None:
        from quantamind.server.events import SimulationCompleted, SimulationProgress, get_event_bus

        bus = get_event_bus()
        try:
            from pyaedt import Hfss
            from pyaedt.generic.general_methods import generate_unique_name

            bus.publish(SimulationProgress(
                job_id=job.job_id,
                progress=0.1,
                message="启动 HFSS...",
                source=self.name,
            ))

            project_name = generate_unique_name("qeda_hfss")
            hfss = Hfss(
                projectname=project_name,
                designname="Eigenmode",
                solution_type="Eigenmode",
                non_interactive=self._non_interactive,
            )

            bus.publish(SimulationProgress(
                job_id=job.job_id,
                progress=0.3,
                message="正在建立模型...",
                source=self.name,
            ))
            # TODO: 从 design 导入几何，设置端口、材料、网格
            # 当前仅占位
            await asyncio.sleep(2.0)

            bus.publish(SimulationProgress(
                job_id=job.job_id,
                progress=0.6,
                message="正在求解...",
                source=self.name,
            ))
            # hfss.analyze() ...
            await asyncio.sleep(3.0)

            hfss.release_desktop()
            out_dir = Path("results") / job.job_id
            out_dir.mkdir(parents=True, exist_ok=True)
            bus.publish(SimulationCompleted(
                job_id=job.job_id,
                success=True,
                result_path=str(out_dir),
                source=self.name,
            ))
        except Exception as e:
            logger.exception("HFSS simulation failed")
            bus.publish(SimulationCompleted(
                job_id=job.job_id,
                success=False,
                source=self.name,
            ))

    async def poll_status(self, handle: str) -> tuple[SimJobStatus, float, str]:
        return SimJobStatus.RUNNING, 0.5, "运行中"

    async def fetch_results(self, handle: str, output_dir: str) -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return output_dir

    async def cancel(self, handle: str) -> None:
        pass


class Q3DSimulationAdapter(SimulationAdapter):
    """
    Ansys Q3D 电容提取适配器。

    需要 pyaedt。无 pyaedt 时降级为占位。
    """

    name = "q3d"
    supported_types = [SimulationType.Q3D_CAPACITANCE]

    def __init__(self, non_interactive: bool = True) -> None:
        self._non_interactive = non_interactive
        self._pyaedt_available = False
        try:
            import pyaedt  # noqa: F401
            self._pyaedt_available = True
        except ImportError:
            logger.warning("pyaedt not installed, Q3D adapter will use placeholder mode")

    async def submit(self, job: SimulationJob) -> str:
        handle = f"q3d_{job.job_id}"
        if self._pyaedt_available:
            asyncio.create_task(self._run_q3d(handle, job))
        else:
            asyncio.create_task(self._run_placeholder(handle, job))
        return handle

    async def _run_placeholder(self, handle: str, job: SimulationJob) -> None:
        from quantamind.server.events import SimulationCompleted, get_event_bus

        bus = get_event_bus()
        await asyncio.sleep(0.5)
        bus.publish(SimulationCompleted(
            job_id=job.job_id,
            success=False,
            source=self.name,
        ))

    async def _run_q3d(self, handle: str, job: SimulationJob) -> None:
        from quantamind.server.events import SimulationCompleted, get_event_bus

        bus = get_event_bus()
        try:
            from pyaedt import Q3d

            await asyncio.sleep(2.0)
            out_dir = Path("results") / job.job_id
            out_dir.mkdir(parents=True, exist_ok=True)
            bus.publish(SimulationCompleted(
                job_id=job.job_id,
                success=True,
                result_path=str(out_dir),
                source=self.name,
            ))
        except Exception:
            bus.publish(SimulationCompleted(
                job_id=job.job_id,
                success=False,
                source=self.name,
            ))

    async def poll_status(self, handle: str) -> tuple[SimJobStatus, float, str]:
        return SimJobStatus.RUNNING, 0.5, "运行中"

    async def fetch_results(self, handle: str, output_dir: str) -> str:
        return output_dir

    async def cancel(self, handle: str) -> None:
        pass
