import { useEffect, useState, type ReactNode } from "react";
import {
  Activity, AlertTriangle, ArrowDown, ArrowRight, Braces, Check, Clock3,
  Database, EyeOff, Gauge, HardDrive, Menu, Minus, RefreshCw, Search,
  FileCheck2, ShieldCheck, X,
} from "lucide-react";
import { api, isDemo } from "./api";
import { duration, formatDate, number, relativeDuration } from "./formatters";
import type { DatasetRun, PlatformStatus, Stage, Status } from "./types";

type Page = "overview" | "runs" | "freshness" | "quality" | "incidents";

const labels: Record<Page, string> = {
  overview: "Visão geral",
  runs: "Execuções",
  freshness: "Atualização dos dados",
  quality: "Qualidade dos dados",
  incidents: "Incidentes",
};

const statusLabel: Record<Status, string> = {
  success: "Saudável",
  running: "Em execução",
  warning: "Atenção",
  failed: "Com falha",
  blocked: "Bloqueada",
  not_started: "Sem evidência",
  not_applicable: "Não aplicável",
  unmonitored: "Sem monitoramento",
};

function triggerLabel(value: unknown) {
  return value === "manual" ? "Execução manual" : value === "scheduled" ? "Execução agendada" : "Outro disparo";
}

function testTypeLabel(value: unknown) {
  const type = String(value || "").toLowerCase();
  const labels: Record<string, string> = { generic: "Genérico", singular: "Singular" };
  return labels[type] || String(value || "—");
}

function TestTypeMark({ type }: { type: unknown }) {
  const value = String(type || "").toLowerCase();
  const singular = value === "singular";
  const Icon = singular ? FileCheck2 : Braces;
  const label = testTypeLabel(type);
  return <span className={`test-type test-type--${singular ? "singular" : "generic"}`} title={`Tipo de teste: ${label}`}><Icon size={14} aria-hidden="true" />{label}</span>;
}

function FailurePolicyMark({ severity }: { severity: unknown }) {
  const value = String(severity || "").toLowerCase();
  const warning = ["warn", "warning"].includes(value);
  const label = warning ? "Gera aviso" : value === "error" ? "Bloqueia pipeline" : "Política não definida";
  return <span className="failure-policy" title={`Em caso de falha: ${label}`}>{label}</span>;
}

