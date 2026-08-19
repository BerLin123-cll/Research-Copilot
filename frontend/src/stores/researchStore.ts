import { create } from "zustand";
import type { AgentEvent, Report, ResearchTask } from "../types";
import { api } from "../lib/api";

/** 计算 WebSocket 地址：优先 VITE_WS_BASE，否则推导自当前页面地址 */
function wsUrlFor(taskId: string): string {
  const base = import.meta.env.VITE_WS_BASE;
  const resolved =
    base && base.length > 0
      ? base
      : (location.protocol === "https:" ? "wss://" : "ws://") + location.host;
  return `${resolved.replace(/\/+$/, "")}/ws/research/${taskId}`;
}

/** 模块级 WebSocket 引用（无需序列化进 store 状态） */
let socket: WebSocket | null = null;

/** 将任务合并/插入到列表头部 */
function upsertTask(list: ResearchTask[], task: ResearchTask): ResearchTask[] {
  const idx = list.findIndex((t) => t.id === task.id);
  if (idx === -1) return [task, ...list];
  const next = [...list];
  next[idx] = task;
  return next;
}

const TASK_STATUSES: ResearchTask["status"][] = ["pending", "running", "completed", "failed"];

interface ResearchStore {
  tasks: ResearchTask[];
  tasksLoading: boolean;
  currentTask: ResearchTask | null;
  events: AgentEvent[];
  wsConnected: boolean;
  activeTaskId: string | null;

  fetchTasks: () => Promise<void>;
  fetchTask: (id: string) => Promise<ResearchTask | null>;
  createResearch: (topic: string) => Promise<ResearchTask | null>;
  deleteResearch: (id: string) => Promise<boolean>;
  fetchReport: (taskId: string) => Promise<Report | null>;
  connectWS: (taskId: string) => void;
  disconnectWS: () => void;
  handleEvent: (ev: AgentEvent) => void;
  clearEvents: () => void;
}

export const useResearchStore = create<ResearchStore>()((set, get) => ({
  tasks: [],
  tasksLoading: false,
  currentTask: null,
  events: [],
  wsConnected: false,
  activeTaskId: null,

  fetchTasks: async () => {
    set({ tasksLoading: true });
    try {
      const tasks = await api.listResearch(50, 0);
      set({ tasks });
    } catch {
      /* 静默失败，页面展示空态 */
    } finally {
      set({ tasksLoading: false });
    }
  },

  fetchTask: async (id) => {
    try {
      const task = await api.getResearch(id);
      set({ currentTask: task, tasks: upsertTask(get().tasks, task) });
      return task;
    } catch {
      return null;
    }
  },

  createResearch: async (topic) => {
    try {
      const task = await api.createResearch(topic);
      set({ tasks: upsertTask(get().tasks, task), currentTask: task });
      return task;
    } catch {
      return null;
    }
  },

  deleteResearch: async (id) => {
    try {
      await api.deleteResearch(id);
      set({ tasks: get().tasks.filter((t) => t.id !== id) });
      return true;
    } catch {
      return false;
    }
  },

  fetchReport: async (taskId) => {
    try {
      return await api.getReport(taskId);
    } catch {
      return null;
    }
  },

  connectWS: (taskId) => {
    // 已连接同一任务时复用现有连接
    if (socket && get().activeTaskId === taskId) return;

    get().disconnectWS();
    set({ activeTaskId: taskId, events: [], wsConnected: false });

    let s: WebSocket;
    try {
      s = new WebSocket(wsUrlFor(taskId));
    } catch {
      set({ wsConnected: false });
      return;
    }
    socket = s;

    s.onopen = () => set({ wsConnected: true });
    s.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data as string) as AgentEvent;
        get().handleEvent(ev);
      } catch {
        /* 忽略无法解析的消息 */
      }
    };
    s.onerror = () => set({ wsConnected: false });
    s.onclose = () => {
      set({ wsConnected: false });
      if (socket === s) socket = null;
    };
  },

  disconnectWS: () => {
    if (socket) {
      try {
        socket.onclose = null;
        socket.close();
      } catch {
        /* noop */
      }
      socket = null;
    }
    set({ wsConnected: false, activeTaskId: null });
  },

  handleEvent: (ev) => {
    switch (ev.type) {
      case "snapshot": {
        set({ currentTask: ev.task, tasks: upsertTask(get().tasks, ev.task) });
        break;
      }
      case "status": {
        set({ events: [...get().events, ev] });
        const t = get().currentTask;
        if (t && TASK_STATUSES.includes(ev.status as ResearchTask["status"])) {
          const updated: ResearchTask = { ...t, status: ev.status as ResearchTask["status"] };
          set({ currentTask: updated, tasks: upsertTask(get().tasks, updated) });
        }
        break;
      }
      case "plan": {
        set({ events: [...get().events, ev] });
        const t = get().currentTask;
        if (t) {
          const updated: ResearchTask = { ...t, plan: ev.steps };
          set({ currentTask: updated, tasks: upsertTask(get().tasks, updated) });
        }
        break;
      }
      case "node_start":
      case "node_end":
      case "tool_call":
      case "tool_result":
      case "analysis":
        set({ events: [...get().events, ev] });
        break;
      case "report_ready": {
        set({ events: [...get().events, ev] });
        const t = get().currentTask;
        if (t) {
          const updated: ResearchTask = { ...t, report_id: ev.report_id };
          set({ currentTask: updated, tasks: upsertTask(get().tasks, updated) });
        }
        // 刷新任务详情以同步最新报告 ID
        const tid = get().activeTaskId ?? t?.id;
        if (tid) void get().fetchTask(tid);
        break;
      }
      case "error": {
        set({ events: [...get().events, ev] });
        const t = get().currentTask;
        if (t) {
          const updated: ResearchTask = { ...t, error: ev.message, status: "failed" };
          set({ currentTask: updated, tasks: upsertTask(get().tasks, updated) });
        }
        break;
      }
      case "done": {
        set({ events: [...get().events, ev] });
        void get().fetchTask(ev.task_id);
        break;
      }
    }
  },

  clearEvents: () => set({ events: [] }),
}));
