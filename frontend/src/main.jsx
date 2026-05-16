import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import Papa from "papaparse";
import cytoscape from "cytoscape";
import {
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  Gauge,
  Layers3,
  Network,
  RotateCcw,
  Search,
  SlidersHorizontal,
  TriangleAlert,
} from "lucide-react";
import "./styles.css";

const DATA_PATH = "/data/ranked_tech_resumes.csv";
const TAXONOMY_PATH = "/data/skill_taxonomy.json";
const GRAPH_PATH = "/data/skill_graph.json";

const COMPETENCIES = [
  {
    id: "agentic_ai",
    label: "Agentic AI",
    domains: ["machine_learning_ai", "ml_frameworks_libraries"],
    hints: [
      "rag",
      "llm",
      "large language models",
      "fine-tuning",
      "fine tuning",
      "vector database",
      "vector databases",
      "mlops",
      "machine learning",
      "artificial intelligence",
      "model evaluation",
      "model training",
      "generative ai",
      "nlp",
      "computer vision",
      "pytorch",
      "tensorflow",
      "scikit-learn",
      "keras",
    ],
  },
  {
    id: "deployment_scaling",
    label: "Deployment & Scaling",
    domains: ["cloud_devops", "networking_security"],
    hints: [
      "deployment",
      "scaling",
      "production",
      "ci/cd",
      "docker",
      "kubernetes",
      "cloud",
      "aws",
      "azure",
      "gcp",
      "linux",
      "monitoring",
      "devops",
      "jenkins",
      "networking",
      "security",
    ],
  },
  {
    id: "data_layer",
    label: "Data Layer",
    domains: ["databases", "data_engineering_big_data"],
    hints: [
      "sql",
      "nosql",
      "mysql",
      "postgresql",
      "mongodb",
      "redis",
      "elasticsearch",
      "database",
      "database design",
      "data pipeline",
      "etl",
      "spark",
      "hadoop",
      "data warehouse",
      "data warehousing",
      "vector database",
    ],
  },
  {
    id: "backend_integration",
    label: "Backend & Integration",
    domains: ["backend", "software_engineering"],
    hints: [
      "api",
      "apis",
      "rest api",
      "graphql",
      "microservices",
      "backend",
      "server-side",
      "integration",
      "auth",
      "authentication",
      "node.js",
      "django",
      "flask",
      "spring boot",
      "asp.net",
      "software development",
    ],
  },
  {
    id: "product_engineering",
    label: "Product Engineering",
    domains: ["frontend", "mobile_development", "software_engineering"],
    hints: [
      "frontend",
      "react",
      "javascript",
      "typescript",
      "html",
      "css",
      "ui",
      "ios",
      "android",
      "mobile",
      "testing",
      "debugging",
      "quality assurance",
      "requirements",
    ],
  },
  {
    id: "analytics_insight",
    label: "Analytics & Insight",
    domains: ["analytics_bi"],
    hints: [
      "analytics",
      "data analysis",
      "business analysis",
      "dashboard",
      "tableau",
      "power bi",
      "excel",
      "reporting",
      "statistics",
      "data visualization",
    ],
  },
];

const FALLBACK_COMPETENCY = {
  id: "core_match",
  label: "Core Match",
  domains: [],
  hints: [],
};