function StatusMark({ status, compact = false, pill = true }: { status: Status; compact?: boolean; pill?: boolean }) {
  const value = String(status).toLowerCase();
  const normalized: Status = ["pass", "passed"].includes(value) ? "success" :
    ["error", "fail", "failed", "runtime error"].includes(value) ? "failed" :
    ["warn", "warning"].includes(value) ? "warning" :
    ["running", "started"].includes(value) ? "running" :
    value === "blocked" ? "blocked" : value === "not_applicable" ? "not_applicable" :
    value === "unmonitored" ? "unmonitored" :
    value === "success" ? "success" : "not_started";
  const Icon = normalized === "success" ? Check : normalized === "failed" ? X :
    normalized === "warning" ? AlertTriangle : normalized === "running" ? RefreshCw :
    normalized === "not_applicable" ? Minus : normalized === "unmonitored" ? EyeOff : Clock3;
  return (
    <span className={`status status--${normalized} ${compact ? "status--compact" : ""} ${pill && !compact ? "status--pill" : ""}`} title={statusLabel[normalized]} aria-label={statusLabel[normalized]}>
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

function QualityMetric({ passed, total }: { passed: unknown; total: unknown }) {
  const passedCount = Number(passed) || 0;
  const totalCount = Number(total) || 0;
  const notPassedCount = Math.max(totalCount - passedCount, 0);
  return (
    <article className="metric metric--quality">
      <span className="metric__index">//</span>
      <p>Testes dbt</p>
      <strong><span>{number(passedCount)}</span><b>/</b><span className={notPassedCount ? "metric__failed" : ""}>{number(notPassedCount)}</span></strong>
      <small>Aprovados / não aprovados</small>
    </article>
  );
}

function RunDurationChart({ runs }: { runs: Record<string, unknown>[] }) {
  const history = runs.slice(0, 10).reverse();
  const maxDuration = Math.max(...history.map((run) => Number(run.duration_seconds) || 0), 1);
  return (
    <article className="metric metric--history">
      <p>Histórico de duração</p>
      <div className="run-chart" role="img" aria-label={`Duração total das últimas ${history.length} execuções`}>
        {history.length ? history.map((run) => {
          const seconds = Number(run.duration_seconds) || 0;
          const status = String(run.status || "not_started").toLowerCase();
          const normalized = ["failed", "error"].includes(status) ? "failed" : ["warning", "warn"].includes(status) ? "warning" : status === "running" ? "running" : "success";
          return <span
            className={`run-chart__bar run-chart__bar--${normalized}`}
            key={String(run.run_id)}
            style={{ height: `${Math.max(16, (seconds / maxDuration) * 100)}%` }}
            title={`${formatDate(run.started_at)} · ${duration(seconds)} · ${statusLabel[normalized]}`}
          />;
        }) : <small>Sem histórico disponível</small>}
      </div>
      {history.length ? <div className="run-chart__legend" aria-label="Legenda dos status"><span className="is-success">Saudável</span><span className="is-warning">Atenção</span><span className="is-failed">Falha</span></div> : <small>Aguardando execuções</small>}
    </article>
  );
}

function Tracker({ stages }: { stages: Stage[] }) {
  const [selected, setSelected] = useState<Stage | null>(null);
  return (
    <><div className="tracker" aria-label="Etapas da execução">
      {stages.map((stage, index) => (
        <div className="tracker__segment" key={stage.id}>
          <button className={`stage stage--${stage.status}`} onClick={() => setSelected(stage)} aria-label={`Abrir detalhes de ${stage.label}`}>
            <span className="stage__number">0{index + 1}</span>
            <span className="stage__icon"><StatusMark status={stage.status} compact /></span>
            <strong>{stage.label}</strong>
            <small>{statusLabel[stage.status]}</small>
          </button>
          {index < stages.length - 1 && <div className="tracker__line" />}
        </div>
      ))}
    </div>{selected && <StagePanel stage={selected} onClose={() => setSelected(null)} />}</>
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
        <p className="panel__note">{isDemo ? "Esta amostra representa as evidências consolidadas de uma execução típica da plataforma." : "Os detalhes exibidos são consolidados pela API de observabilidade. Use Airflow ou MinIO para inspeção operacional de baixo nível."}</p>
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
        <div><p className="kicker">Ativos monitorados</p><h2>Jornada por dataset</h2></div>
        <span>{number(filtered.length)} registros</span>
      </header>
      <div className="filters">
        <label><Search size={15} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filtrar dataset" /></label>
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filtrar status">
          <option value="all">Todos os status</option><option value="success">Saudável</option><option value="warning">Atenção</option><option value="failed">Com falha</option>
        </select>
      </div>
      {!filtered.length ? <Empty>Nenhum dataset registrado nesta execução.</Empty> : (
        <div className="table-wrap"><table><thead><tr><th>Dataset</th><th>Origem</th><th>MinIO</th><th>Raw</th><th>Staging</th><th>Intermediate</th><th>Analytics</th><th>Power BI</th><th>Linhas</th><th>Status</th></tr></thead>
          <tbody>{filtered.map((row) => <tr key={row.dataset}>
            <td><button className="dataset-link" onClick={() => onSelect(row.dataset)}><strong>{row.dataset}</strong></button></td>
            {(["source", "minio", "raw", "staging", "intermediate", "analytics", "powerbi"] as const).map((stage) => <td key={stage}><StatusMark status={row.stages?.[stage] || "not_started"} compact /></td>)}
            <td>{number(row.raw_row_count)}</td><td><StatusMark status={row.status} /></td>
          </tr>)}</tbody></table></div>
      )}
    </section>
  );
}

function DatasetPanel({ data, onClose }: { data: Record<string, unknown>; onClose: () => void }) {
  const ingestion = (data.ingestion || {}) as Record<string, unknown>;
  const freshness = (data.freshness || {}) as Record<string, unknown>;
  const stages = (data.stages || {}) as Record<string, Status>;
  const journey: [string, Status, string][] = [
    ["Origem", stages.source || "not_started", `${number(ingestion.source_row_count)} linhas`],
    ["MinIO", stages.minio || "not_started", String(ingestion.minio_object || "Sem objeto")],
    ["Raw", stages.raw || "not_started", `${number(ingestion.raw_row_count)} linhas`],
    ["Staging", stages.staging || "not_started", "Transformação dbt"],
    ["Intermediate", stages.intermediate || "not_started", "Transformação dbt"],
    ["Analytics", stages.analytics || "not_started", "Transformação dbt"],
    ["Power BI", stages.powerbi || "unmonitored", "Sem telemetria de atualização"],
  ];
  return <div className="scrim" onMouseDown={onClose}><aside className="panel dataset-panel" onMouseDown={(e) => e.stopPropagation()}>
    <button className="icon-button panel__close" onClick={onClose}><X /></button>
    <p className="kicker">Jornada do dataset / evidência mais recente</p><h2>{String(data.dataset)}</h2>
    <div className="dataset-journey">{journey.map(([label, status, note], index) => <div key={label}><article><StatusMark status={status} compact /><span><strong>{label}</strong><small>{note}</small></span></article>{index < journey.length - 1 && <ArrowDown />}</div>)}</div>
    <dl className="definition-list"><div><dt>{freshness.freshness_type === "business" ? "Idade do último evento" : "Atualização técnica"}</dt><dd>{relativeDuration(freshness.age_seconds)}</dd></div><div><dt>Última carga</dt><dd>{formatDate(ingestion.finished_at)}</dd></div><div><dt>Localização do arquivo</dt><dd className="path-value">{String(ingestion.minio_object || "—")}</dd></div><div><dt>Tamanho do Parquet</dt><dd>{ingestion.file_size_bytes ? `${(Number(ingestion.file_size_bytes) / 1024 / 1024).toFixed(2)} MB` : "—"}</dd></div></dl>
  </aside></div>;
}

function Overview() {
  const [data, setData] = useState<PlatformStatus | null>(null);
  const [datasets, setDatasets] = useState<DatasetRun[]>([]);
  const [runs, setRuns] = useState<Record<string, unknown>[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [consultedAt, setConsultedAt] = useState<Date | null>(null);
  const load = async (announce = false) => {
    if (refreshing) return;
    setRefreshing(true);
    setError("");
    setFeedback("");
    try {
      const [result, runHistory] = await Promise.all([api.status(), api.runs().catch(() => [])]);
      setData(result);
      setRuns(runHistory);
      setDatasets(result.run_id ? await api.runDatasets(result.run_id) : []);
      setConsultedAt(new Date());
      if (announce) setFeedback("Dados atualizados com sucesso.");
    } catch {
      setError("A API de observabilidade não está respondendo.");
      if (announce) setFeedback("Não foi possível atualizar os dados.");
    } finally {
      setRefreshing(false);
    }
  };
  useEffect(() => { void load(); }, []);
  if (error) return <Empty>{error} Verifique o serviço na porta 8000.</Empty>;
  if (!data) return <div className="loading"><RefreshCw /> Consolidando sinais da plataforma…</div>;
  return <>
    <section className="hero">
      <div><h1>Modern Data<br /><em>Platform</em></h1></div>
      <div className={`health health--${data.platform_status}`}><span>Status da plataforma</span><strong>{statusLabel[data.platform_status].toUpperCase()}</strong><small>AdventureWorks · {formatDate(data.last_successful_run)} · {triggerLabel(data.trigger_type)}</small></div>
    </section>
    <div className="metrics">
      <Metric eyebrow="Última execução bem-sucedida" value={formatDate(data.last_successful_run)} note="Horário de Brasília" />
      <Metric eyebrow="Duração do pipeline" value={duration(data.pipeline_duration_seconds)} note="Ingestão + transformação" />
      <Metric eyebrow="Último dado comercial" value={formatDate(data.last_business_event_at)} note="Evento mais recente na origem" />
      <QualityMetric passed={data.tests.passed} total={data.tests.total} />
      <RunDurationChart runs={runs} />
    </div>
    <section className="section-block tracker-block">
      <header className="section-heading"><div><p className="kicker">Acompanhamento / execução mais recente</p><h2>Jornada do pipeline</h2></div><div className="refresh-area"><button className="text-button" onClick={() => void load(true)} disabled={refreshing}><RefreshCw className={refreshing ? "spin" : ""} size={15} /> {refreshing ? "Atualizando…" : "Atualizar"}</button><small aria-live="polite">{feedback || (consultedAt ? `Última consulta: ${consultedAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}` : "")}</small></div></header>
      <Tracker stages={data.stages} />
    </section>
    <DatasetTable rows={datasets} onSelect={(dataset) => api.dataset(dataset).then(setSelectedDataset)} />
    {selectedDataset && <DatasetPanel data={selectedDataset} onClose={() => setSelectedDataset(null)} />}
  </>;
}

function Runs() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.runs().then(setRows).catch(() => setError("Não foi possível consultar as execuções.")); }, []);
  const open = async (runId: unknown) => {
    setError("");
    try { setSelected(await api.run(String(runId))); } catch { setError("Não foi possível abrir os detalhes da execução."); }
  };
  return <DataPage kicker="Histórico de orquestração" title="Execuções do pipeline">
    {error && <p className="inline-error" role="alert">{error}</p>}
    {!rows.length && !error ? <Empty>Nenhuma execução registrada.</Empty> : <div className="run-list" role="list">{rows.map((row, i) => <button type="button" role="listitem" key={String(row.run_id)} onClick={() => void open(row.run_id)}><span>{String(i + 1).padStart(2, "0")}</span><div><strong>{formatDate(row.started_at)}</strong><small>{triggerLabel(row.trigger_type)}</small></div><b><small>Duração</small>{duration(row.duration_seconds)}</b><StatusMark status={String(row.status) as Status} /><span className="details-label">Ver detalhes <ArrowRight size={13} aria-hidden="true" /></span></button>)}</div>}
    {selected && <RunPanel data={selected} onClose={() => setSelected(null)} />}
  </DataPage>;
}

