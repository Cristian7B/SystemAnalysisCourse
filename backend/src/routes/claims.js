const express = require('express');
const { query } = require('../config/db');
const { authenticate } = require('../middleware/auth');
const { notifyUser } = require('../services/notificationService');
const { getIO } = require('../sockets/io');

const router = express.Router();

// Determine which claim window a user qualifies for
const getWindowType = (user, item) => {
    const now = new Date();
    const charityEnd = new Date(item.charity_window_end);
    const trustedEnd = new Date(item.trusted_window_end);

    if (user.role === 'charity' && now <= charityEnd) return 'charity';
    if (user.role === 'trusted_collector' && now <= trustedEnd) return 'trusted_collector';
    if (now > trustedEnd) return 'general';

    // Role doesn't match current window
    if (now <= charityEnd) return null; // only charity window open
    if (now <= trustedEnd && user.role !== 'trusted_collector') return null;
    return 'general';
};

// POST /api/claims/:surplusId — claim an item
router.post('/:surplusId', authenticate, async (req, res, next) => {
    try {
        const { rows: itemRows } = await query(
            `SELECT * FROM surplus_items WHERE id = $1 AND status = 'available'`,
            [req.params.surplusId]
        );
        if (!itemRows.length) {
            return res.status(404).json({ error: 'Item not available for claiming' });
        }
        const item = itemRows[0];

        // Don't let donor claim own item
        if (item.donor_id === req.user.id) {
            return res.status(400).json({ error: 'Cannot claim your own item' });
        }

        const windowType = getWindowType(req.user, item);
        if (!windowType) {
            return res.status(403).json({
                error: 'This item is not yet available for your role',
                charityWindowEnd: item.charity_window_end,
                trustedWindowEnd: item.trusted_window_end,
            });
        }

        // Check for existing pending claim by this user
        const existing = await query(
            `SELECT id FROM claims WHERE surplus_id = $1 AND claimant_id = $2`,
            [item.id, req.user.id]
        );
        if (existing.rows.length) {
            return res.status(409).json({ error: 'Already submitted a claim for this item' });
        }

        const { rows: claimRows } = await query(
            `INSERT INTO claims (surplus_id, claimant_id, window_type)
       VALUES ($1, $2, $3) RETURNING *`,
            [item.id, req.user.id, windowType]
        );

        // Update surplus status
        await query("UPDATE surplus_items SET status = 'claimed' WHERE id = $1", [item.id]);

        // Notify donor
        await notifyUser(item.donor_id, {
            type: 'claim_received',
            title: 'New Claim on Your Donation',
            body: `${req.user.name} has claimed "${item.title}"`,
            payload: { claimId: claimRows[0].id, surplusId: item.id },
        });

        try { getIO().emit('surplus:claimed', { id: item.id }); } catch (_) { }

        res.status(201).json(claimRows[0]);
    } catch (err) {
        next(err);
    }
});

// GET /api/claims — my claims
router.get('/', authenticate, async (req, res, next) => {
    try {
        const { rows } = await query(
            `SELECT c.*, s.title, s.category, s.quantity_kg, s.pickup_start, s.pickup_end,
              s.location_label, u.name AS donor_name
       FROM claims c
       JOIN surplus_items s ON s.id = c.surplus_id
       JOIN users u ON u.id = s.donor_id
       WHERE c.claimant_id = $1
       ORDER BY c.created_at DESC`,
            [req.user.id]
        );
        res.json({ claims: rows });
    } catch (err) {
        next(err);
    }
});

// GET /api/claims/incoming — incoming claims on my donations
router.get('/incoming', authenticate, async (req, res, next) => {
    try {
        const { rows } = await query(
            `SELECT c.*, s.title, s.category, s.quantity_kg,
              cu.name AS claimant_name, cu.email AS claimant_email,
              cu.role AS claimant_role, cu.badge_level AS claimant_badge
       FROM claims c
       JOIN surplus_items s ON s.id = c.surplus_id
       JOIN users cu ON cu.id = c.claimant_id
       WHERE s.donor_id = $1 AND c.status != 'cancelled'
       ORDER BY c.created_at DESC`,
            [req.user.id]
        );
        res.json({ claims: rows });
    } catch (err) {
        next(err);
    }
});

