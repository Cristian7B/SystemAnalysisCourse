import { useState, useEffect } from 'react';
import { admin as adminApi } from '../api';
import toast from 'react-hot-toast';
import './Admin.css';

const TABS = ['Users', 'Organizations', 'Posts', 'Logs'];

export default function Admin() {
    const [tab, setTab] = useState('Users');
    const [users, setUsers] = useState([]);
    const [orgs, setOrgs] = useState([]);
    const [posts, setPosts] = useState([]);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState('');

    const fetchData = async () => {
        setLoading(true);
        try {
            if (tab === 'Users') {
                const { data } = await adminApi.users({ search });
                setUsers(data.users);
            } else if (tab === 'Organizations') {
                const { data } = await adminApi.organizations({ verified: 'false' });
                setOrgs(data.organizations);
            } else if (tab === 'Posts') {
                const { data } = await adminApi.surplusAll();
                setPosts(data.items);
            } else if (tab === 'Logs') {
                const { data } = await adminApi.logs();
                setLogs(data.logs);
            }
        } catch (err) { toast.error('Failed to load data'); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchData(); }, [tab]);

    const handleBan = async (userId, currentBanned) => {
        try {
            await adminApi.banUser(userId, { ban: !currentBanned });
            toast.success(currentBanned ? 'User unbanned' : 'User banned');
            fetchData();
        } catch { toast.error('Action failed'); }
    };

    const handleVerifyOrg = async (orgId, approve) => {
        const note = approve ? '' : prompt('Reason for rejection:') || '';
        try {
            await adminApi.verifyOrg(orgId, { approve, note });
            toast.success(approve ? 'Organization verified!' : 'Rejected');
            fetchData();
        } catch { toast.error('Action failed'); }
    };

    const handleRemovePost = async (postId) => {
        if (!confirm('Remove this post?')) return;
        try {
            await adminApi.removeSurplus(postId, { note: 'Removed by admin' });
            toast.success('Post removed');
            fetchData();
        } catch { toast.error('Action failed'); }
    };

    return (
        <div className="page">
            <div className="container">
                <div className="admin-header">
                    <h1>🛡️ Admin Panel</h1>
                    <p>Moderation tools and platform management</p>
                </div>

                <div className="admin-tabs">
                    {TABS.map(t => (
                        <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
                            {t === 'Organizations' && orgs.length > 0 && tab !== 'Organizations'
                                ? `${t} (${orgs.length} pending)` : t}
                        </button>
                    ))}
                </div>

                {loading && <div className="flex-center" style={{ padding: '40px' }}><div className="spinner" /></div>}

                {/* USERS */}
                {tab === 'Users' && !loading && (
                    <div className="card card-body">
                        <div className="flex-between mb-16">
                            <h3>User Management</h3>
                            <input className="form-input" style={{ width: 240 }} placeholder="Search by name/email..."
                                value={search} onChange={e => setSearch(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && fetchData()} />
                        </div>
                        <div className="admin-table">
                            <div className="table-header">
                                <span>Name</span><span>Email</span><span>Role</span><span>Badge</span><span>Pickups</span><span>Actions</span>
                            </div>
                            {users.map(u => (
                                <div key={u.id} className={`table-row ${u.is_banned ? 'banned' : ''}`}>
                                    <span className="font-bold">{u.name}</span>
                                    <span className="text-muted">{u.email}</span>
                                    <span><span className="badge badge-blue">{u.role}</span></span>
                                    <span>{u.badge_level}</span>
                                    <span>{u.successful_pickups}</span>
                                    <span className="row-actions">
                                        <button
                                            className={`btn btn-sm ${u.is_banned ? 'btn-secondary' : 'btn-danger'}`}
                                            onClick={() => handleBan(u.id, u.is_banned)}
                                        >
                                            {u.is_banned ? 'Unban' : 'Ban'}
                                        </button>
                                    </span>
                                </div>
                            ))}
                            {users.length === 0 && <p className="text-muted" style={{ padding: 24 }}>No users found</p>}
                        </div>
                    </div>
                )}

                {/* ORGANIZATIONS */}
                {tab === 'Organizations' && !loading && (
                    <div className="card card-body">
                        <h3 className="mb-16">Pending Verifications</h3>
                        {orgs.length === 0
                            ? <p className="text-muted">No pending verifications 🎉</p>
                            : orgs.map(org => (
                                <div key={org.id} className="org-card">
                                    <div className="org-header">
                                        <div>
                                            <h4>{org.name}</h4>
                                            <span className="text-muted">{org.owner_name} — {org.owner_email}</span>
                                        </div>
                                        <span className="badge badge-amber">Pending</span>
                                    </div>
                                    {org.description && <p style={{ margin: '8px 0' }}>{org.description}</p>}
                                    {org.document_url && (
                                        <a href={org.document_url} target="_blank" rel="noreferrer" className="btn btn-secondary btn-sm">
                                            📄 View Document
                                        </a>
                                    )}
                                    <div className="org-actions">
                                        <button className="btn btn-primary btn-sm" onClick={() => handleVerifyOrg(org.id, true)}>✅ Approve</button>
                                        <button className="btn btn-danger btn-sm" onClick={() => handleVerifyOrg(org.id, false)}>❌ Reject</button>
                                    </div>
                                </div>
                            ))}
                    </div>
                )}

                {/* POSTS */}
                {tab === 'Posts' && !loading && (
                    <div className="card card-body">
                        <h3 className="mb-16">All Surplus Posts</h3>
                        <div className="admin-table">
                            <div className="table-header">
                                <span>Title</span><span>Donor</span><span>Category</span><span>Status</span><span>Action</span>
                            </div>
                            {posts.map(p => (
                                <div key={p.id} className={`table-row ${p.status === 'removed' ? 'banned' : ''}`}>
                                    <span className="font-bold">{p.title}</span>
                                    <span className="text-muted">{p.donor_name}</span>
                                    <span className="badge badge-gray">{p.category}</span>
                                    <span><span className={`badge ${p.status === 'available' ? 'badge-green' : p.status === 'completed' ? 'badge-blue' : 'badge-gray'}`}>{p.status}</span></span>
                                    <span>
                                        {p.status !== 'removed' && (
                                            <button className="btn btn-danger btn-sm" onClick={() => handleRemovePost(p.id)}>Remove</button>
                                        )}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* LOGS */}
                {tab === 'Logs' && !loading && (
                    <div className="card card-body">
                        <h3 className="mb-16">Moderation Audit Log</h3>
                        <div className="admin-table">
                            <div className="table-header">
                                <span>Admin</span><span>Action</span><span>Target</span><span>Note</span><span>Date</span>
                            </div>
                            {logs.map(l => (
                                <div key={l.id} className="table-row">
                                    <span className="font-bold">{l.admin_name}</span>
                                    <span><span className="badge badge-blue">{l.action}</span></span>
                                    <span className="text-muted">{l.target_type}</span>
                                    <span className="text-muted">{l.note || '—'}</span>
                                    <span className="text-muted">{new Date(l.created_at).toLocaleDateString()}</span>
                                </div>
                            ))}
                            {logs.length === 0 && <p className="text-muted" style={{ padding: 24 }}>No actions logged yet</p>}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
