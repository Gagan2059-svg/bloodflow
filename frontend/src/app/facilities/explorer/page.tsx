"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ActivitySquare, Map, Box, Activity, ShieldAlert, CheckCircle2, TrendingUp, GitPullRequest, BarChart2, FileJson, RefreshCw, Search } from "lucide-react";
import { getInventory } from "@/lib/api";

const NAV = [
  { href: "/", icon: Activity, label: "Command Center" },
  { href: "/network", icon: Map, label: "Facility Map" },
  { href: "/facilities/explorer", icon: Box, label: "Inventory Explorer", active: true },
  { href: "/simulator", icon: GitPullRequest, label: "Digital Twin" },
  { href: "/forecasts", icon: TrendingUp, label: "Forecasts" },
  { href: "/analytics", icon: BarChart2, label: "Analytics" },
  { href: "/alerts", icon: ShieldAlert, label: "Alerts & Events" },
  { href: "/recommendations", icon: CheckCircle2, label: "AI Recommendations" },
  { href: "/audit", icon: FileJson, label: "Audit Logs" },
];

const STATUS_COLORS: Record<string, string> = {
  AVAILABLE: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  RESERVED: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  IN_TRANSIT: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  EXPIRED: "bg-destructive/10 text-destructive border-destructive/20",
  USED: "bg-muted text-muted-foreground border-border",
};

export default function InventoryExplorerPage() {
  const [inventory, setInventory] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [bloodGroup, setBloodGroup] = useState("");
  const [component, setComponent] = useState("");
  const [status, setStatus] = useState("AVAILABLE");
  const PAGE_SIZE = 50;

  const load = async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: PAGE_SIZE };
      if (bloodGroup) params.blood_group = bloodGroup;
      if (component) params.component = component;
      if (status) params.status = status;
      const data = await getInventory(params);
      setInventory(data.items || []);
      setTotal(data.total || 0);
    } catch (e) {}
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [page, bloodGroup, component, status]);

  const isExpiringSoon = (expDate: string) => {
    const diff = new Date(expDate).getTime() - Date.now();
    return diff > 0 && diff < 72 * 3600 * 1000;
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <aside className="w-64 border-r border-border bg-sidebar flex flex-col shrink-0">
        <div className="h-14 flex items-center px-4 font-semibold text-lg border-b border-border text-primary">
          <ActivitySquare className="mr-2 h-5 w-5" /> BloodFlow
        </div>
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {NAV.map(n => (
            <Link key={n.href} href={n.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${n.active ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"}`}>
              <n.icon className="h-4 w-4" /> {n.label}
            </Link>
          ))}
        </nav>
      </aside>

      <main className="flex-1 overflow-y-auto flex flex-col">
        <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-card/50 backdrop-blur shrink-0">
          <h1 className="text-sm font-medium text-muted-foreground">Facilities / <span className="text-foreground">Inventory Explorer</span></h1>
          <div className="flex items-center gap-3">
            <a href="http://localhost:8000/api/v1/inventory/export/csv" target="_blank"
              className="text-xs text-primary hover:underline">Export CSV</a>
            <button onClick={load} className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"><RefreshCw className="h-3.5 w-3.5" /></button>
          </div>
        </header>

        <div className="p-6 flex flex-col flex-1 gap-4 min-h-0">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Inventory Explorer</h2>
            <p className="text-sm text-muted-foreground mt-1">{total.toLocaleString()} total units in your network</p>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            <select value={bloodGroup} onChange={e => { setBloodGroup(e.target.value); setPage(1); }}
              className="bg-background border border-input rounded-lg px-3 py-2 text-sm">
              <option value="">All Blood Groups</option>
              {["O+","O-","A+","A-","B+","B-","AB+","AB-"].map(g => <option key={g} value={g}>{g}</option>)}
            </select>
            <select value={component} onChange={e => { setComponent(e.target.value); setPage(1); }}
              className="bg-background border border-input rounded-lg px-3 py-2 text-sm">
              <option value="">All Components</option>
              {["RBC","PLASMA","PLATELETS","WHOLE_BLOOD","CRYOPRECIPITATE"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}
              className="bg-background border border-input rounded-lg px-3 py-2 text-sm">
              <option value="">All Statuses</option>
              {["AVAILABLE","RESERVED","IN_TRANSIT","USED","EXPIRED"].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div className="border border-border bg-card rounded-xl overflow-hidden flex flex-col flex-1 min-h-0">
            <div className="overflow-auto flex-1">
              {loading ? (
                <div className="p-6 space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="h-10 animate-pulse bg-muted rounded" />)}</div>
              ) : inventory.length === 0 ? (
                <div className="p-12 text-center text-muted-foreground">No inventory units found for these filters.</div>
              ) : (
                <table className="w-full text-sm text-left">
                  <thead className="text-xs uppercase bg-muted/50 border-b border-border text-muted-foreground sticky top-0">
                    <tr>
                      <th className="px-5 py-3 font-medium">Blood Group</th>
                      <th className="px-5 py-3 font-medium">Component</th>
                      <th className="px-5 py-3 font-medium">Status</th>
                      <th className="px-5 py-3 font-medium">Expires</th>
                      <th className="px-5 py-3 font-medium">Vol (mL)</th>
                      <th className="px-5 py-3 font-medium">Location</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {inventory.map((u: any) => (
                      <tr key={u.id} className={`hover:bg-muted/30 transition-colors ${isExpiringSoon(u.expiration_date) ? "bg-amber-500/5" : ""}`}>
                        <td className="px-5 py-3 font-bold text-primary">{u.blood_group}</td>
                        <td className="px-5 py-3">{u.component}</td>
                        <td className="px-5 py-3">
                          <span className={`border text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[u.status] || "bg-muted text-muted-foreground"}`}>{u.status}</span>
                        </td>
                        <td className={`px-5 py-3 text-xs ${isExpiringSoon(u.expiration_date) ? "text-amber-600 font-semibold" : "text-muted-foreground"}`}>
                          {new Date(u.expiration_date).toLocaleDateString()}
                          {isExpiringSoon(u.expiration_date) && " ⚠"}
                        </td>
                        <td className="px-5 py-3 text-muted-foreground">{u.quantity_ml}</td>
                        <td className="px-5 py-3 text-muted-foreground">{u.storage_location || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            {/* Pagination */}
            <div className="border-t border-border px-5 py-3 flex items-center justify-between bg-muted/20">
              <span className="text-xs text-muted-foreground">Page {page} of {Math.max(1, Math.ceil(total / PAGE_SIZE))}</span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                  className="text-xs px-3 py-1.5 border border-border rounded-md disabled:opacity-40 hover:bg-accent">Prev</button>
                <button disabled={page >= Math.ceil(total / PAGE_SIZE)} onClick={() => setPage(p => p + 1)}
                  className="text-xs px-3 py-1.5 border border-border rounded-md disabled:opacity-40 hover:bg-accent">Next</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
