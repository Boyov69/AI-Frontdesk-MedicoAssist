import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Phone,
  Calendar,
  Brain,
  Shield,
  Clock,
  Users,
  ArrowRight,
  CheckCircle,
  Star,
  Stethoscope,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const features = [
  {
    icon: Phone,
    title: 'Risposta Automatica AI',
    description:
      "Anna, la nostra assistente virtuale, risponde alle chiamate 24/7 in italiano naturale. Nessun paziente rimane senza risposta.",
  },
  {
    icon: Calendar,
    title: 'Prenotazione Intelligente',
    description:
      "Gestione appuntamenti automatica con verifica disponibilità, conferma via email e promemoria SMS.",
  },
  {
    icon: Brain,
    title: 'Comprensione Avanzata',
    description:
      'Identifica il paziente tramite Codice Fiscale, capisce le richieste e gestisce NRE e ticket sanitario.',
  },
  {
    icon: Shield,
    title: 'GDPR & GARANTE Compliant',
    description:
      'Conforme al Regolamento (UE) 2016/679 e al D.Lgs. 196/2003. Dati crittografati e audit trail completo.',
  },
  {
    icon: Clock,
    title: 'Disponibile 24/7',
    description:
      'Il vostro studio non chiude mai. Prenotazioni anche fuori orario, weekend e festivi.',
  },
  {
    icon: Users,
    title: 'Multi-Studio',
    description:
      'Gestione centralizzata di più studi medici con configurazione personalizzata per ogni sede.',
  },
];

const stats = [
  { value: '98%', label: 'Chiamate gestite automaticamente' },
  { value: '< 3s', label: 'Tempo medio di risposta' },
  { value: '24/7', label: 'Disponibilità garantita' },
  { value: '€0', label: 'Costo per chiamata extra' },
];

export default function Homepage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero Section */}
      <section className="hero-gradient relative overflow-hidden pt-24 pb-20 lg:pt-32 lg:pb-28">
        {/* Background decorations */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-400/20 rounded-full blur-3xl" />
          <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-accent-400/15 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 text-primary-200 text-sm font-medium mb-6 glass">
                <Stethoscope className="w-4 h-4" />
                Assistente AI per Medici Specialisti
              </span>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-6">
                Il tuo studio medico,
                <br />
                <span className="text-primary-300">sempre raggiungibile.</span>
              </h1>

              <p className="text-lg sm:text-xl text-primary-100/90 max-w-2xl mx-auto mb-10">
                MedicoAssist è l'assistente AI che risponde alle chiamate, prenota appuntamenti
                e gestisce il front desk del tuo studio medico specialistico — 24 ore su 24.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  to="/prezzi"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white text-primary-700 font-semibold rounded-xl hover:bg-primary-50 transition-all shadow-lg hover:shadow-xl"
                >
                  Inizia Gratuitamente
                  <ArrowRight className="w-5 h-5" />
                </Link>
                <a
                  href="#demo"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4 glass text-white font-semibold rounded-xl hover:bg-white/15 transition-all"
                >
                  Guarda la Demo
                </a>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-gray-50 border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="text-3xl font-extrabold gradient-text">{stat.value}</div>
              <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="funzionalita" className="py-20 lg:py-28 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Tutto ciò che serve al tuo studio
            </h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              Un'unica soluzione AI per la gestione completa del front desk medico.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="p-6 rounded-2xl border border-gray-100 card-hover bg-white"
              >
                <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-500 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Come funziona
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Il paziente chiama',
                desc: "Anna risponde immediatamente in italiano naturale e identifica il paziente tramite Codice Fiscale.",
              },
              {
                step: '02',
                title: "Capisce l'esigenza",
                desc: 'AI avanzata comprende la richiesta: prenotazione, modifica, annullamento o informazioni.',
              },
              {
                step: '03',
                title: 'Azione automatica',
                desc: 'Prenota, modifica o annulla appuntamenti. Invia conferma via email e promemoria automatici.',
              },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="text-center"
              >
                <div className="inline-flex w-16 h-16 items-center justify-center rounded-full bg-primary-100 text-primary-700 font-bold text-xl mb-4">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{item.title}</h3>
                <p className="text-gray-500">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonial */}
      <section className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <Star className="w-8 h-8 text-yellow-400 mx-auto mb-6" />
          <blockquote className="text-2xl font-medium text-gray-700 italic mb-6">
            "Da quando usiamo MedicoAssist, il 95% delle chiamate viene gestito automaticamente.
            I pazienti sono soddisfatti e il nostro personale può concentrarsi sulla cura."
          </blockquote>
          <div>
            <div className="font-semibold text-gray-900">Dott.ssa Rossi</div>
            <div className="text-gray-500 text-sm">Studio Medico Specialistico — Milano</div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 hero-gradient relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-0 right-0 w-72 h-72 bg-primary-400/20 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-6">
            Pronto a trasformare il tuo studio?
          </h2>
          <p className="text-primary-100 text-lg mb-8 max-w-2xl mx-auto">
            Inizia oggi con MedicoAssist. Setup in 10 minuti, nessun hardware necessario.
          </p>
          <Link
            to="/prezzi"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-700 font-semibold rounded-xl hover:bg-primary-50 transition-all shadow-xl"
          >
            <CheckCircle className="w-5 h-5" />
            Prova Gratuita — 14 Giorni
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
}