function parseList(value) {
  if (!value || value === "nan") return [];

  try {
    const normalized = String(value).replaceAll("'", '"');
    const parsed = JSON.parse(normalized);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => String(item).trim()).filter(Boolean);
    }
  } catch {
    return String(value)
      .split(/[;,]/)
      .map((item) => item.replace(/[[\]'"]/g, "").trim())
      .filter(Boolean);
  }

  return [];
}

function normalizeSkill(skill) {
  return String(skill || "").trim().toLowerCase();
}

function buildSkillDomainMap(taxonomy) {
  const map = new Map();
  Object.entries(taxonomy || {}).forEach(([domain, skills]) => {
    skills.forEach((skill) => map.set(normalizeSkill(skill), domain));
  });
  return map;
}

function valueToPercent(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  return Math.max(0, Math.min(100, Math.round(number * 100)));
}

function getCandidateLabel(candidate) {
  if (!candidate) return "No candidate";
  const role = candidate.job_position_name || "Candidate";
  const score = valueToPercent(candidate.final_fit_score);
  return `${role} - ${score}%`;
}

function competencyForSkill(skill, skillDomainMap) {
  const normalized = normalizeSkill(skill);
  const domain = skillDomainMap.get(normalized);
  return (
    COMPETENCIES.find((competency) => {
      const domainMatch = domain && competency.domains.includes(domain);
      const hintMatch = competency.hints.some((hint) => normalized.includes(hint));
      return domainMatch || hintMatch;
    }) || FALLBACK_COMPETENCY
  );
}

function getJobCompetencies(jobRows, skillDomainMap) {
  const skillCounts = new Map();
  const text = jobRows
    .slice(0, 25)
    .map((row) => row.job_text || row.job_position_name || "")
    .join(" ")
    .toLowerCase();

  jobRows.forEach((row) => {
    parseList(row.job_skills_filtered).forEach((skill) => {
      const normalized = normalizeSkill(skill);
      skillCounts.set(normalized, (skillCounts.get(normalized) || 0) + 1);
    });
  });

  const competencyData = COMPETENCIES.map((competency) => {
    const skills = [...skillCounts.keys()].filter((skill) => {
      const domain = skillDomainMap.get(skill);
      const domainMatch = domain && competency.domains.includes(domain);
      const hintMatch = competency.hints.some((hint) => skill.includes(hint));
      return domainMatch || hintMatch;
    });

    const skillScore = skills.reduce((sum, skill) => sum + skillCounts.get(skill), 0);
    const hintScore = competency.hints.reduce(
      (sum, hint) => sum + (text.includes(hint) ? 2 : 0),
      0,
    );

    return {
      ...competency,
      skills,
      relevance: skillScore + hintScore,
    };
  })
    .filter((competency) => competency.relevance > 0)
    .sort((a, b) => b.relevance - a.relevance)
    .slice(0, 6);

  if (competencyData.length >= 4) return competencyData;

  const used = new Set(competencyData.map((competency) => competency.id));
  for (const competency of COMPETENCIES) {
    if (!used.has(competency.id)) {
      competencyData.push({
        ...competency,
        skills: [],
        relevance: 0,
      });
    }
    if (competencyData.length === 4) break;
  }

  return competencyData;
}

function scoreCandidateForCompetency(candidate, competency, skillDomainMap) {
  const resumeSkills = new Set(parseList(candidate.resume_skills_filtered).map(normalizeSkill));
  const jobSkills = parseList(candidate.job_skills_filtered).map(normalizeSkill);

  const competencySkills = jobSkills.filter((skill) => {
    const match = competencyForSkill(skill, skillDomainMap);
    return match.id === competency.id;
  });

  const requiredSkills = competencySkills.length > 0 ? competencySkills : competency.skills;
  const matchedSkills = requiredSkills.filter((skill) => resumeSkills.has(normalizeSkill(skill)));
  const coverage =
    requiredSkills.length > 0 ? matchedSkills.length / requiredSkills.length : Number(candidate.direct_match || 0);

  const evidenceBase = Number(candidate.project_evidence_score || 0);
  const evidence = matchedSkills.length > 0 ? evidenceBase : 0;
  const alignment = Number(candidate.role_domain_alignment || 0);
  const score = 100 * (coverage * 0.7 + evidence * 0.2 + alignment * 0.1);

  return {
    score: Math.round(Math.max(0, Math.min(100, score))),
    matchedSkills,
    missingSkills: requiredSkills.filter((skill) => !resumeSkills.has(normalizeSkill(skill))),
    requiredSkills,
  };
}

function buildRadarRows(selectedCandidate, benchmarkCandidate, competencies, skillDomainMap) {
  return competencies.map((competency) => {
    const selected = scoreCandidateForCompetency(selectedCandidate, competency, skillDomainMap);
    const benchmark = scoreCandidateForCompetency(benchmarkCandidate, competency, skillDomainMap);

    return {
      metric: competency.label,
      selected: selected.score,
      benchmark: benchmark.score,
      requiredSkills: selected.requiredSkills,
      selectedMatched: selected.matchedSkills,
      selectedMissing: selected.missingSkills,
    };
  });
}

function formatScore(value) {
  return `${valueToPercent(value)}%`;
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b));
}

