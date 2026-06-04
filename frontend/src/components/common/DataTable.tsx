import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  render: (item: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  page?: number;
  total?: number;
  size?: number;
  onPageChange?: (page: number) => void;
  sortKey?: string;
  sortDir?: 'asc' | 'desc';
  onSort?: (key: string) => void;
  emptyMessage?: string;
}

export default function DataTable<T>({
  columns,
  data,
  loading,
  error,
  onRetry,
  page = 1,
  total = 0,
  size = 20,
  onPageChange,
  sortKey,
  sortDir,
  onSort,
  emptyMessage,
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key}>{col.header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={col.key}>
                    <div
                      className="skeleton"
                      style={{ height: 20, width: `${60 + Math.random() * 30}%` }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (error) {
    return (
      <div className="table-error">
        <p>{error}</p>
        {onRetry && (
          <button className="btn btn-primary btn-sm" onClick={onRetry}>
            Retry
          </button>
        )}
      </div>
    );
  }

  if (data.length === 0) {
    return <EmptyState message={emptyMessage || 'No data found'} />;
  }

  const totalPages = Math.ceil(total / size);

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={col.sortable ? 'sortable' : ''}
                onClick={() => col.sortable && onSort?.(col.key)}
              >
                <span className="th-content">
                  {col.header}
                  {col.sortable && sortKey === col.key && (
                    sortDir === 'asc' ? (
                      <ChevronUp size={14} />
                    ) : (
                      <ChevronDown size={14} />
                    )
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => {
            const row = item as Record<string, unknown>;
            return (
              <tr key={(row.id as string) || idx}>
                {columns.map((col) => (
                  <td key={col.key}>{col.render(item)}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      {totalPages > 1 && onPageChange && (
        <div className="pagination">
          <button
            className="btn btn-outline btn-sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft size={16} />
          </button>
          <span className="pagination-info">
            Page {page} of {totalPages} ({total} total)
          </span>
          <button
            className="btn btn-outline btn-sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
