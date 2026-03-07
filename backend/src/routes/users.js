const express = require('express');
const bcrypt = require('bcryptjs');
const { body, validationResult } = require('express-validator');
const { query } = require('../config/db');
const { authenticate } = require('../middleware/auth');
const { upload } = require('../config/upload');

const router = express.Router();

// GET /api/users/:id/profile — public profile
router.get('/:id/profile', async (req, res, next) => {
    try {
        const { rows } = await query(
            `SELECT id, name, badge_level, role, avatar_url, bio, successful_pickups, kg_redistributed, created_at
       FROM users WHERE id = $1 AND is_banned = FALSE`,
            [req.params.id]
        );
        if (!rows.length) return res.status(404).json({ error: 'User not found' });
        res.json(rows[0]);
    } catch (err) { next(err); }
});

// PATCH /api/users/me — update own profile
router.patch(
    '/me',
    authenticate,
    upload.single('avatar'),
    [
        body('name').optional().trim().isLength({ min: 2, max: 120 }),
        body('phone').optional().trim(),
        body('bio').optional().trim(),
    ],
    async (req, res, next) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });
            const { name, phone, bio } = req.body;
            const avatarUrl = req.file ? `/uploads/${req.file.filename}` : undefined;
            const updates = [];
            const values = [];
            let idx = 1;
            if (name) { updates.push(`name = $${idx}`); values.push(name); idx++; }
            if (phone !== undefined) { updates.push(`phone = $${idx}`); values.push(phone); idx++; }
            if (bio !== undefined) { updates.push(`bio = $${idx}`); values.push(bio); idx++; }
            if (avatarUrl) { updates.push(`avatar_url = $${idx}`); values.push(avatarUrl); idx++; }
            if (!updates.length) return res.status(400).json({ error: 'No fields to update' });
            values.push(req.user.id);
            const { rows } = await query(
                `UPDATE users SET ${updates.join(', ')} WHERE id = $${idx}
         RETURNING id, name, email, role, badge_level, avatar_url, bio, phone`,
                values
            );
            res.json(rows[0]);
        } catch (err) { next(err); }
    }
);

// POST /api/users/me/change-password
router.post('/me/change-password', authenticate,
    [body('currentPassword').notEmpty(), body('newPassword').isLength({ min: 8 }).matches(/[A-Z]/).matches(/[0-9]/)],
    async (req, res, next) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });
            const { currentPassword, newPassword } = req.body;
            const { rows } = await query('SELECT password_hash FROM users WHERE id = $1', [req.user.id]);
            const valid = await bcrypt.compare(currentPassword, rows[0].password_hash);
            if (!valid) return res.status(401).json({ error: 'Incorrect current password' });
            const hash = await bcrypt.hash(newPassword, 12);
            await query('UPDATE users SET password_hash = $1 WHERE id = $2', [hash, req.user.id]);
            res.json({ message: 'Password updated' });
        } catch (err) { next(err); }
    }
);

// POST /api/users/organizations — register an organization
router.post('/organizations', authenticate,
    [body('name').trim().isLength({ min: 2, max: 200 })],
    upload.single('document'),
    async (req, res, next) => {
        try {
            const { name, description, website } = req.body;
            const documentUrl = req.file ? `/uploads/${req.file.filename}` : null;
            const { rows } = await query(
                `INSERT INTO organizations (user_id, name, description, document_url, website)
         VALUES ($1, $2, $3, $4, $5) RETURNING *`,
                [req.user.id, name, description || null, documentUrl, website || null]
            );
            res.status(201).json(rows[0]);
        } catch (err) { next(err); }
    }
);

module.exports = router;
