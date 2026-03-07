import { useEffect, useState } from 'react';
import { metrics as metricsApi } from '../api';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend,
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import './Dashboard.css';

const BADGE_EMOJI = { newcomer: '🌱', helper: '🤝', champion: '🏆', hero: '⭐' };
const CATEGORY_COLORS = ['#22c55e', '#f59e0b', '#3b82f6', '#8b5cf6', '#06b6d4', '#ec4899', '#60a5fa', '#94a3b8'];

export default function Dashboard() {
    const { user } = useAuth();
    const [platform, setPlatform] = useState(null);
    const [timeseries, setTimeseries] = useState([]);
    const [categories, setCategories] = useState([]);
    const [leaderboard, setLeaderboard] = useState([]);
    const [userMetrics, setUserMetrics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            metricsApi.platform(),
            metricsApi.timeseries(),
            metricsApi.categories(),
            metricsApi.leaderboard(),
            user ? metricsApi.user() : Promise.resolve(null),
        ]).then(([p, ts, cats, lb, um]) => {
            setPlatform(p.data);
            setTimeseries(ts.data.data);
            setCategories(cats.data.data);
            setLeaderboard(lb.data.leaderboard);
            if (um) setUserMetrics(um.data);
        }).catch(console.error)
            .finally(() => setLoading(false));
    }, [user]);

    if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

    return (
        <div className="page">
            <div className="container">
                <div className="dashboard-header">
                    <h1>Impact Dashboard</h1>
                    <p>Measuring the difference we make together</p>
                </div>

                {/* Platform stats */}
                <div className="grid-4 mb-24">
                    {[
                        { label: 'kg Redistributed', value: platform?.total_kg ?? 0, icon: '⚖️', color: 'green' },
                        { label: 'Successful Pickups', value: platform?.total_pickups ?? 0, icon: '🤝', color: 'blue' },
                        { label: 'Active Donors', value: platform?.total_donors ?? 0, icon: '🎁', color: 'amber' },
                        { label: 'Success Rate', value: `${platform?.success_rate_pct ?? 0}%`, icon: '📈', color: 'purple' },
                    ].map(stat => (
                        <div key={stat.label} className={`stat-card card card-body stat-${stat.color}`}>
                            <div className="stat-icon">{stat.icon}</div>
                            <div className="stat-value">{stat.value}</div>
                            <div className="stat-label">{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* Personal stats */}
                {user && userMetrics && (
                    <div className="card card-body mb-24">
                        <div className="flex-between mb-16">
                            <h3>Your Impact</h3>
                            <span className="badge badge-green">
                                {BADGE_EMOJI[user.badge_level]} {user.badge_level}
                            </span>
                        </div>
                        <div className="grid-4">
                            <div className="user-stat"><span className="user-stat-val">{userMetrics.kg_redistributed}kg</span><span className="user-stat-label">Redistributed</span></div>
                            <div className="user-stat"><span className="user-stat-val">{userMetrics.successful_pickups}</span><span className="user-stat-label">Pickups</span></div>
                            <div className="user-stat"><span className="user-stat-val">{userMetrics.posts_count}</span><span className="user-stat-label">Posts</span></div>
                            <div className="user-stat"><span className="user-stat-val">{userMetrics.claims_completed}</span><span className="user-stat-label">Claims Done</span></div>
                        </div>
                    </div>
                )}

                <div className="grid-2 mb-24">
                    {/* Timeseries chart */}
                    <div className="card card-body">
                        <h3 className="mb-16">kg Redistributed (Last 30 Days)</h3>
                        {timeseries.length > 0 ? (
                            <ResponsiveContainer width="100%" height={220}>
                                <LineChart data={timeseries}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                                    <Tooltip
                                        contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)', borderRadius: 8, color: 'var(--text-primary)' }}
                                    />
                                    <Line type="monotone" dataKey="kg" stroke="#22c55e" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="chart-empty">No data yet — start redistributing food!</div>
                        )}
                    </div>

                    {/* Category breakdown */}
                    <div className="card card-body">
                        <h3 className="mb-16">By Category</h3>
                        {categories.length > 0 ? (
                            <ResponsiveContainer width="100%" height={220}>
                                <PieChart>
                                    <Pie data={categories} dataKey="count" nameKey="category" cx="50%" cy="50%" outerRadius={80} label={({ category }) => category}>
                                        {categories.map((_, i) => (
                                            <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-color)', borderRadius: 8 }} />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="chart-empty">No data yet</div>
                        )}
                    </div>
                </div>

                {/* Leaderboard */}
                <div className="card card-body">
                    <h3 className="mb-16">🏆 Community Leaderboard</h3>
                    {leaderboard.length === 0
                        ? <p className="text-muted">No pickups yet. Be the first!</p>
                        : (
                            <div className="leaderboard">
                                {leaderboard.map((user, i) => (
                                    <div key={i} className={`leaderboard-row ${i < 3 ? `top-${i + 1}` : ''}`}>
                                        <span className="lb-rank">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`}</span>
                                        <span className="lb-name">{user.name}</span>
                                        <span className={`badge ${['badge-green', 'badge-amber', 'badge-blue', 'badge-gray'][['newcomer', 'helper', 'champion', 'hero'].indexOf(user.badge_level)] || 'badge-gray'}`}>
                                            {BADGE_EMOJI[user.badge_level]} {user.badge_level}
                                        </span>
                                        <span className="lb-kg">{user.kg_redistributed}kg</span>
                                        <span className="text-muted">{user.successful_pickups} pickups</span>
                                    </div>
                                ))}
                            </div>
                        )}
                </div>
            </div>
        </div>
    );
}
