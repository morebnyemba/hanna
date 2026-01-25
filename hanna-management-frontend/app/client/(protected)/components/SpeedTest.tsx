'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Wifi, Download, Upload, Clock, Activity, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';

interface SpeedTestResult {
  downloadSpeed: number; // Mbps
  uploadSpeed: number; // Mbps
  ping: number; // ms
  jitter: number; // ms
  timestamp: string;
  server: string;
}

interface SpeedTestHistory {
  results: SpeedTestResult[];
}

// Simulate a speed test
const simulateSpeedTest = (): Promise<SpeedTestResult> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Starlink typical speeds: 50-200 Mbps download, 10-40 Mbps upload
      resolve({
        downloadSpeed: Math.floor(80 + Math.random() * 120),
        uploadSpeed: Math.floor(15 + Math.random() * 25),
        ping: Math.floor(20 + Math.random() * 30),
        jitter: Math.floor(2 + Math.random() * 8),
        timestamp: new Date().toISOString(),
        server: 'Harare, Zimbabwe',
      });
    }, 3000);
  });
};

// Get previous test results from localStorage
const getStoredResults = (): SpeedTestResult[] => {
  if (typeof window === 'undefined') return [];
  const stored = localStorage.getItem('speedTestHistory');
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return [];
    }
  }
  return [];
};

// Store results in localStorage
const storeResult = (result: SpeedTestResult) => {
  if (typeof window === 'undefined') return;
  const history = getStoredResults();
  history.unshift(result);
  // Keep only last 10 results
  const trimmed = history.slice(0, 10);
  localStorage.setItem('speedTestHistory', JSON.stringify(trimmed));
};

type TestPhase = 'idle' | 'ping' | 'download' | 'upload' | 'complete';

