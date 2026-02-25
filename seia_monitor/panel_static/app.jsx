const { useEffect, useMemo, useState } = React;

const STATUS_OPTIONS = [
  { value: "", label: "Todos los estados" },
  { value: "contactado", label: "Contactado" },
  { value: "en_conversaciones", label: "En conversaciones" },
  { value: "fallido", label: "Fallido" },
  { value: "completado", label: "Completado" },
];

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

function DashboardLayout({ children }) {
  return <div className="max-w-7xl mx-auto px-6 py-6">{children}</div>;
}

function StatusBadge({ status }) {
  const config = {
    contactado: "bg-blue-500/15 text-blue-300",
    en_conversaciones: "bg-amber-500/15 text-amber-300",
    completado: "bg-emerald-500/15 text-emerald-300",
    fallido: "bg-red-500/15 text-red-300",
  };
  const cls = config[status] || "bg-slate-500/15 text-slate-300";
  const label = (status || "-").replaceAll("_", " ");
  return (
    <span className={`inline-flex rounded-md px-2.5 py-1 text-xs font-medium capitalize ${cls}`}>
      {label}
    </span>
  );
}

function KpiCard({ label, value }) {
  return (
    <article className="rounded-xl border border-panel-border bg-panel-card p-4 transition-all duration-150 hover:bg-panel-hover">
      <p className="text-[11px] uppercase tracking-wide text-panel-muted">{label}</p>
      <p className="mt-1 text-3xl font-bold text-panel-text">{value}</p>
    </article>
  );
}

function Header({ onRefresh }) {
  return (
    <header className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-panel-text">Panel de Monitoreo</h1>
        <p className="mt-1 text-sm text-panel-secondary">Control comercial y legal de proyectos SEIA</p>
      </div>
      <button
        onClick={onRefresh}
        className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white transition-all duration-150 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
      >
        Actualizar datos
      </button>
    </header>
  );
}

