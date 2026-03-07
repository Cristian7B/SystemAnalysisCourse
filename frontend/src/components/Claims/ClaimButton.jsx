import { useState } from 'react';
import { claims as claimsApi } from '../../api';
import toast from 'react-hot-toast';
import { useAuth } from '../../contexts/AuthContext';

export default function ClaimButton({ item, onSuccess }) {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);

    const now = new Date();
    const charityEnd = new Date(item.charity_window_end);
    const trustedEnd = new Date(item.trusted_window_end);

    const canClaim = () => {
        if (!user) return false;
        if (user.role === 'charity') return now <= charityEnd;
        if (user.role === 'trusted_collector') return now <= trustedEnd;
        return now > trustedEnd;
    };

    const windowMsg = () => {
        if (user?.role === 'general_recipient' && now <= trustedEnd) {
            const mins = Math.round((trustedEnd - now) / 60000);
            return `Available in ~${mins}m`;
        }
        if (user?.role === 'trusted_collector' && now <= charityEnd && user.role !== 'charity') {
            const mins = Math.round((charityEnd - now) / 60000);
            return `Open to you in ~${mins}m`;
        }
        return null;
    };

    const handleClaim = async () => {
        setLoading(true);
        try {
            await claimsApi.create(item.id);
            toast.success('Item claimed! The donor will confirm your pickup.');
            onSuccess?.();
        } catch (err) {
            toast.error(err.response?.data?.error || 'Failed to claim item');
        } finally {
            setLoading(false);
        }
    };

    const waitMsg = windowMsg();
    if (waitMsg) return <span className="badge badge-amber">{waitMsg}</span>;

    return (
        <button
            className="btn btn-primary btn-sm"
            onClick={handleClaim}
            disabled={loading || !canClaim() || item.status !== 'available'}
        >
            {loading ? '...' : item.status === 'available' ? '📦 Claim' : '✅ Claimed'}
        </button>
    );
}