export default function SpeedTest() {
  const [testing, setTesting] = useState(false);
  const [phase, setPhase] = useState<TestPhase>('idle');
  const [progress, setProgress] = useState(0);
  const [currentResult, setCurrentResult] = useState<SpeedTestResult | null>(null);
  const [history, setHistory] = useState<SpeedTestResult[]>([]);

  useEffect(() => {
    // Initialize history from localStorage on mount
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setHistory(getStoredResults());
  }, []);

  const runSpeedTest = async () => {
    setTesting(true);
    setProgress(0);
    setCurrentResult(null);

    // Simulate ping test
    setPhase('ping');
    for (let i = 0; i <= 20; i++) {
      await new Promise(r => setTimeout(r, 50));
      setProgress(i);
    }

    // Simulate download test
    setPhase('download');
    for (let i = 20; i <= 60; i++) {
      await new Promise(r => setTimeout(r, 40));
      setProgress(i);
    }

    // Simulate upload test
    setPhase('upload');
    for (let i = 60; i <= 100; i++) {
      await new Promise(r => setTimeout(r, 40));
      setProgress(i);
    }

    // Get final result
    const result = await simulateSpeedTest();
    setCurrentResult(result);
    storeResult(result);
    setHistory(getStoredResults());
    setPhase('complete');
    setTesting(false);
  };

  const getSpeedRating = (downloadSpeed: number): { label: string; color: string; icon: React.ReactNode } => {
    if (downloadSpeed >= 150) {
      return { label: 'Excellent', color: 'text-green-600', icon: <CheckCircle className="w-5 h-5 text-green-600" /> };
    } else if (downloadSpeed >= 100) {
      return { label: 'Very Good', color: 'text-green-500', icon: <CheckCircle className="w-5 h-5 text-green-500" /> };
    } else if (downloadSpeed >= 50) {
      return { label: 'Good', color: 'text-blue-600', icon: <CheckCircle className="w-5 h-5 text-blue-600" /> };
    } else if (downloadSpeed >= 25) {
      return { label: 'Fair', color: 'text-yellow-600', icon: <AlertCircle className="w-5 h-5 text-yellow-600" /> };
    } else {
      return { label: 'Poor', color: 'text-red-600', icon: <AlertCircle className="w-5 h-5 text-red-600" /> };
    }
  };

  const getPhaseLabel = () => {
    switch (phase) {
      case 'ping': return 'Testing latency...';
      case 'download': return 'Testing download speed...';
      case 'upload': return 'Testing upload speed...';
      case 'complete': return 'Test complete!';
      default: return 'Ready to test';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wifi className="w-5 h-5 text-purple-500" />
          Starlink Speed Test
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Speed Test UI */}
        <div className="flex flex-col items-center py-6">
          {/* Circular Progress Indicator */}
          <div className="relative w-48 h-48 mb-6">
            <svg className="w-48 h-48 transform -rotate-90" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                cx="50"
                cy="50"
                r="45"
                stroke="#e5e7eb"
                strokeWidth="8"
                fill="none"
              />
              {/* Progress circle */}
              <circle
                cx="50"
                cy="50"
                r="45"
                stroke={testing ? '#8b5cf6' : currentResult ? '#22c55e' : '#d1d5db'}
                strokeWidth="8"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 45}`}
                strokeDashoffset={`${2 * Math.PI * 45 * (1 - progress / 100)}`}
                className="transition-all duration-300"
              />
            </svg>
            {/* Center content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              {testing ? (
                <>
                  <Activity className="w-8 h-8 text-purple-500 animate-pulse mb-2" />
                  <span className="text-sm text-gray-500">{getPhaseLabel()}</span>
                </>
              ) : currentResult ? (
                <>
                  <span className="text-3xl font-bold text-gray-900">{currentResult.downloadSpeed}</span>
                  <span className="text-sm text-gray-500">Mbps</span>
                </>
              ) : (
                <>
                  <Wifi className="w-8 h-8 text-gray-400 mb-2" />
                  <span className="text-sm text-gray-500">Start Test</span>
                </>
              )}
            </div>
          </div>

          {/* Test Button */}
          <Button
            onClick={runSpeedTest}
            disabled={testing}
            size="lg"
            className="w-full max-w-xs"
          >
            {testing ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Activity className="w-4 h-4 mr-2" />
                Run Speed Test
              </>
            )}
          </Button>
        </div>

        {/* Current Result */}
        {currentResult && !testing && (
          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-medium text-gray-900">Latest Result</h4>
              <div className="flex items-center gap-2">
                {getSpeedRating(currentResult.downloadSpeed).icon}
                <span className={`font-medium ${getSpeedRating(currentResult.downloadSpeed).color}`}>
                  {getSpeedRating(currentResult.downloadSpeed).label}
                </span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-sm text-purple-700 mb-1">
                  <Download className="w-4 h-4" />
                  Download
                </div>
                <div className="text-2xl font-bold text-purple-800">{currentResult.downloadSpeed} Mbps</div>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-sm text-blue-700 mb-1">
                  <Upload className="w-4 h-4" />
                  Upload
                </div>
                <div className="text-2xl font-bold text-blue-800">{currentResult.uploadSpeed} Mbps</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-sm text-green-700 mb-1">
                  <Clock className="w-4 h-4" />
                  Ping
                </div>
                <div className="text-2xl font-bold text-green-800">{currentResult.ping} ms</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-sm text-orange-700 mb-1">
                  <Activity className="w-4 h-4" />
                  Jitter
                </div>
                <div className="text-2xl font-bold text-orange-800">{currentResult.jitter} ms</div>
              </div>
            </div>

            <p className="text-xs text-gray-500 mt-4 text-center">
              Tested at {new Date(currentResult.timestamp).toLocaleString()} • Server: {currentResult.server}
            </p>
          </div>
        )}

        {/* Test History */}
        {history.length > 0 && (
          <div className="border-t pt-6">
            <h4 className="font-medium text-gray-900 mb-4">Recent Tests</h4>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {history.slice(0, 5).map((result, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getSpeedRating(result.downloadSpeed).icon}
                    <div>
                      <div className="font-medium text-gray-900">
                        {result.downloadSpeed} Mbps / {result.uploadSpeed} Mbps
                      </div>
                      <div className="text-xs text-gray-500">
                        Ping: {result.ping}ms • Jitter: {result.jitter}ms
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 text-right">
                    {new Date(result.timestamp).toLocaleDateString()}
                    <br />
                    {new Date(result.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tips */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h5 className="font-medium text-purple-900 mb-2">Speed Tips for Starlink</h5>
          <ul className="text-sm text-purple-800 space-y-1">
            <li>• Ensure the dish has a clear view of the sky</li>
            <li>• Check for obstructions using the Starlink app</li>
            <li>• Router placement affects WiFi speeds</li>
            <li>• Speeds may vary during peak hours</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
