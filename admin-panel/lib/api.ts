/**
 * API Client for Sybil Admin Panel
 * Communicates with FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ========================================
// Types
// ========================================

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  response: string;
  timestamp: string;
}

export interface WhitelistEntry {
  id: number;
  phone_number: string;
  name?: string;
  notes?: string;
  added_by?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WhitelistCreateRequest {
  phone_number: string;
  name?: string;
  notes?: string;
  added_by?: string;
}

export interface WhitelistUpdateRequest {
  phone_number?: string;
  name?: string;
  notes?: string;
  is_active?: boolean;
}

export interface WhitelistStats {
  total: number;
  active: number;
  inactive: number;
}

// ========================================
// Chat API
// ========================================

export async function sendChatMessage(message: string, history?: ChatMessage[]): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ 
      message,
      history: history || []
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function checkChatHealth() {
  const response = await fetch(`${API_BASE_URL}/admin/chat/health`);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

// ========================================
// Whitelist API
// ========================================

export async function getWhitelist(includeInactive: boolean = false): Promise<WhitelistEntry[]> {
  const url = new URL(`${API_BASE_URL}/admin/whitelist`);
  url.searchParams.set('include_inactive', includeInactive.toString());

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json();
  return data.entries || [];
}

export async function addToWhitelist(entry: WhitelistCreateRequest): Promise<WhitelistEntry> {
  const response = await fetch(`${API_BASE_URL}/admin/whitelist`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(entry),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function updateWhitelist(
  id: number,
  update: WhitelistUpdateRequest
): Promise<WhitelistEntry> {
  const response = await fetch(`${API_BASE_URL}/admin/whitelist/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function toggleWhitelistStatus(id: number): Promise<WhitelistEntry> {
  const response = await fetch(`${API_BASE_URL}/admin/whitelist/${id}/toggle`, {
    method: 'PATCH',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function deleteFromWhitelist(id: number, hardDelete: boolean = false): Promise<void> {
  const url = new URL(`${API_BASE_URL}/admin/whitelist/${id}`);
  url.searchParams.set('hard_delete', hardDelete.toString());

  const response = await fetch(url.toString(), {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
}

export async function checkPhoneNumber(phoneNumber: string): Promise<boolean> {
  const encoded = encodeURIComponent(phoneNumber);
  const response = await fetch(`${API_BASE_URL}/admin/whitelist/check/${encoded}`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json();
  return data.is_whitelisted;
}

export async function getWhitelistStats(): Promise<WhitelistStats> {
  const response = await fetch(`${API_BASE_URL}/admin/whitelist/stats`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

// ========================================
// Prompt Configuration API
// ========================================

export interface PromptConfig {
  tone: string;
  use_smart_brevity: boolean;
  people_references: string;
  use_formatting: boolean;
  use_emojis: boolean;
  default_response_length: string;
  ask_about_depth: boolean;
  tone_adapts_by_user: boolean;
  custom_instructions: string;
}

export async function getPromptConfig(): Promise<PromptConfig> {
  const response = await fetch(`${API_BASE_URL}/admin/sybil/prompt-config`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function updatePromptConfig(config: PromptConfig): Promise<PromptConfig> {
  const response = await fetch(`${API_BASE_URL}/admin/sybil/prompt-config`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

