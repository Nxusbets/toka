import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUserStore } from '../stores/userStore';
import { useRoleStore } from '../stores/roleStore';
import { useAuditStore } from '../stores/auditStore';
import { useAIStore } from '../stores/aiStore';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { Users, Shield, Activity, Bot, ArrowRight } from 'lucide-react';
import { formatDateTime } from '../utils/format';

export default function Dashboard() {
  const navigate = useNavigate();
  const { users, total: totalUsers, loading: usersLoading, fetchUsers } = useUserStore();
  const { roles, total: totalRoles, loading: rolesLoading, fetchRoles } = useRoleStore();
  const { logs, loading: logsLoading, fetchLogs } = useAuditStore();
  const { query: aiQuery, loading: aiLoading } = useAIStore();
  const [aiInput, setAiInput] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [dashError, setDashError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchUsers(1, 100),
      fetchRoles(1, 100),
      fetchLogs({ page: 1, size: 5 }),
    ]).catch(() => setDashError('Failed to load dashboard data'));
  }, []);

  const activeUsers = users.filter((u) => u.is_active).length;

  const handleAiSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiInput.trim()) return;
    const res = await aiQuery(aiInput);
    if (res) {
      setAiResponse(res.answer);
    }
    setAiInput('');
  };

  if (dashError) {
    return (
      <div className="page">
        <h1 className="page-title">Dashboard</h1>
        <div className="error-state">
          <p>{dashError}</p>
          <button
            className="btn btn-primary"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h1 className="page-title">Dashboard</h1>

      <div className="stats-grid">
        <div
          className="stat-card"
          onClick={() => navigate('/users')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/users')}
        >
          <div className="stat-icon users-icon">
            <Users size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-value">
              {usersLoading ? '...' : totalUsers}
            </span>
            <span className="stat-label">Total Users</span>
          </div>
        </div>
        <div
          className="stat-card"
          onClick={() => navigate('/users')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/users')}
        >
          <div className="stat-icon active-icon">
            <Activity size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-value">
              {usersLoading ? '...' : activeUsers}
            </span>
            <span className="stat-label">Active Users</span>
          </div>
        </div>
        <div
          className="stat-card"
          onClick={() => navigate('/roles')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && navigate('/roles')}
        >
          <div className="stat-icon roles-icon">
            <Shield size={24} />
          </div>
          <div className="stat-info">
            <span className="stat-value">
              {rolesLoading ? '...' : totalRoles}
            </span>
            <span className="stat-label">Roles</span>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Audit Logs</h2>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => navigate('/audit')}
            >
              View All <ArrowRight size={14} />
            </button>
          </div>
          {logsLoading ? (
            <LoadingSpinner size={24} />
          ) : logs.length === 0 ? (
            <p className="text-muted">No audit logs found</p>
          ) : (
            <div className="recent-logs">
              {logs.slice(0, 5).map((log) => (
                <div key={log.id} className="log-item">
                  <span className="log-event badge badge-info">
                    {log.event_type}
                  </span>
                  <span className="log-user">{log.user_email}</span>
                  <span className="log-time">
                    {formatDateTime(log.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="dashboard-section">
          <div className="section-header">
            <h2>Quick AI Query</h2>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => navigate('/ai')}
            >
              Full Chat <ArrowRight size={14} />
            </button>
          </div>
          <form onSubmit={handleAiSubmit} className="ai-mini-form">
            <input
              type="text"
              className="form-input"
              placeholder="Ask something..."
              value={aiInput}
              onChange={(e) => setAiInput(e.target.value)}
              disabled={aiLoading}
            />
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={aiLoading || !aiInput.trim()}
            >
              <Bot size={16} />
            </button>
          </form>
          {aiLoading && <LoadingSpinner size={20} />}
          {aiResponse && (
            <div className="ai-mini-response">
              <p>{aiResponse}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