function RunPanel({ data, onClose }: { data: Record<string, unknown>; onClose: () => void }) {
  const datasets = (data.datasets || []) as DatasetRun[];
  const failedDatasets = datasets.filter((dataset) => dataset.status === "failed");
  const failedTests = (data.failed_tests || []) as Record<string, unknown>[];
  const failed = String(data.status).toLowerCase() === "failed";
  const warning = String(data.status).toLowerCase() === "warning";
  const failureScope = String(data.failure_scope || "");
  const testNames = failedTests.map((test) => String(test.test_name || "Teste sem nome")).join(", ");
  const invalidRecords = failedTests.reduce((total, test) => total + (Number(test.failed_records) || 0), 0);
  const qualityDiagnosis = failedTests.length === 1
    ? `O teste dbt ${testNames} ${warning ? "gerou um aviso" : "registrou uma falha"} nesta execução${invalidRecords ? `, com ${number(invalidRecords)} registro(s) inválido(s)` : ""}.`
    : `${failedTests.length} testes dbt registraram ocorrências nesta execução: ${testNames}.`;
  const diagnosis = data.error_message ? String(data.error_message) :
    failureScope === "quality" ? qualityDiagnosis :
    failureScope === "dataset" ? `${failedDatasets.length} dataset(s) não concluíram o processamento.` :
    failed ? "A execução foi encerrada com falha na orquestração. Todos os datasets listados concluíram saudáveis e nenhuma mensagem técnica foi registrada; consulte o log desta run no Airflow." : "";
  return <div className="scrim" onMouseDown={onClose}><aside className="panel dataset-panel" onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label="Detalhes da execução">
    <button className="icon-button panel__close" onClick={onClose} aria-label="Fechar"><X /></button>
    <p className="kicker">Evidências da execução</p><h2>{formatDate(data.started_at)}</h2><StatusMark status={data.status as Status} />
    <dl className="definition-list"><div><dt>Início</dt><dd>{formatDate(data.started_at)}</dd></div><div><dt>Término</dt><dd>{formatDate(data.finished_at)}</dd></div><div><dt>Tipo</dt><dd>{triggerLabel(data.trigger_type)}</dd></div><div><dt>Duração total</dt><dd>{duration(data.duration_seconds)}</dd></div></dl>
    {diagnosis ? <section className={`run-diagnosis ${warning ? "run-diagnosis--warning" : ""}`} role="alert"><AlertTriangle size={20} /><div><strong>{failureScope === "quality" ? warning ? "Atenção em testes dbt" : "Falha em testes dbt" : failureScope === "dataset" ? "Falha no processamento" : "Falha de orquestração"}</strong><p>{diagnosis}</p></div></section> : null}
    {failedTests.length ? <><h3>Testes com ocorrência</h3><ul className="evidence-list evidence-list--issues">{failedTests.map((test) => <li key={String(test.test_name)}><span><strong>{String(test.test_name)}</strong><small>{String(test.error_message || "Sem mensagem registrada")}</small></span><StatusMark status={test.status as Status} /></li>)}</ul></> : null}
    <h3>{failedDatasets.length ? "Datasets afetados" : "Datasets processados"}</h3>{datasets.length ? <ul className="evidence-list">{datasets.map((dataset) => <li key={dataset.dataset}><span>{dataset.dataset}</span><StatusMark status={dataset.status} /></li>)}</ul> : <Empty>Nenhuma evidência de dataset registrada.</Empty>}
  </aside></div>;
}

