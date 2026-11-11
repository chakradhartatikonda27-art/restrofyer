export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id?: string;
  tenant_name?: string;
  tenant_slug?: string;
  branch_id?: string;
  branch_name?: string;
  is_super_admin: boolean;
}

export function saveAuthSession(token: string, user: AuthUser) {
  if (typeof window === "undefined") return;
  localStorage.setItem("saas_auth_token", token);
  localStorage.setItem("saas_user_profile", JSON.stringify(user));
  if (user.branch_id) {
    localStorage.setItem("saas_active_branch_id", user.branch_id);
  } else {
    localStorage.removeItem("saas_active_branch_id");
  }
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("saas_user_profile");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("saas_auth_token");
}

export function clearAuthSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("saas_auth_token");
  localStorage.removeItem("saas_user_profile");
  localStorage.removeItem("saas_active_branch_id");
}

export function setActiveBranch(branchId: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem("saas_active_branch_id", branchId);
}

export function getActiveBranch(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("saas_active_branch_id");
}
