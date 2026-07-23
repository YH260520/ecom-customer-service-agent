import asyncio
import logging
from typing import Optional
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger("MCPClientManager")
logging.basicConfig(level=logging.INFO)


class MCPClientManager:
    """
    管理 MCP 客户端连接,并在连接失败时自动降级为本地工具。

    核心能力:
    1. 带超时的连接尝试,避免 MCP 服务卡住拖垂整个 Agent
    2. 连接失败自动降级为本地工具,保证业务连续性
    3. 后台定期尝试重新连接 MCP,恢复后自动切换回来
    """

    def __init__(
        self,
        mcp_server_config: dict,
        local_fallback_tools: list[BaseTool],
        connect_timeout: float = 5.0,
        max_retries: int = 2,
        retry_interval: float = 2.0,
        health_check_interval: float = 60.0,
    ):
        self.mcp_server_config = mcp_server_config
        self.local_fallback_tools = local_fallback_tools
        self.connect_timeout = connect_timeout
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.health_check_interval = health_check_interval

        self._client: Optional[MultiServerMCPClient] = None
        self._cached_tools: list[BaseTool] = []
        self._mcp_available: bool = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    # ------------------------
    # 核心:尝试连接 MCP,失败则降级
    # ------------------------
    async def _try_connect_mcp(self) -> Optional[list[BaseTool]]:
        """尝试连接 MCP 服务器并获取工具列表,带超时和重试。返回 None 表示彻底失败。"""
        client = MultiServerMCPClient(self.mcp_server_config)

        for attempt in range(1, self.max_retries + 1):
            try:
                tools = await asyncio.wait_for(
                    client.get_tools(), timeout=self.connect_timeout
                )
                if not tools:
                    raise RuntimeError("MCP 服务器返回空工具列表")

                self._client = client
                logger.info(f"✅ MCP 连接成功,获取到 {len(tools)} 个工具")
                return tools

            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(
                    f"⚠️ MCP 连接尝试 {attempt}/{self.max_retries} 失败: {type(e).__name__}: {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_interval)

        logger.error("❌ MCP 连接彻底失败,已达最大重试次数,将降级为本地工具")
        return None

    # ------------------------
    # 对外统一接口:获取当前可用的工具列表
    # ------------------------
    async def get_tools(self, force_refresh: bool = False) -> list[BaseTool]:
        """
        获取工具列表。优先返回 MCP 工具,失败时自动降级为本地工具。
        force_refresh=True 时会强制重新尝试连接 MCP(用于健康检查恢复场景)。
        """
        async with self._lock:
            if self._cached_tools and not force_refresh:
                return self._cached_tools

            mcp_tools = await self._try_connect_mcp()

            if mcp_tools is not None:
                self._mcp_available = True
                self._cached_tools = mcp_tools
            else:
                self._mcp_available = False
                self._cached_tools = self.local_fallback_tools
                logger.info(f"🔄 已切换为本地降级工具,共 {len(self._cached_tools)} 个")

            return self._cached_tools

    @property
    def is_mcp_available(self) -> bool:
        return self._mcp_available

    # ------------------------
    # 后台健康检查:定期尝试恢复 MCP 连接
    # ------------------------
    async def _health_check_loop(self):
        while True:
            await asyncio.sleep(self.health_check_interval)
            if not self._mcp_available:
                logger.info("🔍 当前处于降级模式,尝试恢复 MCP 连接...")
                await self.get_tools(force_refresh=True)
            else:
                logger.debug("💚 MCP 当前状态健康,跳过恢复检查")

    def start_health_check(self):
        """启动后台健康检查任务,建议在应用启动时调用一次。"""
        if self._health_check_task is None or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info(f"🩺 健康检查已启动,每 {self.health_check_interval}s 检查一次")

    def stop_health_check(self):
        """停止后台健康检查任务,建议在应用关闭时调用。"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            logger.info("🛑 健康检查已停止")

    # ------------------------
    # 支持 async with 用法
    # ------------------------
    async def __aenter__(self):
        await self.get_tools()
        self.start_health_check()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop_health_check()
