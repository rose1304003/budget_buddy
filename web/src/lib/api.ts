import { getInitData } from "./telegram";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export type Me = {
  tg_user_id: number;
  first_name: string;
  last_name: string;
  username: string;
  language_code: string;
};

export type Category = {
  id: number;
  name: string;
  kind: "expense" | "income" | "debt";
  color: string;
  icon: string;
  is_active: boolean;
};

export type Tx = {
  id: number;
  type: "expense" | "income";
  amount: number;
  note: string;
  occurred_at?: string;
  category_id?: number | null;
};

export type Stats = {
  balance: number;
  week_spent: number;
  week_income: number;
  month_spent: number;
  month_income: number;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Make an API request with proper error handling.
 * @param path - API endpoint path
 * @param init - Fetch request options
 * @returns Promise resolving to the response data
 * @throws ApiError if the request fails
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers || {});
  headers.set("Content-Type", "application/json");
  headers.set("X-TG-Init-Data", getInitData());

  try {
    const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

    if (!res.ok) {
      let errorMessage = `Request failed with status ${res.status}`;
      let errorDetail: string | undefined;

      try {
        const errorText = await res.text();
        if (errorText) {
          try {
            const errorJson = JSON.parse(errorText);
            errorDetail = errorJson.detail || errorJson.message || errorText;
            errorMessage = errorDetail;
          } catch {
            errorDetail = errorText;
            errorMessage = errorText;
          }
        }
      } catch {
        // If we can't read the error, use the status code
        errorMessage = `Request failed with status ${res.status}`;
      }

      throw new ApiError(errorMessage, res.status, errorDetail);
    }

    // Handle 204 No Content responses
    if (res.status === 204) {
      return undefined as T;
    }

    return (await res.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network or other errors
    throw new ApiError(
      error instanceof Error ? error.message : "Network error",
      0
    );
  }
}

export const api = {
  /** Get current authenticated user information */
  me: () => request<Me>("/api/me"),

  /** Get user statistics */
  stats: () => request<Stats>("/api/stats"),

  /** List all categories for the current user */
  categories: () => request<Category[]>("/api/categories"),

  /** Create a new category */
  createCategory: (payload: Partial<Category>) =>
    request<Category>("/api/categories", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Update an existing category */
  patchCategory: (id: number, payload: Partial<Category>) =>
    request<Category>(`/api/categories/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  /** List transactions for the current user */
  transactions: (limit = 50) =>
    request<Tx[]>(`/api/transactions?limit=${limit}`),

  /** Create a new transaction */
  createTx: (payload: Partial<Tx>) =>
    request<Tx>("/api/transactions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Delete a transaction */
  deleteTx: (id: number) =>
    request<void>(`/api/transactions/${id}`, { method: "DELETE" }),
};
