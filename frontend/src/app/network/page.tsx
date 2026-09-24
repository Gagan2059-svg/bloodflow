import React from "react";
import NetworkGraph from "@/components/NetworkGraph";
import { ActivitySquare, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NetworkPage() {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background">
      <header className="h-14 border-b border-border px-6 flex items-center bg-card/50 backdrop-blur shrink-0">
        <Link href="/" className="flex items-center text-muted-foreground hover:text-foreground mr-6 transition-colors">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Link>
        <div className="flex items-center font-semibold text-lg text-primary mr-8">
          <ActivitySquare className="mr-2 h-5 w-5" />
          BloodFlow
        </div>
        <h1 className="text-sm font-medium text-muted-foreground">Network Operations / <span className="text-foreground">Facility Map</span></h1>
      </header>

      <main className="flex-1 overflow-hidden p-6">
        <div className="max-w-7xl mx-auto h-full flex flex-col space-y-4">
          <div className="flex justify-between items-end">
            <div>
              <h2 className="text-xl font-bold">Network Digital Twin</h2>
              <p className="text-sm text-muted-foreground">Real-time simulation of regional facility dependencies and blood transfers.</p>
            </div>
            <div className="flex gap-2 text-sm">
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-primary inline-block"></span> Surplus</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-destructive inline-block"></span> Deficit</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-[var(--chart-2)] inline-block"></span> Stable</span>
            </div>
          </div>
          
          <div className="flex-1">
            <NetworkGraph />
          </div>
        </div>
      </main>
    </div>
  );
}
