import { apiRequest, API_BASE_URL } from "@/lib/api";
import { getActiveBranch, getStoredToken } from "@/lib/auth";

export interface MenuCsvFilter {
  menuId?: string;
  cuisineId?: string;
  foodType?: string;
  categoryId?: string;
}

export async function exportMenuItemsCsv(filter?: string | MenuCsvFilter): Promise<void> {
  const token = getStoredToken();
  const branch = getActiveBranch();
  const params = new URLSearchParams();
  if (typeof filter === "string" && filter) {
    params.set("menu_id", filter);
  } else if (filter && typeof filter === "object") {
    if (filter.menuId) params.set("menu_id", filter.menuId);
    if (filter.cuisineId) params.set("cuisine_id", filter.cuisineId);
    if (filter.foodType) params.set("food_type", filter.foodType);
    if (filter.categoryId) params.set("category_id", filter.categoryId);
  }
  const qs = params.toString();
  const url = `${API_BASE_URL}/menus/items/export/csv${qs ? `?${qs}` : ""}`;

  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token || ""}`,
      "X-Branch-Id": branch || "",
    },
  });
  if (!res.ok) {
    throw new Error("CSV export failed");
  }
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `menu_items_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export async function saveMenuItemRecord(
  payload: Record<string, any>,
  editingId: string | null
) {
  if (editingId) {
    return apiRequest(`/menus/items/${editingId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }
  return apiRequest("/menus/items", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteMenuItemRecord(itemId: string) {
  return apiRequest(`/menus/items/${itemId}`, { method: "DELETE" });
}

export async function toggleItemAvailabilityRecord(itemId: string) {
  return apiRequest(`/menus/items/${itemId}/toggle-availability`, {
    method: "PATCH",
  });
}

export async function toggleItemCustomerSiteRecord(itemId: string) {
  return apiRequest(`/menus/items/${itemId}/toggle-customer-site`, {
    method: "PATCH",
  });
}

export async function uploadMenuImage(file: File): Promise<string> {
  const token = getStoredToken();
  const branch = getActiveBranch();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/menus/upload-image`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token || ""}`,
      ...(branch ? { "X-Branch-Id": branch } : {}),
    },
    body: formData,
  });

  if (!res.ok) {
    let msg = "Image upload failed";
    try {
      const err = await res.json();
      msg = err.detail || msg;
    } catch {
      // ignore json parse failure
    }
    throw new Error(msg);
  }
  const data = await res.json();
  return data.image_url;
}
