import React from 'react'

// const sampleIngestions = ['Entry 1', 'Entry 2', 'Entry 3', 'Entry 4', 'Entry 5']
// const sampleConfigs = ['Connector Entry 1', 'Rules Entry 1', 'Output Target Entry 1', 'Connector Entry 2', 'Rules Entry 2']

export default function App() {
  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">Fortude</div>
        <nav className="topnav">
          <button className="link">Ingest</button>
          <button className="link">History</button>
          <button className="link">Configure</button>
        </nav>
        <div className="profile-toggle" aria-hidden />
      </header>

      <main className="dashboard">
        <h1 className="title">Dashboard</h1>

        <div className="cta-wrap">
          <button className="btn primary">Start Ingestion</button>
        </div>

        <div className="panels">
          <section className="panel">
            <h2>Past Ingestions</h2>
            <ul className="list">
              {/* {sampleIngestions.map((t, i) => (
                <li key={i} className="list-item">
                  <span className="item-label">{t}</span>
                  <button className="btn small">View</button>
                </li>
              ))} */}
            </ul>
            <button className="btn full" onClick={() => (window.location.href = '/ingestion-history.html')}>View All</button>
          </section>

          <section className="panel">
            <h2>Configurations</h2>
            <ul className="list">
              {/* {sampleConfigs.map((t, i) => (
                <li key={i} className="list-item">
                  <span className="item-label">{t}</span>
                  <div style={{display:'flex',gap:'0.5rem'}}>
                    <button className="btn small">View</button>
                    <button className="btn small">Delete</button>
                  </div>
                </li>
              ))} */}
            </ul>
            <button className="btn full" onClick={() => (window.location.href = '/configurations.html')}>View All</button>
          </section>
        </div>
      </main>
    </div>
  )
}

