"use client";

import React from "react";
import { ActivitySquare, Map, Box, Activity, GitPullRequest, Search, FileJson } from "lucide-react";
import Link from "next/link";

const mockLogs = [
  { id: "LOG-001", time: "2026-09-18 10:45:12", user: "system", action: "TRANSFER_COMPLETED", entity: "Transfer: 121a", ip: "10.0.0.45" },
  { id: "LOG-002", time: "2026-09-18 10:30:00", user: "admin@regional.local", action: "RECOMMENDATION_APPROVED", entity: "Rec: REC-995", ip: "192.168.1.10" },
  { id: "LOG-003", time: "2026-09-18 09:15:22", user: "system", action: "ANOMALY_DETECTED", entity: "Facility: B (O- Demand)", ip: "10.0.0.45" },
  { id: "LOG-004", time: "2026-09-18 08:00:01", user: "system", action: "FORECAST_GENERATED", entity: "Model: GradientBoosting v2", ip: "10.0.0.50" },
  { id: "LOG-005", time: "2026-09-17 22:30:15", user: "operator@hub.local", action: "USER_LOGIN", entity: "User Session", ip: "172.16.0.5" },
];

export default function AuditLogsPage() {
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
            <p className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">System</p>
          </div>
          <Link href="/audit" className="flex items-center gap-3 px-3 py-2 rounded-md bg-sidebar-accent text-sidebar-accent-foreground text-sm font-medium">
            <FileJson className="h-4 w-4" /> Audit Logs
          </Link>
        </nav>
      </aside>

      <main className="flex-1 overflow-y-auto flex flex-col">
        <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-card/50 backdrop-blur shrink-0">
          <h1 className="text-sm font-medium text-muted-foreground">System / <span className="text-foreground">Audit Logs</span></h1>
        </header>

        <div className="p-6 max-w-7xl mx-auto w-full flex-1 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">System Audit Log</h2>
              <p className="text-sm text-muted-foreground mt-1">Immutable record of all system actions, ML inferences, and user operations.</p>
            </div>
            
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input 
                type="text" 
                placeholder="Search logs..." 
                className="pl-9 pr-4 py-2 border border-input rounded-md text-sm bg-background w-64 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          <div className="border border-border rounded-lg bg-card overflow-hidden flex-1">
             <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs uppercase bg-muted/50 border-b border-border text-muted-foreground">
                  <tr>
                    <th className="px-6 py-3 font-medium">Timestamp</th>
                    <th className="px-6 py-3 font-medium">User/System</th>
                    <th className="px-6 py-3 font-medium">Action</th>
                    <th className="px-6 py-3 font-medium">Entity</th>
                    <th className="px-6 py-3 font-medium">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono text-xs">
                  {mockLogs.map((log, i) => (
                    <tr key={i} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-muted-foreground">{log.time}</td>
                      <td className="px-6 py-4 text-primary">{log.user}</td>
                      <td className="px-6 py-4 font-semibold">{log.action}</td>
                      <td className="px-6 py-4 text-muted-foreground">{log.entity}</td>
                      <td className="px-6 py-4 text-muted-foreground">{log.ip}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
