import { useState } from 'react';
import type { Role, Permission } from '../../types';

interface RoleFormProps {
  initialData?: Partial<Role>;
  permissions: Permission[];
  onSave: (data: Partial<Role> & { permission_ids?: string[] }) => Promise<void>;
  onCancel: () => void;
  saving: boolean;
}

export default function RoleForm({
  initialData = {},
  permissions,
  onSave,
  onCancel,
  saving,
}: RoleFormProps) {
  const [form, setForm] = useState({
    name: initialData.name || '',
    description: initialData.description || '',
  });
  const [selectedPermIds, setSelectedPermIds] = useState<string[]>(
    initialData.permissions?.map((p) => p.id) || [],
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSave({
      name: form.name,
      description: form.description,
      permission_ids: selectedPermIds,
    });
  };

  const togglePerm = (permId: string) => {
    if (selectedPermIds.includes(permId)) {
      setSelectedPermIds(selectedPermIds.filter((id) => id !== permId));
    } else {
      setSelectedPermIds([...selectedPermIds, permId]);
    }
  };

  const grouped = permissions.reduce<Record<string, Permission[]>>(
    (acc, p) => {
      if (!acc[p.resource]) acc[p.resource] = [];
      acc[p.resource].push(p);
      return acc;
    },
    {},
  );

  return (
    <form onSubmit={handleSubmit} className="form">
      <div className="form-group">
        <label htmlFor="name">Role Name</label>
        <input
          id="name"
          type="text"
          className={`form-input ${errors.name ? 'input-error' : ''}`}
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          disabled={saving}
        />
        {errors.name && <span className="field-error">{errors.name}</span>}
      </div>
      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          className="form-input"
          value={form.description}
          onChange={(e) =>
            setForm({ ...form, description: e.target.value })
          }
          disabled={saving}
          rows={3}
        />
      </div>
      <div className="form-group">
        <label>Permissions</label>
        {Object.entries(grouped).map(([resource, perms]) => (
          <div key={resource} className="perm-group">
            <h4 className="perm-resource">{resource}</h4>
            <div className="checkbox-group">
              {perms.map((perm) => (
                <label key={perm.id} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedPermIds.includes(perm.id)}
                    onChange={() => togglePerm(perm.id)}
                    disabled={saving}
                  />
                  {perm.action}
                  {perm.description && (
                    <span className="text-muted"> — {perm.description}</span>
                  )}
                </label>
              ))}
            </div>
          </div>
        ))}
        {permissions.length === 0 && (
          <p className="text-muted">No permissions available</p>
        )}
      </div>
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving...' : 'Save Role'}
        </button>
        <button
          type="button"
          className="btn btn-outline"
          onClick={onCancel}
          disabled={saving}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
