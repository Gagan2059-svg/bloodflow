"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ActivitySquare, Map, Box, Activity, ShieldAlert, CheckCircle2, TrendingUp, GitPullRequest, BarChart2, FileJson, RefreshCw } from "lucide-react";
import { getFacilities, generateForecast } from "@/lib/api";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const NAV = [
  { href: "/", icon: Activity, label: "Command Center" },
  { href: "/network", icon: Map, label: "Facility Map" },
  { href: "/facilities/explorer", icon: Box, label: "Inventory Explorer" },
  { href: "/simulator", icon: GitPullRequest, label: "Digital Twin" },
  { href: "/forecasts", icon: TrendingUp, label: "Forecasts", active: true },
  { href: "/analytics", icon: BarChart2, label: "Analytics" },
  { href: "/alerts", icon: ShieldAlert, label: "Alerts & Events" },
  { href: "/recommendations", icon: CheckCircle2, label: "AI Recommendations" },
  { href: "/audit", icon: FileJson, label: "Audit Logs" },
];

export default function ForecastsPage() {
  const [facilities, setFacilities] = useState<any[]>([]);
  const [selectedFacility, setSelectedFacility] = useState("");
  const [bloodGroup, setBloodGroup] = useState("O+");
  const [component, setComponent] = useState("RBC");
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [modelMAE, setModelMAE] = useState<number | null>(null);

  useEffect(() => {
    getFacilities().then(data => {
      const list = Array.isArray(data) ? data : [];
      setFacilities(list);
      if (list.length > 0) setSelectedFacility(list[0].id);
    }).catch(() => {});
  }, []);

  const handleRun = async () => {
    if (!selectedFacility) return;
    setLoading(true);
    setForecast(null);
    try {
      const data = await generateForecast(selectedFacility, bloodGroup, component, 7);
      setForecast(data);
      setModelMAE(data?.models?.gradient_boosting?.mae ?? null);
    } catch (e) {}
    finally { setLoading(false); }
  };

  // Build chart data from forecast response
  const chartData = forecast ? Object.entries(forecast.models?.gradient_boosting?.predictions || {}).map(([date, val]: any, i) => ({
    date: date.slice(5), // MM-DD
    "Gradient Boosting": Math.round(val),
    "Moving Avg": Math.round(Object.values(forecast.models?.moving_average_7d?.predictions || {})[i] as number || 0),
    "Naive": Math.round(Object.values(forecast.models?.naive?.predictions || {})[i] as number || 0),
  })) : [];

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
        <header className="h-14 border-b border-border px-6 flex items-center bg-card/50 backdrop-blur shrink-0">
          <h1 className="text-sm font-medium text-muted-foreground">ML Ops / <span className="text-foreground">Demand Forecasts</span></h1>
        </header>

        <div className="p-6 max-w-7xl mx-auto w-full flex-1 space-y-6">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Predictive Demand Forecasting</h2>
            <p className="text-sm text-muted-foreground mt-1">Real ML models trained on historical DemandRecord data. Select a facility and component to generate a forecast.</p>
          </div>

          {/* Controls */}
          <div className="border border-border bg-card rounded-xl p-5 flex flex-wrap gap-4 items-end">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-muted-foreground">Facility</label>
              <select value={selectedFacility} onChange={e => setSelectedFacility(e.target.value)}
                className="bg-background border border-input rounded-lg px-3 py-2 text-sm min-w-[200px]">
                {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-muted-foreground">Blood Group</label>
              <select value={bloodGroup} onChange={e => setBloodGroup(e.target.value)}
                className="bg-background border border-input rounded-lg px-3 py-2 text-sm">
                {["O+","O-","A+","A-","B+","B-","AB+","AB-"].map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-muted-foreground">Component</label>
              <select value={component} onChange={e => setComponent(e.target.value)}
                className="bg-background border border-input rounded-lg px-3 py-2 text-sm">
                {["RBC","PLASMA","PLATELETS","WHOLE_BLOOD"].map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <button onClick={handleRun} disabled={loading || !selectedFacility}
              className="bg-primary text-primary-foreground px-5 py-2 rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors disabled:opacity-50">
              {loading ? "Generating..." : "Run Forecast"}
            </button>
          </div>

          {/* Model scores */}
          {forecast && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border border-primary/30 bg-card p-5 rounded-xl border-l-4 border-l-primary">
                <div className="text-xs text-muted-foreground mb-1">Gradient Boosting</div>
                <div className="text-3xl font-semibold">{modelMAE !== null ? `${modelMAE.toFixed(2)}` : "—"}</div>
                <div className="text-xs text-muted-foreground mt-1">MAE (hold-out) · Active Model</div>
              </div>
              <div className="border border-border bg-card p-5 rounded-xl">
                <div className="text-xs text-muted-foreground mb-1">Exponential Smoothing</div>
                <div className="text-3xl font-semibold">Baseline</div>
                <div className="text-xs text-muted-foreground mt-1">Benchmark comparison</div>
              </div>
              <div className="border border-border bg-card p-5 rounded-xl">
                <div className="text-xs text-muted-foreground mb-1">Data Points Used</div>
                <div className="text-3xl font-semibold">{forecast.historical_data_points ?? "—"}</div>
                <div className="text-xs text-muted-foreground mt-1">Historical demand records</div>
              </div>
            </div>
          )}

          {/* Forecast chart */}
          {loading && <div className="h-80 animate-pulse bg-muted rounded-xl" />}
          {forecast && chartData.length > 0 && (
            <div className="border border-border bg-card rounded-xl p-5">
              <h3 className="font-medium mb-4">7-Day Forecast — {bloodGroup} {component}</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="gbGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: "var(--popover)", borderColor: "var(--border)", borderRadius: "8px" }} />
                    <Legend />
                    <Area type="monotone" dataKey="Gradient Boosting" stroke="hsl(var(--primary))" fill="url(#gbGrad)" strokeWidth={2.5} />
                    <Area type="monotone" dataKey="Moving Avg" stroke="var(--muted-foreground)" fillOpacity={0} strokeWidth={1.5} strokeDasharray="5 5" />
                    <Area type="monotone" dataKey="Naive" stroke="hsl(var(--destructive))" fillOpacity={0} strokeWidth={1.5} strokeDasharray="3 3" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {!forecast && !loading && (
            <div className="border border-border bg-card rounded-xl p-16 text-center text-muted-foreground">
              <TrendingUp className="h-10 w-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Select a facility and click "Run Forecast" to generate real ML predictions.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
