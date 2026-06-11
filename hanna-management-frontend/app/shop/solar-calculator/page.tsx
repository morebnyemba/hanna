'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FiSun, FiArrowLeft, FiArrowRight, FiMessageCircle, FiPlus, FiMinus, FiZap, FiCheck } from 'react-icons/fi';

// ─── Appliance database ───────────────────────────────────────────────────────

const ROOMS = [
  {
    id: 'lounge',
    label: 'Lounge / Living Room',
    icon: '🛋️',
    appliances: [
      { id: 'tv_32', label: '32" LED TV', watts: 40, defaultHours: 6 },
      { id: 'tv_55', label: '55" LED TV', watts: 80, defaultHours: 6 },
      { id: 'dstv', label: 'DSTV Decoder', watts: 25, defaultHours: 6 },
      { id: 'lights_lounge', label: 'LED Lights (×4)', watts: 24, defaultHours: 5 },
      { id: 'fan_stand', label: 'Stand Fan', watts: 55, defaultHours: 8 },
      { id: 'wifi_router', label: 'WiFi Router', watts: 10, defaultHours: 24 },
    ],
  },
  {
    id: 'bedroom',
    label: 'Main Bedroom',
    icon: '🛏️',
    appliances: [
      { id: 'lights_bed', label: 'LED Lights (×2)', watts: 12, defaultHours: 4 },
      { id: 'fan_bed', label: 'Ceiling / Stand Fan', watts: 55, defaultHours: 8 },
      { id: 'phone_charge', label: 'Phone Chargers (×2)', watts: 20, defaultHours: 4 },
      { id: 'ac_1hp', label: 'Air Conditioner (1HP)', watts: 900, defaultHours: 6 },
      { id: 'ac_1_5hp', label: 'Air Conditioner (1.5HP)', watts: 1200, defaultHours: 6 },
    ],
  },
  {
    id: 'kitchen',
    label: 'Kitchen',
    icon: '🍳',
    appliances: [
      { id: 'fridge', label: 'Refrigerator (200L)', watts: 150, defaultHours: 24 },
      { id: 'fridge_large', label: 'Refrigerator (400L)', watts: 250, defaultHours: 24 },
      { id: 'microwave', label: 'Microwave', watts: 1000, defaultHours: 0.5 },
      { id: 'kettle', label: 'Electric Kettle', watts: 2000, defaultHours: 0.25 },
      { id: 'toaster', label: 'Toaster', watts: 800, defaultHours: 0.1 },
      { id: 'lights_kitchen', label: 'LED Lights (×3)', watts: 18, defaultHours: 4 },
    ],
  },
  {
    id: 'office',
    label: 'Home Office',
    icon: '💼',
    appliances: [
      { id: 'laptop', label: 'Laptop', watts: 65, defaultHours: 8 },
      { id: 'desktop', label: 'Desktop PC + Monitor', watts: 300, defaultHours: 8 },
      { id: 'printer', label: 'Printer', watts: 50, defaultHours: 1 },
      { id: 'lights_office', label: 'LED Lights (×2)', watts: 12, defaultHours: 8 },
      { id: 'router_office', label: 'WiFi Router', watts: 10, defaultHours: 24 },
    ],
  },
  {
    id: 'security',
    label: 'Security / Gate',
    icon: '🔒',
    appliances: [
      { id: 'cctv_4ch', label: 'CCTV System (4 cameras)', watts: 60, defaultHours: 24 },
      { id: 'gate_motor', label: 'Electric Gate Motor', watts: 300, defaultHours: 0.5 },
      { id: 'alarm', label: 'Alarm System', watts: 15, defaultHours: 24 },
      { id: 'intercom', label: 'Video Intercom', watts: 10, defaultHours: 24 },
    ],
  },
  {
    id: 'borehole',
    label: 'Borehole / Water Pump',
    icon: '💧',
    appliances: [
      { id: 'pump_0_5hp', label: 'Submersible Pump (0.5HP)', watts: 375, defaultHours: 3 },
      { id: 'pump_1hp', label: 'Submersible Pump (1HP)', watts: 750, defaultHours: 3 },
      { id: 'pump_1_5hp', label: 'Submersible Pump (1.5HP)', watts: 1100, defaultHours: 3 },
    ],
  },
];

