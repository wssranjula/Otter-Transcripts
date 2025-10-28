// Auth types
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// Prompt types
export interface PromptSections {
  [key: string]: string
}

export interface PromptSectionsResponse {
  sections: PromptSections
}

export interface PromptSectionUpdate {
  section: string
  content: string
}

// Whitelist types
export interface PhoneNumber {
  phone_number: string
  name?: string
  added_at: string
}

export interface WhitelistResponse {
  enabled: boolean
  authorized_numbers: PhoneNumber[]
  blocked_numbers: PhoneNumber[]
  unauthorized_message: string
}

export interface PhoneNumberRequest {
  phone_number: string
  name?: string
}

// Stats types
export interface StatsResponse {
  total_authorized_users: number
  total_blocked_users: number
  total_conversations: number
  recent_activity: Array<{
    timestamp: string
    action: string
    details: string
  }>
}

// UI types
export interface NavItem {
  title: string
  href: string
  icon?: string
}

export interface PromptSection {
  id: string
  title: string
  description: string
  content: string
}
