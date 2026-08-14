import { useEffect, useState, type ReactNode } from "react";
import {
  Activity, AlertTriangle, ArrowDown, Check, ChevronRight, Clock3,
  Database, Gauge, HardDrive, Menu, RefreshCw, Search, ShieldCheck,
  TestTube2, X, XCircle,
} from "lucide-react";
import { api } from "./api";
import type { DatasetRun, PlatformStatus, Stage, Status } from "./types";

type Page = "overview" | "runs" | "freshness" | "quality" | "incidents";

const labels: Record<Page, string> = {
  overview: "Platform Overview",
  runs: "Pipeline Runs",
  freshness: "Data Freshness",
  quality: "Data Quality",
  incidents: "Incidents",
};

const statusLabel: Record<Status, string> = {
  success: "Healthy",
  running: "Running",
  warning: "Warning",
  failed: "Failed",
  blocked: "Blocked",
  not_started: "Not started",
};

function formatDate(value: unknown) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  }).format(new Date(String(value)));
}

function duration(value: unknown) {
  const seconds = Math.round(Number(value || 0));
  if (!seconds) return "—";
  return seconds >= 60 ? `${Math.floor(seconds / 60)}m ${seconds % 60}s` : `${seconds}s`;
}

function number(value: unknown) {
  return new Intl.NumberFormat("pt-BR").format(Number(value || 0));
}

function StatusMark({ status, compact = false }: { status: Status; compact?: boolean }) {
  const value = String(status).toLowerCase();
  const normalized: Status = ["pass", "passed"].includes(value) ? "success" :
    ["error", "fail", "failed", "runtime error"].includes(value) ? "failed" :
    ["warn", "warning"].includes(value) ? "warning" :
    ["running", "started"].includes(value) ? "running" :
    value === "blocked" ? "blocked" :
    value === "success" ? "success" : "not_started";
  const Icon = normalized === "success" ? Check : normalized === "failed" ? X :
    normalized === "warning" ? AlertTriangle : normalized === "running" ? RefreshCw : Clock3;
  return (
    <span className={`status status--${normalized} ${compact ? "status--compact" : ""}`}>
      <Icon size={compact ? 13 : 16} /> {!compact && statusLabel[normalized]}
    </span>
  );
}

function Empty({ children }: { children: ReactNode }) {
  return <div className="empty"><Database size={24} /><p>{children}</p></div>;
}

function Metric({ eyebrow, value, note, accent }: { eyebrow: string; value: string; note: string; accent?: boolean }) {
  return (
    <article className={`metric ${accent ? "metric--accent" : ""}`}>
      <span className="metric__index">//</span>
      <p>{eyebrow}</p><strong>{value}</strong><small>{note}</small>
    </article>
  );
}

function Tracker({ stages, onSelect }: { stages: Stage[]; onSelect: (stage: Stage) => void }) {
  return (
    <div className="tracker" aria-label="Etapas da execução">
      {stages.map((stage, index) => (
        <div className="tracker__segment" key={stage.id}>
          <button className={`stage stage--${stage.status}`} onClick={() => onSelect(stage)}>
            <span className="stage__number">0{index + 1}</span>
            <span className="stage__icon"><StatusMark status={stage.status} compact /></span>
            <strong>{stage.label}</strong>
            <small>{statusLabel[stage.status]}</small>
            <ChevronRight className="stage__open" size={16} />
          </button>
          {index < stages.length - 1 && <div className="tracker__line" />}
        </div>
      ))}
    </div>
  );
}