function Freshness() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { api.freshness().then(setRows).catch(() => setError("Não foi possível consultar a atualização dos dados.")); }, []);
  return <DataPage kicker="Latência técnica por fonte" title="Atualização dos dados">
    {error ? <Empty>{error}</Empty> : <EditorialTable rows={rows} columns={["dataset", "source_updated_at", "minio_updated_at", "warehouse_updated_at", "analytics_updated_at", "status"]} labels={["Dataset", "Origem", "MinIO", "Warehouse", "Analytics", "Status"]} />}
  </DataPage>;
}

function Quality() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [evidence, setEvidence] = useState<Record<string, unknown>[] | null>(null);
  useEffect(() => { api.quality().then(setData).catch(() => setError("Não foi possível consultar os resultados dos testes dbt.")); }, []);
  const rows = (data?.results as Record<string, unknown>[] | undefined) || [];
  const openEvidence = async (row: Record<string, unknown>) => {
    try { setEvidence(await api.qualityEvidence(String(row.invocation_id), String(row.test_unique_id))); } catch { setError("Não foi possível consultar as evidências preservadas."); }
  };
  return <DataPage kicker="Resultados persistidos do dbt" title="Qualidade dos dados">
    {error && <p className="inline-error" role="alert">{error}</p>}
    <div className="quality-totals"><strong>{number(data?.total)}<small>testes</small></strong><span>{number(data?.passed)} aprovados</span><span>{number(data?.warnings)} avisos</span><span className="coral">{number(data?.failed)} falhas</span><small>Última execução: {formatDate(data?.last_run_at)}</small></div>
    {!rows.length && !error ? <Empty>Ainda não existem execuções de testes dbt registradas.</Empty> : <div className="table-wrap"><table><thead><tr><th>Teste</th><th>Tipo</th><th>Em caso de falha</th><th>Registros inválidos</th><th>Duração</th><th>Resultado</th><th>Evidências</th></tr></thead><tbody>{rows.map((row) => <tr key={String(row.test_unique_id)}><td><strong>{String(row.test_name)}</strong><small title={String(row.message || "")}>{String(row.message || "Sem mensagem")}</small></td><td><TestTypeMark type={row.test_type} /></td><td><FailurePolicyMark severity={row.severity} /></td><td>{number(row.failed_records)}</td><td>{duration(row.execution_seconds)}</td><td><StatusMark status={row.status as Status} pill /></td><td><button className="action-button" onClick={() => void openEvidence(row)}>Ver evidências <ArrowRight size={13} aria-hidden="true" /></button></td></tr>)}</tbody></table></div>}
    {evidence && <EvidencePanel rows={evidence} onClose={() => setEvidence(null)} />}
  </DataPage>;
}

