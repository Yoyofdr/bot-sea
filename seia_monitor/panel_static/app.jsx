const { useEffect, useMemo, useState } = React;

const STATUS_OPTIONS = [
  { value: "", label: "Todos los estados" },
  { value: "sin_contactar", label: "Sin contactar" },
  { value: "contactado", label: "Contactado" },
  { value: "fallido", label: "Fallido" },
  { value: "completado", label: "Completado" },
];

const BE_LOGO_DATA_URI = "data:image/png;base64,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";

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `Error HTTP ${response.status}`);
  }
  return response.json();
}

function formatMonto(value) {
  if (!value) return "-";
  const raw = String(value).trim();
  const match = raw.match(/(\d[\d\.,]*)/);
  if (match) {
    const numericRaw = match[1];
    // Normaliza formato local: 1.234,56 -> 1234.56 / 1234.56 -> 1234.56
    let normalized = numericRaw;
    if (normalized.includes(",") && normalized.includes(".")) {
      normalized = normalized.replace(/\./g, "").replace(",", ".");
    } else if (normalized.includes(",")) {
      normalized = normalized.replace(",", ".");
    }
    const parsed = Number(normalized);
    if (Number.isFinite(parsed)) {
      const formatted = parsed.toLocaleString("es-CL", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return `${formatted} MM USD`;
    }
  }
  return raw
    .replace(/millones?\s+de\s+d[oó]lares?/gi, "MM USD")
    .replace(/millones?\s+de\s+usd/gi, "MM USD")
    .replace(/millones?/gi, "MM");
}

function DashboardLayout({ children }) {
  return (
    <div>
      <div className="h-14 w-full bg-panel-topbar text-panel-topbarText">
        <div className="mx-auto flex h-full max-w-7xl items-center px-6">
          <img
            src={BE_LOGO_DATA_URI}
            alt="Barros & Errazuriz"
            className="h-9 w-auto object-contain"
          />
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-6 py-6">{children}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  const config = {
    sin_contactar: "bg-slate-100 text-slate-700",
    contactado: "bg-blue-100 text-blue-700",
    completado: "bg-emerald-100 text-emerald-700",
    fallido: "bg-red-100 text-red-700",
  };
  const cls = config[status] || "bg-slate-100 text-slate-700";
  const label = (status || "-").replaceAll("_", " ");
  return (
    <span className={`inline-flex rounded-md px-2.5 py-1 text-xs font-medium capitalize ${cls}`}>
      {label}
    </span>
  );
}

function KpiCard({ label, value }) {
  return (
    <article className="rounded-md border border-panel-border bg-panel-card p-4 transition-all duration-150 hover:bg-panel-hover">
      <p className="text-[11px] uppercase tracking-wide text-panel-muted">{label}</p>
      <p className="mt-1 text-4xl font-semibold text-panel-text">{value}</p>
    </article>
  );
}

function Header() {
  return (
    <header className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-3xl font-semibold text-panel-text">Panel de Monitoreo</h1>
      </div>
    </header>
  );
}

function FilterBar({ filters, lawyers, regions, onChange, onClear }) {
  return (
    <section className="mt-6 rounded-md border border-panel-border bg-panel-card p-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <input
          value={filters.search}
          onChange={(e) => onChange("search", e.target.value)}
          placeholder="Buscar por proyecto"
          className="h-10 flex-1 rounded-sm border border-panel-border bg-white px-3 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-slate-400/40"
        />
        <div className="flex gap-3">
          <select
            value={filters.pipeline_status}
            onChange={(e) => onChange("pipeline_status", e.target.value)}
            className="h-10 min-w-[180px] rounded-sm border border-panel-border bg-white px-3 text-sm text-panel-text focus:outline-none focus:ring-2 focus:ring-slate-400/40"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <select
            value={filters.region}
            onChange={(e) => onChange("region", e.target.value)}
            className="h-10 min-w-[180px] rounded-sm border border-panel-border bg-white px-3 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-slate-400/40"
          >
            <option value="">Todas las regiones</option>
            {regions.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
          <select
            value={filters.responsable_lawyer_id}
            onChange={(e) => onChange("responsable_lawyer_id", e.target.value)}
            className="h-10 min-w-[200px] rounded-sm border border-panel-border bg-white px-3 text-sm text-panel-text focus:outline-none focus:ring-2 focus:ring-slate-400/40"
          >
            <option value="">Todos los responsables</option>
            {lawyers.map((lawyer) => (
              <option key={lawyer.id} value={String(lawyer.id)}>
                {lawyer.nombre}
              </option>
            ))}
          </select>
          <button
            onClick={onClear}
            className="h-10 rounded-sm border border-panel-border bg-white px-3 text-sm text-panel-secondary transition-all duration-150 hover:bg-[#f3f4f6] focus:outline-none focus:ring-2 focus:ring-slate-400/40"
          >
            Limpiar filtros
          </button>
        </div>
      </div>
    </section>
  );
}

function ProjectTable({
  projects,
  lawyers,
  onUpdateManagement,
  onOpenSummary,
}) {
  return (
    <section className="mt-6 overflow-hidden rounded-md border border-panel-border bg-panel-card">
      <div>
        <table className="w-full table-fixed text-xs">
          <thead className="sticky top-0 z-10 bg-[#f8fafc]">
            <tr className="border-b border-panel-border text-left text-xs uppercase tracking-wide text-panel-muted">
              <th className="w-[24%] px-3 py-3 font-medium">Proyecto</th>
              <th className="w-[10%] px-3 py-3 font-medium">Región</th>
              <th className="w-[12%] px-3 py-3 font-medium">Monto</th>
              <th className="w-[12%] px-3 py-3 font-medium">Estado</th>
              <th className="w-[14%] px-3 py-3 font-medium">Responsable</th>
              <th className="w-[20%] px-3 py-3 font-medium">Contactos</th>
              <th className="w-[8%] px-3 py-3 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((item) => (
              <tr
                key={item.project_id}
                className="border-b border-panel-border/60 transition-all duration-150 hover:bg-[#f9fafb]"
              >
                <td className="px-3 py-3">
                  <div className="line-clamp-3 font-medium text-panel-text">{item.nombre_proyecto}</div>
                  {item.is_new ? (
                    <span className="mt-1 inline-flex rounded-sm bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                      NUEVO
                    </span>
                  ) : null}
                </td>
                <td className="px-3 py-3 text-panel-secondary">{item.region || "-"}</td>
                <td className="px-3 py-3 text-panel-secondary">
                  <span className="line-clamp-2">{formatMonto(item.monto_inversion)}</span>
                </td>
                <td className="px-3 py-3">
                  <select
                    value={item.pipeline_status || "sin_contactar"}
                    onChange={(e) =>
                      onUpdateManagement(item.project_id, {
                        pipeline_status: e.target.value,
                      })
                    }
                    className="h-8 w-full rounded-sm border border-panel-border bg-white px-2 text-xs capitalize text-panel-text focus:outline-none focus:ring-2 focus:ring-slate-400/40"
                  >
                    {STATUS_OPTIONS.filter((x) => x.value).map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-3">
                  <select
                    value={item.responsable_lawyer_id || ""}
                    onChange={(e) =>
                      onUpdateManagement(item.project_id, {
                        responsable_lawyer_id: e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                    className="h-8 w-full rounded-sm border border-panel-border bg-white px-2 text-xs text-panel-text focus:outline-none focus:ring-2 focus:ring-slate-400/40"
                  >
                    <option value="">Sin asignar</option>
                    {lawyers.map((lawyer) => (
                      <option key={lawyer.id} value={lawyer.id}>
                        {lawyer.nombre}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-3">
                  <div className="space-y-2 text-[11px] leading-tight">
                    <div>
                      <div className="text-panel-muted">Titular</div>
                      <div className="truncate text-panel-text">{item.titular_nombre || "-"}</div>
                      <div className="truncate text-panel-text">{item.titular_email || "-"}</div>
                      <div className="truncate text-panel-secondary">{item.titular_telefono || "-"}</div>
                    </div>
                    <div>
                      <div className="text-panel-muted">Rep. legal</div>
                      <div className="truncate text-panel-text">{item.rep_legal_nombre || "-"}</div>
                      <div className="truncate text-panel-text">{item.rep_legal_email || "-"}</div>
                      <div className="truncate text-panel-secondary">{item.rep_legal_telefono || "-"}</div>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3">
                  <div className="flex">
                    <button
                      onClick={() => onOpenSummary(item)}
                      className="w-full rounded-sm border border-panel-border bg-white px-2 py-1.5 text-[11px] text-panel-text transition-all duration-150 hover:bg-[#f3f4f6] focus:outline-none focus:ring-2 focus:ring-slate-400/40"
                    >
                      Resumen
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {projects.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-panel-muted">
                  No hay proyectos para los filtros seleccionados.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SummaryModal({ project, onClose }) {
  if (!project) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 px-4">
      <div className="max-h-[80vh] w-full max-w-3xl overflow-auto rounded-md border border-panel-border bg-panel-card p-5">
        <div className="mb-3 flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-panel-text">Resumen del proyecto</h3>
            <p className="text-sm text-panel-secondary">{project.nombre_proyecto}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-sm border border-panel-border px-2.5 py-1 text-xs text-panel-secondary transition-all duration-150 hover:bg-panel-hover"
          >
            Cerrar
          </button>
        </div>
        {project.url_detalle ? (
          <div className="mb-3">
            <a
              href={project.url_detalle}
              target="_blank"
              rel="noreferrer"
              className="inline-flex rounded-sm bg-panel-topbar px-3 py-1.5 text-xs font-medium text-white transition-all duration-150 hover:brightness-110"
            >
              Abrir ficha SEIA
            </a>
          </div>
        ) : null}
        <div className="mb-4 rounded-sm border border-panel-border bg-[#f9fafb] p-3 text-xs text-panel-secondary">
          <div><span className="text-panel-muted">Monto inversión:</span> {formatMonto(project.monto_inversion)}</div>
          <div><span className="text-panel-muted">Nombre titular:</span> {project.titular_nombre || "-"}</div>
          <div><span className="text-panel-muted">Titular:</span> {project.titular_email || "-"}</div>
          <div><span className="text-panel-muted">Nombre rep. legal:</span> {project.rep_legal_nombre || "-"}</div>
          <div><span className="text-panel-muted">Rep. legal:</span> {project.rep_legal_email || "-"}</div>
          <div><span className="text-panel-muted">Teléfono titular:</span> {project.titular_telefono || "-"}</div>
          <div><span className="text-panel-muted">Teléfono rep. legal:</span> {project.rep_legal_telefono || "-"}</div>
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-panel-text">
          {project.descripcion_completa || "No hay resumen disponible para este proyecto."}
        </p>
      </div>
    </div>
  );
}

function App() {
  const [kpis, setKpis] = useState(null);
  const [lawyers, setLawyers] = useState([]);
  const [regions, setRegions] = useState([]);
  const [projects, setProjects] = useState([]);
  const [summaryProject, setSummaryProject] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    pipeline_status: "",
    region: "",
    responsable_lawyer_id: "",
  });

  const kpisGeneral = useMemo(() => {
    return [
      { label: "Total proyectos", value: kpis?.total_projects || 0 },
      { label: "Sin responsable", value: kpis?.without_lawyer || 0 },
      { label: "Seguimientos vencidos", value: kpis?.overdue_followups || 0 },
    ];
  }, [kpis]);

  const kpisEstado = useMemo(() => {
    const byStatus = kpis?.by_pipeline_status || {};
    return [
      { label: "Sin contactar", value: byStatus.sin_contactar || 0 },
      { label: "Contactado", value: byStatus.contactado || 0 },
      { label: "Fallido", value: byStatus.fallido || 0 },
      { label: "Completado", value: byStatus.completado || 0 },
    ];
  }, [kpis]);

  async function loadLawyers() {
    const data = await api("/api/lawyers");
    setLawyers(data.items || []);
  }

  async function loadRegions() {
    const data = await api("/api/regions");
    setRegions(data.items || []);
  }

  async function loadKpis() {
    const data = await api("/api/dashboard/kpis");
    setKpis(data);
  }

  async function loadProjects() {
    const params = new URLSearchParams();
    if (filters.search.trim()) params.set("search", filters.search.trim());
    if (filters.pipeline_status) params.set("pipeline_status", filters.pipeline_status);
    if (filters.region.trim()) params.set("region", filters.region.trim());
    if (filters.responsable_lawyer_id) params.set("responsable_lawyer_id", filters.responsable_lawyer_id);
    params.set("limit", "200");

    const data = await api(`/api/projects?${params.toString()}`);
    setProjects(data.items || []);
  }

  async function openSummary(project) {
    if (project.descripcion_completa) {
      setSummaryProject(project);
      return;
    }
    const detail = await api(`/api/projects/${project.project_id}`);
    setSummaryProject(detail);
  }

  async function refreshAll() {
    setLoading(true);
    try {
      await Promise.all([loadLawyers(), loadRegions(), loadKpis(), loadProjects()]);
    } finally {
      setLoading(false);
    }
  }

  async function updateManagement(projectId, payload) {
    await api(`/api/projects/${projectId}/management`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    await Promise.all([loadProjects(), loadKpis()]);
  }

  useEffect(() => {
    refreshAll().catch((err) => alert(`Error cargando panel: ${err.message}`));
  }, []);

  useEffect(() => {
    loadProjects().catch((err) => alert(`Error cargando proyectos: ${err.message}`));
  }, [filters.search, filters.pipeline_status, filters.region, filters.responsable_lawyer_id]);

  return (
    <DashboardLayout>
      <Header />

      <section className="mt-6 space-y-3">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {kpisGeneral.map((item) => (
            <KpiCard key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {kpisEstado.map((item) => (
            <KpiCard key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
      </section>

      <FilterBar
        filters={filters}
        lawyers={lawyers}
        regions={regions}
        onChange={(field, value) => setFilters((prev) => ({ ...prev, [field]: value }))}
        onClear={() =>
          setFilters({
            search: "",
            pipeline_status: "",
            region: "",
            responsable_lawyer_id: "",
          })
        }
      />

      <ProjectTable
        projects={projects}
        lawyers={lawyers}
        onUpdateManagement={updateManagement}
        onOpenSummary={openSummary}
      />

      <SummaryModal project={summaryProject} onClose={() => setSummaryProject(null)} />

      {loading ? (
        <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center bg-black/25">
          <div className="rounded-sm border border-panel-border bg-panel-card px-4 py-2 text-sm text-panel-secondary">
            Actualizando...
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
