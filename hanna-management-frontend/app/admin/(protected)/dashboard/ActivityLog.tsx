'use client';

import { FiUsers, FiZap, FiAlertCircle, FiShield } from 'react-icons/fi';
import { ActivityLogItem } from './page'; // Import type from the main page

const iconMap: { [key: string]: React.ElementType } = {
  FiUsers,
  FiZap,
  FiAlertCircle,
  FiShield,
};

const ActivityItem = ({ item }: { item: ActivityLogItem }) => {
  const Icon = iconMap[item.iconName] || FiAlertCircle;
  const timeAgo = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <li className="flex items-start space-x-4 py-3">
      <div className={`p-2 rounded-full bg-gray-100 ${item.iconColor}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1">
        <p className="text-sm text-gray-800">{item.text}</p>
        <p className="text-xs text-gray-500">{timeAgo}</p>
      </div>
    </li>
  );
};

export const ActivityLog = ({ activities }: { activities: ActivityLogItem[] }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200 h-full">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
      <ul className="divide-y divide-gray-200">
        {activities.map((item) => (
          <ActivityItem key={item.id} item={item} />
        ))}
      </ul>
    </div>
  );
};