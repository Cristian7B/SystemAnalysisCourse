import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import './Auth.css';

const ROLES = [
    { value: 'donor', emoji: '🎁', label: 'Donor', desc: 'Share surplus food with your community' },
    { value: 'general_recipient', emoji: '🤝', label: 'Recipient', desc: 'Get food from donors and organizations' },
    { value: 'charity', emoji: '🏥', label: 'Organization', desc: 'Verified charity with priority access' },
];

export default function Register() {
    const { register } = useAuth();
    const navigate = useNavigate();
    const [form, setForm] = useState({ name: '', email: '', password: '', role: 'general_recipient' });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await register(form);
            toast.success('Account created! Welcome to FoodRescue 🎉');
            navigate('/');
        } catch (err) {
            toast.error(err.response?.data?.error || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card card" style={{ maxWidth: 520 }}>
                <div className="auth-logo">🍎</div>
                <h2 className="auth-title">Join FoodRescue</h2>
                <p className="auth-sub">Create an account and start making a difference</p>

                {/* Role selector */}
                <div className="role-grid">
                    {ROLES.map(r => (
                        <button
                            key={r.value}
                            type="button"
                            className={`role-card ${form.role === r.value ? 'selected' : ''}`}
                            onClick={() => setForm({ ...form, role: r.value })}
                        >
                            <span className="role-emoji">{r.emoji}</span>
                            <span className="role-label">{r.label}</span>
                            <span className="role-desc">{r.desc}</span>
                        </button>
                    ))}
                </div>

                <form onSubmit={handleSubmit} className="auth-form" style={{ marginTop: 20 }}>
                    <div className="form-group">
                        <label className="form-label">Full name</label>
                        <input
                            type="text" className="form-input" required
                            value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                            placeholder="Jane Smith"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Email address</label>
                        <input
                            type="email" className="form-input" required
                            value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
                            placeholder="you@example.com"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Password <span className="text-muted">(8+ chars, uppercase + number)</span></label>
                        <input
                            type="password" className="form-input" required
                            value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
                            placeholder="••••••••"
                        />
                    </div>
                    <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
                        {loading ? <span className="spinner" style={{ width: 20, height: 20 }} /> : 'Create Account'}
                    </button>
                </form>

                <p className="auth-switch">
                    Already have an account? <Link to="/login">Sign in</Link>
                </p>
            </div>
        </div>
    );
}
