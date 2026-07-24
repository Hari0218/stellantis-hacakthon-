import React, { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import './BlastGraph.css';

export default function BlastGraph({ fullGraph, analysisResult }) {
  const fgRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const containerRef = useRef();

  useEffect(() => {
    if (containerRef.current) {
      const { width, height } = containerRef.current.getBoundingClientRect();
      setDimensions({ width, height });
    }
  }, []);

  const getRiskColor = (nodeId) => {
    if (!analysisResult) return '#4f4f65'; // base color
    
    // Highlight affected ones
    const isAffected = analysisResult.affected_nodes.includes(nodeId);
    if (!isAffected) return '#2a2a35'; // dimmed for unaffected

    const band = analysisResult.risk_band;
    if (band === 'HIGH') return '#ff4757'; // vibrant red
    if (band === 'MEDIUM') return '#ffa502'; // warning orange
    if (band === 'LOW') return '#2ed573'; // success green
    return '#3742fa'; // default accent
  };

  const getNodeSize = (node) => {
    if (node.type === 'SERVICE') return 12;
    if (node.type === 'API_ENDPOINT') return 8;
    if (node.type === 'DB_TABLE') return 10;
    return 6;
  };

  // Enhance graph data to add colors and sizes dynamically
  const enhancedData = React.useMemo(() => {
    if (!fullGraph || !fullGraph.nodes) return { nodes: [], links: [] };
    
    return {
      nodes: fullGraph.nodes.map(n => ({
        ...n,
        color: getRiskColor(n.id),
        val: getNodeSize(n)
      })),
      links: fullGraph.links.map(l => ({
        ...l,
        color: analysisResult?.affected_nodes.includes(l.source) || analysisResult?.affected_nodes.includes(l.target) 
          ? 'rgba(255,255,255,0.4)' 
          : 'rgba(255,255,255,0.05)'
      }))
    };
  }, [fullGraph, analysisResult]);

  useEffect(() => {
    // Re-center on update
    if (fgRef.current && enhancedData.nodes.length > 0) {
      fgRef.current.d3Force('charge').strength(-200);
      fgRef.current.zoomToFit(400);
    }
  }, [enhancedData]);

  if (!fullGraph) {
    return <div className="graph-loading">Loading graph dependencies...</div>;
  }

  return (
    <div ref={containerRef} className="blast-graph-container glass-panel">
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={enhancedData}
        nodeLabel="id"
        nodeColor="color"
        nodeRelSize={1}
        nodeVal="val"
        linkColor="color"
        linkDirectionalParticles={d => 
          (analysisResult?.affected_nodes.includes(typeof d.source === 'object' ? d.source.id : d.source) && 
           analysisResult?.affected_nodes.includes(typeof d.target === 'object' ? d.target.id : d.target)) ? 4 : 0
        }
        linkDirectionalParticleSpeed={0.005}
        backgroundColor="transparent"
      />
      <div className="graph-overlay">
        <h3>System Dependency Map</h3>
        <div className="legend">
          <span className="legend-item"><span className="dot service"></span> Services</span>
          <span className="legend-item"><span className="dot api"></span> Routes</span>
          <span className="legend-item"><span className="dot db"></span> Database</span>
        </div>
      </div>
    </div>
  );
}
