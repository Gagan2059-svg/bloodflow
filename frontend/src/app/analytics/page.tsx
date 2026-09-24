"use client";

import React from "react";
import { ActivitySquare, Map, Box, Activity, BarChart2, TrendingUp, TrendingDown, ArrowUpRight, GitPullRequest } from "lucide-react";
import Link from "next/link";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts";

const utilizationData = [
  { name: 'Mon', RBC: 400, Plasma: 240, Platelets: 200 },
  { name: 'Tue', RBC: 300, Plasma: 139, Platelets: 221 },
  { name: 'Wed', RBC: 200, Plasma: 980, Platelets: 229 },
  { name: 'Thu', RBC: 278, Plasma: 390, Platelets: 200 },
  { name: 'Fri', RBC: 189, Plasma: 480, Platelets: 218 },
  { name: 'Sat', RBC: 239, Plasma: 380, Platelets: 250 },
  { name: 'Sun', RBC: 349, Plasma: 430, Platelets: 210 },
];

const wastageData = [
  { facility: 'Hub A', expired: 12, discarded: 4 },
  { facility: 'Hosp B', expired: 5, discarded: 1 },
  { facility: 'Hosp C', expired: 2, discarded: 0 },
  { facility: 'Hub D', expired: 8, discarded: 2 },
];

export default function AnalyticsPage() {
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
            <Activity className="h-4 w-4" /> Command Center
          </Link>
          <Link href="/network" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground text-sm font-medium transition-colors">
            <Map className="h-4 w-4" /> Facility Map
          </Link>
          <Link href="/facilities/explorer" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground text-sm font-medium transition-colors">
            <Box className="h-4 w-4" /> Inventory Explorer
          </Link>
          <Link href="/simulator" className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground text-sm font-medium transition-colors">
            <GitPullRequest className="h-4 w-4" /> Digital Twin
          </Link>
          <div className="pt-4 pb-2">
            <p className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Reports</p>
          </div>
          <Link href="/analytics" className="flex items-center gap-3 px-3 py-2 rounded-md bg-sidebar-accent text-sidebar-accent-foreground text-sm font-medium">
            <BarChart2 className="h-4 w-4" /> Network Analytics
          </Link>
        </nav>
      </aside>

      <main className="flex-1 overflow-y-auto flex flex-col">
        <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-card/50 backdrop-blur shrink-0">
          <h1 className="text-sm font-medium text-muted-foreground">Reports / <span className="text-foreground">Network Analytics</span></h1>
        </header>

        <div className="p-6 max-w-7xl mx-auto w-full flex-1 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">Performance Metrics</h2>
              <p className="text-sm text-muted-foreground mt-1">Key performance indicators across the regional blood network.</p>
            </div>
            <select className="bg-background border border-input rounded p-2 text-sm">
                <option>Last 7 Days</option>
                <option>Last 30 Days</option>
                <option>This Quarter</option>
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard title="Overall Fulfillment Rate" value="98.2%" trend="up" change="+0.4%" />
            <MetricCard title="Total Wastage" value="32 units" trend="down" change="-12%" isGood={true} />
            <MetricCard title="Avg Transfer Time" value="42 min" trend="down" change="-5 min" isGood={true} />
            <MetricCard title="Emergency Response SLA" value="99.9%" trend="up" change="+0.1%" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
             <div className="border border-border bg-card rounded-lg p-5">
              <h3 className="font-medium mb-4">Component Utilization Trends</h3>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={utilizationData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="name" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                    <Legend iconType="circle" />
                    <Line type="monotone" dataKey="RBC" stroke="var(--primary)" strokeWidth={2} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Plasma" stroke="var(--chart-2)" strokeWidth={2} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Platelets" stroke="var(--warning)" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="border border-border bg-card rounded-lg p-5">
              <h3 className="font-medium mb-4">Wastage by Facility</h3>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={wastageData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="facility" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                    <Tooltip cursor={{ fill: 'var(--muted)' }} contentStyle={{ backgroundColor: 'var(--popover)', borderColor: 'var(--border)', borderRadius: '8px' }} />
                    <Legend iconType="circle" />
                    <Bar dataKey="expired" stackId="a" fill="var(--destructive)" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="discarded" stackId="a" fill="var(--warning)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function MetricCard({ title, value, trend, change, isGood = false }: any) {
  const isUp = trend === 'up';
  // If isGood is true, then 'down' is good (like wastage). Otherwise, 'up' is good (like fulfillment).
  const goodColor = (isGood ? !isUp : isUp) ? 'text-emerald-500' : 'text-destructive';

  return (
    <div className="border border-border bg-card p-5 rounded-lg flex flex-col justify-between">
      <div className="text-sm font-medium text-muted-foreground mb-2">{title}</div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-semibold tracking-tight">{value}</span>
      </div>
      <div className={`mt-3 flex items-center text-xs font-medium ${goodColor}`}>
        {isUp ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
        {change} vs last period
      </div>
    </div>
  );
}
