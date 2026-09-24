"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ActivitySquare, Map, Box, Activity, ShieldAlert, CheckCircle2, TrendingUp, GitPullRequest, BarChart2, FileJson, RefreshCw } from "lucide-react";
import { getAlerts, acknowledgeAlert, resolveAlert } from "@/lib/api";

const NAV = [
  { href: "/", icon: Activity, label: "Command Center" },
  { href: "/network", icon: Map, label: "Facility Map" },
  { href: "/facilities/explorer", icon: Box, label: "Inventory Explorer" },
  { href: "/simulator", icon: GitPullRequest, label: "Digital Twin" },
  { href: "/forecasts", icon: TrendingUp, label: "Forecasts" },
  { href: "/analytics", icon: BarChart2, label: "Analytics" },
  { href: "/alerts", icon: ShieldAlert, label: "Alerts & Events", active: true },
  { href: "/recommendations", icon: CheckCircle2, label: "AI Recommendations" },
  { href: "/audit", icon: FileJson, label: "Audit Logs" },
];

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "bg-destructive/10 text-destructive",
  HIGH: "bg-destructive/10 text-destructive",
  WARNING: "bg-amber-500/10 text-amber-600",
  INFO: "bg-primary/10 text-primary",
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("OPEN");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filter !== "ALL") params.status = filter;
      const data = await getAlerts(params);
      setAlerts(Array.isArray(data) ? data : []);
    } catch (e) {}
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleAck = async (id: string) => {
    setActionLoading(id + "_ack");
    try { await acknowledgeAlert(id); await load(); } finally { setActionLoading(null); }
  };

  const handleResolve = async (id: string) => {
    setActionLoading(id + "_resolve");
    try { await resolveAlert(id); await load(); } finally { setActionLoading(null); }
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
          <h1 className="text-sm font-medium text-muted-foreground">Operations / <span className="text-foreground">Alerts</span></h1>
          <button onClick={load} className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"><RefreshCw className="h-3.5 w-3.5" /> Refresh</button>
        </header>

        <div className="p-6 max-w-5xl mx-auto w-full flex-1 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-semibold">Alerts & Events</h2>
              <p className="text-sm text-muted-foreground mt-1">Network anomalies and system events ({alerts.length} shown)</p>
            </div>
            <div className="flex gap-2">
              {["ALL", "OPEN", "ACKNOWLEDGED", "RESOLVED"].map(s => (
                <button key={s} onClick={() => setFilter(s)}
                  className={`text-xs px-3 py-1.5 rounded-md font-medium transition-colors ${filter === s ? "bg-primary text-primary-foreground" : "border border-border hover:bg-accent text-muted-foreground"}`}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="border border-border rounded-xl bg-card overflow-hidden flex-1">
            {loading ? (
              <div className="p-6 space-y-3">{[1,2,3,4].map(i => <div key={i} className="h-12 animate-pulse bg-muted rounded" />)}</div>
            ) : alerts.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground">No alerts found for this filter.</div>
            ) : (
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-muted/50 border-b border-border text-muted-foreground">
                  <tr>
                    <th className="px-5 py-3 font-medium">Severity</th>
                    <th className="px-5 py-3 font-medium">Title</th>
                    <th className="px-5 py-3 font-medium">Type</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Created</th>
                    <th className="px-5 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {alerts.map((a: any) => (
                    <tr key={a.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-5 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${SEVERITY_COLORS[a.severity] || "bg-muted text-muted-foreground"}`}>{a.severity}</span>
                      </td>
                      <td className="px-5 py-3">
                        <div className="font-medium">{a.title}</div>
                        <div className="text-xs text-muted-foreground">{a.description?.slice(0, 60)}</div>
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">{a.alert_type}</td>
                      <td className="px-5 py-3">
                        <span className="text-xs border border-border px-2 py-0.5 rounded-full">{a.status}</span>
                      </td>
                      <td className="px-5 py-3 text-muted-foreground text-xs">{new Date(a.created_at).toLocaleString()}</td>
                      <td className="px-5 py-3">
                        <div className="flex gap-2">
                          {a.status === "OPEN" && (
                            <button onClick={() => handleAck(a.id)} disabled={actionLoading === a.id + "_ack"}
                              className="text-xs text-primary hover:underline">Ack</button>
                          )}
                          {a.status !== "RESOLVED" && (
                            <button onClick={() => handleResolve(a.id)} disabled={actionLoading === a.id + "_resolve"}
                              className="text-xs text-muted-foreground hover:text-foreground hover:underline">Resolve</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
