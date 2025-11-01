import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Shield, Copy, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'

export default function ViewSecret() {
  const { secretId } = useParams()
  const [secret, setSecret] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [revealed, setRevealed] = useState(false)

  const fetchSecret = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/secrets/${secretId}`)
      setSecret(data)
      setRevealed(true)
    } catch (error: any) {
      setError(
        error.response?.data?.detail ||
          error.response?.status === 404
          ? 'Secret not found'
          : error.response?.status === 410
          ? 'This secret has expired or reached max views'
          : 'Failed to load secret'
      )
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = () => {
    if (secret?.content) {
      navigator.clipboard.writeText(secret.content)
      toast.success('Secret copied to clipboard')
    }
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white shadow rounded-lg p-6">
          <div className="text-center">
            <Shield className="w-12 h-12 text-red-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Unable to Load Secret</h2>
            <p className="text-gray-700">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!revealed && !error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white shadow rounded-lg p-6">
          <div className="text-center">
            <Shield className="w-12 h-12 text-primary-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Secure Secret</h2>
            <p className="text-gray-700 mb-4">
              Click below to reveal this secret. This action cannot be undone.
            </p>
            <button
              onClick={fetchSecret}
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Reveal Secret'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-2xl w-full bg-white shadow rounded-lg p-6">
        <div className="mb-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Secret Content</h2>
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 relative">
            <pre className="whitespace-pre-wrap break-words text-sm font-mono text-gray-900">
              {secret.content}
            </pre>
            <button
              onClick={copyToClipboard}
              className="absolute top-2 right-2 p-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              title="Copy to clipboard"
            >
              <Copy className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>

        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
          <p className="text-sm text-yellow-700">
            <strong>Note:</strong> This secret has been viewed {secret.current_views} of{' '}
            {secret.max_views} times. Make sure to save it now if needed.
          </p>
        </div>

        {secret.has_attachment && (
          <div className="mt-4">
            <a
              href={secret.attachment_url}
              download={secret.attachment_name}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
            >
              Download Attachment ({secret.attachment_name})
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
