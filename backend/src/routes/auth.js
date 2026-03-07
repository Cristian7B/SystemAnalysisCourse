const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const { query } = require('../config/db');
const { authenticate } = require('../middleware/auth');
const { notifyUser } = require('../services/notificationService');

const router = express.Router();

const generateTokens = (userId) => {
    const accessToken = jwt.sign({ userId }, process.env.JWT_SECRET, {
        expiresIn: process.env.JWT_EXPIRES_IN || '15m',
    });
    const refreshToken = jwt.sign({ userId }, process.env.JWT_REFRESH_SECRET, {
        expiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
    });
    return { accessToken, refreshToken };
};

// POST /api/auth/register
router.post(
    '/register',
    [
        body('name').trim().isLength({ min: 2, max: 120 }),
        body('email').isEmail().normalizeEmail(),
        body('password').isLength({ min: 8 }).matches(/[A-Z]/).matches(/[0-9]/),
        body('role').isIn(['donor', 'charity', 'trusted_collector', 'general_recipient']),
    ],
    async (req, res, next) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

            const { name, email, password, role, phone, bio } = req.body;

            const existing = await query('SELECT id FROM users WHERE email = $1', [email]);
            if (existing.rows.length) return res.status(409).json({ error: 'Email already registered' });

            const hash = await bcrypt.hash(password, 12);
            const { rows } = await query(
                `INSERT INTO users (name, email, password_hash, role, phone, bio)
         VALUES ($1, $2, $3, $4, $5, $6)
         RETURNING id, name, email, role, badge_level, is_verified`,
                [name, email, hash, role, phone || null, bio || null]
            );

            const user = rows[0];
            const { accessToken, refreshToken } = generateTokens(user.id);
            await query('UPDATE users SET refresh_token = $1 WHERE id = $2', [refreshToken, user.id]);

            res.status(201).json({ user, accessToken, refreshToken });
        } catch (err) {
            next(err);
        }
    }
);

// POST /api/auth/login
router.post(
    '/login',
    [body('email').isEmail().normalizeEmail(), body('password').notEmpty()],
    async (req, res, next) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

            const { email, password } = req.body;
            const { rows } = await query('SELECT * FROM users WHERE email = $1', [email]);
            if (!rows.length) return res.status(401).json({ error: 'Invalid credentials' });

            const user = rows[0];
            if (user.is_banned) return res.status(403).json({ error: 'Account banned' });

            const valid = await bcrypt.compare(password, user.password_hash);
            if (!valid) return res.status(401).json({ error: 'Invalid credentials' });

            const { accessToken, refreshToken } = generateTokens(user.id);
            await query('UPDATE users SET refresh_token = $1 WHERE id = $2', [refreshToken, user.id]);

            const { password_hash, refresh_token, ...safeUser } = user;
            res.json({ user: safeUser, accessToken, refreshToken });
        } catch (err) {
            next(err);
        }
    }
);

// POST /api/auth/refresh
router.post('/refresh', async (req, res, next) => {
    try {
        const { refreshToken } = req.body;
        if (!refreshToken) return res.status(401).json({ error: 'No refresh token' });

        const decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET);
        const { rows } = await query('SELECT * FROM users WHERE id = $1 AND refresh_token = $2', [
            decoded.userId,
            refreshToken,
        ]);
        if (!rows.length) return res.status(401).json({ error: 'Invalid refresh token' });

        const tokens = generateTokens(decoded.userId);
        await query('UPDATE users SET refresh_token = $1 WHERE id = $2', [tokens.refreshToken, decoded.userId]);
        res.json(tokens);
    } catch (err) {
        res.status(401).json({ error: 'Invalid or expired refresh token' });
    }
});

// POST /api/auth/logout
router.post('/logout', authenticate, async (req, res, next) => {
    try {
        await query('UPDATE users SET refresh_token = NULL WHERE id = $1', [req.user.id]);
        res.json({ message: 'Logged out successfully' });
    } catch (err) {
        next(err);
    }
});

// GET /api/auth/me
router.get('/me', authenticate, async (req, res) => {
    res.json({ user: req.user });
});

module.exports = router;
