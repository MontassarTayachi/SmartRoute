const DashboardPage = ({ title, description }) => (
  <section className="page-panel">
    <div className="resource-header">
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
    </div>

    <div className="dashboard-grid">
      <article className="kpi-card">
        <span className="kpi-label">Véhicules en ligne</span>
        <div className="kpi-value">128</div>
      </article>
      <article className="kpi-card">
        <span className="kpi-label">Livraisons actives</span>
        <div className="kpi-value">42</div>
      </article>
      <article className="kpi-card">
        <span className="kpi-label">Optimisation IA</span>
        <div className="kpi-value">+17 %</div>
      </article>
    </div>
  </section>
);

export default DashboardPage;