function StagePanel({ stage, onClose }: { stage: Stage; onClose: () => void }) {
  return (
    <div className="scrim" onMouseDown={onClose}>
      <aside className="panel" onMouseDown={(event) => event.stopPropagation()} aria-label="Detalhes da etapa">
        <button className="icon-button panel__close" onClick={onClose} aria-label="Fechar"><X size={20} /></button>
        <p className="kicker">Stage dossier / {stage.id}</p>
        <h2>{stage.label}</h2>
        <StatusMark status={stage.status} />
        <div className="panel__rule" />
        <dl className="definition-list">
          <div><dt>Conclusão</dt><dd>{formatDate(stage.completed_at)}</dd></div>
          <div><dt>Duração</dt><dd>{duration(stage.duration_seconds)}</dd></div>
          <div><dt>Dependência</dt><dd>{stage.status === "not_started" ? "Aguardando etapa anterior" : "Verificada"}</dd></div>
        </dl>
        <p className="panel__note">Os detalhes exibidos são consolidados pela API de observabilidade. Use Airflow ou MinIO para inspeção operacional de baixo nível.</p>
        <div className="tool-links"><a href="http://localhost:8080" target="_blank" rel="noreferrer">View Airflow Run</a><a href="http://localhost:9001" target="_blank" rel="noreferrer">View MinIO Objects</a></div>
      </aside>
    </div>
  );
}

function DatasetTable({ rows, onSelect }: { rows: DatasetRun[]; onSelect: (dataset: string) => void }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const filtered = rows.filter((row) =>
    row.dataset.toLowerCase().includes(query.toLowerCase()) &&
    (status === "all" || row.status === status));
  return (
    <section className="section-block">
      <header className="section-heading">
        <div><p className="kicker">Dataset register</p><h2>Jornada por dataset</h2></div>
        <span>{filtered.length.toString().padStart(2, "0")} registros</span>
      </header>
      <div className="filters">
        <label><Search size={15} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filtrar dataset" /></label>
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filtrar status">
          <option value="all">Todos os status</option><option value="success">Healthy</option><option value="failed">Failed</option>
        </select>
      </div>
      {!filtered.length ? <Empty>Nenhum dataset registrado nesta execução.</Empty> : (
        <div className="table-wrap"><table><thead><tr><th>Dataset</th><th>Source</th><th>MinIO</th><th>Raw</th><th>dbt</th><th>Mart</th><th>Rows</th><th>Status</th></tr></thead>
          <tbody>{filtered.map((row) => <tr key={row.dataset}>
            <td><button className="dataset-link" onClick={() => onSelect(row.dataset)}><strong>{row.dataset}</strong><small>{row.minio_object || "sem objeto"}</small></button></td>
            {(["source", "minio", "raw", "dbt", "mart"] as const).map((stage) => <td key={stage}><StatusMark status={row.stages?.[stage] || "not_started"} compact /></td>)}
            <td>{number(row.raw_row_count)}</td><td><StatusMark status={row.status} /></td>
          </tr>)}</tbody></table></div>
      )}
    </section>
  );
}

function DatasetPanel({ data, onClose }: { data: Record<string, unknown>; onClose: () => void }) {
  const ingestion = (data.ingestion || {}) as Record<string, unknown>;
  const freshness = (data.freshness || {}) as Record<string, unknown>;
  const tests = (data.tests || []) as Record<string, unknown>[];
  const succeeded = ingestion.status === "success";
  const journey: [string, Status, string][] = [
    ["Source", succeeded ? "success" : "failed", `${number(ingestion.source_row_count)} rows`],
    ["MinIO", ingestion.minio_uploaded_at ? "success" : "not_started", String(ingestion.minio_object || "No object")],
    ["Raw", ingestion.raw_loaded_at ? "success" : "not_started", `${number(ingestion.raw_row_count)} rows`],
    ["dbt", tests.some((test) => ["error", "fail", "failed"].includes(String(test.status))) ? "failed" : tests.length ? "success" : "not_started", `${tests.length} tests`],
    ["Mart", tests.length ? "success" : "not_started", "Analytics interface"],
  ];
  return <div className="scrim" onMouseDown={onClose}><aside className="panel dataset-panel" onMouseDown={(e) => e.stopPropagation()}>
    <button className="icon-button panel__close" onClick={onClose}><X /></button>
    <p className="kicker">Dataset journey / latest evidence</p><h2>{String(data.dataset)}</h2>
    <div className="dataset-journey">{journey.map(([label, status, note], index) => <div key={label}><article><StatusMark status={status} compact /><span><strong>{label}</strong><small>{note}</small></span></article>{index < journey.length - 1 && <ArrowDown />}</div>)}</div>
    <dl className="definition-list"><div><dt>Freshness</dt><dd>{duration(freshness.age_seconds)}</dd></div><div><dt>Last successful load</dt><dd>{formatDate(ingestion.finished_at)}</dd></div><div><dt>Parquet size</dt><dd>{ingestion.file_size_bytes ? `${(Number(ingestion.file_size_bytes) / 1024 / 1024).toFixed(2)} MB` : "—"}</dd></div></dl>
  </aside></div>;
}