function EvidencePanel({ rows, onClose }: { rows: Record<string, unknown>[]; onClose: () => void }) {
  return <div className="scrim" onMouseDown={onClose}><aside className="panel dataset-panel" onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label="Evidências do teste"><button className="icon-button panel__close" onClick={onClose} aria-label="Fechar"><X /></button><p className="kicker">Registros preservados</p><h2>Evidências</h2>{rows.length ? <pre className="evidence-json">{JSON.stringify(rows, null, 2)}</pre> : <Empty>Este teste não possui registros inválidos preservados.</Empty>}</aside></div>;
}

function Incidents() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { api.incidents().then(setRows).catch(() => setError("Não foi possível consultar as falhas operacionais.")); }, []);
  return <DataPage kicker="Falhas operacionais registradas" title="Incidentes">
    {error ? <Empty>{error}</Empty> : !rows.length ? <div className="all-clear"><ShieldCheck /><div><strong>Nenhuma falha registrada</strong><p>Não há falhas críticas nas evidências disponíveis. Esta é uma visão somente de leitura.</p></div></div> : <div className="incident-list">{rows.map((row, i) => <article key={i}><AlertTriangle /><div><p>{formatDate(row.occurred_at)} · {String(row.origin || "pipeline")} · severidade {String(row.severity || "error")}</p><h3>{String(row.test_name)}</h3><small>{String(row.error || "Falha sem mensagem registrada")}</small></div><strong>{number(row.invalid_records)}<small>inválidos</small></strong></article>)}</div>}
  </DataPage>;
}

