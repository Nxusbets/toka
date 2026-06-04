import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUserStore } from '../stores/userStore';
import DataTable, { Column } from '../components/common/DataTable';
import type { User } from '../types';
import { Edit, Trash2, UserPlus, Search } from 'lucide-react';

export default function UserList() {
  const navigate = useNavigate();
  const { users, total, loading, error, fetchUsers, deleteUser } =
    useUserStore();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const pageSize = 20;

  useEffect(() => {
    fetchUsers(page, pageSize, search || undefined);
  }, [page, search]);

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await deleteUser(id);
      } catch {
        // error handled in store
      }
    }
  };

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const columns: Column<User>[] = [
    {
      key: 'email',
      header: 'Email',
      sortable: true,
      render: (user) => <Link to={`/users/${user.id}`}>{user.email}</Link>,
    },
    {
      key: 'username',
      header: 'Username',
      sortable: true,
      render: (user) => user.username || '\u2014',
    },
    {
      key: 'is_active',
      header: 'Status',
      sortable: true,
      render: (user) => (
        <span
          className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}
        >
          {user.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'roles',
      header: 'Roles',
      render: (user) =>
        user.roles?.length ? (
          <div className="roles-inline">
            {user.roles.map((r) => (
              <span key={r.id} className="badge badge-info">
                {r.name}
              </span>
            ))}
          </div>
        ) : (
          '\u2014'
        ),
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: true,
      render: (user) => new Date(user.created_at).toLocaleDateString(),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (user) => (
        <div className="action-buttons">
          <button
            className="btn btn-outline btn-sm"
            onClick={() => navigate(`/users/${user.id}`)}
            title="Edit user"
          >
            <Edit size={14} />
          </button>
          <button
            className="btn btn-danger btn-sm"
            onClick={() => handleDelete(user.id)}
            title="Delete user"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Users</h1>
        <div className="page-actions">
          <div className="search-box">
            <Search size={16} />
            <input
              type="text"
              className="form-input"
              placeholder="Search users..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/users/new')}
          >
            <UserPlus size={18} />
            Add User
          </button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={users}
        loading={loading}
        error={error}
        onRetry={() => fetchUsers(page, pageSize, search || undefined)}
        page={page}
        total={total}
        size={pageSize}
        onPageChange={setPage}
        sortKey={sortKey}
        sortDir={sortDir}
        onSort={handleSort}
      />
    </div>
  );
}
