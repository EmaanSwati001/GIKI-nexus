import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Share2,
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Info,
  ChevronRight,
  ExternalLink,
  Layers,
  Sparkles,
  X,
} from 'lucide-react';
import { getGraphStats, getEntitySubgraph } from '../services/api';
import { GraphData, GraphNode, GraphEdge, GraphStats } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';

const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  course: { bg: '#0284c7', border: '#0369a1', text: '#ffffff' },
  faculty: { bg: '#0d9488', border: '#0f766e', text: '#ffffff' },
  research_area: { bg: '#9333ea', border: '#7e22ce', text: '#ffffff' },
  unit: { bg: '#4f46e5', border: '#4338ca', text: '#ffffff' },
  program: { bg: '#d97706', border: '#b45309', text: '#ffffff' },
  publication: { bg: '#e11d48', border: '#be123c', text: '#ffffff' },
};

export const KnowledgeGraphPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialType = searchParams.get('entity') || 'course';
  const initialId = searchParams.get('id') || 'CS102';

  const [stats, setStats] = useState<GraphStats | null>(null);
  const [entityType, setEntityType] = useState(initialType);
  const [entityId, setEntityId] = useState(initialId);
  const [depth, setDepth] = useState<number>(1);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Canvas State: Pan & Zoom
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });

  // Load Graph Stats
  useEffect(() => {
    getGraphStats()
      .then(setStats)
      .catch((err) => console.error('Failed to load graph stats', err));
  }, []);

  // Fetch Subgraph
  const loadSubgraph = async (type: string, id: string, d: number) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getEntitySubgraph(type, id.trim(), d);
      // Position nodes radially around the center
      const nodes = (data.nodes || []).map((node, index) => {
        if (index === 0) {
          return { ...node, x: 0, y: 0 };
        }
        const angle = (2 * Math.PI * (index - 1)) / Math.max(1, data.nodes.length - 1);
        const radius = 160 + (index % 3) * 50;
        return {
          ...node,
          x: Math.cos(angle) * radius,
          y: Math.sin(angle) * radius,
        };
      });

      setGraphData({ nodes, edges: data.edges || [] });
      setSelectedNode(nodes.find((n) => n.id.toLowerCase() === id.toLowerCase()) || nodes[0] || null);
      setPan({ x: 0, y: 0 });
      setZoom(1.0);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch subgraph for entity');
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (entityId) {
      loadSubgraph(entityType, entityId, depth);
    }
  }, [entityType, entityId, depth]);

  // Render Canvas
  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
      canvas.width = width * dpr;
      canvas.height = height * dpr;
    }

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Apply Pan and Zoom centered
    const centerX = width / 2 + pan.x;
    const centerY = height / 2 + pan.y;

    ctx.translate(centerX, centerY);
    ctx.scale(zoom, zoom);

    // Draw Subtle Grid
    ctx.strokeStyle = '#f1f5f9';
    ctx.lineWidth = 1 / zoom;
    const gridSize = 40;
    const minX = -width / (2 * zoom) - pan.x / zoom;
    const maxX = width / (2 * zoom) - pan.x / zoom;
    const minY = -height / (2 * zoom) - pan.y / zoom;
    const maxY = height / (2 * zoom) - pan.y / zoom;

    ctx.beginPath();
    for (let x = Math.floor(minX / gridSize) * gridSize; x < maxX; x += gridSize) {
      ctx.moveTo(x, minY);
      ctx.lineTo(x, maxY);
    }
    for (let y = Math.floor(minY / gridSize) * gridSize; y < maxY; y += gridSize) {
      ctx.moveTo(minX, y);
      ctx.lineTo(maxX, y);
    }
    ctx.stroke();

    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      ctx.restore();
      return;
    }

    // Node lookup map
    const nodeMap = new Map<string, GraphNode>();
    graphData.nodes.forEach((n) => nodeMap.set(n.id, n));

    // Draw Edges
    (graphData.edges || []).forEach((edge) => {
      const source = nodeMap.get(edge.source);
      const target = nodeMap.get(edge.target);
      if (!source || !target) return;

      const sx = source.x || 0;
      const sy = source.y || 0;
      const tx = target.x || 0;
      const ty = target.y || 0;

      ctx.beginPath();
      ctx.strokeStyle = '#cbd5e1';
      ctx.lineWidth = 1.5;
      ctx.moveTo(sx, sy);
      ctx.lineTo(tx, ty);
      ctx.stroke();

      // Draw Edge Label at midpoint
      const midX = (sx + tx) / 2;
      const midY = (sy + ty) / 2;

      ctx.save();
      ctx.font = '9px Inter, sans-serif';
      ctx.fillStyle = '#64748b';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const edgeLabel = edge.type.replace(/_/g, ' ').toLowerCase();
      ctx.fillText(edgeLabel, midX, midY - 6);
      ctx.restore();
    });

    // Draw Nodes
    graphData.nodes.forEach((node) => {
      const nx = node.x || 0;
      const ny = node.y || 0;
      const isSelected = selectedNode?.id === node.id;
      const colors = NODE_COLORS[node.type] || { bg: '#64748b', border: '#475569', text: '#fff' };
      const radius = isSelected ? 24 : 18;

      // Selection Halo
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(nx, ny, radius + 6, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(2, 132, 199, 0.15)';
        ctx.fill();
        ctx.strokeStyle = '#0284c7';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Node Circle
      ctx.beginPath();
      ctx.arc(nx, ny, radius, 0, 2 * Math.PI);
      ctx.fillStyle = colors.bg;
      ctx.fill();
      ctx.strokeStyle = colors.border;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node Type Icon/Letter or short code
      ctx.font = 'bold 10px Inter, sans-serif';
      ctx.fillStyle = colors.text;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const initial = node.label ? node.label.slice(0, 3) : node.type[0].toUpperCase();
      ctx.fillText(initial, nx, ny);

      // Node Label Below
      ctx.font = isSelected ? 'bold 11px Inter, sans-serif' : '10px Inter, sans-serif';
      ctx.fillStyle = isSelected ? '#0f172a' : '#334155';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(node.label || node.id, nx, ny + radius + 5);
    });

    ctx.restore();
  }, [graphData, selectedNode, zoom, pan]);

  useEffect(() => {
    drawGraph();
  }, [drawGraph]);

  // Handle Canvas Mouse Drag & Click
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    dragStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDraggingRef.current) return;
    setPan({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y,
    });
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = false;
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const centerX = canvas.clientWidth / 2 + pan.x;
    const centerY = canvas.clientHeight / 2 + pan.y;

    const worldX = (mouseX - centerX) / zoom;
    const worldY = (mouseY - centerY) / zoom;

    // Check hit test
    for (const node of graphData.nodes) {
      const nx = node.x || 0;
      const ny = node.y || 0;
      const dist = Math.hypot(worldX - nx, worldY - ny);
      if (dist <= 25) {
        setSelectedNode(node);
        return;
      }
    }
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((z) => Math.min(Math.max(0.3, z * factor), 3.0));
  };

  return (
    <div className="space-y-4">
      {/* Header & Graph Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200/80 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Share2 className="w-3.5 h-3.5 text-sky-600" />
            <span>Interactive Subgraph Traversal</span>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 mt-0.5">
            Academic Knowledge Graph
          </h1>
        </div>

        {stats && (
          <div className="flex items-center gap-2 flex-wrap text-xs text-slate-500">
            <span className="font-semibold text-slate-700">
              {stats.node_count.toLocaleString()} Nodes
            </span>
            <span>•</span>
            <span className="font-semibold text-slate-700">
              {stats.edge_count.toLocaleString()} Relationships
            </span>
            <span>•</span>
            <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
              In-Memory NetworkX
            </span>
          </div>
        )}
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-start">
        {/* Left Column: Explorer Controls */}
        <div className="card p-4 space-y-4">
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Entity Type
            </label>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="input-field text-xs py-1.5 cursor-pointer"
            >
              <option value="course">Course (e.g. CS102)</option>
              <option value="faculty">Faculty Member</option>
              <option value="research_area">Research Area</option>
              <option value="unit">Academic Unit</option>
              <option value="program">Degree Program</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Entity Identifier / Code
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={entityId}
                onChange={(e) => setEntityId(e.target.value)}
                placeholder="e.g. CS102 or faculty ID"
                className="input-field text-xs py-1.5"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') loadSubgraph(entityType, entityId, depth);
                }}
              />
              <button
                onClick={() => loadSubgraph(entityType, entityId, depth)}
                className="btn-primary text-xs py-1.5 px-3 flex-shrink-0"
              >
                Go
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Traversal Depth
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDepth(1)}
                className={`py-1 text-xs font-semibold rounded-lg border transition-all ${
                  depth === 1
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                1 Hop (Direct)
              </button>
              <button
                type="button"
                onClick={() => setDepth(2)}
                className={`py-1 text-xs font-semibold rounded-lg border transition-all ${
                  depth === 2
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                2 Hops (Network)
              </button>
            </div>
          </div>

          {/* Quick Sample Explore Buttons */}
          <div className="pt-3 border-t border-slate-100">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
              Sample Entities
            </span>
            <div className="flex flex-wrap gap-1.5">
              {[
                { type: 'course', id: 'CS102', label: 'CS102' },
                { type: 'course', id: 'CS201', label: 'CS201' },
                { type: 'course', id: 'AI311', label: 'AI311' },
                { type: 'unit', id: 'fcse', label: 'FCSE Unit' },
                { type: 'program', id: 'bs_ai', label: 'BS AI' },
              ].map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setEntityType(s.type);
                    setEntityId(s.id);
                  }}
                  className="px-2 py-1 rounded text-[11px] font-mono bg-slate-50 text-slate-700 border border-slate-200 hover:border-sky-300 hover:bg-sky-50 transition-colors"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="pt-3 border-t border-slate-100 space-y-1.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Node Type Legend
            </span>
            {Object.entries(NODE_COLORS).map(([type, c]) => (
              <div key={type} className="flex items-center gap-2 text-xs text-slate-600">
                <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: c.bg }} />
                <span className="capitalize">{type.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Center: Canvas Workspace */}
        <div className="lg:col-span-3 space-y-3">
          <div className="card relative h-[560px] overflow-hidden bg-white select-none">
            {/* Canvas Toolbar overlay */}
            <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-white/90 backdrop-blur-xs p-1.5 rounded-lg border border-slate-200 shadow-xs">
              <button
                onClick={() => setZoom((z) => Math.min(3.0, z * 1.2))}
                className="p-1 rounded text-slate-600 hover:bg-slate-100"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={() => setZoom((z) => Math.max(0.3, z * 0.8))}
                className="p-1 rounded text-slate-600 hover:bg-slate-100"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setPan({ x: 0, y: 0 });
                  setZoom(1.0);
                }}
                className="p-1 rounded text-slate-600 hover:bg-slate-100"
                title="Reset View"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            </div>

            {loading && (
              <div className="absolute inset-0 z-20 bg-white/60 backdrop-blur-xs flex items-center justify-center">
                <LoadingSpinner message="Traversing graph relationships..." />
              </div>
            )}

            {error && (
              <div className="absolute inset-0 z-20 flex items-center justify-center p-6 bg-white/90">
                <div className="text-center">
                  <p className="text-sm font-semibold text-rose-700">{error}</p>
                  <button
                    onClick={() => loadSubgraph(entityType, entityId, depth)}
                    className="btn-secondary text-xs mt-3 py-1 px-3"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            <canvas
              ref={canvasRef}
              className="w-full h-full cursor-grab active:cursor-grabbing"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onClick={handleCanvasClick}
              onWheel={handleWheel}
            />
          </div>

          {/* Node Inspector Drawer / Box */}
          {selectedNode && (
            <div className="card p-4 bg-slate-50 border-slate-200">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="default" size="sm">
                      {selectedNode.type}
                    </Badge>
                    <span className="font-mono text-xs font-bold text-slate-700">
                      ID: {selectedNode.id}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900">
                    {selectedNode.label || selectedNode.id}
                  </h3>

                  {/* Render Node Details if present */}
                  {selectedNode.details && (
                    <div className="mt-2 text-xs text-slate-600 flex flex-wrap gap-x-4 gap-y-1">
                      {Object.entries(selectedNode.details)
                        .filter(([k, v]) => typeof v === 'string' || typeof v === 'number')
                        .slice(0, 4)
                        .map(([k, v]) => (
                          <span key={k}>
                            <strong className="capitalize">{k.replace('_', ' ')}:</strong>{' '}
                            {String(v)}
                          </span>
                        ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => {
                      setEntityType(selectedNode.type);
                      setEntityId(selectedNode.id);
                    }}
                    className="btn-secondary text-xs py-1 px-2.5"
                  >
                    Center Graph
                  </button>

                  {selectedNode.type === 'course' && (
                    <Link
                      to={`/courses/${selectedNode.id}`}
                      className="btn-primary text-xs py-1 px-2.5 inline-flex items-center gap-1"
                    >
                      <span>Course Page</span>
                      <ChevronRight className="w-3 h-3" />
                    </Link>
                  )}

                  {selectedNode.type === 'faculty' && (
                    <Link
                      to={`/faculty/${selectedNode.id}`}
                      className="btn-primary text-xs py-1 px-2.5 inline-flex items-center gap-1"
                    >
                      <span>Faculty Page</span>
                      <ChevronRight className="w-3 h-3" />
                    </Link>
                  )}

                  {selectedNode.type === 'program' && (
                    <Link
                      to={`/programs/${selectedNode.id}`}
                      className="btn-primary text-xs py-1 px-2.5 inline-flex items-center gap-1"
                    >
                      <span>Program Page</span>
                      <ChevronRight className="w-3 h-3" />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphPage;
