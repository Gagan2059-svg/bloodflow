"use client";

import React, { useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  { id: '1', position: { x: 250, y: 0 }, data: { label: 'Regional Center A (Surplus)' }, style: { background: 'var(--primary)', color: '#fff', border: 'none', borderRadius: '8px' } },
  { id: '2', position: { x: 100, y: 150 }, data: { label: 'Hospital North (Deficit)' }, style: { background: 'var(--destructive)', color: '#fff', border: 'none', borderRadius: '8px' } },
  { id: '3', position: { x: 400, y: 150 }, data: { label: 'Blood Bank East (Stable)' }, style: { background: 'var(--chart-2)', color: '#fff', border: 'none', borderRadius: '8px' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true, label: 'Transfer: 12 units (ETA: 45m)', markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--primary)' }, style: { stroke: 'var(--primary)', strokeWidth: 2 } },
  { id: 'e1-3', source: '1', target: '3', label: 'Route available', markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--muted-foreground)' }, style: { stroke: 'var(--muted-foreground)' } },
];

export default function NetworkGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="w-full h-[600px] border border-border rounded-lg overflow-hidden bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        colorMode="dark"
      >
        <Controls className="bg-card text-foreground fill-foreground" />
        <MiniMap nodeStrokeColor={() => "var(--border)"} nodeColor={(n) => n.style?.background as string} maskColor="var(--background)" />
        <Background color="var(--muted-foreground)" gap={16} />
      </ReactFlow>
    </div>
  );
}