function titleCase(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function normalizeGraph(rawGraph) {
  const nodes = rawGraph?.nodes || [];
  const edges = rawGraph?.edges || rawGraph?.links || [];

  return {
    nodes,
    edges,
  };
}

function domainOptions(graph) {
  return uniqueSorted(
    graph.nodes
      .filter((node) => node.node_type === "domain")
      .map((node) => node.id),
  );
}

function buildGraphElements(graph, filters) {
  const { selectedDomain, edgeType, minWeight } = filters;
  const allowedNodeIds = new Set();
  const taxonomyEdges = graph.edges.filter((edge) => edge.relation === "belongs_to_domain");

  graph.nodes.forEach((node) => {
    if (!selectedDomain || node.node_type === "domain" || node.domain === selectedDomain) {
      allowedNodeIds.add(node.id);
    }
  });

  if (selectedDomain) {
    taxonomyEdges
      .filter((edge) => edge.target === selectedDomain)
      .forEach((edge) => {
        allowedNodeIds.add(edge.source);
        allowedNodeIds.add(edge.target);
      });
  }

  const nodes = graph.nodes
    .filter((node) => allowedNodeIds.has(node.id))
    .map((node) => ({
      data: {
        id: node.id,
        label: node.id,
        nodeType: node.node_type,
        domain: node.domain || node.id,
      },
      classes: node.node_type === "domain" ? "domain-node" : "skill-node",
    }));

  const edges = graph.edges
    .filter((edge) => {
      if (!allowedNodeIds.has(edge.source) || !allowedNodeIds.has(edge.target)) return false;
      if (edgeType !== "all" && edge.relation !== edgeType) return false;
      if (edge.relation === "co_occurs" && Number(edge.weight || 0) < minWeight) return false;
      return true;
    })
    .map((edge, index) => ({
      data: {
        id: `${edge.source}-${edge.target}-${index}`,
        source: edge.source,
        target: edge.target,
        weight: Number(edge.weight || 1),
        relation: edge.relation,
      },
      classes: edge.relation === "belongs_to_domain" ? "taxonomy-edge" : "semantic-edge",
    }));

  return [...nodes, ...edges];
}

function graphStats(graph) {
  return {
    skills: graph.nodes.filter((node) => node.node_type === "skill").length,
    domains: graph.nodes.filter((node) => node.node_type === "domain").length,
    edges: graph.edges.length,
  };
}

function nodeDetails(graph, nodeId) {
  if (!nodeId) return null;

  const node = graph.nodes.find((item) => item.id === nodeId);
  if (!node) return null;

  const connectedEdges = graph.edges
    .filter((edge) => edge.source === nodeId || edge.target === nodeId)
    .sort((a, b) => Number(b.weight || 0) - Number(a.weight || 0));

  const strongest = connectedEdges
    .filter((edge) => edge.relation === "co_occurs")
    .slice(0, 10)
    .map((edge) => ({
      skill: edge.source === nodeId ? edge.target : edge.source,
      weight: edge.weight,
    }));

  const domainSkills =
    node.node_type === "domain"
      ? graph.nodes
          .filter((item) => item.node_type === "skill" && item.domain === node.id)
          .map((item) => item.id)
      : [];

  return {
    node,
    strongest,
    domainSkills,
    edgeCount: connectedEdges.length,
  };
}

function axisPoint(index, total, center, radius) {
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total;
  return {
    x: center + Math.cos(angle) * radius,
    y: center + Math.sin(angle) * radius,
    angle,
  };
}

function polygonPoints(rows, key, center, radius) {
  return rows
    .map((row, index) => {
      const value = Math.max(0, Math.min(100, Number(row[key] || 0)));
      const point = axisPoint(index, rows.length, center, radius * (value / 100));
      return `${point.x},${point.y}`;
    })
    .join(" ");
}

function RadarGraphic({ rows }) {
  const center = 260;
  const radius = 176;
  const rings = [20, 40, 60, 80, 100];

  if (!rows.length) {
    return <div className="empty-radar">No radar data available for this role.</div>;
  }

  return (
    <svg className="radar-svg" viewBox="0 0 520 520" role="img" aria-label="Candidate radar chart">
      {rings.map((ring) => (
        <polygon
          className="radar-ring"
          key={ring}
          points={rows
            .map((_, index) => {
              const point = axisPoint(index, rows.length, center, radius * (ring / 100));
              return `${point.x},${point.y}`;
            })
            .join(" ")}
        />
      ))}

      {rows.map((row, index) => {
        const point = axisPoint(index, rows.length, center, radius);
        const labelPoint = axisPoint(index, rows.length, center, radius + 48);
        const anchor =
          Math.abs(Math.cos(point.angle)) < 0.2
            ? "middle"
            : Math.cos(point.angle) > 0
              ? "start"
              : "end";

        return (
          <g key={row.metric}>
            <line className="radar-axis" x1={center} y1={center} x2={point.x} y2={point.y} />
            <circle className="radar-dot muted-dot" cx={point.x} cy={point.y} r="4" />
            <text
              className="radar-label"
              x={labelPoint.x}
              y={labelPoint.y}
              textAnchor={anchor}
              dominantBaseline="middle"
            >
              {row.metric}
            </text>
          </g>
        );
      })}

      <polygon className="radar-area benchmark-area" points={polygonPoints(rows, "benchmark", center, radius)} />
      <polygon className="radar-area selected-area" points={polygonPoints(rows, "selected", center, radius)} />
      <polygon className="radar-line benchmark-line" points={polygonPoints(rows, "benchmark", center, radius)} />
      <polygon className="radar-line selected-line" points={polygonPoints(rows, "selected", center, radius)} />

      {rows.map((row, index) => {
        const selected = axisPoint(index, rows.length, center, radius * (row.selected / 100));
        const benchmark = axisPoint(index, rows.length, center, radius * (row.benchmark / 100));
        return (
          <g key={`${row.metric}-points`}>
            <circle className="radar-dot benchmark-dot" cx={benchmark.x} cy={benchmark.y} r="5" />
            <circle className="radar-dot selected-dot" cx={selected.x} cy={selected.y} r="5" />
          </g>
        );
      })}
    </svg>
  );
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error) {
    console.error(error);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="status-screen">
          <TriangleAlert aria-hidden="true" />
          <p>Frontend crashed: {this.state.error.message}</p>
        </main>
      );
    }

    return this.props.children;
  }
}

