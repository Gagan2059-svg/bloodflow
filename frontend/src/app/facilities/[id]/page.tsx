"use client";

import React from "react";
import { ActivitySquare, Map, Box, Activity, AlertTriangle, ArrowUpRight, ArrowDownRight, Package } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

const inventoryData = [
  { group: "O+", count: 420 },
  { group: "O-", count: 85 },
  { group: "A+", count: 350 },
  { group: "A-", count: 60 },
  { group: "B+", count: 120 },
  { group: "B-", count: 25 },
  { group: "AB+", count: 45 },
  { group: "AB-", count: 15 },
];

export default function FacilityDetail() {
  const params = useParams();
  
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <aside className="w-64 border-r border-border bg-sidebar flex flex-col">
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
          <Link href="/facilities/explorer" className="flex items-center gap-3 px-3 py-2 rounded-md bg-sidebar-accent text-sidebar-accent-foreground text-sm font-medium">
            <Box className="h-4 w-4" /> Inventory Explorer
          </Link>
        </nav>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-card/50 backdrop-blur">
          <h1 className="text-sm font-medium text-muted-foreground">Regional Network / Facilities / <span className="text-foreground">Regional Blood Center 1</span></h1>
        </header>

        <div className="p-6 max-w-7xl mx-auto space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">Regional Blood Center 1</h2>
              <p className="text-muted-foreground">ID: {params.id}</p>
            </div>
            <div className="flex gap-2">
              <span className="px-3 py-1 bg-emerald-500/10 text-emerald-500 rounded-md text-sm font-medium border border-emerald-500/20">Operational</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard title="Network Health" value="91" unit="/ 100" trend="up" />
            <KpiCard title="Total Inventory" value="2,431" unit="units" trend="down" change="-2.1%" />
            <KpiCard title="72h Shortage Risk" value="12" unit="%" trend="up" alert={true} change="+4%" />
            <KpiCard title="At-Risk Inventory" value="84" unit="units" trend="down" change="-10" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="border border-border bg-card rounded-lg p-5">
              <h3 className="font-medium mb-4 flex items-center gap-2"><Package className="h-4 w-4 text-muted-foreground" /> Inventory by Blood Group</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={inventoryData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="group" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip cursor={{ fill: 'var(--muted)' }} contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                    <Bar dataKey="count" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="border border-border bg-card rounded-lg p-5">
              <h3 className="font-medium mb-4 flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-warning" /> Pending Actions</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-muted/50 rounded-md border border-border text-sm">
                  <div>
                    <div className="font-medium">Incoming Transfer</div>
                    <div className="text-muted-foreground">36 units O+ RBC from Facility C</div>
                  </div>
                  <span className="text-primary font-medium">ETA 45m</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-muted/50 rounded-md border border-border text-sm">
                  <div>
                    <div className="font-medium">Outgoing Transfer</div>
                    <div className="text-muted-foreground">22 units A- Plasma to Facility E</div>
                  </div>
                  <span className="text-muted-foreground">Processing</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function KpiCard({ title, value, unit, change, trend, alert = false }: any) {
  return (
    <div className="border border-border bg-card p-5 rounded-lg flex flex-col justify-between">
      <div className="text-sm font-medium text-muted-foreground mb-2">{title}</div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-semibold tracking-tight">{value}</span>
        <span className="text-sm text-muted-foreground">{unit}</span>
      </div>
      {change && (
        <div className={`mt-3 flex items-center text-xs font-medium ${alert ? 'text-destructive' : trend === 'up' ? 'text-emerald-500' : 'text-emerald-500'}`}>
          {trend === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
          {change} from previous period
        </div>
      )}
    </div>
  );
}
