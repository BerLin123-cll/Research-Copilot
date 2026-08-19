import { useEffect } from "react";
import { useResearchStore } from "../stores/researchStore";

/**
 * 连接研究任务的实时事件流：
 * - 页面挂载时 connectWS，卸载时 disconnectWS
 * - 断线后自动重连，最多重试 3 次
 * @param taskId 研究任务 ID（为空时不建立连接）
 * @returns 当前是否已连接
 */
export function useWebSocket(taskId: string): boolean {
  const connectWS = useResearchStore((s) => s.connectWS);
  const disconnectWS = useResearchStore((s) => s.disconnectWS);
  const wsConnected = useResearchStore((s) => s.wsConnected);

  useEffect(() => {
    if (!taskId) return;

    const MAX_ATTEMPTS = 3;
    let attempts = 0;

    const connect = () => {
      attempts += 1;
      connectWS(taskId);
    };

    // 首次连接
    connect();

    // 轮询检测断线并自动重连
    const timer = window.setInterval(() => {
      const st = useResearchStore.getState();
      if (st.wsConnected || st.activeTaskId !== taskId) {
        attempts = 0;
        return;
      }
      if (attempts < MAX_ATTEMPTS) connect();
    }, 3000);

    return () => {
      window.clearInterval(timer);
      disconnectWS();
    };
  }, [taskId, connectWS, disconnectWS]);

  return wsConnected;
}
