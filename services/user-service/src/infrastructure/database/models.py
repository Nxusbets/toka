from uuid import uuid4

from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database import Base


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user_roles = relationship("UserRoleModel", back_populates="user", cascade="all, delete-orphan", primaryjoin="UserModel.id == UserRoleModel.user_id")


class RoleModel(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "users"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user_roles = relationship("UserRoleModel", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermissionModel", back_populates="role", cascade="all, delete-orphan")


class PermissionModel(Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "users"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    role_permissions = relationship("RolePermissionModel", back_populates="permission", cascade="all, delete-orphan")


class UserRoleModel(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "users"}

    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("users.roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)

    user = relationship("UserModel", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("RoleModel", back_populates="user_roles")


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "users"}

    role_id = Column(UUID(as_uuid=True), ForeignKey("users.roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("users.permissions.id", ondelete="CASCADE"), primary_key=True)

    role = relationship("RoleModel", back_populates="role_permissions")
    permission = relationship("PermissionModel", back_populates="role_permissions")