function FilterBar({ filters, lawyers, onChange }) {
  return (
    <section className="mt-6 rounded-xl border border-panel-border bg-panel-card p-4">
      <div className="flex flex-col gap-3 lg:flex-row">
        <input
          value={filters.search}
          onChange={(e) => onChange("search", e.target.value)}
          placeholder="Buscar por proyecto o titular"
          className="h-10 flex-1 rounded-lg border border-panel-border bg-panel-main px-3 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40"
        />
        <div className="flex gap-3">
          <select
            value={filters.pipeline_status}
            onChange={(e) => onChange("pipeline_status", e.target.value)}
            className="h-10 min-w-[180px] rounded-lg border border-panel-border bg-panel-main px-3 text-sm text-panel-text focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <input
            value={filters.region}
            onChange={(e) => onChange("region", e.target.value)}
            placeholder="Región exacta"
            className="h-10 min-w-[180px] rounded-lg border border-panel-border bg-panel-main px-3 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          />
          <select
            value={filters.responsable_lawyer_id}
            onChange={(e) => onChange("responsable_lawyer_id", e.target.value)}
            className="h-10 min-w-[200px] rounded-lg border border-panel-border bg-panel-main px-3 text-sm text-panel-text focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          >
            <option value="">Todos los responsables</option>
            {lawyers.map((lawyer) => (
              <option key={lawyer.id} value={String(lawyer.id)}>
                {lawyer.nombre}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
}

function ProjectTable({
  projects,
  lawyers,
  onSelectProject,
  onUpdateManagement,
}) {
  return (
    <section className="mt-6 overflow-hidden rounded-xl border border-panel-border bg-panel-card">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 z-10 bg-panel-card">
            <tr className="border-b border-panel-border text-left text-xs uppercase tracking-wide text-panel-muted">
              <th className="px-4 py-3 font-medium">Proyecto</th>
              <th className="px-4 py-3 font-medium">Región</th>
              <th className="px-4 py-3 font-medium">Estado SEIA</th>
              <th className="px-4 py-3 font-medium">Estado interno</th>
              <th className="px-4 py-3 font-medium">Responsable</th>
              <th className="px-4 py-3 font-medium">Próxima acción</th>
              <th className="px-4 py-3 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((item) => (
              <tr
                key={item.project_id}
                className="border-b border-white/5 transition-all duration-150 hover:bg-white/5"
              >
                <td className="px-4 py-3">
                  <div className="font-medium text-panel-text">{item.nombre_proyecto}</div>
                  {item.is_new ? (
                    <span className="mt-1 inline-flex rounded-md bg-emerald-500/20 px-2 py-0.5 text-[11px] font-semibold text-emerald-300">
                      NUEVO
                    </span>
                  ) : null}
                </td>
                <td className="px-4 py-3 text-panel-secondary">{item.region || "-"}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex rounded-md bg-slate-500/15 px-2.5 py-1 text-xs text-slate-300">
                    {item.estado || "-"}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={item.pipeline_status || "contactado"}
                    onChange={(e) =>
                      onUpdateManagement(item.project_id, {
                        pipeline_status: e.target.value,
                      })
                    }
                    className="h-9 min-w-[170px] rounded-lg border border-panel-border bg-panel-main px-2.5 text-xs capitalize text-panel-text focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    {STATUS_OPTIONS.filter((x) => x.value).map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={item.responsable_lawyer_id || ""}
                    onChange={(e) =>
                      onUpdateManagement(item.project_id, {
                        responsable_lawyer_id: e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                    className="h-9 min-w-[190px] rounded-lg border border-panel-border bg-panel-main px-2.5 text-xs text-panel-text focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    <option value="">Sin asignar</option>
                    {lawyers.map((lawyer) => (
                      <option key={lawyer.id} value={lawyer.id}>
                        {lawyer.nombre}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3 text-panel-secondary">{item.proxima_accion_at || "-"}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => onSelectProject(item.project_id)}
                    className="rounded-lg border border-panel-border bg-panel-main px-3 py-1.5 text-xs text-panel-text transition-all duration-150 hover:bg-panel-hover focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                  >
                    Ver detalle
                  </button>
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

function DetailPanel({
  project,
  activity,
  onClose,
  onSaveNotes,
  onAddActivity,
}) {
  const [notes, setNotes] = useState(project?.notas || "");
  const [activityBy, setActivityBy] = useState("");
  const [activityType, setActivityType] = useState("nota");
  const [activityContent, setActivityContent] = useState("");

  useEffect(() => {
    setNotes(project?.notas || "");
  }, [project?.project_id]);

  if (!project) return null;

  return (
    <aside className="mt-6 rounded-xl border border-panel-border bg-panel-card p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-panel-text">Detalle del proyecto</h2>
        <button
          onClick={onClose}
          className="rounded-lg border border-panel-border px-2.5 py-1 text-xs text-panel-secondary transition-all duration-150 hover:bg-panel-hover"
        >
          Cerrar
        </button>
      </div>

      <div className="space-y-2 text-sm">
        <p><span className="text-panel-muted">ID:</span> {project.project_id}</p>
        <p><span className="text-panel-muted">Proyecto:</span> {project.nombre_proyecto}</p>
        <p><span className="text-panel-muted">Etiqueta:</span> {project.is_new ? "NUEVO" : "-"}</p>
        <p><span className="text-panel-muted">Titular:</span> {project.titular || "-"}</p>
        <p>
          <span className="text-panel-muted">Estado interno:</span>{" "}
          <StatusBadge status={project.pipeline_status || "contactado"} />
        </p>
        <p><span className="text-panel-muted">Responsable:</span> {project.responsable_lawyer_nombre || "Sin asignar"}</p>
        <p><span className="text-panel-muted">Prioridad:</span> {project.prioridad || "media"}</p>
        <p><span className="text-panel-muted">Probabilidad cierre:</span> {project.probabilidad_cierre ?? "-"}%</p>
      </div>

      <div className="mt-4">
        <label className="mb-1 block text-xs uppercase tracking-wide text-panel-muted">Notas</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="min-h-[90px] w-full rounded-lg border border-panel-border bg-panel-main px-3 py-2 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40"
        />
        <button
          onClick={() => onSaveNotes(notes)}
          className="mt-2 w-full rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white transition-all duration-150 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        >
          Guardar notas
        </button>
      </div>

      <div className="mt-6">
        <h3 className="mb-2 text-xs uppercase tracking-wide text-panel-muted">Registrar actividad</h3>
        <div className="space-y-2">
          <input
            value={activityBy}
            onChange={(e) => setActivityBy(e.target.value)}
            placeholder="Creado por"
            className="h-10 w-full rounded-lg border border-panel-border bg-panel-main px-3 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          />
          <input
            value={activityType}
            onChange={(e) => setActivityType(e.target.value)}
            placeholder="Tipo"
            className="h-10 w-full rounded-lg border border-panel-border bg-panel-main px-3 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          />
          <textarea
            value={activityContent}
            onChange={(e) => setActivityContent(e.target.value)}
            placeholder="Comentario o seguimiento"
            className="min-h-[90px] w-full rounded-lg border border-panel-border bg-panel-main px-3 py-2 text-sm text-panel-text placeholder:text-panel-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          />
          <button
            onClick={async () => {
              if (!activityContent.trim()) return;
              await onAddActivity({
                content: activityContent.trim(),
                activity_type: activityType.trim() || "nota",
                created_by: activityBy.trim() || null,
              });
              setActivityContent("");
            }}
            className="w-full rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white transition-all duration-150 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            Guardar actividad
          </button>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="mb-2 text-xs uppercase tracking-wide text-panel-muted">Historial</h3>
        <ul className="max-h-[260px] space-y-2 overflow-auto">
          {activity.map((item) => (
            <li
              key={item.id}
              className="rounded-lg border border-panel-border bg-panel-main px-3 py-2 text-xs leading-relaxed text-panel-secondary"
            >
              {item.created_at} - {item.activity_type} - {item.content} ({item.created_by || "sin autor"})
            </li>
          ))}
          {activity.length === 0 ? (
            <li className="rounded-lg border border-panel-border bg-panel-main px-3 py-3 text-xs text-panel-muted">
              Sin actividad registrada.
            </li>
          ) : null}
        </ul>
      </div>
    </aside>
  );
}

function App() {
  const [kpis, setKpis] = useState(null);
  const [lawyers, setLawyers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    pipeline_status: "",
    region: "",
    responsable_lawyer_id: "",
  });

  const kpiCards = useMemo(() => {
    const byStatus = kpis?.by_pipeline_status || {};
    return [
      { label: "Total proyectos", value: kpis?.total_projects || 0 },
      { label: "Sin responsable", value: kpis?.without_lawyer || 0 },
      { label: "Seguimientos vencidos", value: kpis?.overdue_followups || 0 },
      { label: "En conversaciones", value: byStatus.en_conversaciones || 0 },
      { label: "Completado", value: byStatus.completado || 0 },
    ];
  }, [kpis]);

  async function loadLawyers() {
    const data = await api("/api/lawyers");
    setLawyers(data.items || []);
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

  async function selectProject(projectId) {
    const [project, activityResp] = await Promise.all([
      api(`/api/projects/${projectId}`),
      api(`/api/projects/${projectId}/activity`),
    ]);
    setSelectedProject(project);
    setActivity(activityResp.items || []);
  }

  async function refreshAll() {
    setLoading(true);
    try {
      await Promise.all([loadLawyers(), loadKpis(), loadProjects()]);
      if (selectedProject?.project_id) {
        await selectProject(selectedProject.project_id);
      }
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
    if (selectedProject?.project_id === projectId) {
      await selectProject(projectId);
    }
  }

  async function saveNotes(notes) {
    if (!selectedProject?.project_id) return;
    await updateManagement(selectedProject.project_id, { notas: notes });
  }

  async function addActivity(payload) {
    if (!selectedProject?.project_id) return;
    await api(`/api/projects/${selectedProject.project_id}/activity`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await selectProject(selectedProject.project_id);
  }

  useEffect(() => {
    refreshAll().catch((err) => alert(`Error cargando panel: ${err.message}`));
  }, []);

  useEffect(() => {
    loadProjects().catch((err) => alert(`Error cargando proyectos: ${err.message}`));
  }, [filters.search, filters.pipeline_status, filters.region, filters.responsable_lawyer_id]);

  return (
    <DashboardLayout>
      <Header onRefresh={() => refreshAll().catch((err) => alert(err.message))} />

      <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        {kpiCards.map((item) => (
          <KpiCard key={item.label} label={item.label} value={item.value} />
        ))}
      </section>

      <FilterBar
        filters={filters}
        lawyers={lawyers}
        onChange={(field, value) => setFilters((prev) => ({ ...prev, [field]: value }))}
      />

      <ProjectTable
        projects={projects}
        lawyers={lawyers}
        onSelectProject={selectProject}
        onUpdateManagement={updateManagement}
      />

      <DetailPanel
        project={selectedProject}
        activity={activity}
        onClose={() => setSelectedProject(null)}
        onSaveNotes={saveNotes}
        onAddActivity={addActivity}
      />

      {loading ? (
        <div className="pointer-events-none fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="rounded-lg border border-panel-border bg-panel-card px-4 py-2 text-sm text-panel-secondary">
            Actualizando...
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
