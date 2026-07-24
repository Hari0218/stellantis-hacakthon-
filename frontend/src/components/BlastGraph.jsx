import React, { useRef, useEffect, useState, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import './BlastGraph.css';

const TYPE_COLOR = {
  SERVICE:      '#6c5ce7',
  API_ENDPOINT: '#f39c12',
  DB_TABLE:     '#27ae60',
  FILE:         '#4a90e2',
};

export default function BlastGraph({ fullGraph, analysisResult }) {
  const fgRef       = useRef();
  const containerRef = useRef();
  const [dims, setDims] = useState({ width: 900, height: 640 });

  /* ── Measure container robustly ── */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => {
      const r = el.getBoundingClientRect();
      if (r.width > 50 && r.height > 50) {
        setDims({ width: r.width, height: r.height });
      }
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const affectedSet = useMemo(
    () => new Set(analysisResult?.affected_nodes || []),
    [analysisResult]
  );

  const scale = analysisResult?.change_scale;

  const hitColor = scale === 'major' ? '#ff4757'
    : scale === 'moderate' ? '#ffa502'
    : '#2ed573';

  /* ── Build enhanced graph data ── */
  const graphData = useMemo(() => {
    if (!fullGraph?.nodes) return { nodes: [], links: [] };

    const nodes = fullGraph.nodes.map(n => {
      const hit = affectedSet.has(n.id);
      return {
        ...n,
        color: hit ? hitColor : (TYPE_COLOR[n.type] || '#4f4f65'),
        val:   n.type === 'SERVICE' ? 14 : n.type === 'DB_TABLE' ? 11 : n.type === 'API_ENDPOINT' ? 9 : 7,
        __hit: hit,
      };
    });

    const links = (fullGraph.links || []).map(l => {
      const src = typeof l.source === 'object' ? l.source.id : l.source;
      const tgt = typeof l.target === 'object' ? l.target.id : l.target;
      const hot = affectedSet.has(src) || affectedSet.has(tgt);
      return { ...l, color: hot ? 'rgba(255,100,100,0.6)' : 'rgba(255,255,255,0.07)', __hot: hot };
    });

    return { nodes, links };
  }, [fullGraph, affectedSet, hitColor]);

  /* ── Zoom to fit after data changes ── */
  useEffect(() => {
    if (!fgRef.current || graphData.nodes.length === 0) return;
    const t = setTimeout(() => {
      fgRef.current?.d3Force('charge')?.strength(-250);
      fgRef.current?.zoomToFit(600, 60);
    }, 400);
    return () => clearTimeout(t);
  }, [graphData]);

  const nodeCount    = graphData.nodes.length;
  const affectedCount = affectedSet.size;

  /* ── Node label painter ── */
  const paintNode = (node, ctx, globalScale) => {
    const r = Math.sqrt(node.val) * 1.6;
    // circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = node.color;
    ctx.fill();
    // glow for affected
    if (node.__hit) {
      ctx.shadowBlur = 18;
      ctx.shadowColor = node.color;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
    // label when zoomed in
    if (globalScale > 1.8) {
      const label = (node.id || '').split('/').pop() || node.id;
      ctx.font = `${Math.max(8, 11 / globalScale)}px sans-serif`;
      ctx.fillStyle = '#fff';
      ctx.textAlign = 'center';
      ctx.fillText(label, node.x, node.y + r + 7);
    }
  };

  return (
    <div className="blast-graph-wrapper">
      {/* Header bar */}
      <div className="graph-header">
        <div className="graph-title-row">
          <h3>🕸 Dependency Graph</h3>
          <span className="graph-stats">
            {nodeCount} nodes
            {affectedCount > 0 && <span className="affected-stat"> · {affectedCount} affected</span>}
          </span>
        </div>
        <div className="legend">
          <span className="legend-item"><span className="dot svc"></span>Services</span>
          <span className="legend-item"><span className="dot api"></span>Routes</span>
          <span className="legend-item"><span className="dot db"></span>Database</span>
          <span className="legend-item"><span className="dot file"></span>Files</span>
          {affectedCount > 0 && <span className="legend-item"><span className="dot affected"></span>Affected</span>}
        </div>
      </div>

      {/* Canvas */}
      {!fullGraph ? (
        <div className="graph-loading">
          <span className="spinner-lg" />
          Loading dependency graph…
        </div>
      ) : nodeCount === 0 ? (
        <div className="graph-loading">No nodes found in graph data.</div>
      ) : (
        <div ref={containerRef} className="blast-graph-canvas">
          <ForceGraph2D
            ref={fgRef}
            width={dims.width}
            height={dims.height}
            graphData={graphData}
            nodeCanvasObject={paintNode}
            nodeCanvasObjectMode={() => 'replace'}
            linkColor="color"
            linkWidth={l => l.__hot ? 2 : 1}
            linkDirectionalArrowLength={5}
            linkDirectionalArrowRelPos={1}
            linkDirectionalParticles={l => l.__hot ? 4 : 0}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleColor={() => hitColor}
            backgroundColor="transparent"
            enableZoomInteraction
            enablePanInteraction
            onNodeClick={node => {
              fgRef.current?.centerAt(node.x, node.y, 500);
              fgRef.current?.zoom(3.5, 500);
            }}
          />
        </div>
      )}

      {/* Help text */}
      <div className="graph-footer">
        Click a node to zoom in · Scroll to zoom · Drag to pan
      </div>
    </div>
  );
}
