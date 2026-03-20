import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Search, 
  FileText, 
  CheckCircle, 
  Activity, 
  Github, 
  AlertTriangle,
  Send
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area
} from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// --- Components ---

const Sidebar = () => (
  <div className="sidebar">
    <div className="logo">RISK PLATFORM</div>
    <ul className="nav-links">
      <li className="nav-item">
        <NavLink to="/" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={20} /> Dashboard
        </NavLink>
      </li>
      <li className="nav-item">
        <NavLink to="/analysis" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
          <Search size={20} /> Analysis
        </NavLink>
      </li>
      <li className="nav-item">
        <NavLink to="/reports" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileText size={20} /> Risk Reports
        </NavLink>
      </li>
      <li className="nav-item">
        <NavLink to="/approval" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
          <CheckCircle size={20} /> Approval Panel
        </NavLink>
      </li>
    </ul>
    <div style={{marginTop: 'auto', padding: '16px', color: 'var(--text-muted)', fontSize: '0.8rem'}}>
      System v1.0.4 Online
    </div>
  </div>
);

// --- Pages ---

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [deployments, setDeployments] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/analytics`).then(r => r.json()).then(setStats);
    fetch(`${API_BASE}/api/deployments`).then(r => r.json()).then(setDeployments);
  }, []);

  const pieData = stats ? [
    { name: 'Low', value: stats.risk_distribution.low, color: '#10b981' },
    { name: 'Med', value: stats.risk_distribution.medium, color: '#f59e0b' },
    { name: 'High', value: stats.risk_distribution.high, color: '#ef4444' },
  ] : [];

  return (
    <div className="animate-slide">
      <div className="header-section">
        <h1>Global Overview</h1>
        <p>Deployment confidence and risk metrics across your infrastructure.</p>
      </div>

      <div className="grid-cols-3" style={{marginBottom: '32px'}}>
        <div className="glass-card stat-box">
          <div className="stat-title">Total Releases</div>
          <div className="stat-val">{stats?.total_deployments || 0}</div>
        </div>
        <div className="glass-card stat-box">
          <div className="stat-title">Approval Rate</div>
          <div className="stat-val" style={{color: '#10b981'}}>
            {stats?.total_deployments ? Math.round((stats.status_distribution.approved / stats.total_deployments) * 100) : 0}%
          </div>
        </div>
        <div className="glass-card stat-box">
          <div className="stat-title">Avg Risk Score</div>
          <div className="stat-val" style={{color: '#f59e0b'}}>34.2</div>
        </div>
      </div>

      <div className="grid-cols-2">
        <div className="glass-card">
          <h3 style={{marginBottom: '20px'}}>Risk Distribution</h3>
          <div style={{height: '250px'}}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => <Cell key={index} fill={entry.color} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="glass-card">
          <h3 style={{marginBottom: '20px'}}>Recent Activity</h3>
          <ul style={{listStyle: 'none'}}>
            {deployments.slice(0, 5).map(d => (
              <li key={d.id} style={{padding: '12px 0', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between'}}>
                <div>
                  <div style={{fontWeight: 600}}>Commit {d.commit_hash.substring(0, 7)}</div>
                  <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{d.author}</div>
                </div>
                <span className={`badge badge-${d.risk_prediction?.risk_level?.toLowerCase() || 'med'}`}>{d.status}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

const Analysis = () => {
  const [repo, setRepo] = useState({ owner: '', repo: '', commit: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/analyze-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ owner: repo.owner, repo: repo.repo, commit_sha: repo.commit })
      });
      const data = await res.json();
      setResult(data);
    } catch (err) { alert("Analysis failed"); }
    setLoading(false);
  };

  return (
    <div className="animate-slide">
      <div className="header-section">
        <h1>New Deployment Analysis</h1>
        <p>Analyze a specific commit to determine risk before pushing to production.</p>
      </div>

      <div className="grid-cols-2">
        <div className="glass-card">
          <form onSubmit={handleAnalyze}>
            <div className="form-group">
              <label>Repository Owner</label>
              <input className="form-input" placeholder="e.g. facebook" value={repo.owner} onChange={e => setRepo({...repo, owner: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Repository Name</label>
              <input className="form-input" placeholder="e.g. react" value={repo.repo} onChange={e => setRepo({...repo, repo: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Commit SHA</label>
              <input className="form-input" placeholder="Full hash or branch" value={repo.commit} onChange={e => setRepo({...repo, commit: e.target.value})} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Activity size={18} /> {loading ? "Analyzing..." : "Run AI Analysis"}
            </button>
          </form>
        </div>

        {result && (
          <div className="glass-card animate-slide">
            <h3 style={{marginBottom: '16px'}}>Metrics Found</h3>
            <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
              <div style={{padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px'}}>
                <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Files Changed</div>
                <div style={{fontSize: '1.2rem', fontWeight: 600}}>{result.files_changed}</div>
              </div>
              <div style={{padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px'}}>
                <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Line Delta</div>
                <div style={{fontSize: '1.2rem', fontWeight: 600, color: '#10b981'}}>+{result.lines_added} / -{result.lines_deleted}</div>
              </div>
              <div style={{padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px'}}>
                <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Author</div>
                <div style={{fontSize: '1.2rem', fontWeight: 600}}>{result.author}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const Reports = () => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/risk-history`).then(r => r.json()).then(setHistory);
  }, []);

  return (
    <div className="animate-slide">
      <div className="header-section">
        <h1>Risk History Reports</h1>
        <p>Comprehensive logs of all AI predictions and scoring variables.</p>
      </div>
      <div className="glass-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Deployment ID</th>
              <th>Risk Score</th>
              <th>Level</th>
              <th>Recommendation</th>
              <th>Reasoning</th>
            </tr>
          </thead>
          <tbody>
            {history.map(item => (
              <tr key={item.id}>
                <td>#{item.id}</td>
                <td>{item.deployment_id}</td>
                <td style={{fontWeight: 700}}>{item.risk_score.toFixed(1)}</td>
                <td><span className={`badge badge-${item.risk_level.toLowerCase()}`}>{item.risk_level}</span></td>
                <td>{item.recommendation}</td>
                <td style={{fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '400px'}}>{item.reasoning}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const Approval = () => {
  const [deployments, setDeployments] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/deployments`).then(r => r.json()).then(data => {
      setDeployments(data.filter(d => d.status === 'pending_review' || d.status === 'pending'));
    });
  }, []);

  return (
    <div className="animate-slide">
      <div className="header-section">
        <h1>Approval Panel</h1>
        <p>Approve or Reject deployments based on AI confidence scoring.</p>
      </div>

      <div className="glass-card">
        {deployments.length === 0 ? (
          <div style={{textAlign: 'center', padding: '40px', color: 'var(--text-muted)'}}>
            <CheckCircle size={48} style={{marginBottom: '16px', opacity: 0.2}} />
            <p>Queue is empty. Your release pipeline is clear.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Commit</th>
                <th>Author</th>
                <th>AI Risk Score</th>
                <th>Reasoning</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {deployments.map(d => (
                <tr key={d.id}>
                  <td>{d.commit_hash.substring(0, 7)}</td>
                  <td>{d.author}</td>
                  <td>
                    <div style={{color: '#f87171', fontWeight: 700}}>{d.risk_prediction?.risk_score || 'Calculating...'}</div>
                    <div style={{fontSize: '0.7rem', color: 'var(--text-muted)'}}>{d.risk_prediction?.risk_level} Risk</div>
                  </td>
                  <td style={{maxWidth: '350px'}}>
                    <div style={{fontSize: '0.85rem', marginBottom: '4px'}}>{d.risk_prediction?.reasoning}</div>
                    <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
                       <span className="badge badge-med" style={{background: 'rgba(59,130,246,0.1)', color: '#60a5fa'}}>Requires: {d.risk_prediction?.required_approval || 'TBD'}</span>
                       {d.risk_prediction?.estimated_delay_hours > 0 && <span className="badge badge-med" style={{background: 'rgba(245,158,11,0.1)', color: '#fbbf24'}}>Delay: {d.risk_prediction?.estimated_delay_hours}h</span>}
                       {d.risk_prediction?.reasoning.includes('anomaly') && <span className="badge badge-high" style={{background: 'rgba(239,68,68,0.2)', color: '#f87171'}}>⚠️ ANOMALY</span>}
                    </div>
                  </td>
                  <td>
                    <div style={{display: 'flex', gap: '8px'}}>
                      <button className="btn btn-primary" style={{padding: '6px 12px', fontSize: '0.8rem', background: '#10b981'}}>Approve</button>
                      <button className="btn btn-primary" style={{padding: '6px 12px', fontSize: '0.8rem', background: '#ef4444'}}>Reject</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// --- Main App ---

export default function App() {
  return (
    <Router>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/approval" element={<Approval />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
