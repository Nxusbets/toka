import { useEffect, useState } from 'react';
import { useRoleStore } from '../stores/roleStore';
import DataTable, { Column } from '../components/common/DataTable';
import type { Role } from '../types';
import { Trash2, Plus, ChevronDown, ChevronRight } from 'lucide-react';

export default function RoleList() {
  const { roles, total, loading, error, fetchRoles, deleteRole } =
    useRoleStore();
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchRoles(page, 20);
  }, [page]);

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this role?')) {
      try {
        await deleteRole(id);
      } catch {
        // handled in store
      }
    }
  };

  const columns: Column<Role>[] = [
    {
      key: 'name',
      header: 'Name',
      sortable: true,
      render: (role) => (
        <button
          className="link-btn"
          onClick={() =>
            setExpandedId(expandedId === role.id ? null : role.id)
          }
        >
          {expandedId === role.id ? (
            <ChevronDown size={14} />
          ) : (
            <ChevronRight size={14} />
          )}
          {role.name}
        </button>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (role) => role.description || '\u2014',
    },
    {
      key: 'is_system',
      header: 'System',
      render: (role) => (
        <span
          className={`badge ${role.is_system ? 'badge-warning' : 'badge-success'}`}
        >
          {role.is_system ? 'System' : 'Custom'}
        </span>
      ),
    },
    {
      key: 'permissions',
      header: 'Permissions',
      render: (role) => (
        <span>{role.permissions?.length || 0} permissions</span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (role) => (
        <div className="action-buttons">
          {!role.is_system && (
            <button
              className="btn btn-danger btn-sm"
              onClick={() => handleDelete(role.id)}
              title="Delete role"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Roles</h1>
        <button className="btn btn-primary">
          <Plus size={18} />
          Create Role
        </button>
      </div>
      <div className="role-list">
        <DataTable
          columns={columns}
          data={roles}
          loading={loading}
          error={error}
          onRetry={() => fetchRoles(page, 20)}
          page={page}
          total={total}
          size={20}
          onPageChange={setPage}
          emptyMessage="No roles found"
        />
        {roles.map(
          (role) =>
            expandedId === role.id && (
              <div key={role.id} className="expanded-section">
                <h4>Permissions for {role.name}</h4>
                {role.permissions && role.permissions.length > 0 ? (
                  <table className="data-table compact">
                    <thead>
                      <tr>
                        <th>Resource</th>
                        <th>Action</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {role.permissions.map((perm) => (
                        <tr key={perm.id}>
                          <td>{perm.resource}</td>
                          <td>
                            <span className="badge badge-info">
                              {perm.action}
                            </span>
                          </td>
                          <td>{perm.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-muted">No permissions assigned</p>
                )}
              </div>
            ),
        )}
      </div>
    </div>
  );
}