function Overview() {
  const [data, setData] = useState<PlatformStatus | null>(null);
  const [datasets, setDatasets] = useState<DatasetRun[]>([]);
  const [selected, setSelected] = useState<Stage | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const load = () => {
    setError("");
    api.status().then((result) => {
      setData(result);
      if (result.run_id) api.runDatasets(result.run_id).then(setDatasets).catch(() => setDatasets([]));
    }).catch(() => setError("A API de observabilidade não está respondendo."));
  };
  useEffect(load, []);
  if (error) return <Empty>{error} Verifique o serviço na porta 8000.</Empty>;
  if (!data) return <div className="loading"><RefreshCw /> Consolidando sinais da plataforma…</div>;
  return <>
    <section className="hero">
      <div><p className="kicker">Morning edition / operational brief</p><h1>Modern Data<br /><em>Platform</em></h1></div>
      <div className={`health health--${data.platform_status}`}><span>Platform status</span><strong>{statusLabel[data.platform_status].toUpperCase()}</strong><small>AdventureWorks / {data.run_id || "sem execução"}</small></div>
    </section>
    <div className="metrics">
      <Metric eyebrow="Last successful run" value={formatDate(data.last_successful_run)} note="Última carga observada" />
      <Metric eyebrow="Pipeline duration" value={duration(data.pipeline_duration_seconds)} note="Ingestão + transformação" />
      <Metric eyebrow="Data freshness" value={duration(data.freshness_seconds)} note="Maior idade registrada" />
      <Metric eyebrow="dbt tests" value={`${data.tests.passed} / ${data.tests.total}`} note="Testes aprovados" />
      <Metric eyebrow="Datasets impacted" value={String(data.datasets_impacted)} note="Exigem investigação" accent={data.datasets_impacted > 0} />
    </div>
    <section className="section-block tracker-block">
      <header className="section-heading"><div><p className="kicker">Execution tracking / latest run</p><h2>Pipeline tracker</h2></div><button className="text-button" onClick={load}><RefreshCw size={15} /> Atualizar</button></header>
      <Tracker stages={data.stages} onSelect={setSelected} />
    </section>
    <DatasetTable rows={datasets} onSelect={(dataset) => api.dataset(dataset).then(setSelectedDataset)} />
    {selected && <StagePanel stage={selected} onClose={() => setSelected(null)} />}
    {selectedDataset && <DatasetPanel data={selectedDataset} onClose={() => setSelectedDataset(null)} />}
  </>;
}

function Runs() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  useEffect(() => { api.runs().then(setRows).catch(() => setRows([])); }, []);
  return <DataPage kicker="Archive / orchestration history" title="Pipeline Runs">
    {!rows.length ? <Empty>Nenhuma execução de ingestão registrada.</Empty> : <div className="run-list">{rows.map((row, i) => <article key={String(row.run_id)}><span>{String(i + 1).padStart(2, "0")}</span><div><strong>{formatDate(row.started_at)}</strong><small>{String(row.run_id)}</small></div><StatusMark status={String(row.status) as Status} /><b>{duration(row.duration_seconds)}</b><ChevronRight /></article>)}</div>}
  </DataPage>;
}