// PATCH /api/claims/:id/confirm — donor confirms pickup
router.patch('/:id/confirm', authenticate, async (req, res, next) => {
    try {
        const { rows: claimRows } = await query(
            `SELECT c.*, s.donor_id, s.title, s.quantity_kg
       FROM claims c JOIN surplus_items s ON s.id = c.surplus_id
       WHERE c.id = $1`,
            [req.params.id]
        );
        if (!claimRows.length) return res.status(404).json({ error: 'Claim not found' });
        const claim = claimRows[0];
        if (claim.donor_id !== req.user.id) return res.status(403).json({ error: 'Forbidden' });

        await query(
            `UPDATE claims SET status = 'confirmed', confirmed_at = NOW() WHERE id = $1`,
            [claim.id]
        );

        await notifyUser(claim.claimant_id, {
            type: 'claim_confirmed',
            title: 'Pickup Confirmed!',
            body: `Your claim for "${claim.title}" has been confirmed. Please pick up on time.`,
            payload: { claimId: claim.id },
        });

        res.json({ message: 'Confirmed' });
    } catch (err) {
        next(err);
    }
});

// PATCH /api/claims/:id/complete — mark as successfully picked up
router.patch('/:id/complete', authenticate, async (req, res, next) => {
    try {
        const { rows: claimRows } = await query(
            `SELECT c.*, s.donor_id, s.title, s.quantity_kg
       FROM claims c JOIN surplus_items s ON s.id = c.surplus_id
       WHERE c.id = $1`,
            [req.params.id]
        );
        if (!claimRows.length) return res.status(404).json({ error: 'Claim not found' });
        const claim = claimRows[0];
        if (claim.donor_id !== req.user.id && claim.claimant_id !== req.user.id) {
            return res.status(403).json({ error: 'Forbidden' });
        }

        await query(
            `UPDATE claims SET status = 'completed', completed_at = NOW() WHERE id = $1`,
            [claim.id]
        );
        await query(
            `UPDATE surplus_items SET status = 'completed' WHERE id = $1`,
            [claim.surplus_id]
        );

        // Insert pickup log
        await query(
            `INSERT INTO pickup_logs (claim_id, donor_id, claimant_id, kg_redistributed)
       VALUES ($1, $2, $3, $4)`,
            [claim.id, claim.donor_id, claim.claimant_id, claim.quantity_kg]
        );

        // Update user stats
        await query(
            `UPDATE users SET
         successful_pickups = successful_pickups + 1,
         kg_redistributed = kg_redistributed + $1
       WHERE id = $2`,
            [claim.quantity_kg, claim.claimant_id]
        );
        await query(
            `UPDATE users SET kg_redistributed = kg_redistributed + $1 WHERE id = $2`,
            [claim.quantity_kg, claim.donor_id]
        );

        // Badge upgrade logic (service handles it)
        const { checkAndUpgradeBadge } = require('../services/badgeService');
        await checkAndUpgradeBadge(claim.claimant_id);

        res.json({ message: 'Pickup completed' });
    } catch (err) {
        next(err);
    }
});

// PATCH /api/claims/:id/cancel
router.patch('/:id/cancel', authenticate, async (req, res, next) => {
    try {
        const { rows } = await query('SELECT * FROM claims WHERE id = $1', [req.params.id]);
        if (!rows.length) return res.status(404).json({ error: 'Claim not found' });
        const claim = rows[0];
        if (claim.claimant_id !== req.user.id && req.user.role !== 'admin') {
            return res.status(403).json({ error: 'Forbidden' });
        }
        await query(
            `UPDATE claims SET status = 'cancelled', cancelled_at = NOW() WHERE id = $1`,
            [claim.id]
        );
        await query(
            `UPDATE surplus_items SET status = 'available' WHERE id = $1 AND status = 'claimed'`,
            [claim.surplus_id]
        );
        try { getIO().emit('surplus:available', { id: claim.surplus_id }); } catch (_) { }
        res.json({ message: 'Cancelled' });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
