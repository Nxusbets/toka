import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usersApi, rolesApi } from '../services/api';
import type { User, Role } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorState from '../components/common/ErrorState';
import UserForm from '../components/users/UserForm';
import toast from 'react-hot-toast';

export default function UserEdit() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id === 'new';

  const [user, setUser] = useState<Partial<User> | null>(
    isNew ? { email: '', username: '', is_active: true } : null,
  );
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const rolesRes = await rolesApi.list({ page: 1, size: 100 });
        setRoles(rolesRes.data.items);

        if (!isNew) {
          const userRes = await usersApi.get(id!);
          setUser(userRes.data);
          setSelectedRoleIds(
            userRes.data.roles?.map((r) => r.id) || [],
          );
        }
      } catch (err: any) {
        setFetchError(
          err?.response?.data?.detail || 'Failed to load data',
        );
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleSave = async (data: Partial<User>) => {
    setSaving(true);
    try {
      if (isNew) {
        const res = await usersApi.create(data);
        const newId = res.data.id;
        for (const roleId of selectedRoleIds) {
          await usersApi.assignRole(newId, roleId);
        }
        toast.success('User created successfully');
      } else {
        await usersApi.update(id!, data);
        const currentRoleIds = user?.roles?.map((r) => r.id) || [];
        const toAdd = selectedRoleIds.filter((r) => !currentRoleIds.includes(r));
        const toRemove = currentRoleIds.filter((r) => !selectedRoleIds.includes(r));
        for (const roleId of toAdd) {
          await usersApi.assignRole(id!, roleId);
        }
        for (const roleId of toRemove) {
          await usersApi.removeRole(id!, roleId);
        }
        toast.success('User updated successfully');
      }
      navigate('/users');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save user');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (fetchError && !user) {
    return (
      <ErrorState message={fetchError} onRetry={() => navigate('/users')} />
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">
          {isNew ? 'Create User' : 'Edit User'}
        </h1>
      </div>
      {user && (
        <UserForm
          initialData={user}
          roles={roles}
          selectedRoleIds={selectedRoleIds}
          onRoleChange={setSelectedRoleIds}
          onSave={handleSave}
          onCancel={() => navigate('/users')}
          saving={saving}
          isNew={isNew}
        />
      )}
    </div>
  );
}
