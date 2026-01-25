'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Armchair, 
  Calendar, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  Sparkles,
  Droplets,
  Sun,
  Wind,
  Wrench,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface MaintenanceTask {
  id: string;
  title: string;
  description: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  icon: React.ReactNode;
  tips: string[];
  completed?: boolean;
  lastCompleted?: string;
}

const maintenanceTasks: MaintenanceTask[] = [
  {
    id: 'dust',
    title: 'Dust & Wipe Surfaces',
    description: 'Remove dust and debris from all furniture surfaces',
    frequency: 'weekly',
    icon: <Sparkles className="w-5 h-5 text-blue-500" />,
    tips: [
      'Use a soft, lint-free microfiber cloth',
      'Dust in the direction of the wood grain',
      'Pay attention to crevices and decorative details',
      'Avoid using water on unfinished wood'
    ]
  },
  {
    id: 'clean',
    title: 'Deep Clean',
    description: 'Thorough cleaning of all furniture pieces',
    frequency: 'monthly',
    icon: <Droplets className="w-5 h-5 text-cyan-500" />,
    tips: [
      'Use appropriate cleaners for each material type',
      'Test cleaning products on an inconspicuous area first',
      'Wipe spills immediately to prevent staining',
      'Allow furniture to dry completely before use'
    ]
  },
  {
    id: 'sunlight',
    title: 'Check Sun Exposure',
    description: 'Protect furniture from direct sunlight damage',
    frequency: 'daily',
    icon: <Sun className="w-5 h-5 text-yellow-500" />,
    tips: [
      'Rotate furniture periodically to ensure even fading',
      'Use curtains or blinds during peak sunlight hours',
      'Apply UV-protective window film if needed',
      'Consider furniture covers for outdoor pieces'
    ]
  },
  {
    id: 'ventilation',
    title: 'Ensure Proper Ventilation',
    description: 'Maintain good air circulation around furniture',
    frequency: 'daily',
    icon: <Wind className="w-5 h-5 text-green-500" />,
    tips: [
      'Keep furniture away from heating/cooling vents',
      'Maintain consistent humidity levels (40-60%)',
      'Allow air circulation behind wardrobes and cabinets',
      'Use dehumidifiers in damp environments'
    ]
  },
  {
    id: 'inspect',
    title: 'Hardware Inspection',
    description: 'Check and tighten all hinges, handles, and screws',
    frequency: 'quarterly',
    icon: <Wrench className="w-5 h-5 text-orange-500" />,
    tips: [
      'Tighten loose screws and bolts',
      'Apply lubricant to squeaky hinges',
      'Replace worn or damaged hardware',
      'Check drawer slides and door alignments'
    ]
  },
  {
    id: 'polish',
    title: 'Wood Treatment & Polish',
    description: 'Apply protective polish or oil to wood surfaces',
    frequency: 'yearly',
    icon: <Sparkles className="w-5 h-5 text-amber-500" />,
    tips: [
      'Use furniture polish sparingly',
      'Choose products suited for your wood type',
      'Apply in thin, even coats',
      'Buff with a soft cloth for shine'
    ]
  }
];

const frequencyColors: Record<string, { bg: string; text: string; label: string }> = {
  daily: { bg: 'bg-green-100', text: 'text-green-800', label: 'Daily' },
  weekly: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Weekly' },
  monthly: { bg: 'bg-purple-100', text: 'text-purple-800', label: 'Monthly' },
  quarterly: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Every 3 Months' },
  yearly: { bg: 'bg-red-100', text: 'text-red-800', label: 'Yearly' },
};

export default function MaintenanceTips() {
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set());

  const toggleTask = (taskId: string) => {
    setExpandedTask(expandedTask === taskId ? null : taskId);
  };

  const markComplete = (taskId: string) => {
    const newCompleted = new Set(completedTasks);
    if (newCompleted.has(taskId)) {
      newCompleted.delete(taskId);
    } else {
      newCompleted.add(taskId);
    }
    setCompletedTasks(newCompleted);
  };

  const completedCount = completedTasks.size;
  const totalTasks = maintenanceTasks.length;
  const progressPercent = (completedCount / totalTasks) * 100;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Armchair className="w-5 h-5 text-amber-600" />
          Furniture Maintenance Guide
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Overview */}
        <div className="bg-amber-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-amber-800">Maintenance Progress</span>
            <span className="text-sm font-bold text-amber-800">{completedCount}/{totalTasks} completed</span>
          </div>
          <div className="w-full bg-amber-200 rounded-full h-2">
            <div
              className="bg-amber-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Upcoming Schedule */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Calendar className="w-5 h-5 text-blue-600" />
            <h4 className="font-medium text-blue-900">Recommended Schedule</h4>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-gray-700">Daily: Sun & ventilation check</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-gray-700">Weekly: Dusting</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500" />
              <span className="text-gray-700">Monthly: Deep clean</span>
            </div>
          </div>
        </div>

        {/* Maintenance Tasks */}
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900 flex items-center gap-2">
            <Wrench className="w-4 h-4" />
            Maintenance Tasks
          </h4>
          
          {maintenanceTasks.map((task) => (
            <div
              key={task.id}
              className={`border rounded-lg overflow-hidden transition-all ${
                completedTasks.has(task.id) ? 'bg-green-50 border-green-200' : 'bg-white'
              }`}
            >
              <div
                className="p-4 cursor-pointer"
                onClick={() => toggleTask(task.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${completedTasks.has(task.id) ? 'bg-green-100' : 'bg-gray-100'}`}>
                      {task.icon}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h5 className={`font-medium ${completedTasks.has(task.id) ? 'text-green-800 line-through' : 'text-gray-900'}`}>
                          {task.title}
                        </h5>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${frequencyColors[task.frequency].bg} ${frequencyColors[task.frequency].text}`}>
                          {frequencyColors[task.frequency].label}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        markComplete(task.id);
                      }}
                    >
                      {completedTasks.has(task.id) ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <Clock className="w-5 h-5 text-gray-400" />
                      )}
                    </Button>
                    {expandedTask === task.id ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Tips */}
              {expandedTask === task.id && (
                <div className="px-4 pb-4 border-t bg-gray-50">
                  <h6 className="font-medium text-gray-700 mt-3 mb-2">Tips:</h6>
                  <ul className="space-y-2">
                    {task.tips.map((tip, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Care Warnings */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h5 className="font-medium text-yellow-800 mb-2">Important Care Notes</h5>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• Avoid placing hot items directly on furniture surfaces</li>
                <li>• Use coasters and placemats to prevent water rings</li>
                <li>• Lift furniture when moving - don&apos;t drag</li>
                <li>• Keep furniture away from radiators and air conditioners</li>
                <li>• Contact us if you notice any structural issues</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Contact Support */}
        <div className="text-center pt-4 border-t">
          <p className="text-sm text-gray-600 mb-3">
            Need professional maintenance or repair service?
          </p>
          <Button variant="outline" className="w-full max-w-xs">
            <Wrench className="w-4 h-4 mr-2" />
            Request Service
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
