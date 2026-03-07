import { useState, useEffect } from 'react';
import { claims as claimsApi } from '../api';
import toast from 'react-hot-toast';
import './MyClaims.css';

const STATUS_BADGE = {
    pending: 'badge-amber',
    confirmed: 'badge-blue',
    completed: 'badge-green',
    cancelled: 'badge-gray',
    no_show: 'badge-red',
};

export default function MyClaims() {
    const [claims, setClaims] = useState([]);
    const [incoming, setIncoming] = useState([]);
    const [tab, setTab] = useState('mine');
    const [loading, setLoading] = useState(true);

    const fetchClaims = async () => {
        setLoading(true);
        try {
            const [mine, inc] = await Promise.all([claimsApi.list(), claimsApi.incoming()]);
            setClaims(mine.data.claims);
            setIncoming(inc.data.claims);
        } catch { toast.error('Failed to load claims'); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchClaims(); }, []);

    const handleAction = async (action, claimId) => {
        try {
            if (action === 'complete') await claimsApi.complete(claimId);
            else if (action === 'confirm') await claimsApi.confirm(claimId);
            else if (action === 'cancel') await claimsApi.cancel(claimId);
            toast.success('Done!');
            fetchClaims();
        } catch (err) { toast.error(err.response?.data?.error || 'Action failed'); }
    };

    const renderClaims = (list, isIncoming) => (
        <div className="claims-list">
            {list.length === 0 && <p className="text-muted">No claims yet.</p>}
            {list.map(claim => (
                <div key={claim.id} className="claim-card card card-body">
                    <div className="claim-header">
                        <div>
                            <h4 className="claim-title">{claim.title}</h4>
                            <span className="text-muted">{claim.category?.replace('_', ' ')} · {claim.quantity_kg}kg</span>
                        </div>
                        <div className="claim-badges">
                            <span className={`badge ${STATUS_BADGE[claim.status] || 'badge-gray'}`}>{claim.status}</span>
                            <span className="badge badge-purple">{claim.window_type}</span>
                        </div>
                    </div>
                    <div className="claim-meta">
                        {isIncoming
                            ? <span>👤 {claim.claimant_name} · <span className={`badge badge-gray`}>{claim.claimant_role}</span></span>
                            : <span>🏪 By {claim.donor_name}</span>
                        }
                        <span>🕐 Pickup: {new Date(claim.pickup_start).toLocaleDateString()} — {new Date(claim.pickup_end).toLocaleDateString()}</span>
                    </div>
                    <div className="claim-actions">
                        {isIncoming && claim.status === 'pending' && (
                            <>
                                <button className="btn btn-primary btn-sm" onClick={() => handleAction('confirm', claim.id)}>✅ Confirm Pickup</button>
                                <button className="btn btn-secondary btn-sm" onClick={() => handleAction('cancel', claim.id)}>Cancel</button>
                            </>
                        )}
                        {isIncoming && claim.status === 'confirmed' && (
                            <button className="btn btn-primary btn-sm" onClick={() => handleAction('complete', claim.id)}>✅ Mark Completed</button>
                        )}
                        {!isIncoming && claim.status === 'pending' && (
                            <button className="btn btn-danger btn-sm" onClick={() => handleAction('cancel', claim.id)}>Cancel Claim</button>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );

    return (
        <div className="page">
            <div className="container">
                <h1 style={{ marginBottom: 8 }}>📦 Claims</h1>
                <p className="text-muted mb-24">Manage your surplus claims and incoming requests</p>

                <div className="admin-tabs">
                    <button className={`tab-btn ${tab === 'mine' ? 'active' : ''}`} onClick={() => setTab('mine')}>
                        My Claims ({claims.length})
                    </button>
                    <button className={`tab-btn ${tab === 'incoming' ? 'active' : ''}`} onClick={() => setTab('incoming')}>
                        Incoming ({incoming.length})
                    </button>
                </div>

                {loading
                    ? <div className="flex-center" style={{ padding: 40 }}><div className="spinner" /></div>
                    : tab === 'mine'
                        ? renderClaims(claims, false)
                        : renderClaims(incoming, true)
                }
            </div>
        </div>
    );
}
