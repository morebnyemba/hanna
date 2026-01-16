// src/pages/retailer/BranchInstallerCalendarPage.jsx
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  User,
  Clock,
  MapPin,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const BranchInstallerCalendarPage = () => {
  const [installers, setInstallers] = useState([]);
  const [selectedInstaller, setSelectedInstaller] = useState('');
  const [schedule, setSchedule] = useState({});
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [weekDates, setWeekDates] = useState([]);

  useEffect(() => {
    loadInstallers();
  }, []);

  useEffect(() => {
    generateWeekDates();
  }, [currentDate]);

  useEffect(() => {
    if (selectedInstaller && weekDates.length > 0) {
      loadSchedule();
    }
  }, [selectedInstaller, weekDates]);

  const loadInstallers = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${API_BASE}/crm-api/branch/installers/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        const installersList = data.results || data;
        setInstallers(installersList);
        if (installersList.length > 0 && !selectedInstaller) {
          setSelectedInstaller(installersList[0].id);
        }
      }
    } catch (err) {
      console.error('Error loading installers:', err);
      toast.error('Failed to load installers');
    } finally {
      setLoading(false);
    }
  };

  const generateWeekDates = () => {
    const dates = [];
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

    for (let i = 0; i < 7; i++) {
      const date = new Date(startOfWeek);
      date.setDate(startOfWeek.getDate() + i);
      dates.push(date);
    }

    setWeekDates(dates);
  };

  const loadSchedule = async () => {
    if (!selectedInstaller || weekDates.length === 0) return;

    try {
      const token = localStorage.getItem('access_token');
      const startDate = weekDates[0].toISOString().split('T')[0];
      const endDate = weekDates[6].toISOString().split('T')[0];

      const response = await fetch(
        `${API_BASE}/crm-api/branch/installers/${selectedInstaller}/schedule/?start_date=${startDate}&end_date=${endDate}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSchedule(data.schedule || {});
      }
    } catch (err) {
      console.error('Error loading schedule:', err);
      toast.error('Failed to load schedule');
    }
  };

  const goToPreviousWeek = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() - 7);
    setCurrentDate(newDate);
  };

  const goToNextWeek = () => {
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + 7);
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'border-yellow-400 bg-yellow-50',
      confirmed: 'border-blue-400 bg-blue-50',
      in_progress: 'border-purple-400 bg-purple-50',
      completed: 'border-green-400 bg-green-50',
      cancelled: 'border-red-400 bg-red-50',
    };
    return colors[status] || 'border-gray-400 bg-gray-50';
  };

  const formatDateKey = (date) => {
    return date.toISOString().split('T')[0];
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading calendar...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <CalendarIcon className="w-8 h-8 text-blue-600" />
          Installer Calendar
        </h1>
        <p className="text-gray-600 mt-1">
          View installer schedules and assignments
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Installer
            </label>
            <select
              value={selectedInstaller}
              onChange={(e) => setSelectedInstaller(e.target.value)}
              className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {installers.map((installer) => (
                <option key={installer.id} value={installer.id}>
                  {installer.name} {installer.specialization && `(${installer.specialization})`}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={goToPreviousWeek}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={goToToday}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Today
            </button>
            <button
              onClick={goToNextWeek}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="grid grid-cols-7 gap-px bg-gray-200">
          {weekDates.map((date, index) => {
            const dateKey = formatDateKey(date);
            const daySchedule = schedule[dateKey] || { assignments: [], availability: [], is_available: true };
            const isToday = date.toDateString() === new Date().toDateString();
            const dayName = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][date.getDay()];

            return (
              <div key={index} className="bg-white min-h-[200px]">
                <div className={`p-3 border-b border-gray-200 ${isToday ? 'bg-blue-50' : ''}`}>
                  <p className="text-xs font-medium text-gray-600">{dayName}</p>
                  <p className={`text-lg font-semibold ${isToday ? 'text-blue-600' : 'text-gray-900'}`}>
                    {date.getDate()}
                  </p>
                </div>

                <div className="p-2 space-y-2">
                  {!daySchedule.is_available && (
                    <div className="bg-red-50 border border-red-200 rounded p-2 text-xs">
                      <p className="text-red-800 font-medium">Unavailable</p>
                    </div>
                  )}

                  {daySchedule.assignments && daySchedule.assignments.map((assignment) => (
                    <div
                      key={assignment.id}
                      className={`border-l-4 rounded p-2 text-xs ${getStatusColor(assignment.status)}`}
                    >
                      <div className="flex items-start gap-1 mb-1">
                        {assignment.status === 'completed' ? (
                          <CheckCircle2 className="w-3 h-3 text-green-600 mt-0.5 flex-shrink-0" />
                        ) : assignment.is_overdue ? (
                          <AlertCircle className="w-3 h-3 text-red-600 mt-0.5 flex-shrink-0" />
                        ) : (
                          <Clock className="w-3 h-3 text-gray-600 mt-0.5 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">
                            {assignment.installation_details?.customer_name}
                          </p>
                          {assignment.scheduled_start_time && (
                            <p className="text-gray-600">
                              {assignment.scheduled_start_time.substring(0, 5)}
                            </p>
                          )}
                          <p className="text-gray-500 truncate">
                            {assignment.installation_details?.installation_type_display}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}

                  {daySchedule.assignments && daySchedule.assignments.length === 0 && daySchedule.is_available && (
                    <p className="text-xs text-gray-400 text-center py-4">
                      No assignments
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p className="text-sm font-medium text-gray-700 mb-3">Status Legend</p>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-l-4 border-yellow-400 bg-yellow-50 rounded"></div>
            <span className="text-sm text-gray-600">Pending</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-l-4 border-blue-400 bg-blue-50 rounded"></div>
            <span className="text-sm text-gray-600">Confirmed</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-l-4 border-purple-400 bg-purple-50 rounded"></div>
            <span className="text-sm text-gray-600">In Progress</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-l-4 border-green-400 bg-green-50 rounded"></div>
            <span className="text-sm text-gray-600">Completed</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-l-4 border-red-400 bg-red-50 rounded"></div>
            <span className="text-sm text-gray-600">Cancelled</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BranchInstallerCalendarPage;
