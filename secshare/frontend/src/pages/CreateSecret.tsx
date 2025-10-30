import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Copy } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'

export default function CreateSecret() {
  const [content, setContent] = useState('')
  const [maxViews, setMaxViews] = useState(1)
  const [expiresInHours, setExpiresInHours] = useState(24)
  const [loading, setLoading] = useState(false)
  const [createdSecret, setCreatedSecret] = useState<any>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const { data } = await api.post('/secrets', {
        content,
        max_views: maxViews,
        expires_in_hours: expiresInHours,
      })
      setCreatedSecret(data)
      toast.success('Secret created successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create secret')
    } finally {
      setLoading(false)
    }
  }

  const copyLink = () => {
    const url = `${window.location.origin}/s/${createdSecret.id}`
    navigator.clipboard.writeText(url)
    toast.success('Link copied to clipboard')
  }

  if (createdSecret) {
    const url = `${window.location.origin}/s/${createdSecret.id}`

    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Secret Created!</h1>
          <p className="text-gray-700 mb-4">
            Share this link with the recipient. It will expire after {maxViews} view
            {maxViews > 1 ? 's' : ''} or in {expiresInHours} hours.
          </p>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={url}
              readOnly
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 font-mono text-sm"
            />
            <button
              onClick={copyLink}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
          <div className="mt-6 flex space-x-3">
            <button
              onClick={() => {
                setCreatedSecret(null)
                setContent('')
              }}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            >
              Create Another
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Create Secret</h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="content" className="block text-sm font-medium text-gray-700">
              Secret Content
            </label>
            <textarea
              id="content"
              rows={6}
              required
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your secret message, API key, password, etc."
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="maxViews" className="block text-sm font-medium text-gray-700">
                Max Views
              </label>
              <select
                id="maxViews"
                value={maxViews}
                onChange={(e) => setMaxViews(Number(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
              >
                <option value={1}>1 view (one-time)</option>
                <option value={3}>3 views</option>
                <option value={5}>5 views</option>
                <option value={10}>10 views</option>
              </select>
            </div>

            <div>
              <label htmlFor="expiresInHours" className="block text-sm font-medium text-gray-700">
                Expires In
              </label>
              <select
                id="expiresInHours"
                value={expiresInHours}
                onChange={(e) => setExpiresInHours(Number(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm px-3 py-2 border"
              >
                <option value={1}>1 hour</option>
                <option value={6}>6 hours</option>
                <option value={24}>24 hours</option>
                <option value={72}>3 days</option>
                <option value={168}>7 days</option>
              </select>
            </div>
          </div>

          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <p className="text-sm text-yellow-700">
              <strong>Warning:</strong> Once shared, the secret link can be accessed by anyone who
              has it. Make sure to share it securely.
            </p>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Secret'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
