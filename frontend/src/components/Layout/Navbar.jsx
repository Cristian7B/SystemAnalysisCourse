import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import './Navbar.css';

const ROLE_BADGE = {
    donor: { label: 'Donor', cls: 'badge-green' },
    charity: { label: 'Charity', cls: 'badge-blue' },
    trusted_collector: { label: 'Trusted', cls: 'badge-amber' },
    general_recipient: { label: 'Recipient', cls: 'badge-gray' },
    admin: { label: 'Admin', cls: 'badge-red' },
};

const BADGE_EMOJI = { newcomer: '🌱', helper: '🤝', champion: '🏆', hero: '⭐' };

export default function Navbar() {
    const { user, logout } = useAuth();
    const { unread, notifications, markAllRead } = useNotifications();
    const [showNotifs, setShowNotifs] = useState(false);
    const [showMenu, setShowMenu] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="navbar">
            <div className="navbar-inner">
                <Link to="/" className="navbar-brand">
                    <span className="navbar-logo">🍎</span>
                    <span className="navbar-title">FoodRescue</span>
                </Link>

                <button className="navbar-burger" onClick={() => setMobileOpen(!mobileOpen)}>
                    <span /><span /><span />
                </button>

                <div className={`navbar-links ${mobileOpen ? 'open' : ''}`}>
                    <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
                        <span>🗺️</span> Map
                    </Link>
                    <Link to="/dashboard" className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}>
                        <span>📊</span> Dashboard
                    </Link>
                    {user && (
                        <Link to="/post" className={`nav-link ${isActive('/post') ? 'active' : ''}`}>
                            <span>➕</span> Post Surplus
                        </Link>
                    )}
                    {user?.role === 'admin' && (
                        <Link to="/admin" className={`nav-link ${isActive('/admin') ? 'active' : ''}`}>
                            <span>🛡️</span> Admin
                        </Link>
                    )}
                </div>

                <div className="navbar-actions">
                    {user ? (
                        <>
                            {/* Notifications */}
                            <div className="notif-wrapper">
                                <button
                                    className="notif-btn"
                                    onClick={() => { setShowNotifs(!showNotifs); if (!showNotifs) markAllRead(); }}
                                >
                                    🔔
                                    {unread > 0 && <span className="notif-badge">{unread > 9 ? '9+' : unread}</span>}
                                </button>
                                {showNotifs && (
                                    <div className="notif-dropdown">
                                        <div className="notif-header">
                                            <span>Notifications</span>
                                            <button className="btn btn-ghost btn-sm" onClick={markAllRead}>Mark all read</button>
                                        </div>
                                        <div className="notif-list">
                                            {notifications.length === 0 && (
                                                <div className="notif-empty">No notifications yet</div>
                                            )}
                                            {notifications.slice(0, 10).map(n => (
                                                <div key={n.id} className={`notif-item ${!n.is_read ? 'unread' : ''}`}>
                                                    <div className="notif-item-title">{n.title}</div>
                                                    <div className="notif-item-body">{n.body}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* User menu */}
                            <div className="user-menu-wrapper">
                                <button className="user-btn" onClick={() => setShowMenu(!showMenu)}>
                                    <div className="user-avatar">
                                        {user.avatar_url
                                            ? <img src={user.avatar_url} alt={user.name} />
                                            : user.name.charAt(0).toUpperCase()}
                                    </div>
                                    <div className="user-info">
                                        <span className="user-name">{user.name}</span>
                                        <span className={`badge ${ROLE_BADGE[user.role]?.cls}`}>
                                            {BADGE_EMOJI[user.badge_level]} {ROLE_BADGE[user.role]?.label}
                                        </span>
                                    </div>
                                    <span className="chevron">▾</span>
                                </button>
                                {showMenu && (
                                    <div className="user-dropdown">
                                        <Link to="/profile" className="dropdown-item" onClick={() => setShowMenu(false)}>👤 Profile</Link>
                                        <Link to="/my-claims" className="dropdown-item" onClick={() => setShowMenu(false)}>📦 My Claims</Link>
                                        <hr className="dropdown-divider" />
                                        <button className="dropdown-item text-danger" onClick={handleLogout}>🚪 Sign Out</button>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="auth-btns">
                            <Link to="/login" className="btn btn-ghost btn-sm">Sign In</Link>
                            <Link to="/register" className="btn btn-primary btn-sm">Get Started</Link>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}
