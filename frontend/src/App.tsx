import { NavLink, Route, Routes } from "react-router-dom";
import { BookOpen, FlaskConical, LayoutDashboard } from "lucide-react";
import { Dashboard } from "./pages/Dashboard";
import { KnowledgeBase } from "./pages/KnowledgeBase";
import { ResearchDetail } from "./pages/ResearchDetail";
import { cn } from "./lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  exact?: boolean;
}

const navItems: NavItem[] = [
  { to: "/", label: "研究台", icon: LayoutDashboard, exact: true },
  { to: "/knowledge", label: "知识库", icon: BookOpen },
];

/** 应用外壳：左侧图标导航 + 右侧内容区 */
export default function App() {
  return (
    <div className="flex h-screen bg-[var(--rc-bg)] text-[var(--rc-text)]">
      {/* 左侧导航 */}
      <aside className="flex w-64 flex-col border-r border-white/5 bg-[var(--rc-surface)]">
        <div className="flex h-16 items-center gap-3 px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 shadow-lg shadow-indigo-500/20">
            <FlaskConical className="h-5 w-5 text-white" />
          </div>
          <div className="leading-tight">
            <h1 className="text-base font-bold tracking-tight text-slate-100">智研助手</h1>
            <p className="text-[10px] font-medium text-slate-500">Research Copilot</p>
          </div>
        </div>

        <nav className="mt-6 flex flex-1 flex-col gap-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              className={({ isActive }) =>
                cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-indigo-500/15 text-indigo-300 shadow-sm ring-1 ring-inset ring-indigo-500/20"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200",
                )
              }
            >
              <item.icon className="h-4 w-4 transition-transform group-hover:scale-110" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/5 p-4">
          <div className="flex items-center gap-3 rounded-xl bg-white/5 p-3">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-emerald-400 to-cyan-400 shadow-sm" />
            <div className="min-w-0">
              <p className="truncate text-xs font-medium text-slate-200">研究者</p>
              <p className="truncate text-[10px] text-slate-500">Pro Plan</p>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-white/5 bg-[var(--rc-surface)]/50 px-6 backdrop-blur">
          <h2 className="text-sm font-semibold text-slate-200">控制台</h2>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
            服务正常
          </div>
        </header>

        <main className="custom-scrollbar flex-1 overflow-auto bg-gradient-to-br from-[var(--rc-bg)] to-[var(--rc-surface)] p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/research/:id" element={<ResearchDetail />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
            <Route path="*" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