function SkillGraphView({ graph }) {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [edgeType, setEdgeType] = useState("all");
  const [minWeight, setMinWeight] = useState(120);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedNodeId, setSelectedNodeId] = useState("");

  const domains = useMemo(() => domainOptions(graph), [graph]);
  const filters = useMemo(
    () => ({ selectedDomain, edgeType, minWeight }),
    [selectedDomain, edgeType, minWeight],
  );
  const elements = useMemo(() => buildGraphElements(graph, filters), [graph, filters]);
  const stats = useMemo(() => graphStats(graph), [graph]);
  const details = useMemo(() => nodeDetails(graph, selectedNodeId), [graph, selectedNodeId]);

  useEffect(() => {
    if (!containerRef.current) return undefined;

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      minZoom: 0.22,
      maxZoom: 2.2,
      wheelSensitivity: 0.18,
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 10,
            "font-weight": 700,
            color: "#263241",
            "text-valign": "center",
            "text-halign": "center",
            "text-wrap": "wrap",
            "text-max-width": 82,
            "background-color": "#8fb7b0",
            "border-color": "#ffffff",
            "border-width": 2,
            width: 34,
            height: 34,
          },
        },
        {
          selector: ".domain-node",
          style: {
            "background-color": "#197b73",
            color: "#ffffff",
            width: 72,
            height: 72,
            "font-size": 11,
            "text-max-width": 68,
          },
        },
        {
          selector: ".skill-node",
          style: {
            "background-color": "#d7e9e5",
          },
        },
        {
          selector: "edge",
          style: {
            width: "mapData(weight, 1, 1400, 1, 8)",
            "line-color": "#9aa8b5",
            opacity: 0.55,
            "curve-style": "bezier",
          },
        },
        {
          selector: ".taxonomy-edge",
          style: {
            "line-color": "#c6d4d0",
            width: 1.2,
            opacity: 0.45,
          },
        },
        {
          selector: ".semantic-edge",
          style: {
            "line-color": "#7185a8",
          },
        },
        {
          selector: ".highlighted",
          style: {
            "background-color": "#c437ad",
            "border-color": "#ffffff",
            "border-width": 4,
            color: "#ffffff",
          },
        },
        {
          selector: ".faded",
          style: {
            opacity: 0.18,
          },
        },
      ],
      layout: {
        name: "cose",
        animate: false,
        fit: true,
        padding: 36,
        nodeRepulsion: 9000,
        idealEdgeLength: 95,
        gravity: 0.38,
        numIter: 1000,
      },
    });

    cy.on("tap", "node", (event) => {
      const nodeId = event.target.id();
      setSelectedNodeId(nodeId);
      cy.elements().removeClass("highlighted faded");
      event.target.addClass("highlighted");
      event.target.neighborhood().addClass("highlighted");
      cy.elements().difference(event.target.closedNeighborhood()).addClass("faded");
    });

    cy.on("tap", (event) => {
      if (event.target === cy) {
        setSelectedNodeId("");
        cy.elements().removeClass("highlighted faded");
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [elements]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    const term = searchTerm.trim().toLowerCase();
    cy.elements().removeClass("highlighted faded");

    if (!term) return;

    const match = cy.nodes().filter((node) => node.id().toLowerCase().includes(term));
    if (!match.length) return;

    const node = match[0];
    setSelectedNodeId(node.id());
    node.addClass("highlighted");
    node.neighborhood().addClass("highlighted");
    cy.elements().difference(node.closedNeighborhood()).addClass("faded");
    cy.animate(
      {
        center: { eles: node },
        zoom: 1.2,
      },
      { duration: 350 },
    );
  }, [searchTerm]);

  function resetGraph() {
    setSearchTerm("");
    setSelectedNodeId("");
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass("highlighted faded");
    cy.fit(undefined, 36);
  }

  return (
    <>
      <aside className="sidebar graph-sidebar">
        <div className="brand-row">
          <Network aria-hidden="true" />
          <div>
            <p className="eyebrow">Knowledge Graph</p>
            <h1>Skill Explorer</h1>
          </div>
        </div>

        <label className="field-label" htmlFor="domain-filter">
          Domain filter
        </label>
        <select
          id="domain-filter"
          value={selectedDomain}
          onChange={(event) => setSelectedDomain(event.target.value)}
        >
          <option value="">All domains</option>
          {domains.map((domain) => (
            <option key={domain} value={domain}>
              {titleCase(domain)}
            </option>
          ))}
        </select>

        <label className="field-label" htmlFor="edge-type">
          Edge type
        </label>
        <select
          id="edge-type"
          value={edgeType}
          onChange={(event) => setEdgeType(event.target.value)}
        >
          <option value="all">All relationships</option>
          <option value="co_occurs">Semantic co-occurrence</option>
          <option value="belongs_to_domain">Taxonomy only</option>
        </select>

        <label className="field-label" htmlFor="edge-weight">
          Minimum co-occurrence weight
        </label>
        <div className="range-control">
          <SlidersHorizontal aria-hidden="true" />
          <input
            id="edge-weight"
            max="600"
            min="0"
            onChange={(event) => setMinWeight(Number(event.target.value))}
            type="range"
            value={minWeight}
          />
          <strong>{minWeight}</strong>
        </div>

        <label className="field-label" htmlFor="graph-search">
          Search skill
        </label>
        <div className="search-box">
          <Search aria-hidden="true" />
          <input
            id="graph-search"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="python, sql, docker..."
          />
        </div>

        <button className="utility-button" type="button" onClick={resetGraph}>
          <RotateCcw aria-hidden="true" />
          Reset view
        </button>

        <section className="graph-stat-grid">
          <div>
            <span>Skills</span>
            <strong>{stats.skills}</strong>
          </div>
          <div>
            <span>Domains</span>
            <strong>{stats.domains}</strong>
          </div>
          <div>
            <span>Edges</span>
            <strong>{stats.edges}</strong>
          </div>
        </section>
      </aside>

      <section className="main-panel graph-main">
        <div className="toolbar">
          <div>
            <p className="eyebrow">Interactive graph</p>
            <h2>Skills, domains, and semantic links</h2>
          </div>
          <div className="legend">
            <span className="legend-item domain">Domain</span>
            <span className="legend-item skill">Skill</span>
            <span className="legend-item semantic">Co-occurs</span>
          </div>
        </div>
        <section className="graph-canvas" ref={containerRef} />
      </section>

      <aside className="detail-panel">
        <div className="panel-heading">
          <Layers3 aria-hidden="true" />
          <div>
            <p className="eyebrow">Explainability</p>
            <h2>{details ? details.node.id : "Select a node"}</h2>
          </div>
        </div>

        {details ? (
          <>
            <section className="node-summary">
              <div>
                <span>Type</span>
                <strong>{titleCase(details.node.node_type)}</strong>
              </div>
              <div>
                <span>Domain</span>
                <strong>{titleCase(details.node.domain || details.node.id)}</strong>
              </div>
              <div>
                <span>Connections</span>
                <strong>{details.edgeCount}</strong>
              </div>
            </section>

            {details.node.node_type === "domain" ? (
              <section>
                <h3><CheckCircle2 aria-hidden="true" /> Domain skills</h3>
                <div className="chip-list">
                  {details.domainSkills.slice(0, 24).map((skill) => (
                    <span className="chip positive" key={skill}>{skill}</span>
                  ))}
                </div>
              </section>
            ) : (
              <section>
                <h3><CheckCircle2 aria-hidden="true" /> Strongest related skills</h3>
                <div className="related-list">
                  {details.strongest.length ? (
                    details.strongest.map((item) => (
                      <div key={`${item.skill}-${item.weight}`}>
                        <span>{item.skill}</span>
                        <strong>{item.weight}</strong>
                      </div>
                    ))
                  ) : (
                    <p className="muted">No co-occurrence links visible for this node.</p>
                  )}
                </div>
              </section>
            )}
          </>
        ) : (
          <p className="muted">
            Click a skill or domain to see its strongest relationships and why it matters for ranking explainability.
          </p>
        )}
      </aside>
    </>
  );
}

