from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, List
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_db, current_tenant_id_ctx, is_super_admin_ctx
from app.core.security import decode_token
from app.core.permissions import Permission, RoleEnum, ROLE_PERMISSIONS
from app.models.saas import Tenant, PlatformUser
from app.models.organization import User, Branch

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def get_current_token_payload(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def get_current_user_or_admin(
    payload: dict = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
):
    user_id = payload.get("sub")
    is_super = payload.get("is_super_admin", False)
    
    if is_super:
        admin = db.query(PlatformUser).filter(PlatformUser.id == user_id, PlatformUser.is_active == True).first()
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Platform admin not found or inactive")
        is_super_admin_ctx.set(True)
        return admin

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or disabled")
        
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant organization does not exist")
    if tenant.status == "Suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant organization is suspended. Contact SaaS support.")
        
    # Inject active tenant context
    current_tenant_id_ctx.set(user.tenant_id)
    is_super_admin_ctx.set(False)
    
    return user

def get_current_user(
    user = Depends(get_current_user_or_admin)
) -> User:
    if isinstance(user, PlatformUser):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin cannot access tenant-scoped workspace directly without impersonation context")
    return user

def get_current_super_admin(
    admin = Depends(get_current_user_or_admin)
) -> PlatformUser:
    if not isinstance(admin, PlatformUser) or admin.role != "SUPER_ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SaaS Super Admin access required")
    return admin

def require_permission(required_perm: Permission):
    def permission_checker(current_user: User = Depends(get_current_user)):
        user_role = getattr(current_user, "role", None)
        try:
            role_enum = RoleEnum(user_role)
            allowed_permissions = ROLE_PERMISSIONS.get(role_enum, set())
            if required_perm not in allowed_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation not permitted. Required permission: '{required_perm.value}'"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unknown role '{user_role}' assigned to user"
            )
        return current_user
    return permission_checker

def get_active_branch_id(
    x_branch_id: Optional[str] = Header(None, alias="X-Branch-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    # 1. If explicit branch header provided and user has permission to switch
    if x_branch_id:
        branch = db.query(Branch).filter(
            Branch.id == x_branch_id, 
            Branch.tenant_id == current_user.tenant_id,
            Branch.is_active == True
        ).first()
        if branch:
            return branch.id
            
    # 2. If user has assigned primary branch
    if current_user.branch_id:
        return current_user.branch_id
        
    # 3. Default to the tenant's first active branch
    first_branch = db.query(Branch).filter(
        Branch.tenant_id == current_user.tenant_id,
        Branch.is_active == True
    ).first()
    if not first_branch:
        raise HTTPException(status_code=400, detail="No active branch found for tenant")
    return first_branch.id


def get_optional_branch_id(
    x_branch_id: Optional[str] = Header(None, alias="X-Branch-Id"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[str]:
    if x_branch_id:
        branch = db.query(Branch).filter(
            Branch.id == x_branch_id,
            Branch.tenant_id == current_user.tenant_id,
            Branch.is_active == True
        ).first()
        if branch:
            return branch.id
    if current_user.branch_id:
        return current_user.branch_id
    first_branch = db.query(Branch).filter(
        Branch.tenant_id == current_user.tenant_id,
        Branch.is_active == True
    ).first()
    return first_branch.id if first_branch else None
