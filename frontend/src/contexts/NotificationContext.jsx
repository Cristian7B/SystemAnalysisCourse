import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { notifications as notifApi } from '../api';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [unread, setUnread] = useState(0);

    const fetchNotifications = useCallback(async () => {
        if (!user) return;
        try {
            const { data } = await notifApi.list();
            setNotifications(data.notifications);
            setUnread(data.unread);
        } catch (_) { }
    }, [user]);

    useEffect(() => {
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, [fetchNotifications]);

    const markAllRead = async () => {
        await notifApi.readAll();
        setUnread(0);
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    };

    const addNotification = (notif) => {
        setNotifications(prev => [notif, ...prev]);
        setUnread(prev => prev + 1);
    };

    return (
        <NotificationContext.Provider value={{ notifications, unread, fetchNotifications, markAllRead, addNotification }}>
            {children}
        </NotificationContext.Provider>
    );
};

export const useNotifications = () => useContext(NotificationContext);
