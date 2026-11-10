export interface Account {
  id: string
  name: string
  active: boolean
}

export interface Subtask {
  id: number
  agent: string
  prompt: string
  status: 'pending' | 'done' | 'failed'
  result: string | null
}

export interface ChatResponse {
  answer: string
  subtasks: Subtask[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? response.statusText)
  }
  return response.json()
}

function jsonRequest(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

export const getAccounts = () => request<Account[]>('/accounts')

export const setAccountState = (id: string, active: boolean) =>
  request<Account>(`/accounts/${id}`, jsonRequest('PATCH', { active }))

export const sendChat = (prompt: string) =>
  request<ChatResponse>('/chat', jsonRequest('POST', { prompt }))
