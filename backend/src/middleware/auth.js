const jwt = require('jsonwebtoken');
const { query } = require('../config/db');

const authenticate = async (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({ error: 'No token provided' });
        }
        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, process.env.JWT_SECRET);

        const { rows } = await query(
            'SELECT id, name, email, role, badge_level, is_verified, is_banned FROM users WHERE id = $1',
            [decoded.userId]
        );
        if (!rows.length) return res.status(401).json({ error: 'User not found' });
        if (rows[0].is_banned) return res.status(403).json({ error: 'Account banned' });

        req.user = rows[0];
        next();
    } catch (err) {
        if (err.name === 'TokenExpiredError') {
            return res.status(401).json({ error: 'Token expired' });
        }
        return res.status(401).json({ error: 'Invalid token' });
    }
};

const requireRole = (...roles) => (req, res, next) => {
    if (!req.user) return res.status(401).json({ error: 'Unauthorized' });
    if (!roles.includes(req.user.role)) {
        return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
};

const optionalAuth = async (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;
        if (!authHeader || !authHeader.startsWith('Bearer ')) return next();
        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        const { rows } = await query('SELECT id, name, email, role, badge_level FROM users WHERE id = $1', [decoded.userId]);
        if (rows.length) req.user = rows[0];
    } catch (_) { }
    next();
};

module.exports = { authenticate, requireRole, optionalAuth };