function Freshness() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  useEffect(() => { api.freshness().then(setRows).catch(() => setRows([])); }, []);
  return <DataPage kicker="SLA desk / latency by source" title="Data Freshness">
    <EditorialTable rows={rows} columns={["dataset", "source_updated_at", "minio_updated_at", "warehouse_updated_at", "analytics_updated_at", "status"]} labels={["Dataset", "Source", "MinIO", "Warehouse", "Analytics", "Status"]} />
  </DataPage>;
}

function Quality() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  useEffect(() => { api.quality().then(setData).catch(() => setData(null)); }, []);
  const rows = (data?.results as Record<string, unknown>[] | undefined) || [];
  return <DataPage kicker="Verification ledger / dbt" title="Data Quality">
    <div className="quality-totals"><strong>{number(data?.total)}<small>tests</small></strong><span>{number(data?.passed)} passed</span><span>{number(data?.warnings)} warning</span><span className="coral">{number(data?.failed)} failed</span></div>
    <EditorialTable rows={rows} columns={["test_name", "test_type", "failed_records", "status"]} labels={["Test", "Type", "Invalid records", "Result"]} />
  </DataPage>;
}

function Incidents() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  useEffect(() => { api.incidents().then(setRows).catch(() => setRows([])); }, []);
  return <DataPage kicker="Exception desk / critical signals" title="Incidents">
    {!rows.length ? <div className="all-clear"><ShieldCheck /><div><strong>No open incident</strong><p>Nenhuma falha crítica foi capturada no histórico disponível.</p></div></div> : <div className="incident-list">{rows.map((row, i) => <article key={i}><AlertTriangle /><div><p>{formatDate(row.occurred_at)} / {String(row.run_id || "run")}</p><h3>{String(row.test_name)}</h3><small>{String(row.error || "Falha em teste dbt")}</small></div><strong>{number(row.invalid_records)}<small>invalid</small></strong></article>)}</div>}
  </DataPage>;
}

function EditorialTable({ rows, columns, labels }: { rows: Record<string, unknown>[]; columns: string[]; labels: string[] }) {
  if (!rows.length) return <Empty>Nenhum dado disponível para esta visão.</Empty>;
  return <div className="table-wrap"><table><thead><tr>{labels.map((label) => <th key={label}>{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column}>{column.includes("at") ? formatDate(row[column]) : column.includes("seconds") ? duration(row[column]) : column === "status" ? <StatusMark status={(row[column] || "not_started") as Status} /> : String(row[column] ?? "—")}</td>)}</tr>)}</tbody></table></div>;
}

function DataPage({ kicker, title, children }: { kicker: string; title: string; children: ReactNode }) {
  return <><header className="page-title"><p className="kicker">{kicker}</p><h1>{title}</h1><p>Leitura consolidada dos sinais operacionais preservados no warehouse.</p></header><section className="section-block">{children}</section></>;
}

export default function App() {
  const [page, setPage] = useState<Page>("overview");
  const [menu, setMenu] = useState(false);
  return <div className="app-shell">
    <aside className={`sidebar ${menu ? "sidebar--open" : ""}`}>
      <div className="brand"><span>MDP</span><strong>CONTROL<br />CENTER</strong></div>
      <nav>{(Object.keys(labels) as Page[]).map((key, index) => <button className={page === key ? "active" : ""} key={key} onClick={() => { setPage(key); setMenu(false); }}><span>0{index + 1}</span>{labels[key]}</button>)}</nav>
      <div className="sidebar__foot"><Activity size={17} /><span>Operational layer<br /><b>Local environment</b></span></div>
    </aside>
    <main>
      <header className="topbar"><button className="icon-button mobile-menu" onClick={() => setMenu(!menu)}><Menu /></button><span>AdventureWorks / Data Engineering</span><div><i /> Live signals</div></header>
      <div className="content">{page === "overview" ? <Overview /> : page === "runs" ? <Runs /> : page === "freshness" ? <Freshness /> : page === "quality" ? <Quality /> : <Incidents />}</div>
      <footer><span>Modern Data Platform / Observability</span><span>PostgreSQL · MinIO · dbt · Airflow</span></footer>
    </main>
  </div>;
}
