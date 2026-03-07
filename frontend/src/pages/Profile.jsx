import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { users as usersApi } from '../api';
import toast from 'react-hot-toast';
import './Profile.css';

const BADGE_MAP = {
    newcomer: { emoji: '🌱', label: 'Newcomer', desc: '0-4 pickups', color: 'gray' },
    helper: { emoji: '🤝', label: 'Helper', desc: '5-19 pickups', color: 'green' },
    champion: { emoji: '🏆', label: 'Champion', desc: '20-49 pickups', color: 'amber' },
    hero: { emoji: '⭐', label: 'Hero', desc: '50+ pickups', color: 'purple' },
};

export default function Profile() {
    const { user, updateUser } = useAuth();
    const [form, setForm] = useState({ name: user?.name || '', phone: user?.phone || '', bio: user?.bio || '' });
    const [avatar, setAvatar] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const fd = new FormData();
            Object.entries(form).forEach(([k, v]) => fd.append(k, v));
            if (avatar) fd.append('avatar', avatar);
            const { data } = await usersApi.updateMe(fd);
            updateUser(data);
            toast.success('Profile updated!');
        } catch (err) {
            toast.error(err.response?.data?.error || 'Update failed');
        } finally {
            setLoading(false);
        }
    };

    const badge = BADGE_MAP[user?.badge_level] || BADGE_MAP.newcomer;

    return (
        <div className="page">
            <div className="container">
                <div className="profile-layout">
                    {/* Sidebar */}
                    <div className="profile-sidebar">
                        <div className="card card-body text-center">
                            <div className="profile-avatar">
                                {avatar
                                    ? <img src={URL.createObjectURL(avatar)} alt="preview" />
                                    : user?.avatar_url
                                        ? <img src={user.avatar_url} alt={user.name} />
                                        : <span>{user?.name?.charAt(0).toUpperCase()}</span>
                                }
                                <label className="avatar-change" htmlFor="avatar-input">📷</label>
                                <input id="avatar-input" type="file" accept="image/*" hidden
                                    onChange={e => setAvatar(e.target.files[0])} />
                            </div>
                            <h3 style={{ marginTop: 16 }}>{user?.name}</h3>
                            <p className="text-muted" style={{ fontSize: '0.85rem' }}>{user?.email}</p>

                            <div className={`badge-card badge-${badge.color} mt-16`}>
                                <div className="badge-emoji">{badge.emoji}</div>
                                <div className="badge-label">{badge.label}</div>
                                <div className="badge-desc">{badge.desc}</div>
                            </div>

                            <div className="role-display mt-16">
                                <span className="badge badge-blue">{user?.role?.replace('_', ' ')}</span>
                                {user?.is_verified && <span className="badge badge-green">✅ Verified</span>}
                            </div>

                            <div className="profile-stats mt-16">
                                <div className="prof-stat">
                                    <span className="prof-stat-val">{user?.kg_redistributed || 0}kg</span>
                                    <span className="prof-stat-label">Redistributed</span>
                                </div>
                                <div className="prof-stat">
                                    <span className="prof-stat-val">{user?.successful_pickups || 0}</span>
                                    <span className="prof-stat-label">Pickups</span>
                                </div>
                            </div>
                        </div>

                        {/* Badge progression */}
                        <div className="card card-body mt-16">
                            <h3 className="mb-12">Badge Progress</h3>
                            <div className="badge-progress">
                                {Object.entries(BADGE_MAP).map(([key, b]) => (
                                    <div key={key} className={`bp-item ${user?.badge_level === key ? 'current' : ''}`}>
                                        <span>{b.emoji}</span>
                                        <div>
                                            <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{b.label}</div>
                                            <div className="text-muted" style={{ fontSize: '0.75rem' }}>{b.desc}</div>
                                        </div>
                                        {user?.badge_level === key && <span className="badge badge-green" style={{ marginLeft: 'auto' }}>Current</span>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Main form */}
                    <div className="profile-main">
                        <div className="card card-body">
                            <h3 className="mb-20">Edit Profile</h3>
                            <form onSubmit={handleSubmit}>
                                <div className="form-group">
                                    <label className="form-label">Full name</label>
                                    <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Phone</label>
                                    <input className="form-input" value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="+1 234 567 8900" />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Bio</label>
                                    <textarea className="form-textarea" value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} placeholder="Tell the community about yourself..." />
                                </div>
                                <button type="submit" className="btn btn-primary" disabled={loading}>
                                    {loading ? <span className="spinner" style={{ width: 18, height: 18 }} /> : 'Save Changes'}
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
