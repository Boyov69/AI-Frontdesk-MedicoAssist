import { CheckCircle, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const plans = [
  {
    name: 'Base',
    price: '49',
    period: '/mese',
    description: 'Per studi medici piccoli',
    features: [
      'Assistente AI telefonica',
      'Fino a 100 chiamate/mese',
      'Dashboard base',
      'Conferme email automatiche',
      'Supporto via email',
    ],
    cta: 'Inizia Gratis',
    popular: false,
  },
  {
    name: 'Professionale',
    price: '99',
    period: '/mese',
    description: 'Per studi medici in crescita',
    features: [
      'Chiamate illimitate',
      'Gestione appuntamenti completa',
      'Integrazione agenda',
      'Report e statistiche avanzate',
      'Promemoria SMS + Email',
      'Supporto prioritario',
      'Gestione NRE e ticket',
    ],
    cta: 'Prova 14 Giorni Gratis',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: 'Su misura',
    period: '',
    description: 'Per poliambulatori e gruppi',
    features: [
      'Multi-studio',
      'API personalizzate',
      'White-label',
      'Supporto dedicato 24/7',
      'SLA garantito 99.9%',
      'Integrazioni personalizzate',
      'Formazione inclusa',
    ],
    cta: 'Contattaci',
    popular: false,
  },
];

export default function Pricing() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <section className="pt-28 pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Piani e Prezzi
            </h1>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              Scegli il piano più adatto al tuo studio. Tutti i piani includono 14 giorni di prova gratuita.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className={`relative rounded-2xl p-8 card-hover ${
                  plan.popular
                    ? 'bg-primary-600 text-white shadow-2xl shadow-primary-600/25 scale-105'
                    : 'bg-white border border-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-accent-500 text-white text-xs font-bold px-4 py-1 rounded-full">
                    PIÙ POPOLARE
                  </div>
                )}

                <div className="mb-6">
                  <h3 className={`text-xl font-bold ${plan.popular ? 'text-white' : 'text-gray-900'}`}>
                    {plan.name}
                  </h3>
                  <p className={`text-sm mt-1 ${plan.popular ? 'text-primary-100' : 'text-gray-500'}`}>
                    {plan.description}
                  </p>
                </div>

                <div className="mb-6">
                  <span className={`text-4xl font-extrabold ${plan.popular ? 'text-white' : 'text-gray-900'}`}>
                    {plan.price === 'Su misura' ? '' : '€'}{plan.price}
                  </span>
                  <span className={`text-sm ${plan.popular ? 'text-primary-200' : 'text-gray-400'}`}>
                    {plan.period}
                  </span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckCircle className={`w-5 h-5 shrink-0 mt-0.5 ${
                        plan.popular ? 'text-primary-200' : 'text-primary-600'
                      }`} />
                      <span className={`text-sm ${plan.popular ? 'text-primary-50' : 'text-gray-600'}`}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-3 px-6 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
                    plan.popular
                      ? 'bg-white text-primary-700 hover:bg-primary-50'
                      : 'bg-primary-600 text-white hover:bg-primary-700'
                  }`}
                >
                  {plan.cta}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