function EditorialTable({ rows, columns, labels }: { rows: Record<string, unknown>[]; columns: string[]; labels: string[] }) {
  if (!rows.length) return <Empty>Nenhum dado disponível para esta visão.</Empty>;
  return <div className="table-wrap"><table><thead><tr>{labels.map((label) => <th key={label}>{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column}>{column.endsWith("_at") ? formatDate(row[column]) : column.endsWith("_seconds") ? duration(row[column]) : column === "status" ? <StatusMark status={(row[column] || "not_started") as Status} /> : String(row[column] ?? "—")}</td>)}</tr>)}</tbody></table></div>;
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
      <div className="sidebar__foot"><Activity size={17} /><span>Operational layer<br /><b>{isDemo ? "Ambiente demonstrativo" : "Ambiente local"}</b></span></div>
    </aside>
    <main>
      <header className="topbar"><button className="icon-button mobile-menu" onClick={() => setMenu(!menu)} aria-label={menu ? "Fechar menu" : "Abrir menu"} aria-expanded={menu}><Menu /></button><span>AdventureWorks · Observabilidade</span>{isDemo && <span className="demo-badge">Ambiente demonstrativo</span>}</header>
      <div className="content">{page === "overview" ? <Overview /> : page === "runs" ? <Runs /> : page === "freshness" ? <Freshness /> : page === "quality" ? <Quality /> : <Incidents />}</div>
      <footer><span>Modern Data Platform / Observability</span><span>PostgreSQL · MinIO · dbt · Airflow</span></footer>
    </main>
  </div>;
}
