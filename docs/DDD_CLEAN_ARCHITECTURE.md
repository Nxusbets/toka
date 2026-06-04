# Domain-Driven Design (DDD) y Clean Architecture

## Aplicación de DDD

### Ubiquitous Language (Lenguaje Ubicuo)

El dominio es la **gestión de usuarios** con autenticación, autorización y auditoría. El lenguaje ubicuo se refleja en:

| Término | Significado | Ubicación en Código |
|---|---|---|
| **User** | Persona que accede al sistema | `User` entity en auth-service y user-service |
| **Role** | Conjunto de permisos asignables | `Role` entity en user-service |
| **Permission** | Acción permitida sobre un recurso | `Permission` entity en user-service |
| **AuditLog** | Registro de evento de auditoría | `AuditLog` entity en audit-service |
| **RefreshToken** | Token para renovar sesión | `RefreshToken` entity en auth-service |
| **Query** | Consulta al agente de IA | `Query` entity en ai-agent-service |

### Bounded Contexts (Contextos Delimitados)

Cada microservicio corresponde a un Bounded Context:

```
┌─────────────────────────────────────────────────┐
│                 Sistema Toka                      │
├─────────────┬──────────┬──────────┬──────────────┤
│ Auth Context │User Ctx  │Audit Ctx │  AI Ctx      │
│              │          │          │              │
│ Autenticación│ Gestión  │ Auditoría│ Agentes IA   │
│ JWT/OAuth2   │ usuarios │ eventos  │ RAG          │
│              │ roles    │          │              │
└──────────────┴──────────┴──────────┴──────────────┘
```

### Aggregates

1. **User Aggregate** (Auth Context)
   - Root: `User`
   - Contiene: `RefreshToken[]`
   - Invariante: Email único, username único

2. **User Aggregate** (User Context)
   - Root: `User`
   - Contiene: `Role[]` (via UserRole)
   - Invariante: Usuario activo debe tener al menos un rol

3. **Role Aggregate** (User Context)
   - Root: `Role`
   - Contiene: `Permission[]` (via RolePermission)

### Domain Events

Los eventos de dominio representan hechos ocurridos en el sistema:

- `UserRegistered(user_id, email, timestamp)` → publicado por Auth Service
- `UserLoggedIn(user_id, email, ip_address, timestamp)` → publicado por Auth Service
- `UserLoggedOut(user_id, timestamp)` → publicado por Auth Service
- `UserUpdated(user_id, changes, timestamp)` → publicado por User Service
- `RoleAssigned(user_id, role_id, assigned_by, timestamp)` → publicado por User Service
- `AiQueryCompleted(user_id, query, tokens_used, timestamp)` → publicado por AI Agent Service

## Aplicación de Clean Architecture

### Capas por Microservicio

Cada microservicio sigue la misma estructura de 4 capas:

```
┌─────────────────────────────────────────────────────┐
│                     API Layer                        │
│  (FastAPI routes, middlewares, DI, DTOs de entrada)  │
├─────────────────────────────────────────────────────┤
│                  Application Layer                   │
│  (Use Cases, DTOs de salida, Ports)                  │
├─────────────────────────────────────────────────────┤
│                   Domain Layer                       │
│  (Entities, Value Objects, Repository interfaces,    │
│   Domain Events)                                     │
├─────────────────────────────────────────────────────┤
│                Infrastructure Layer                  │
│  (Database repos, Message Queue, Cache, External     │
│   APIs)                                              │
└─────────────────────────────────────────────────────┘
```

### Regla de Dependencia

> Las dependencias apuntan hacia adentro. El Domain Layer no depende de nada externo.

```
Infrastructure → Domain
Application → Domain
API → Application → Domain
API → Infrastructure (solo para DI)
```

### Ejemplo: Flujo de "Registrar Usuario"

**1. API Layer** (`api/routes/auth_routes.py`):
```python
@router.post("/register")
async def register(request: RegisterRequest, use_case: RegisterUserUseCase = Depends()):
    return await use_case.execute(request)
```

**2. Application Layer** (`application/use_cases/auth_use_cases.py`):
```python
class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.publisher = event_publisher

    async def execute(self, dto: RegisterRequest) -> TokenResponse:
        user = User(email=dto.email, username=dto.username)
        user.password_hash = hash_password(dto.password)
        await self.user_repo.save(user)
        await self.publisher.publish(UserRegistered(user_id=user.id, email=user.email))
        return TokenResponse(access_token=create_jwt(user), refresh_token=create_refresh(user))
```

**3. Domain Layer** (`domain/entities/user.py`):
```python
@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    username: str = ""
    password_hash: str = ""
    is_active: bool = True
    is_verified: bool = False
```

**4. Infrastructure Layer** (`infrastructure/database/repositories.py`):
```python
class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        model = UserModel(id=user.id, email=user.email, ...)
        self.session.add(model)
        await self.session.commit()
        return user
```

### Value Objects

- `Email`: valida formato de email
- `PasswordHash`: encapsula bcrypt hashing
- `UserId`: UUID tipado
- `Token`: JWT con claims

### Repositories (Interfaces en Domain, Implementaciones en Infrastructure)

**Domain** (contrato):
```python
class UserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> User | None: ...
    @abstractmethod
    async def save(self, user: User) -> User: ...
```

**Infrastructure** (implementación):
```python
class SQLAlchemyUserRepository(UserRepository):
    async def find_by_email(self, email: str) -> User | None:
        # SQLAlchemy query → mapping to domain User
```

## Beneficios de este Enfoque

1. **Testabilidad**: Domain y Application no dependen de infraestructura → tests unitarios sin DB
2. **Independencia tecnológica**: Cambiar de PostgreSQL a MySQL solo requiere nueva implementación de repositorio
3. **Aislamiento**: Cada Bounded Context (microservicio) es independiente y puede evolucionar separadamente
4. **Mantenibilidad**: Código organizado por propósito de negocio, no por framework
5. **Escalabilidad**: Cada microservicio escala independientemente según demanda