function App() {
  const [rows, setRows] = useState([]);
  const [taxonomy, setTaxonomy] = useState({});
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [status, setStatus] = useState("loading");
  const [activeView, setActiveView] = useState("radar");
  const [selectedRole, setSelectedRole] = useState("");
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(1);

  useEffect(() => {
    async function loadData() {
      try {
        const [csvText, taxonomyJson, graphJson] = await Promise.all([
          fetch(DATA_PATH).then((response) => {
            if (!response.ok) throw new Error("Could not load ranking CSV");
            return response.text();
          }),
          fetch(TAXONOMY_PATH).then((response) => {
            if (!response.ok) throw new Error("Could not load taxonomy JSON");
            return response.json();
          }),
          fetch(GRAPH_PATH).then((response) => {
            if (!response.ok) throw new Error("Could not load graph JSON");
            return response.json();
          }),
        ]);

        const parsed = Papa.parse(csvText, {
          header: true,
          dynamicTyping: true,
          skipEmptyLines: true,
        });

        const validRows = parsed.data.filter((row) => row.job_position_name);
        setRows(validRows);
        setTaxonomy(taxonomyJson);
        setGraph(normalizeGraph(graphJson));
        setSelectedRole(validRows[0]?.job_position_name || "");
        setStatus("ready");
      } catch (error) {
        console.error(error);
        setStatus("error");
      }
    }

    loadData();
  }, []);

  const skillDomainMap = useMemo(() => buildSkillDomainMap(taxonomy), [taxonomy]);
  const roles = useMemo(
    () => uniqueSorted(rows.map((row) => row.job_position_name)),
    [rows],
  );
  const roleRows = useMemo(
    () =>
      rows
        .filter((row) => row.job_position_name === selectedRole)
        .sort((a, b) => Number(b.final_fit_score || 0) - Number(a.final_fit_score || 0)),
    [rows, selectedRole],
  );

  useEffect(() => {
    setSelectedIndex(roleRows.length > 1 ? 1 : 0);
  }, [selectedRole, roleRows.length]);

  const filteredCandidates = useMemo(() => {
    const cleanQuery = query.trim().toLowerCase();
    if (!cleanQuery) return roleRows.slice(0, 30);
    return roleRows
      .filter((row, index) => {
        const text = `${index + 1} ${row.resume_skills_filtered} ${row.resume_text}`.toLowerCase();
        return text.includes(cleanQuery);
      })
      .slice(0, 30);
  }, [query, roleRows]);

  const benchmarkCandidate = roleRows[0];
  const selectedCandidate = roleRows[selectedIndex] || benchmarkCandidate;
  const competencies = useMemo(
    () => getJobCompetencies(roleRows, skillDomainMap),
    [roleRows, skillDomainMap],
  );
  const radarRows = useMemo(() => {
    if (!selectedCandidate || !benchmarkCandidate) return [];
    return buildRadarRows(selectedCandidate, benchmarkCandidate, competencies, skillDomainMap);
  }, [selectedCandidate, benchmarkCandidate, competencies, skillDomainMap]);

  const selectedMatched = uniqueSorted(radarRows.flatMap((row) => row.selectedMatched));
  const selectedMissing = uniqueSorted(radarRows.flatMap((row) => row.selectedMissing));

  if (status === "loading") {
    return (
      <main className="status-screen">
        <Gauge aria-hidden="true" />
        <p>Loading recruiter radar...</p>
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="status-screen">
        <TriangleAlert aria-hidden="true" />
        <p>Could not load data. Run <code>npm run sync-data</code> in the frontend folder.</p>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <nav className="view-tabs" aria-label="Dashboard views">
        <button
          className={activeView === "radar" ? "view-tab active" : "view-tab"}
          onClick={() => setActiveView("radar")}
          type="button"
        >
          <BarChart3 aria-hidden="true" />
          Radar
        </button>
        <button
          className={activeView === "graph" ? "view-tab active" : "view-tab"}
          onClick={() => setActiveView("graph")}
          type="button"
        >
          <Network aria-hidden="true" />
          Skill Graph
        </button>
      </nav>

      {activeView === "graph" ? (
        <SkillGraphView graph={graph} />
      ) : (
        <>
      <aside className="sidebar">
        <div className="brand-row">
          <BarChart3 aria-hidden="true" />
          <div>
            <p className="eyebrow">Resume Ranker</p>
            <h1>Recruiter Radar</h1>
          </div>
        </div>

        <label className="field-label" htmlFor="role">
          Job role
        </label>
        <select
          id="role"
          value={selectedRole}
          onChange={(event) => setSelectedRole(event.target.value)}
        >
          {roles.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>

        <label className="field-label" htmlFor="candidate-search">
          Candidate search
        </label>
        <div className="search-box">
          <Search aria-hidden="true" />
          <input
            id="candidate-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search skills or resume text"
          />
        </div>

        <div className="list-header">
          <span>Top candidates</span>
          <strong>{roleRows.length}</strong>
        </div>
        <div className="candidate-list">
          {filteredCandidates.map((candidate) => {
            const index = roleRows.indexOf(candidate);
            return (
              <button
                className={index === selectedIndex ? "candidate active" : "candidate"}
                key={`${candidate.job_position_name}-${index}`}
                onClick={() => setSelectedIndex(index)}
                type="button"
              >
                <span>Candidate {index + 1}</span>
                <strong>{formatScore(candidate.final_fit_score)}</strong>
              </button>
            );
          })}
        </div>
      </aside>

      <section className="main-panel">
        <div className="toolbar">
          <div>
            <p className="eyebrow">Selected role</p>
            <h2>{selectedRole}</h2>
          </div>
          <div className="legend">
            <span className="legend-item benchmark">Best candidate</span>
            <span className="legend-item selected">Selected candidate</span>
          </div>
        </div>

        <section className="radar-section">
          <RadarGraphic rows={radarRows} />
        </section>

        <section className="score-strip">
          {[
            ["Final fit", selectedCandidate?.final_fit_score],
            ["Shortlist", selectedCandidate?.shortlist_score],
            ["Direct match", selectedCandidate?.direct_match],
            ["Domain alignment", selectedCandidate?.role_domain_alignment],
            ["Evidence", selectedCandidate?.project_evidence_score],
          ].map(([label, value]) => (
            <div className="score-tile" key={label}>
              <span>{label}</span>
              <strong>{formatScore(value)}</strong>
            </div>
          ))}
        </section>
      </section>

      <aside className="detail-panel">
        <div className="panel-heading">
          <BriefcaseBusiness aria-hidden="true" />
          <div>
            <p className="eyebrow">Comparison</p>
            <h2>Candidate {selectedIndex + 1}</h2>
          </div>
        </div>

        <section>
          <h3><CheckCircle2 aria-hidden="true" /> Matched skills</h3>
          <div className="chip-list">
            {selectedMatched.length ? (
              selectedMatched.map((skill) => <span className="chip positive" key={skill}>{skill}</span>)
            ) : (
              <p className="muted">No matched competency skills found.</p>
            )}
          </div>
        </section>

        <section>
          <h3><TriangleAlert aria-hidden="true" /> Missing skills</h3>
          <div className="chip-list">
            {selectedMissing.length ? (
              selectedMissing.map((skill) => <span className="chip warning" key={skill}>{skill}</span>)
            ) : (
              <p className="muted">No missing skills inside selected radar metrics.</p>
            )}
          </div>
        </section>

        <section>
          <h3><Layers3 aria-hidden="true" /> Competency breakdown</h3>
          <div className="breakdown-list">
            {radarRows.map((row) => (
              <details key={row.metric} open>
                <summary>
                  <span>{row.metric}</span>
                  <strong>{row.selected}%</strong>
                </summary>
                <p className="skill-line">
                  {row.requiredSkills.length
                    ? row.requiredSkills.join(", ")
                    : "No explicit JD skills mapped to this metric."}
                </p>
              </details>
            ))}
          </div>
        </section>
      </aside>
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>,
);
