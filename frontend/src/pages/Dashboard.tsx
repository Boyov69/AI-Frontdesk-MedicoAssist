import { useState } from 'react';
import {
  Phone,
  Calendar,
  Users,
  BarChart3,
  Clock,
  TrendingUp,
  Activity,
  MessageSquare,
} from 'lucide-react';
import Navbar from '../components/Navbar';

const statsCards = [
  { title: 'Chiamate Oggi', value: '47', change: '+12%', icon: Phone, color: 'text-blue-600 bg-blue-50' },
  { title: 'Appuntamenti', value: '23', change: '+8%', icon: Calendar, color: 'text-emerald-600 bg-emerald-50' },
  { title: 'Pazienti Attivi', value: '1.247', change: '+3%', icon: Users, color: 'text-violet-600 bg-violet-50' },
  { title: 'Tasso AI', value: '94%', change: '+2%', icon: Activity, color: 'text-amber-600 bg-amber-50' },
];

const recentCalls = [
  { time: '14:32', caller: 'Marco B.', tipo: 'Prenotazione', stato: 'Completata', durata: '2:15' },
  { time: '14:18', caller: 'Laura M.', tipo: 'Informazioni', stato: 'Completata', durata: '1:30' },
  { time: '13:55', caller: 'Giuseppe R.', tipo: 'Annullamento', stato: 'Completata', durata: '1:45' },
  { time: '13:40', caller: '06 1234...', tipo: 'Prenotazione', stato: 'Trasferita', durata: '3:20' },
  { time: '13:22', caller: 'Anna P.', tipo: 'Modifica', stato: 'Completata', durata: '2:00' },
];

const upcomingAppointments = [
  { ora: '09:00', paziente: 'Rossi Maria', prestazione: 'Visita Specialistica', durata: '30 min' },
  { ora: '09:30', paziente: 'Bianchi Giuseppe', prestazione: 'Visita di Controllo', durata: '20 min' },
  { ora: '10:00', paziente: 'Verdi Lucia', prestazione: 'Riabilitazione Motoria', durata: '45 min' },
  { ora: '10:45', paziente: 'Ferrari Marco', prestazione: 'Terapia Manuale', durata: '45 min' },
  { ora: '11:30', paziente: 'Romano Anna', prestazione: 'Consulto Specialistico', durata: '30 min' },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'calls' | 'appointments'>('overview');

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar isDashboard />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Panoramica del tuo studio medico specialistico</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsCards.map((card) => (
            <div
              key={card.title}
              className="bg-white rounded-2xl p-6 border border-gray-100 card-hover"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${card.color}`}>
                  <card.icon className="w-5 h-5" />
                </div>
                <span className="text-sm text-emerald-600 font-medium flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  {card.change}
                </span>
              </div>
              <div className="text-2xl font-bold text-gray-900">{card.value}</div>
              <div className="text-sm text-gray-500 mt-1">{card.title}</div>
            </div>
          ))}
        </div>

        {/* Tab navigation */}
        <div className="flex gap-2 mb-6">
          {[
            { id: 'overview' as const, label: 'Panoramica', icon: BarChart3 },
            { id: 'calls' as const, label: 'Chiamate', icon: Phone },
            { id: 'appointments' as const, label: 'Appuntamenti', icon: Calendar },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Recent Calls */}
          <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-50">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Phone className="w-5 h-5 text-primary-600" />
                  Chiamate Recenti
                </h2>
                <span className="text-xs bg-primary-50 text-primary-700 px-2 py-1 rounded-full font-medium">
                  Oggi
                </span>
              </div>
            </div>
            <div className="divide-y divide-gray-50">
              {recentCalls.map((call, i) => (
                <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary-50 flex items-center justify-center">
                      <MessageSquare className="w-4 h-4 text-primary-600" />
                    </div>
                    <div>
                      <div className="font-medium text-gray-900 text-sm">{call.caller}</div>
                      <div className="text-xs text-gray-400">{call.tipo}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-xs font-medium ${
                      call.stato === 'Completata' ? 'text-emerald-600' : 'text-amber-600'
                    }`}>
                      {call.stato}
                    </div>
                    <div className="text-xs text-gray-400 flex items-center gap-1 justify-end">
                      <Clock className="w-3 h-3" />
                      {call.durata}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Upcoming Appointments */}
          <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-50">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-emerald-600" />
                  Appuntamenti di Oggi
                </h2>
                <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-1 rounded-full font-medium">
                  5 in programma
                </span>
              </div>
            </div>
            <div className="divide-y divide-gray-50">
              {upcomingAppointments.map((appt, i) => (
                <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="text-sm font-mono font-semibold text-primary-700 w-12">{appt.ora}</div>
                    <div>
                      <div className="font-medium text-gray-900 text-sm">{appt.paziente}</div>
                      <div className="text-xs text-gray-400">{appt.prestazione}</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {appt.durata}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
