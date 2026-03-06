import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { ContentItem, ContentStats } from '../api/types'

export default function Dashboard() {
  const [query, setQuery] = useState('')
  const [stats, setStats] = useState<ContentStats | null>(null)
  const [recentContent, setRecentContent] = useState<ContentItem[]>([])
  const [searchResults, setSearchResults] = useState<ContentItem[] | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.getContentStats().then(setStats).catch(console.error)
    api.listContent({ limit: 6 }).then((r) => setRecentContent(r.items)).catch(console.error)
  }, [])

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) { setSearchResults(null); return }
    setLoading(true)
    try {
      const res = await api.searchContent(query)
      setSearchResults(res.items)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const displayItems = searchResults ?? recentContent

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="pt-4">
        <h1 className="text-2xl font-semibold mb-2">Content Intelligence Hub</h1>
        <p className="text-muted-foreground text-sm">Search, explore, and repurpose your marketing content.</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Search content... (e.g., 'cloud migration for CTOs')"
          className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20" />
        <button type="submit" disabled={loading}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {stats && stats.total > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Total Content" value={stats.total} />
          <StatCard label="Avg Performance" value={`${stats.avg_performance}%`} />
          <StatCard label="Content Types" value={Object.keys(stats.by_content_type).length} />
          <StatCard label="Personas" value={Object.keys(stats.by_persona).length} />
        </div>
      )}

      <div>
        <h2 className="text-lg font-medium mb-3">
          {searchResults ? `Search Results (${searchResults.length})` : 'Recent Content'}
        </h2>
        {displayItems.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            {searchResults ? 'No results found.' : 'No content yet. Add watched folders in Settings to get started.'}
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayItems.map((item) => (
              <ContentCard key={item.id} item={item} onClick={() => navigate(`/content/${item.id}`)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold mt-1">{value}</p>
    </div>
  )
}

function ContentCard({ item, onClick }: { item: ContentItem; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className="text-left rounded-lg border border-border p-4 hover:bg-accent/50 transition-colors">
      <div className="flex gap-2 mb-2">
        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground">{item.content_type}</span>
        {item.performance_score > 0 && (
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground">{item.performance_score}%</span>
        )}
      </div>
      <h3 className="font-medium text-sm line-clamp-2">{item.title}</h3>
      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{item.summary}</p>
    </button>
  )
}
