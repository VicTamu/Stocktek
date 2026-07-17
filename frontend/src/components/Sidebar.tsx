import {
  BarChart3,
  BookOpen,
  Database,
  History,
  HardDrive,
  LayoutDashboard,
  Settings,
} from "lucide-react";

const items = [
  { label: "Watchlist", icon: LayoutDashboard, active: true },
  { label: "Signals", icon: BarChart3, active: false },
  { label: "Research", icon: BookOpen, active: false },
  { label: "Backtests", icon: History, active: false },
  { label: "Settings", icon: Settings, active: false },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <span />
          <span />
          <span />
        </div>
        <div>
          <strong>StockTek</strong>
          <span>V1 local analyst</span>
        </div>
      </div>

      <nav className="nav-list" aria-label="Primary navigation">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button className={item.active ? "nav-item active" : "nav-item"} key={item.label}>
              <Icon size={18} strokeWidth={2} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-cards">
        <div className="sidebar-card">
          <div>
            <Database size={16} />
            <span>Data status</span>
          </div>
          <strong>Daily-close research</strong>
          <p>Free sources, cached locally, reviewed after market close.</p>
        </div>

        <div className="sidebar-card">
          <div>
            <HardDrive size={16} />
            <span>Storage</span>
          </div>
          <strong>Local DuckDB cache</strong>
          <div className="storage-meter">
            <span />
          </div>
          <p>No broker connection or auto-trading in V1.</p>
        </div>
      </div>
    </aside>
  );
}
