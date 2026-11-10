import { useState, type FormEvent } from 'react'
import { sendChat, type ChatResponse } from '../api'

interface Props {
  onDone: () => void
}

export default function Chat({ onDone }: Props) {
  const [prompt, setPrompt] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<ChatResponse | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!prompt.trim() || pending) return
    setPending(true)
    setError(null)
    try {
      setResponse(await sendChat(prompt))
      onDone()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setPending(false)
    }
  }

  return (
    <section>
      <h2>Ask the agent</h2>
      <form onSubmit={submit}>
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Cancel user 101 and tell me the capital of France."
          rows={3}
        />
        <button type="submit" disabled={pending || !prompt.trim()}>
          {pending ? 'Working...' : 'Send'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {response && (
        <div className="response">
          <p className="answer">{response.answer}</p>
          <ol className="subtasks">
            {response.subtasks.map((subtask) => (
              <li key={subtask.id}>
                <span className={`badge ${subtask.status}`}>{subtask.status}</span>
                <strong>{subtask.agent}</strong>: {subtask.prompt}
                {subtask.result && <pre>{subtask.result}</pre>}
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  )
}
