CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS users;

-- Auth schema
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked BOOLEAN DEFAULT FALSE
);

-- Users schema
CREATE TABLE IF NOT EXISTS users.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users.user_roles (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES users.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS users.role_permissions (
    role_id UUID NOT NULL REFERENCES users.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES users.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Seed roles
INSERT INTO users.roles (name, description, is_system) VALUES
    ('admin', 'Full system access', TRUE),
    ('manager', 'Management level access', TRUE),
    ('user', 'Standard user access', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Seed permissions
INSERT INTO users.permissions (name, resource, action, description) VALUES
    ('users:read', 'users', 'read', 'View users'),
    ('users:create', 'users', 'create', 'Create users'),
    ('users:update', 'users', 'update', 'Update users'),
    ('users:delete', 'users', 'delete', 'Delete users'),
    ('roles:read', 'roles', 'read', 'View roles'),
    ('roles:create', 'roles', 'create', 'Create roles'),
    ('roles:update', 'roles', 'update', 'Update roles'),
    ('roles:delete', 'roles', 'delete', 'Delete roles'),
    ('audit:read', 'audit', 'read', 'View audit logs'),
    ('ai:query', 'ai', 'query', 'Query AI agent')
ON CONFLICT (name) DO NOTHING;

-- Assign all permissions to admin role
INSERT INTO users.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM users.roles r, users.permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Assign read permissions to user role
INSERT INTO users.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM users.roles r, users.permissions p
WHERE r.name = 'user' AND p.action = 'read'
ON CONFLICT DO NOTHING;

-- Assign users:read, users:create, users:update, audit:read, ai:query to manager
INSERT INTO users.role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM users.roles r, users.permissions p
WHERE r.name = 'manager'
  AND p.name IN ('users:read', 'users:create', 'users:update', 'audit:read', 'ai:query')
ON CONFLICT DO NOTHING;
