import { useState, useEffect } from 'react'
import { Check } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../lib/api'

const plans = [
  {
    name: 'Free',
    price: '$0',
    description: 'Perfect for trying out SecShare',
    features: [
      '10 secrets per month',
      'No attachments',
      '1 user',
      '24/7 support',
    ],
    priceId: null,
  },
  {
    name: 'Pro',
    price: '$19',
    description: 'For professionals who need more',
    features: [
      '100 secrets per month',
      'Attachments up to 10MB',
      'Secure chat',
      '1 user',
      'Priority support',
    ],
    priceId: 'pro',
  },
  {
    name: 'Team',
    price: '$49',
    description: 'For teams collaborating securely',
    features: [
      '500 secrets per month',
      'Attachments up to 50MB',
      'Secure chat',
      '5 users',
      'Team management',
      'Priority support',
    ],
    priceId: 'team',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'For large organizations',
    features: [
      'Unlimited secrets',
      'Custom attachment limits',
      'Secure chat',
      'Unlimited users',
      'SSO integration',
      'Dedicated support',
      'Custom contracts',
    ],
    priceId: null,
  },
]

export default function Billing() {
  const [subscription, setSubscription] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSubscription()
  }, [])

  const fetchSubscription = async () => {
    try {
      const { data } = await api.get('/subscriptions/me')
      setSubscription(data)
    } catch (error) {
      toast.error('Failed to fetch subscription')
    } finally {
      setLoading(false)
    }
  }

  const handleUpgrade = async (priceId: string) => {
    try {
      const { data } = await api.post('/subscriptions/checkout', {
        price_id: priceId,
        success_url: `${window.location.origin}/billing?success=true`,
        cancel_url: `${window.location.origin}/billing`,
      })
      window.location.href = data.checkout_url
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create checkout session')
    }
  }

  const handleManageBilling = async () => {
    try {
      const { data } = await api.post('/subscriptions/portal')
      window.location.href = data.portal_url
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to open billing portal')
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Choose Your Plan</h1>
        <p className="text-gray-600">
          Current plan: <span className="font-semibold">{subscription?.plan}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`bg-white rounded-lg shadow-md overflow-hidden ${
              subscription?.plan === plan.name.toUpperCase()
                ? 'ring-2 ring-primary-600'
                : ''
            }`}
          >
            <div className="p-6">
              <h3 className="text-xl font-semibold text-gray-900">{plan.name}</h3>
              <p className="mt-2 text-sm text-gray-600">{plan.description}</p>
              <p className="mt-4">
                <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                {plan.price !== 'Custom' && (
                  <span className="text-base font-medium text-gray-500">/month</span>
                )}
              </p>

              <ul className="mt-6 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start">
                    <Check className="w-5 h-5 text-primary-600 mr-2 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-8">
                {subscription?.plan === plan.name.toUpperCase() ? (
                  <button
                    onClick={handleManageBilling}
                    className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200"
                  >
                    Manage Billing
                  </button>
                ) : plan.priceId ? (
                  <button
                    onClick={() => handleUpgrade(plan.priceId!)}
                    className="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
                  >
                    Upgrade to {plan.name}
                  </button>
                ) : plan.name === 'Enterprise' ? (
                  <a
                    href="mailto:sales@secshare.com"
                    className="block w-full text-center bg-gray-900 text-white px-4 py-2 rounded-md hover:bg-gray-800"
                  >
                    Contact Sales
                  </a>
                ) : (
                  <button disabled className="w-full bg-gray-100 text-gray-400 px-4 py-2 rounded-md cursor-not-allowed">
                    Current Plan
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
