import { useEffect, useState } from 'react';
import { useAuditStore } from '../stores/auditStore';
import DataTable, { Column } from '../components/common/DataTable';
import type { AuditLog } from '../types';
import { formatDateTime } from '../utils/format';
import { ChevronDown, ChevronRight } from 'lucide-react';

const EVENT_TYPES = [
  'user.login',
  'user.logout',
  'user.created',
  'user.updated',
  'user.deleted',
  'role.created',
  'role.updated',
  'role.deleted',
];

export default function AuditLogs() {
  const { logs, total, loading, error, fetchLogs } = useAuditStore();
  const [page, setPage] = useState(1);
  const [eventType, setEventType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchLogs({
      page,
      size: 20,
      event_type: eventType || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
  }, [page, eventType, startDate, endDate]);

  const columns: Column<AuditLog>[] = [
    {
      key: 'event_type',
      header: 'Event',
      render: (log) => (
        <span className="badge badge-info">{log.event_type}</span>
      ),
    },
    {
      key: 'user_email',
      header: 'User',
      render: (log) => log.user_email,
    },
    {
      key: 'resource',
      header: 'Resource',
      render: (log) => log.resource,
    },
    {
      key: 'action',
      header: 'Action',
      render: (log) => log.action,
    },
    {
      key: 'ip_address',
      header: 'IP',
      render: (log) => log.ip_address,
    },
    {
      key: 'timestamp',
      header: 'Timestamp',
      sortable: true,
      render: (log) => formatDateTime(log.timestamp),
    },
    {
      key: 'metadata',
      header: 'Details',
      render: (log) => (
        <button
          className="btn btn-outline btn-sm"
          onClick={() =>
            setExpandedId(expandedId === log.id ? null : log.id)
          }
          title="View metadata"
        >
          {expandedId === log.id ? (
            <ChevronDown size={14} />
          ) : (
            <ChevronRight size={14} />
          )}
        </button>
      ),
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Audit Logs</h1>
      </div>
      <div className="filters">
        <div className="form-group">
          <label>Event Type</label>
          <select
            className="form-input"
            value={eventType}
            onChange={(e) => {
              setEventType(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All</option>
            {EVENT_TYPES.map((et) => (
              <option key={et} value={et}>
                {et}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Start Date</label>
          <input
            type="date"
            className="form-input"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="form-group">
          <label>End Date</label>
          <input
            type="date"
            className="form-input"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
          />
        </div>
      </div>
      <DataTable
        columns={columns}
        data={logs}
        loading={loading}
        error={error}
        onRetry={() =>
          fetchLogs({
            page,
            size: 20,
            event_type: eventType || undefined,
            start_date: startDate || undefined,
            end_date: endDate || undefined,
          })
        }
        page={page}
        total={total}
        size={20}
        onPageChange={setPage}
        emptyMessage="No audit logs found"
      />
      {logs.map(
        (log) =>
          expandedId === log.id && (
            <div key={log.id} className="expanded-section">
              <h4>Metadata</h4>
              {log.metadata && Object.keys(log.metadata).length > 0 ? (
                <pre className="metadata-json">
                  {JSON.stringify(log.metadata, null, 2)}
                </pre>
              ) : (
                <p className="text-muted">No metadata</p>
              )}
            </div>
          ),
      )}
    </div>
  );
}
