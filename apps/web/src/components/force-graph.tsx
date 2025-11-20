'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import * as d3 from 'd3-force';
import { select } from 'd3-selection';
import { zoom as d3Zoom, zoomIdentity } from 'd3-zoom';
import { drag as d3Drag } from 'd3-drag';
import 'd3-transition'; // Adds transition methods to selections
import type { DependencyGraphNode, DependencyGraphEdge } from '@/lib/db';

interface ForceGraphProps {
  data: {
    nodes: DependencyGraphNode[];
    edges: DependencyGraphEdge[];
  };
}

interface SimulationNode extends d3.SimulationNodeDatum, DependencyGraphNode {
  x?: number;
  y?: number;
}

interface SimulationLink extends d3.SimulationLinkDatum<SimulationNode> {
  source: SimulationNode | number;
  target: SimulationNode | number;
  shared_dependencies: string[];
}

export function ForceGraph({ data }: ForceGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!svgRef.current || data.nodes.length === 0) return;

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Clear existing content
    select(svgRef.current).selectAll('*').remove();

    // Create SVG groups
    const svg = select(svgRef.current);
    const g = svg.append('g');

    // Setup zoom behavior
    const zoomBehavior = d3Zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoomBehavior);

    // Prepare data for simulation
    const nodes: SimulationNode[] = data.nodes.map(d => ({ ...d }));
    const links: SimulationLink[] = data.edges.map(d => ({
      source: d.source,
      target: d.target,
      shared_dependencies: d.shared_dependencies
    }));

    // Create force simulation
    const simulation = d3.forceSimulation<SimulationNode>(nodes)
      .force('link', d3.forceLink<SimulationNode, SimulationLink>(links)
        .id(d => d.id)
        .distance(100)
        .strength(0.5)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.3)
      .attr('stroke-width', d => Math.min(d.shared_dependencies.length, 5));

    // Helper function to get node color based on risk level
    const getNodeColor = (riskLevel: string): string => {
      switch (riskLevel.toLowerCase()) {
        case 'safe':
          return '#22c55e'; // green-500
        case 'moderate':
          return '#eab308'; // yellow-500
        case 'high':
        case 'critical':
          return '#ef4444'; // red-500
        default:
          return '#9ca3af'; // gray-400
      }
    };

    // Create drag behavior
    const dragBehavior = d3Drag<SVGGElement, SimulationNode>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    // Create nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .call(dragBehavior as any);

    // Add circles to nodes
    node.append('circle')
      .attr('r', d => Math.max(5, Math.min(20, Math.sqrt(d.stars) / 2)))
      .attr('fill', d => getNodeColor(d.risk_level))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d.id);

        // Highlight connected nodes
        const connectedNodeIds = new Set<number>();
        links.forEach(l => {
          const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
          const targetId = typeof l.target === 'object' ? l.target.id : l.target;

          if (sourceId === d.id) connectedNodeIds.add(targetId);
          if (targetId === d.id) connectedNodeIds.add(sourceId);
        });

        // Update node opacity
        node.selectAll('circle')
          .attr('opacity', (n) => {
            const nodeData = n as SimulationNode;
            return nodeData.id === d.id || connectedNodeIds.has(nodeData.id) ? 1 : 0.2;
          });

        // Update link opacity
        link.attr('opacity', (l) => {
          const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
          const targetId = typeof l.target === 'object' ? l.target.id : l.target;
          return sourceId === d.id || targetId === d.id ? 0.8 : 0.1;
        });
      })
      .on('dblclick', (event, d) => {
        event.stopPropagation();
        router.push(`/servers/${d.id}`);
      });

    // Add labels to nodes
    node.append('text')
      .text(d => d.name.length > 20 ? d.name.substring(0, 17) + '...' : d.name)
      .attr('x', 0)
      .attr('y', d => Math.max(5, Math.min(20, Math.sqrt(d.stars) / 2)) + 12)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'currentColor')
      .attr('class', 'pointer-events-none select-none')
      .style('opacity', 0.8);

    // Add tooltips
    node.append('title')
      .text(d => `${d.name}\nStars: ${d.stars}\nRisk: ${d.risk_level}\nType: ${d.host_type}`);

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as SimulationNode).x ?? 0)
        .attr('y1', d => (d.source as SimulationNode).y ?? 0)
        .attr('x2', d => (d.target as SimulationNode).x ?? 0)
        .attr('y2', d => (d.target as SimulationNode).y ?? 0);

      node.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    // Reset selection on background click
    svg.on('click', () => {
      setSelectedNode(null);
      node.selectAll('circle').attr('opacity', 1);
      link.attr('opacity', 0.3);
    });

    // Initial zoom to fit content
    const bounds = g.node()?.getBBox();
    if (bounds) {
      const fullWidth = bounds.width;
      const fullHeight = bounds.height;
      const midX = bounds.x + fullWidth / 2;
      const midY = bounds.y + fullHeight / 2;

      if (fullWidth > 0 && fullHeight > 0) {
        const scale = Math.min(
          0.9 * width / fullWidth,
          0.9 * height / fullHeight,
          1
        );

        const transform = zoomIdentity
          .translate(width / 2, height / 2)
          .scale(scale)
          .translate(-midX, -midY);

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        svg.transition().duration(750).call(zoomBehavior.transform as any, transform);
      }
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [data, router]);

  if (data.nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            No dependency data available
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            Run the harvester to populate the dependency graph
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative bg-white dark:bg-gray-900">
      <svg
        ref={svgRef}
        className="w-full h-full text-gray-900 dark:text-gray-100"
        style={{ cursor: 'grab' }}
      />

      {selectedNode !== null && (
        <div className="absolute top-4 left-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg shadow-lg p-4 max-w-xs">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Selected Node
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Double-click on a node to view its details
          </p>
          <button
            onClick={() => {
              setSelectedNode(null);
              const svg = select(svgRef.current);
              svg.selectAll('circle').attr('opacity', 1);
              svg.selectAll('line').attr('opacity', 0.3);
            }}
            className="mt-3 text-sm text-[var(--primary)] hover:underline"
          >
            Clear selection
          </button>
        </div>
      )}
    </div>
  );
}
