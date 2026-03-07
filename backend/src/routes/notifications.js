const express = require('express');
const { query } = require('../config/db');
const { authenticate } = require('../middleware/auth');

const router = express.Router();

// GET /api/notifications — my notifications
router.get('/', authenticate, async (req, res, next) => {
    try {
        const { rows } = await query(
            `SELECT * FROM notifications WHERE user_id = $1 ORDER BY created_at DESC LIMIT 50`,
            [req.user.id]
        );
        const unread = rows.filter(n => !n.is_read).length;
        res.json({ notifications: rows, unread });
    } catch (err) { next(err); }
});

// PATCH /api/notifications/read-all
router.patch('/read-all', authenticate, async (req, res, next) => {
    try {
        await query('UPDATE notifications SET is_read = TRUE WHERE user_id = $1', [req.user.id]);
        res.json({ message: 'All marked as read' });
    } catch (err) { next(err); }
});

// PATCH /api/notifications/:id/read
router.patch('/:id/read', authenticate, async (req, res, next) => {
    try {
        await query(
            'UPDATE notifications SET is_read = TRUE WHERE id = $1 AND user_id = $2',
            [req.params.id, req.user.id]
        );
        res.json({ message: 'Marked as read' });
    } catch (err) { next(err); }
});

// POST /api/notifications/subscribe — save push subscription
router.post('/subscribe', authenticate, async (req, res, next) => {
    try {
        const { endpoint, keys } = req.body;
        if (!endpoint || !keys) return res.status(400).json({ error: 'Invalid subscription' });
        await query(
            `INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (endpoint) DO UPDATE SET p256dh = $3, auth = $4`,
            [req.user.id, endpoint, keys.p256dh, keys.auth]
        );
        res.status(201).json({ message: 'Subscribed' });
    } catch (err) { next(err); }
});

// GET /api/notifications/vapid-key
router.get('/vapid-key', (req, res) => {
    res.json({ publicKey: process.env.VAPID_PUBLIC_KEY });
});

module.exports = router;
