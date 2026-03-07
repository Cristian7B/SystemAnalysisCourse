const express = require('express');
const { query } = require('../config/db');
const { authenticate, requireRole } = require('../middleware/auth');
const { notifyUser } = require('../services/notificationService');

const router = express.Router();

// GET /api/admin/users — list all users
router.get('/users', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { role, search, limit = 50, offset = 0 } = req.query;
        let sql = `SELECT id, name, email, role, badge_level, is_verified, is_banned, successful_pickups, kg_redistributed, created_at FROM users WHERE 1=1`;
        const params = [];
        let idx = 1;
        if (role) { sql += ` AND role = $${idx}`; params.push(role); idx++; }
        if (search) { sql += ` AND (name ILIKE $${idx} OR email ILIKE $${idx})`; params.push(`%${search}%`); idx++; }
        sql += ` ORDER BY created_at DESC LIMIT $${idx} OFFSET $${idx + 1}`;
        params.push(parseInt(limit), parseInt(offset));
        const { rows } = await query(sql, params);
        res.json({ users: rows });
    } catch (err) { next(err); }
});

// PATCH /api/admin/users/:id/ban
router.patch('/users/:id/ban', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { ban, note } = req.body;
        await query('UPDATE users SET is_banned = $1 WHERE id = $2', [ban !== false, req.params.id]);
        await query(
            `INSERT INTO moderation_logs (admin_id, action, target_type, target_id, note)
       VALUES ($1, $2, 'user', $3, $4)`,
            [req.user.id, ban !== false ? 'ban_user' : 'unban_user', req.params.id, note || null]
        );
        await notifyUser(req.params.id, {
            type: 'user_banned',
            title: ban !== false ? 'Account Suspended' : 'Account Reinstated',
            body: ban !== false ? 'Your account has been suspended by an admin.' : 'Your account has been reinstated.',
            payload: {},
        });
        res.json({ message: ban !== false ? 'User banned' : 'User unbanned' });
    } catch (err) { next(err); }
});

// PATCH /api/admin/users/:id/role
router.patch('/users/:id/role', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { role, note } = req.body;
        const validRoles = ['donor', 'charity', 'trusted_collector', 'general_recipient'];
        if (!validRoles.includes(role)) return res.status(400).json({ error: 'Invalid role' });
        await query('UPDATE users SET role = $1 WHERE id = $2', [role, req.params.id]);
        await query(
            `INSERT INTO moderation_logs (admin_id, action, target_type, target_id, note)
       VALUES ($1, 'upgrade_role', 'user', $2, $3)`,
            [req.user.id, req.params.id, note || null]
        );
        res.json({ message: 'Role updated' });
    } catch (err) { next(err); }
});

// GET /api/admin/organizations — pending verifications
router.get('/organizations', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { verified } = req.query;
        let sql = `SELECT o.*, u.name AS owner_name, u.email AS owner_email FROM organizations o JOIN users u ON u.id = o.user_id`;
        const params = [];
        if (verified === 'false') { sql += ` WHERE o.verified_at IS NULL`; }
        else if (verified === 'true') { sql += ` WHERE o.verified_at IS NOT NULL`; }
        sql += ` ORDER BY o.created_at DESC`;
        const { rows } = await query(sql, params);
        res.json({ organizations: rows });
    } catch (err) { next(err); }
});

// PATCH /api/admin/organizations/:id/verify
router.patch('/organizations/:id/verify', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { approve, note } = req.body;
        const { rows } = await query('SELECT * FROM organizations WHERE id = $1', [req.params.id]);
        if (!rows.length) return res.status(404).json({ error: 'Organization not found' });
        const org = rows[0];

        if (approve) {
            await query(
                `UPDATE organizations SET verified_at = NOW(), verified_by = $1 WHERE id = $2`,
                [req.user.id, org.id]
            );
            await query(`UPDATE users SET is_verified = TRUE, role = 'charity' WHERE id = $1`, [org.user_id]);
            await notifyUser(org.user_id, {
                type: 'verification_approved',
                title: '✅ Organization Verified!',
                body: `Your organization "${org.name}" has been verified. You now have priority access to claim surplus items.`,
                payload: { orgId: org.id },
            });
        } else {
            await notifyUser(org.user_id, {
                type: 'verification_rejected',
                title: 'Verification Not Approved',
                body: `Your organization verification was not approved. Reason: ${note || 'Please resubmit correct documents.'}`,
                payload: {},
            });
        }

        await query(
            `INSERT INTO moderation_logs (admin_id, action, target_type, target_id, note)
       VALUES ($1, $2, 'organization', $3, $4)`,
            [req.user.id, approve ? 'verify_org' : 'reject_org', org.id, note || null]
        );
        res.json({ message: approve ? 'Verified' : 'Rejected' });
    } catch (err) { next(err); }
});

// GET /api/admin/surplus — list all posts (including removed)
router.get('/surplus', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { status, limit = 50, offset = 0 } = req.query;
        let sql = `SELECT s.id, s.title, s.status, s.category, s.quantity_kg, s.created_at,
                      u.name AS donor_name, u.email AS donor_email
               FROM surplus_items s JOIN users u ON u.id = s.donor_id`;
        const params = [];
        if (status) { sql += ` WHERE s.status = $1`; params.push(status); }
        sql += ` ORDER BY s.created_at DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
        params.push(parseInt(limit), parseInt(offset));
        const { rows } = await query(sql, params);
        res.json({ items: rows });
    } catch (err) { next(err); }
});

// DELETE /api/admin/surplus/:id
router.delete('/surplus/:id', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { note } = req.body;
        const { rows } = await query('SELECT donor_id FROM surplus_items WHERE id = $1', [req.params.id]);
        if (!rows.length) return res.status(404).json({ error: 'Not found' });
        await query("UPDATE surplus_items SET status = 'removed' WHERE id = $1", [req.params.id]);
        await query(
            `INSERT INTO moderation_logs (admin_id, action, target_type, target_id, note)
       VALUES ($1, 'remove_post', 'surplus', $2, $3)`,
            [req.user.id, req.params.id, note || null]
        );
        await notifyUser(rows[0].donor_id, {
            type: 'post_removed',
            title: 'Post Removed',
            body: 'One of your posts has been removed by a moderator.',
            payload: { surplusId: req.params.id },
        });
        res.json({ message: 'Post removed' });
    } catch (err) { next(err); }
});

// GET /api/admin/logs
router.get('/logs', authenticate, requireRole('admin'), async (req, res, next) => {
    try {
        const { rows } = await query(
            `SELECT ml.*, u.name AS admin_name FROM moderation_logs ml
       JOIN users u ON u.id = ml.admin_id
       ORDER BY ml.created_at DESC LIMIT 100`
        );
        res.json({ logs: rows });
    } catch (err) { next(err); }
});

module.exports = router;
