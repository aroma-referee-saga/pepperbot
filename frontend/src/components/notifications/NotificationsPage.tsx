import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../services/api';

interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  discount_id?: number;
  is_read: boolean;
  created_at: string;
}

const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const fetchNotifications = async () => {
    try {
      const params: any = { limit: 50 };
      if (filter === 'unread') {
        params.unread_only = true;
      }

      const response = await apiClient.getNotifications(params);
      setNotifications(response.data);
    } catch (err: any) {
      setError('Failed to load notifications');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      await apiClient.markNotificationRead(notificationId);
      setNotifications(notifications.map(notification =>
        notification.id === notificationId
          ? { ...notification, is_read: true }
          : notification
      ));
    } catch (err: any) {
      setError('Failed to mark notification as read');
      console.error(err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      const unreadNotifications = notifications.filter(n => !n.is_read);
      await Promise.all(
        unreadNotifications.map(notification =>
          apiClient.markNotificationRead(notification.id)
        )
      );
      setNotifications(notifications.map(notification => ({
        ...notification,
        is_read: true
      })));
    } catch (err: any) {
      setError('Failed to mark all notifications as read');
      console.error(err);
    }
  };

  const handleDeleteNotification = async (notificationId: number) => {
    if (!confirm('Are you sure you want to delete this notification?')) return;

    try {
      await apiClient.deleteNotification(notificationId);
      setNotifications(notifications.filter(notification => notification.id !== notificationId));
    } catch (err: any) {
      setError('Failed to delete notification');
      console.error(err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'discount':
        return '🛍️';
      case 'reminder':
        return '⏰';
      case 'alert':
        return '🚨';
      case 'info':
        return 'ℹ️';
      default:
        return '📢';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'discount':
        return 'bg-green-100 text-green-800';
      case 'reminder':
        return 'bg-yellow-100 text-yellow-800';
      case 'alert':
        return 'bg-red-100 text-red-800';
      case 'info':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'unread') return !notification.is_read;
    if (filter === 'read') return notification.is_read;
    return true;
  });

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-gray-600 hover:text-gray-900 mr-4"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Notifications</h1>
            </div>
            {unreadCount > 0 && (
              <div className="flex items-center">
                <button
                  onClick={handleMarkAllAsRead}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Mark All as Read
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Error message */}
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Filter Tabs */}
          <div className="bg-white rounded-lg shadow mb-6">
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6" aria-label="Tabs">
                <button
                  onClick={() => setFilter('all')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    filter === 'all'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  All ({notifications.length})
                </button>
                <button
                  onClick={() => setFilter('unread')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    filter === 'unread'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Unread ({unreadCount})
                </button>
                <button
                  onClick={() => setFilter('read')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    filter === 'read'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Read ({notifications.filter(n => n.is_read).length})
                </button>
              </nav>
            </div>
          </div>

          {/* Notifications List */}
          {filteredNotifications.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM4.868 12.683A17.925 17.925 0 0112 21c7.962 0 12-1.21 12-2.683m-12 2.683a17.925 17.925 0 01-7.132-8.317M12 21c4.411 0 8-4.03 8-9s-3.589-9-8-9-8 4.03-8 9a9.06 9.06 0 001.832 5.445L4 21l7.132-2.317z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {filter === 'unread' ? 'No unread notifications' : 'No notifications'}
              </h3>
              <p className="text-gray-600">
                {filter === 'unread'
                  ? 'You have read all your notifications.'
                  : 'You don\'t have any notifications yet.'
                }
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`bg-white rounded-lg shadow p-6 ${
                    !notification.is_read ? 'border-l-4 border-indigo-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      {/* Notification Icon */}
                      <div className="flex-shrink-0">
                        <div className="text-2xl">{getNotificationIcon(notification.type)}</div>
                      </div>

                      {/* Notification Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {notification.title}
                          </h3>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getNotificationColor(notification.type)}`}>
                            {notification.type}
                          </span>
                          {!notification.is_read && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                              New
                            </span>
                          )}
                        </div>

                        <p className="text-gray-600 mb-3">{notification.message}</p>

                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-500">
                            {formatDate(notification.created_at)}
                          </span>

                          <div className="flex space-x-2">
                            {!notification.is_read && (
                              <button
                                onClick={() => handleMarkAsRead(notification.id)}
                                className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                              >
                                Mark as Read
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteNotification(notification.id)}
                              className="text-red-600 hover:text-red-800 text-sm font-medium"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default NotificationsPage;