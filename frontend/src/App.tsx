import { useState } from 'react'
import AccountTable from './components/AccountTable'
import Chat from './components/Chat'

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <main>
      <h1>Account Manager</h1>
      <AccountTable refreshKey={refreshKey} />
      <Chat onDone={() => setRefreshKey((key) => key + 1)} />
    </main>
  )
}