interface Selection {
  [applianceId: string]: { selected: boolean; hours: number };
}

// ─── Result calculator ────────────────────────────────────────────────────────

function calculateSystem(selections: Selection) {
  let dailyWh = 0;
  let peakW = 0;

  for (const room of ROOMS) {
    for (const app of room.appliances) {
      const sel = selections[app.id];
      if (sel?.selected) {
        dailyWh += app.watts * sel.hours;
        peakW += app.watts;
      }
    }
  }

  const peakKw = peakW / 1000;
  const dailyKwh = dailyWh / 1000;

  // Inverter: cover peak load × 1.25 safety factor, round to nearest common size
  const inverterSizes = [1, 2, 3, 5, 8, 10, 15, 20];
  const rawInverter = peakKw * 1.25;
  const inverterKva = inverterSizes.find((s) => s >= rawInverter) || 20;

  // Battery: cover 1.5 days, 80% DoD (usable)
  const batteryKwh = Math.ceil((dailyKwh * 1.5) / 0.8 * 10) / 10;
  const battery100Ah = Math.ceil(batteryKwh / 1.2); // 100Ah @ 12V = 1.2kWh
  const battery200Ah = Math.ceil(batteryKwh / 2.4); // 200Ah @ 12V = 2.4kWh

  // Solar panels: cover daily usage × 1.3 (losses), assume 5h peak sun hours
  const panelsNeeded = Math.ceil((dailyKwh * 1.3) / 5);
  const panelW = panelsNeeded <= 4 ? 400 : 550;
  const panelCount = Math.ceil((dailyKwh * 1.3) / (5 * (panelW / 1000)));

  return { dailyKwh, peakKw, inverterKva, batteryKwh, battery200Ah, panelCount, panelW };
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function SolarCalculatorPage() {
  const [step, setStep] = useState<'rooms' | 'appliances' | 'result'>('rooms');
  const [selectedRooms, setSelectedRooms] = useState<string[]>([]);
  const [roomIdx, setRoomIdx] = useState(0);
  const [selections, setSelections] = useState<Selection>({});

  const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '';

  const activeRooms = ROOMS.filter((r) => selectedRooms.includes(r.id));

  const toggleAppliance = (appId: string, defaultHours: number) => {
    setSelections((prev) => ({
      ...prev,
      [appId]: prev[appId]?.selected
        ? { ...prev[appId], selected: false }
        : { selected: true, hours: defaultHours },
    }));
  };

  const setHours = (appId: string, hours: number) => {
    setSelections((prev) => ({ ...prev, [appId]: { ...prev[appId], hours: Math.max(0.1, hours) } }));
  };

  const result = step === 'result' ? calculateSystem(selections) : null;

  const waMessage = result
    ? `Hi! I used your Solar Calculator and my results are:
Daily usage: ${result.dailyKwh.toFixed(1)} kWh
Peak load: ${result.peakKw.toFixed(1)} kW
Recommended: ${result.inverterKva}kVA inverter, ${result.panelCount}×${result.panelW}W panels, ${result.battery200Ah}×200Ah batteries.
Please send me a quote!`
    : '';

  const waLink = whatsappNumber && waMessage
    ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(waMessage)}`
    : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-orange-50/30 to-sky-50/30">
      {/* Header */}
      <div className="bg-white border-b border-orange-100 sticky top-0 z-40 shadow-sm">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/shop/solar" className="flex items-center gap-2 text-orange-600 hover:text-orange-800 font-semibold text-sm transition">
            <FiArrowLeft className="w-4 h-4" />
            Solar Products
          </Link>
          <div className="flex-1 flex justify-center">
            <div className="flex items-center gap-2 text-sm font-bold text-orange-700">
              <FiSun className="w-5 h-5" />
              Solar System Calculator
            </div>
          </div>
          <Link href="/shop" className="text-sm text-gray-400 hover:text-gray-600 transition">Shop</Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8">

        {/* ── STEP: Pick rooms ── */}
        {step === 'rooms' && (
          <div>
            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-orange-100 flex items-center justify-center mx-auto mb-4">
                <FiSun className="w-8 h-8 text-orange-500" />
              </div>
              <h1 className="text-3xl font-extrabold text-orange-900 mb-2">Find Your Solar System</h1>
              <p className="text-gray-500 text-base max-w-md mx-auto">Select the areas you want to power. We'll calculate the right solar system for your needs.</p>
            </div>

            <div className="grid sm:grid-cols-2 gap-3 mb-8">
              {ROOMS.map((room) => {
                const active = selectedRooms.includes(room.id);
                return (
                  <button
                    key={room.id}
                    onClick={() => setSelectedRooms((prev) =>
                      prev.includes(room.id) ? prev.filter((r) => r !== room.id) : [...prev, room.id]
                    )}
                    className={`flex items-center gap-3 p-4 rounded-2xl border-2 text-left transition-all ${
                      active
                        ? 'border-orange-500 bg-orange-50 shadow-sm'
                        : 'border-gray-200 bg-white hover:border-orange-300 hover:bg-orange-50/50'
                    }`}
                  >
                    <span className="text-2xl">{room.icon}</span>
                    <div className="flex-1">
                      <p className={`font-bold text-sm ${active ? 'text-orange-800' : 'text-gray-700'}`}>{room.label}</p>
                      <p className="text-xs text-gray-400">{room.appliances.length} appliances</p>
                    </div>
                    {active && <FiCheck className="w-5 h-5 text-orange-500 flex-shrink-0" />}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => { setRoomIdx(0); setStep('appliances'); }}
              disabled={selectedRooms.length === 0}
              className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white rounded-2xl font-bold text-base transition disabled:bg-gray-300 flex items-center justify-center gap-2 shadow-lg"
            >
              Next: Select Appliances <FiArrowRight className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* ── STEP: Appliances per room ── */}
        {step === 'appliances' && activeRooms.length > 0 && (
          <div>
            {/* Room tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
              {activeRooms.map((room, i) => (
                <button
                  key={room.id}
                  onClick={() => setRoomIdx(i)}
                  className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-bold transition ${
                    i === roomIdx
                      ? 'bg-orange-500 text-white shadow-sm'
                      : 'bg-white border border-orange-200 text-orange-600 hover:bg-orange-50'
                  }`}
                >
                  <span>{room.icon}</span>
                  <span className="hidden sm:inline">{room.label.split(' / ')[0]}</span>
                </button>
              ))}
            </div>

            <div className="bg-white rounded-2xl border border-orange-100 shadow-sm p-6 mb-6">
              <h2 className="font-extrabold text-orange-900 text-lg mb-1 flex items-center gap-2">
                <span>{activeRooms[roomIdx].icon}</span>
                {activeRooms[roomIdx].label}
              </h2>
              <p className="text-xs text-gray-400 mb-4">Select the appliances you use and adjust daily hours.</p>

              <div className="space-y-3">
                {activeRooms[roomIdx].appliances.map((app) => {
                  const sel = selections[app.id];
                  const isOn = sel?.selected ?? false;
                  return (
                    <div
                      key={app.id}
                      className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all cursor-pointer ${
                        isOn ? 'border-orange-400 bg-orange-50' : 'border-gray-100 bg-gray-50 hover:border-orange-200'
                      }`}
                      onClick={() => toggleAppliance(app.id, app.defaultHours)}
                    >
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition ${
                        isOn ? 'bg-orange-500 border-orange-500' : 'border-gray-300'
                      }`}>
                        {isOn && <FiCheck className="w-3 h-3 text-white" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-semibold ${isOn ? 'text-orange-800' : 'text-gray-700'}`}>{app.label}</p>
                        <p className="text-xs text-gray-400">{app.watts}W</p>
                      </div>
                      {isOn && (
                        <div className="flex items-center gap-2 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => setHours(app.id, (sel?.hours ?? app.defaultHours) - 0.5)}
                            className="w-6 h-6 rounded-full bg-orange-200 text-orange-800 flex items-center justify-center hover:bg-orange-300 transition"
                          >
                            <FiMinus className="w-3 h-3" />
                          </button>
                          <span className="text-sm font-bold text-orange-900 w-12 text-center">
                            {(sel?.hours ?? app.defaultHours)}h/day
                          </span>
                          <button
                            onClick={() => setHours(app.id, (sel?.hours ?? app.defaultHours) + 0.5)}
                            className="w-6 h-6 rounded-full bg-orange-200 text-orange-800 flex items-center justify-center hover:bg-orange-300 transition"
                          >
                            <FiPlus className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex gap-3">
              {roomIdx < activeRooms.length - 1 ? (
                <button
                  onClick={() => setRoomIdx((i) => i + 1)}
                  className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-bold transition flex items-center justify-center gap-2"
                >
                  Next Room <FiArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={() => setStep('result')}
                  className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-bold transition flex items-center justify-center gap-2"
                >
                  <FiZap className="w-4 h-4" />
                  Calculate My System
                </button>
              )}
              <button
                onClick={() => { setStep('rooms'); }}
                className="px-4 py-3 border border-gray-200 text-gray-600 rounded-xl font-semibold text-sm hover:bg-gray-50 transition"
              >
                ← Back
              </button>
            </div>
          </div>
        )}

        {/* ── STEP: Result ── */}
        {step === 'result' && result && (
          <div>
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center mx-auto mb-4">
                <FiCheck className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-3xl font-extrabold text-orange-900 mb-1">Your System Recommendation</h2>
              <p className="text-gray-500">Based on your selected appliances and usage hours.</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              {[
                { label: 'Daily Usage', value: `${result.dailyKwh.toFixed(1)} kWh`, sub: 'per day', color: 'bg-sky-50 border-sky-200 text-sky-700' },
                { label: 'Peak Load', value: `${result.peakKw.toFixed(1)} kW`, sub: 'simultaneous', color: 'bg-orange-50 border-orange-200 text-orange-700' },
              ].map(({ label, value, sub, color }) => (
                <div key={label} className={`rounded-2xl border p-4 text-center ${color}`}>
                  <p className="text-xs font-bold uppercase tracking-wider opacity-70 mb-1">{label}</p>
                  <p className="text-2xl font-extrabold">{value}</p>
                  <p className="text-xs opacity-60">{sub}</p>
                </div>
              ))}
            </div>

            {/* Recommended system */}
            <div className="bg-white rounded-2xl border border-orange-200 shadow-sm p-6 mb-6">
              <h3 className="font-extrabold text-orange-900 mb-4 flex items-center gap-2">
                <FiSun className="w-5 h-5 text-orange-500" />
                Recommended Solar Package
              </h3>
              <div className="space-y-3">
                {[
                  { icon: '🔋', label: 'Inverter', value: `${result.inverterKva} kVA`, note: 'Hybrid inverter with MPPT charge controller' },
                  { icon: '☀️', label: 'Solar Panels', value: `${result.panelCount} × ${result.panelW}W`, note: `Total ${(result.panelCount * result.panelW / 1000).toFixed(1)} kWp` },
                  { icon: '⚡', label: 'Battery Bank', value: `${result.battery200Ah} × 200Ah`, note: '12V Lithium or Gel Deep Cycle batteries' },
                ].map(({ icon, label, value, note }) => (
                  <div key={label} className="flex items-center gap-4 p-3 bg-orange-50 rounded-xl">
                    <span className="text-2xl">{icon}</span>
                    <div className="flex-1">
                      <p className="text-xs text-orange-600 font-semibold uppercase tracking-wide">{label}</p>
                      <p className="font-extrabold text-orange-900">{value}</p>
                      <p className="text-xs text-gray-500">{note}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 mb-6 text-sm text-sky-700">
              <strong>Note:</strong> This is an estimate based on your inputs. Final sizing depends on panel orientation, cable losses, and site conditions. Our engineers will verify during installation.
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              {waLink && (
                <a href={waLink} target="_blank" rel="noopener noreferrer"
                  className="flex-1 flex items-center justify-center gap-2 py-4 bg-green-500 hover:bg-green-600 text-white rounded-2xl font-bold text-base transition shadow-lg">
                  <FiMessageCircle className="w-5 h-5" />
                  Get Quote on WhatsApp
                </a>
              )}
              <Link href="/shop/solar"
                className="flex items-center justify-center gap-2 px-6 py-4 bg-orange-500 hover:bg-orange-600 text-white rounded-2xl font-bold text-sm transition">
                <FiSun className="w-4 h-4" />
                Browse Solar Products
              </Link>
              <button onClick={() => { setStep('rooms'); setSelections({}); setSelectedRooms([]); }}
                className="px-6 py-4 border border-gray-200 text-gray-600 rounded-2xl font-semibold text-sm hover:bg-gray-50 transition">
                Start Over
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
