import { useEffect, useState } from 'react'
import { getAccounts, setAccountState, type Account } from '../api'

interface Props {
  refreshKey: number
}

export default function AccountTable({ refreshKey }: Props) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getAccounts()
      .then((data) => {
        setAccounts(data)
        setError(null)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [refreshKey])

  async function toggle(account: Account) {
    try {
      const updated = await setAccountState(account.id, !account.active)
      setAccounts((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <section>
      <h2>Accounts</h2>
      {error && <p className="error">{error}</p>}
      {loading && <p>Loading...</p>}
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((account) => (
            <tr key={account.id}>
              <td>{account.id}</td>
              <td>{account.name}</td>
              <td>
                <input
                  type="checkbox"
                  checked={account.active}
                  onChange={() => toggle(account)}
                  aria-label={`Toggle ${account.name}`}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
