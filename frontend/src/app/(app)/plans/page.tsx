'use client'

import { Check } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/page-header'

interface PlanFeature {
  text: string
  included: boolean
}

interface Plan {
  name: string
  price: string
  priceSuffix?: string
  description: string
  features: PlanFeature[]
  cta: string
  ctaVariant: 'default' | 'outline' | 'secondary'
  ctaDisabled?: boolean
  recommended?: boolean
  current?: boolean
}

const plans: Plan[] = [
  {
    name: 'Free',
    price: '$0',
    priceSuffix: '/mo',
    description: 'Get started with basic cloud testing',
    features: [
      { text: '50 cloud runs / month', included: true },
      { text: '3 test suites', included: true },
      { text: '1 device', included: true },
      { text: 'Community support', included: true },
      { text: 'Team collaboration', included: false },
      { text: 'Priority support', included: false },
    ],
    cta: 'Current Plan',
    ctaVariant: 'secondary',
    ctaDisabled: true,
    current: true,
  },
  {
    name: 'Pro',
    price: '$49',
    priceSuffix: '/mo',
    description: 'For teams shipping quality software fast',
    features: [
      { text: 'Unlimited cloud runs', included: true },
      { text: 'Unlimited test suites', included: true },
      { text: '5 devices', included: true },
      { text: 'Priority support', included: true },
      { text: 'Team collaboration', included: true },
      { text: 'Advanced analytics', included: true },
    ],
    cta: 'Upgrade to Pro',
    ctaVariant: 'default',
    recommended: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'Everything in Pro, tailored to your org',
    features: [
      { text: 'Everything in Pro', included: true },
      { text: 'Custom integrations', included: true },
      { text: 'SLA guarantee', included: true },
      { text: 'Dedicated support', included: true },
      { text: 'SSO / SAML', included: true },
      { text: 'On-premise option', included: true },
    ],
    cta: 'Contact Sales',
    ctaVariant: 'outline',
  },
]

export default function PlansPage() {
  const router = useRouter()

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-5xl mx-auto p-8">
        <PageHeader
          title="Plans"
          description="Choose the plan that fits your testing needs"
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`glass-card relative flex flex-col rounded-2xl p-6 transition-all duration-300 ${
                plan.recommended
                  ? 'border border-primary/40 shadow-[0_0_40px_-12px_rgba(91,196,214,0.15)]'
                  : 'border border-white/5'
              }`}
            >
              {/* Recommended badge */}
              {plan.recommended && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge variant="blue">Recommended</Badge>
                </div>
              )}

              {/* Plan header */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <h2 className="text-lg font-headline font-bold text-white">
                    {plan.name}
                  </h2>
                  {plan.current && (
                    <Badge variant="outline">Current</Badge>
                  )}
                </div>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className={`text-3xl font-headline font-bold ${plan.recommended ? 'text-primary' : 'text-white'}`}>
                    {plan.price}
                  </span>
                  {plan.priceSuffix && (
                    <span className="text-sm text-zinc-500 font-label uppercase tracking-widest">
                      {plan.priceSuffix}
                    </span>
                  )}
                </div>
                <p className="text-xs text-zinc-400">{plan.description}</p>
              </div>

              {/* Divider */}
              <div className="border-t border-white/5 mb-6" />

              {/* Features */}
              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature.text} className="flex items-start gap-2.5">
                    <Check
                      className={`h-4 w-4 mt-0.5 shrink-0 ${
                        feature.included ? 'text-primary' : 'text-zinc-700'
                      }`}
                    />
                    <span
                      className={`text-sm ${
                        feature.included ? 'text-zinc-300' : 'text-zinc-600 line-through'
                      }`}
                    >
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Button
                variant={plan.ctaVariant}
                size="lg"
                disabled={plan.ctaDisabled}
                className={`w-full ${
                  plan.recommended
                    ? 'shadow-glow-cyan'
                    : ''
                }`}
                onClick={() => {
                  if (plan.name === 'Enterprise') {
                    window.open('mailto:sales@testara.ai', '_blank')
                  }
                }}
              >
                {plan.cta}
              </Button>
            </div>
          ))}
        </div>

        {/* FAQ / Bottom note */}
        <div className="mt-12 text-center">
          <p className="text-[10px] font-label uppercase tracking-widest text-zinc-600">
            All plans include local testing at no cost. Cloud runs are counted per execution.
          </p>
        </div>

        <div className="h-12 md:hidden" />
      </div>
    </div>
  )
}
