import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { Copy, Trash2, Eye, Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'

interface Secret {
  id: string
  max_views: number
  current_views: number
  expires_at: string
  has_attachment: boolean
  created_at: string
}

export default function Dashboard() {
  const [secrets, setSecrets] = useState<Secret[]>([])
  const [usage, setUsage] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [secretsRes, usageRes] = await Promise.all([
        api.get('/secrets'),
        api.get('/subscriptions/usage'),
      ])
      setSecrets(secretsRes.data)
      setUsage(usageRes.data)
    } catch (error) {
      toast.error('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const copyLink = (id: string) => {
    const url = `${window.location.origin}/s/${id}`
    navigator.clipboard.writeText(url)
    toast.success('Link copied to clipboard')
  }

  const deleteSecret = async (id: string) => {
    if (!confirm('Delete this secret?')) return

    try {
      await api.delete(`/secrets/${id}`)
      toast.success('Secret deleted')
      fetchData()
    } catch (error) {
      toast.error('Failed to delete secret')
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  const usagePercent = usage
    ? (usage.secrets_created_this_month / usage.limit_secrets) * 100
    : 0

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage your secrets and view access logs
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <Link
            to="/create"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Secret
          </Link>
        </div>
      </div>

      {usage && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900">Usage this month</h2>
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>
                Secrets: {usage.secrets_created_this_month} / {usage.limit_secrets}
              </span>
              <span>{Math.round(usagePercent)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full"
                style={{ width: `${Math.min(usagePercent, 100)}%` }}
              />
            </div>
          </div>
        </div>
      )}

      <div className="mt-8">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Secret ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Views
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expires
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {secrets.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    No secrets yet. Create your first one!
                  </td>
                </tr>
              ) : (
                secrets.map((secret) => (
                  <tr key={secret.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {secret.id.substring(0, 12)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {secret.current_views} / {secret.max_views}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(secret.expires_at), 'MMM d, yyyy HH:mm')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(secret.created_at), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        onClick={() => copyLink(secret.id)}
                        className="text-primary-600 hover:text-primary-900"
                        title="Copy link"
                      >
                        <Copy className="w-4 h-4 inline" />
                      </button>
                      <Link
                        to={`/s/${secret.id}/logs`}
                        className="text-gray-600 hover:text-gray-900"
                        title="View logs"
                      >
                        <Eye className="w-4 h-4 inline" />
                      </Link>
                      <button
                        onClick={() => deleteSecret(secret.id)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4 inline" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
