"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ActivitySquare, Map, Box, Activity, ShieldAlert, CheckCircle2, TrendingUp, GitPullRequest, BarChart2, FileJson, Check, X, Bot, ArrowRight, RefreshCw } from "lucide-react";
import { getRecommendations, approveRecommendation, rejectRecommendation, runOptimizer } from "@/lib/api";

const NAV = [
  { href: "/", icon: Activity, label: "Command Center" },
  { href: "/network", icon: Map, label: "Facility Map" },
  { href: "/facilities/explorer", icon: Box, label: "Inventory Explorer" },
  { href: "/simulator", icon: GitPullRequest, label: "Digital Twin" },
  { href: "/forecasts", icon: TrendingUp, label: "Forecasts" },
  { href: "/analytics", icon: BarChart2, label: "Analytics" },
  { href: "/alerts", icon: ShieldAlert, label: "Alerts & Events" },
  { href: "/recommendations", icon: CheckCircle2, label: "AI Recommendations", active: true },
  { href: "/audit", icon: FileJson, label: "Audit Logs" },
];

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await getRecommendations();
      setRecs(Array.isArray(data) ? data : []);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleApprove = async (id: string) => {
    setActionLoading(id + "_approve");
    try {
      await approveRecommendation(id);
      setRecs(recs.map(r => r.id === id ? { ...r, status: "APPROVED" } : r));
    } finally { setActionLoading(null); }
  };

  const handleReject = async (id: string) => {
    setActionLoading(id + "_reject");
    try {
      await rejectRecommendation(id);
      setRecs(recs.map(r => r.id === id ? { ...r, status: "REJECTED" } : r));
    } finally { setActionLoading(null); }
  };

  const handleRunOptimizer = async () => {
    setOptimizing(true);
    try {
      await runOptimizer();
      setTimeout(load, 2000);
    } finally { setOptimizing(false); }
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
          <h1 className="text-sm font-medium text-muted-foreground">Operations / <span className="text-foreground">AI Recommendations</span></h1>
          <div className="flex gap-2">
            <button onClick={load} className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"><RefreshCw className="h-3.5 w-3.5" /></button>
            <button onClick={handleRunOptimizer} disabled={optimizing} className="bg-primary text-primary-foreground text-xs px-3 py-1.5 rounded-md font-medium hover:bg-primary/90 disabled:opacity-50">
              {optimizing ? "Running..." : "Run Optimizer Now"}
            </button>
          </div>
        </header>

        <div className="p-6 max-w-5xl mx-auto w-full flex-1">
          <div className="mb-6">
            <h2 className="text-2xl font-semibold tracking-tight">AI Decision Support</h2>
            <p className="text-sm text-muted-foreground mt-1">Review and approve network optimization actions from the OR-Tools engine.</p>
          </div>

          {loading ? (
            <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="h-32 animate-pulse bg-muted rounded-lg" />)}</div>
          ) : recs.length === 0 ? (
            <div className="border border-border bg-card rounded-xl p-12 text-center">
              <CheckCircle2 className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
              <div className="font-medium mb-1">No recommendations</div>
              <p className="text-sm text-muted-foreground mb-4">Click "Run Optimizer Now" to generate transfer recommendations from real inventory data.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {recs.map((rec: any) => (
                <div key={rec.id} className="border border-border bg-card rounded-xl p-5 flex flex-col md:flex-row gap-6 md:items-center">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-primary/10 text-primary">{rec.rec_type}</span>
                      <span className="text-xs text-muted-foreground">Priority: {rec.priority} · Confidence: {rec.confidence ? `${Math.round(rec.confidence * 100)}%` : "N/A"}</span>
                    </div>
                    {rec.quantity && (
                      <div className="text-lg font-medium">{rec.quantity} units — {rec.blood_group || "Any"} {rec.component || ""}</div>
                    )}
                    <div className="text-sm text-muted-foreground">{rec.reason}</div>
                  </div>

                  <div className="flex flex-row md:flex-col gap-2 min-w-[130px]">
                    {rec.status === "PENDING" ? (
                      <>
                        <button onClick={() => handleApprove(rec.id)} disabled={actionLoading === rec.id + "_approve"}
                          className="flex-1 flex items-center justify-center gap-1.5 bg-primary text-primary-foreground py-2 px-3 rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50">
                          <Check className="h-4 w-4" /> Approve
                        </button>
                        <button onClick={() => handleReject(rec.id)} disabled={actionLoading === rec.id + "_reject"}
                          className="flex-1 flex items-center justify-center gap-1.5 bg-background border border-input py-2 px-3 rounded-lg font-medium text-sm hover:bg-accent transition-colors">
                          <X className="h-4 w-4" /> Reject
                        </button>
                      </>
                    ) : (
                      <div className={`px-3 py-2 rounded-lg text-sm font-medium text-center ${rec.status === "APPROVED" ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" : "bg-muted text-muted-foreground"}`}>
                        {rec.status}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
