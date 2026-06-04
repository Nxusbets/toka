import { useState } from 'react';
import type { User, Role } from '../../types';

interface UserFormProps {
  initialData: Partial<User>;
  roles: Role[];
  selectedRoleIds: string[];
  onRoleChange: (ids: string[]) => void;
  onSave: (data: Partial<User>) => Promise<void>;
  onCancel: () => void;
  saving: boolean;
  isNew: boolean;
}

export default function UserForm({
  initialData,
  roles,
  selectedRoleIds,
  onRoleChange,
  onSave,
  onCancel,
  saving,
  isNew,
}: UserFormProps) {
  const [form, setForm] = useState({
    email: initialData.email || '',
    username: initialData.username || '',
    is_active: initialData.is_active ?? true,
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.email.trim()) {
      errs.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(form.email)) {
      errs.email = 'Invalid email format';
    }
    if (!form.username.trim()) {
      errs.username = 'Username is required';
    }
    if (isNew && !form.password) {
      errs.password = 'Password is required';
    }
    if (isNew && form.password && form.password.length < 8) {
      errs.password = 'Password must be at least 8 characters';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    const data: Partial<User> & { password?: string } = {
      email: form.email,
      username: form.username,
      is_active: form.is_active,
    };
    if (isNew && form.password) data.password = form.password;
    await onSave(data as Partial<User>);
  };

  const toggleRole = (roleId: string) => {
    if (selectedRoleIds.includes(roleId)) {
      onRoleChange(selectedRoleIds.filter((id) => id !== roleId));
    } else {
      onRoleChange([...selectedRoleIds, roleId]);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="form">
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          className={`form-input ${errors.email ? 'input-error' : ''}`}
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          disabled={saving}
        />
        {errors.email && <span className="field-error">{errors.email}</span>}
      </div>
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          className={`form-input ${errors.username ? 'input-error' : ''}`}
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          disabled={saving}
        />
        {errors.username && (
          <span className="field-error">{errors.username}</span>
        )}
      </div>
      {isNew && (
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className={`form-input ${errors.password ? 'input-error' : ''}`}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            disabled={saving}
          />
          {errors.password && (
            <span className="field-error">{errors.password}</span>
          )}
        </div>
      )}
      <div className="form-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) =>
              setForm({ ...form, is_active: e.target.checked })
            }
            disabled={saving}
          />
          Active
        </label>
      </div>
      <div className="form-group">
        <label>Roles</label>
        <div className="checkbox-group">
          {roles.map((role) => (
            <label key={role.id} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedRoleIds.includes(role.id)}
                onChange={() => toggleRole(role.id)}
                disabled={saving}
              />
              {role.name}
            </label>
          ))}
          {roles.length === 0 && (
            <p className="text-muted">No roles available</p>
          )}
        </div>
      </div>
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving
            ? 'Saving...'
            : isNew
              ? 'Create User'
              : 'Save Changes'}
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
