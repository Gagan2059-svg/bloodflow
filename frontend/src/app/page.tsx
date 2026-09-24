"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ActivitySquare, Map, Box, Activity, ShieldAlert, CheckCircle2, TrendingUp, GitPullRequest, BarChart2, FileJson, AlertTriangle, Droplets, RefreshCw, ArrowRight } from "lucide-react";
import { getNetworkRisk, getInventorySummary, getAlerts, getRecommendations, runOptimizer } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const NAV = [
  { href: "/", icon: Activity, label: "Command Center", active: true },
  { href: "/network", icon: Map, label: "Facility Map" },
  { href: "/facilities/explorer", icon: Box, label: "Inventory Explorer" },
  { href: "/simulator", icon: GitPullRequest, label: "Digital Twin" },
  { href: "/forecasts", icon: TrendingUp, label: "Forecasts" },
  { href: "/analytics", icon: BarChart2, label: "Analytics" },
  { href: "/alerts", icon: ShieldAlert, label: "Alerts & Events" },
  { href: "/recommendations", icon: CheckCircle2, label: "AI Recommendations" },
  { href: "/audit", icon: FileJson, label: "Audit Logs" },
];

function Sidebar({ active = "/" }) {
  return (
    <aside className="w-64 border-r border-border bg-sidebar flex flex-col shrink-0">
      <div className="h-14 flex items-center px-4 font-semibold text-lg border-b border-border text-primary">
        <ActivitySquare className="mr-2 h-5 w-5" /> BloodFlow
      </div>
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {NAV.map((n) => (
          <Link key={n.href} href={n.href}
            className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${n.href === active ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"}`}>
            <n.icon className="h-4 w-4" /> {n.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

export default function CommandCenter() {
  const [risk, setRisk] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [riskData, sumData, alertsData, recsData] = await Promise.all([
        getNetworkRisk(),
        getInventorySummary(),
        getAlerts({ status: "OPEN" }),
        getRecommendations({ status: "PENDING" }),
      ]);
      setRisk(riskData);
      setSummary(sumData);
      setAlerts(Array.isArray(alertsData) ? alertsData.slice(0, 5) : []);
      setRecs(Array.isArray(recsData) ? recsData.slice(0, 3) : []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleRunOptimizer = async () => {
    setOptimizing(true);
    try {
      await runOptimizer();
      setTimeout(load, 2000); // Reload after background task processes
    } catch(e) {}
    finally { setOptimizing(false); }
  };

  const facilities = risk?.facilities || [];
  const criticalFacilities = facilities.filter((f: any) => f.shortage_risk?.probability > 0.6);
  const totalAvailable = summary?.kpis?.total_available ?? 0;
  const expiring72h = summary?.kpis?.expiring_within_72h ?? 0;

  // Chart data for facility risk
  const chartData = facilities.slice(0, 8).map((f: any) => ({
    name: f.facility_name?.split(" ").slice(0, 2).join(" ") || "Facility",
    shortage: Math.round((f.shortage_risk?.probability || 0) * 100),
    wastage: Math.round((f.wastage_risk?.probability || 0) * 100),
  }));

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar active="/" />
      <main className="flex-1 overflow-y-auto flex flex-col">
        <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-card/50 backdrop-blur shrink-0">
          <h1 className="text-sm font-medium text-muted-foreground">BloodFlow / <span className="text-foreground">Command Center</span></h1>
          <div className="flex items-center gap-3">
            <button onClick={load} className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors">
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
            <button onClick={handleRunOptimizer} disabled={optimizing}
              className="flex items-center gap-2 bg-primary text-primary-foreground text-xs px-3 py-1.5 rounded-md font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
              {optimizing ? "Running..." : "Run Optimizer"}
            </button>
          </div>
        </header>

        <div className="p-6 space-y-6 max-w-7xl mx-auto w-full flex-1">
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm px-4 py-3 rounded-lg flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" /> {error} — <Link href="/login" className="underline">Sign in</Link>
            </div>
          )}

          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard label="Active Facilities" value={loading ? "—" : facilities.length} icon={<Map className="h-5 w-5 text-primary" />} />
            <KPICard label="Available Units" value={loading ? "—" : totalAvailable.toLocaleString()} icon={<Droplets className="h-5 w-5 text-primary" />} />
            <KPICard label="Expiring in 72h" value={loading ? "—" : expiring72h} icon={<AlertTriangle className="h-5 w-5 text-warning" />} highlight={expiring72h > 10 ? "warning" : ""} />
            <KPICard label="Critical Facilities" value={loading ? "—" : criticalFacilities.length} icon={<ShieldAlert className="h-5 w-5 text-destructive" />} highlight={criticalFacilities.length > 0 ? "danger" : ""} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Chart */}
            <div className="border border-border bg-card rounded-xl p-5">
              <h2 className="font-medium mb-4 flex items-center gap-2"><BarChart2 className="h-4 w-4 text-primary" /> Network Risk by Facility</h2>
              {loading ? <div className="h-64 animate-pulse bg-muted rounded" /> : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis dataKey="name" fontSize={11} tickLine={false} axisLine={false} stroke="var(--muted-foreground)" />
                      <YAxis fontSize={11} tickLine={false} axisLine={false} stroke="var(--muted-foreground)" unit="%" />
                      <Tooltip contentStyle={{ backgroundColor: "var(--popover)", borderColor: "var(--border)", borderRadius: "8px", fontSize: "12px" }} />
                      <Bar dataKey="shortage" name="Shortage Risk %" fill="#ef4444" radius={[4,4,0,0]} opacity={0.85} />
                      <Bar dataKey="wastage" name="Wastage Risk %" fill="#991b1b" radius={[4,4,0,0]} opacity={0.7} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Pending Recommendations */}
            <div className="border border-border bg-card rounded-xl p-5 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-medium flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-primary" /> Pending AI Recommendations</h2>
                <Link href="/recommendations" className="text-xs text-primary hover:underline flex items-center gap-1">View all <ArrowRight className="h-3 w-3" /></Link>
              </div>
              {loading ? (
                <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-12 animate-pulse bg-muted rounded" />)}</div>
              ) : recs.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">No pending recommendations. Run optimizer to generate.</div>
              ) : recs.map((r: any) => (
                <div key={r.id} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <div>
                    <div className="text-sm font-medium">{r.reason?.slice(0, 60)}...</div>
                    <div className="text-xs text-muted-foreground">Confidence: {r.confidence ? `${Math.round(r.confidence * 100)}%` : "N/A"}</div>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary font-medium">{r.rec_type}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="border border-border bg-card rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-medium flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-destructive" /> Active Alerts</h2>
              <Link href="/alerts" className="text-xs text-primary hover:underline flex items-center gap-1">View all <ArrowRight className="h-3 w-3" /></Link>
            </div>
            {loading ? (
              <div className="space-y-2">{[1,2].map(i => <div key={i} className="h-12 animate-pulse bg-muted rounded" />)}</div>
            ) : alerts.length === 0 ? (
              <div className="text-muted-foreground text-sm py-4 text-center">No active alerts.</div>
            ) : (
              <div className="divide-y divide-border">
                {alerts.map((a: any) => (
                  <div key={a.id} className="flex items-center gap-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold shrink-0 ${a.severity === "CRITICAL" || a.severity === "HIGH" ? "bg-destructive/10 text-destructive" : "bg-warning/10 text-warning"}`}>{a.severity}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{a.title}</div>
                      <div className="text-xs text-muted-foreground truncate">{a.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function KPICard({ label, value, icon, highlight = "" }: any) {
  return (
    <div className={`border rounded-xl p-5 bg-card ${highlight === "danger" ? "border-destructive/30" : highlight === "warning" ? "border-warning/30" : "border-border"}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
        {icon}
      </div>
      <div className={`text-3xl font-semibold tracking-tight ${highlight === "danger" ? "text-destructive" : highlight === "warning" ? "text-warning" : ""}`}>{value}</div>
    </div>
  );
}
