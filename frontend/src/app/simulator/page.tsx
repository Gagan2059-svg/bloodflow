"use client";

import React, { useState, useEffect } from "react";
import {
  ActivitySquare, Map, Activity, Play, Settings2, BarChart2,
  AlertTriangle, GitPullRequest, RefreshCw, ChevronRight, Cpu, Zap
} from "lucide-react";
import Link from "next/link";
import { getFacilities, runSimulation } from "@/lib/api";

type SimResult = {
  scenario_id: string;
  scenario_description: string;
  horizon_hours: number;
  baseline_shortage_risk_pct: number;
  simulated_shortage_risk_pct: number;
  shortage_delta_pct: number;
  baseline_wastage_units: number;
  simulated_wastage_units: number;
  baseline_service_level_pct: number;
  simulated_service_level_pct: number;
  service_level_delta_pct: number;
  affected_facilities_count: number;
  critical_facilities: string[];
  recommended_mitigations: string[];
};

export default function SimulatorPage() {
  const [facilities, setFacilities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<SimResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Scenario parameters
  const [scenarioType, setScenarioType] = useState("FACILITY_OUTAGE");
  const [facilityOffline, setFacilityOffline] = useState<string>("none");
  const [demandMultiplier, setDemandMultiplier] = useState(1.0);
  const [horizonHours, setHorizonHours] = useState(72);
  const [supplyReductionPct, setSupplyReductionPct] = useState(0.0);

  useEffect(() => {
    getFacilities()
      .then(setFacilities)
      .catch(() => setError("Could not load facilities"))
      .finally(() => setLoading(false));
  }, []);

  const handleRunSimulation = async () => {
    if (facilities.length === 0) return;
    setRunning(true);
    setError(null);
    setResults(null);

    try {
      // Build facility snapshots from real DB data
      const facilitySnapshots = facilities.map((f) => ({
        id: f.id,
        name: f.name,
        inventory: f.total_units ?? 50, // fallback if summary not returned
        capacity: f.capacity ?? 200,
        daily_demand: f.daily_demand ?? 10,
        is_online: true,
      }));

      // Build scenario
      const affectedIds =
        facilityOffline !== "none" ? [facilityOffline] : [];

      const scenario = {
        scenario_type: scenarioType,
        description: buildScenarioDescription(),
        affected_facility_ids: affectedIds,
        demand_multiplier: demandMultiplier,
        transport_delay_multiplier: 1.0,
        supply_reduction_pct: supplyReductionPct,
        facility_offline: facilityOffline !== "none",
        horizon_hours: horizonHours,
      };

      const result = await runSimulation(facilitySnapshots, scenario);
      setResults(result);
    } catch (e: any) {
      setError(e.message || "Simulation failed");
    } finally {
      setRunning(false);
    }
  };

  function buildScenarioDescription(): string {
    const parts: string[] = [];
    if (facilityOffline !== "none") {
      const f = facilities.find((x) => x.id === facilityOffline);
      parts.push(`${f?.name ?? "Facility"} offline`);
    }
    if (demandMultiplier > 1.0) {
      parts.push(`+${Math.round((demandMultiplier - 1) * 100)}% demand surge`);
    }
    if (supplyReductionPct > 0) {
      parts.push(`${Math.round(supplyReductionPct * 100)}% supply reduction`);
    }
    return parts.length > 0 ? parts.join(" + ") : "Baseline stress test";
  }

  const deltaColor = (delta: number, inverse = false) => {
    if (delta === 0) return "text-muted-foreground";
    const bad = inverse ? delta < 0 : delta > 0;
    return bad ? "text-destructive" : "text-emerald-400";
  };

  const deltaArrow = (delta: number) => (delta > 0 ? "↑" : delta < 0 ? "↓" : "–");

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-sidebar flex flex-col shrink-0">
        <div className="h-14 flex items-center px-4 font-semibold text-lg border-b border-border text-primary">
          <ActivitySquare className="mr-2 h-5 w-5" />
          BloodFlow
        </div>
        <nav className="flex-1 p-4 space-y-1">
          <Link href="/" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground text-sm font-medium transition-colors">
            <Activity className="h-4 w-4" /> Network Operations
          </Link>
          <Link href="/network" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground text-sm font-medium transition-colors">
            <Map className="h-4 w-4" /> Facility Map
          </Link>
          <Link href="/simulator" className="flex items-center gap-3 px-3 py-2 rounded-md bg-sidebar-accent text-sidebar-accent-foreground text-sm font-medium">
            <GitPullRequest className="h-4 w-4" /> Digital Twin
          </Link>
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto flex flex-col">
        <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-card/50 backdrop-blur shrink-0">
          <div className="flex items-center gap-2 text-sm">
            <Cpu className="h-4 w-4 text-primary" />
            <span className="text-muted-foreground">Digital Twin /</span>
            <span className="text-foreground font-medium">Simulation Engine</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse inline-block" />
            Live data — {facilities.length} facilities loaded
          </div>
        </header>

        <div className="p-6 max-w-7xl mx-auto w-full flex-1 flex flex-col gap-6">
          {/* Header row */}
          <div className="flex justify-between items-end">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">Scenario Builder</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Configure real facility parameters to stress-test the regional blood supply network.
                Results are computed by a deterministic engine against live inventory snapshots.
              </p>
            </div>
            <button
              onClick={handleRunSimulation}
              disabled={running || loading || facilities.length === 0}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-md font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 text-sm"
            >
              {running
                ? <><RefreshCw className="h-4 w-4 animate-spin" /> Computing…</>
                : <><Play className="h-4 w-4" /> Run Simulation</>
              }
            </button>
          </div>

          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-md text-destructive text-sm">
              {error}
            </div>
          )}

          {/* Config + Results Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Scenario config panel */}
            <div className="border border-border bg-card rounded-lg p-5 space-y-5">
              <h3 className="font-medium flex items-center gap-2">
                <Settings2 className="h-4 w-4 text-muted-foreground" /> Parameters
              </h3>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Scenario Type</label>
                <select
                  value={scenarioType}
                  onChange={(e) => setScenarioType(e.target.value)}
                  className="w-full bg-background border border-input rounded-md p-2 text-sm"
                >
                  <option value="FACILITY_OUTAGE">Facility Outage</option>
                  <option value="DEMAND_SURGE">Demand Surge</option>
                  <option value="SUPPLY_REDUCTION">Supply Reduction</option>
                  <option value="TRANSPORT_DELAY">Transport Delay</option>
                  <option value="CUSTOM">Custom</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Affected Facility (Offline)</label>
                <select
                  value={facilityOffline}
                  onChange={(e) => setFacilityOffline(e.target.value)}
                  className="w-full bg-background border border-input rounded-md p-2 text-sm"
                  disabled={loading}
                >
                  <option value="none">None</option>
                  {facilities.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Demand Multiplier ({demandMultiplier.toFixed(1)}×)
                </label>
                <input
                  type="range"
                  min={0.5}
                  max={3.0}
                  step={0.1}
                  value={demandMultiplier}
                  onChange={(e) => setDemandMultiplier(parseFloat(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0.5× (–50%)</span><span>3.0× (+200%)</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Supply Reduction ({Math.round(supplyReductionPct * 100)}%)
                </label>
                <input
                  type="range"
                  min={0}
                  max={0.9}
                  step={0.05}
                  value={supplyReductionPct}
                  onChange={(e) => setSupplyReductionPct(parseFloat(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>0%</span><span>90%</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Time Horizon ({horizonHours}h)
                </label>
                <input
                  type="range"
                  min={12}
                  max={168}
                  step={12}
                  value={horizonHours}
                  onChange={(e) => setHorizonHours(parseInt(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>12h</span><span>168h (7d)</span>
                </div>
              </div>
            </div>

            {/* Results panel */}
            <div className="lg:col-span-2 border border-border bg-card rounded-lg p-5 flex flex-col">
              <h3 className="font-medium mb-4 flex items-center gap-2">
                <BarChart2 className="h-4 w-4 text-muted-foreground" /> Simulation Results
              </h3>

              {running && (
                <div className="flex-1 flex flex-col items-center justify-center gap-4 text-muted-foreground">
                  <div className="relative">
                    <Cpu className="h-12 w-12 text-primary/30" />
                    <RefreshCw className="h-5 w-5 text-primary absolute top-3.5 left-3.5 animate-spin" />
                  </div>
                  <p className="text-sm">Running deterministic simulation engine…</p>
                  <p className="text-xs opacity-60">Evaluating {facilities.length} facility snapshots against scenario parameters</p>
                </div>
              )}

              {!running && !results && (
                <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground border border-dashed border-border rounded-md">
                  Configure parameters and run the simulation to see impact across your network.
                </div>
              )}

              {!running && results && (
                <div className="space-y-5">
                  {/* Scenario description badge */}
                  <div className="px-3 py-2 bg-primary/10 border border-primary/20 rounded-md text-xs font-medium text-primary">
                    <Zap className="inline h-3 w-3 mr-1" />
                    Scenario: {results.scenario_description}
                    <span className="ml-2 text-muted-foreground">({results.horizon_hours}h horizon)</span>
                  </div>

                  {/* KPI grid */}
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="p-4 bg-muted/30 rounded-lg border border-border">
                      <div className="text-xs text-muted-foreground mb-1">Shortage Risk</div>
                      <div className="text-xl font-bold">
                        <span className="line-through opacity-40 text-sm mr-1">{results.baseline_shortage_risk_pct.toFixed(0)}%</span>
                        <span className={deltaColor(results.shortage_delta_pct)}>
                          {results.simulated_shortage_risk_pct.toFixed(0)}%
                        </span>
                      </div>
                      <div className={`text-xs font-medium ${deltaColor(results.shortage_delta_pct)}`}>
                        {deltaArrow(results.shortage_delta_pct)} {Math.abs(results.shortage_delta_pct).toFixed(1)}pp
                      </div>
                    </div>

                    <div className="p-4 bg-muted/30 rounded-lg border border-border">
                      <div className="text-xs text-muted-foreground mb-1">Wastage (units)</div>
                      <div className="text-xl font-bold">
                        <span className="line-through opacity-40 text-sm mr-1">{results.baseline_wastage_units}</span>
                        <span className={deltaColor(results.simulated_wastage_units - results.baseline_wastage_units)}>
                          {results.simulated_wastage_units}
                        </span>
                      </div>
                      <div className={`text-xs font-medium ${deltaColor(results.simulated_wastage_units - results.baseline_wastage_units)}`}>
                        {deltaArrow(results.simulated_wastage_units - results.baseline_wastage_units)} {Math.abs(results.simulated_wastage_units - results.baseline_wastage_units)} units
                      </div>
                    </div>

                    <div className="p-4 bg-muted/30 rounded-lg border border-border">
                      <div className="text-xs text-muted-foreground mb-1">Service Level</div>
                      <div className="text-xl font-bold">
                        <span className="line-through opacity-40 text-sm mr-1">{results.baseline_service_level_pct.toFixed(0)}%</span>
                        <span className={deltaColor(results.service_level_delta_pct, true)}>
                          {results.simulated_service_level_pct.toFixed(0)}%
                        </span>
                      </div>
                      <div className={`text-xs font-medium ${deltaColor(results.service_level_delta_pct, true)}`}>
                        {deltaArrow(results.service_level_delta_pct)} {Math.abs(results.service_level_delta_pct).toFixed(1)}pp
                      </div>
                    </div>
                  </div>

                  {/* Critical facilities */}
                  {results.critical_facilities.length > 0 && (
                    <div className="p-3 bg-destructive/5 border border-destructive/20 rounded-md">
                      <div className="text-xs font-semibold text-destructive mb-2 flex items-center gap-1.5">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        {results.affected_facilities_count} Critical Facilities
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {results.critical_facilities.map((name) => (
                          <span key={name} className="text-xs px-2 py-0.5 bg-destructive/10 text-destructive rounded-full">{name}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommended mitigations */}
                  {results.recommended_mitigations.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Recommended Mitigations</h4>
                      {results.recommended_mitigations.map((m, i) => (
                        <div key={i} className="flex gap-2 text-sm p-3 bg-muted/20 border border-border rounded-md">
                          <ChevronRight className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                          <span>{m}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="text-xs text-muted-foreground border-t border-border pt-3">
                    Scenario ID: <code className="font-mono">{results.scenario_id}</code>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
