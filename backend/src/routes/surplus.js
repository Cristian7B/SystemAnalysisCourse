const express = require('express');
const { query } = require('../config/db');
const { authenticate, requireRole } = require('../middleware/auth');
const { upload } = require('../config/upload');
const { body, query: queryParam, validationResult } = require('express-validator');
const { notifyNearbyUsers } = require('../services/notificationService');
const { getIO } = require('../sockets/io');

const router = express.Router();

const CHARITY_WINDOW = parseInt(process.env.CHARITY_WINDOW_MINUTES || 120);
const TRUSTED_WINDOW = parseInt(process.env.TRUSTED_WINDOW_MINUTES || 60);

// GET /api/surplus — list with geospatial filter
router.get('/', async (req, res, next) => {
    try {
        const { lat, lng, radius = 10, category, status = 'available', limit = 50, offset = 0 } = req.query;

        let sql = `
      SELECT
        s.id, s.title, s.description, s.category, s.quantity_kg, s.quantity_desc,
        s.photos, s.location_label, s.exact_location,
        ST_Y(s.location::geometry) AS lat,
        ST_X(s.location::geometry) AS lng,
        s.pickup_start, s.pickup_end, s.expires_at,
        s.charity_window_end, s.trusted_window_end,
        s.status, s.view_count, s.created_at,
        u.name AS donor_name, u.badge_level AS donor_badge,
        u.avatar_url AS donor_avatar
      FROM surplus_items s
      JOIN users u ON u.id = s.donor_id
      WHERE s.status = $1
    `;
        const params = [status];
        let paramIdx = 2;

        if (lat && lng) {
            sql += ` AND ST_DWithin(
        s.location::geography,
        ST_SetSRID(ST_MakePoint($${paramIdx}, $${paramIdx + 1}), 4326)::geography,
        $${paramIdx + 2}
      )`;
            params.push(parseFloat(lng), parseFloat(lat), parseFloat(radius) * 1000);
            paramIdx += 3;
        }

        if (category) {
            sql += ` AND s.category = $${paramIdx}`;
            params.push(category);
            paramIdx++;
        }

        sql += ` AND s.expires_at > NOW() ORDER BY s.created_at DESC LIMIT $${paramIdx} OFFSET $${paramIdx + 1}`;
        params.push(parseInt(limit), parseInt(offset));

        const { rows } = await query(sql, params);
        res.json({ items: rows, count: rows.length });
    } catch (err) {
        next(err);
    }
});

// GET /api/surplus/:id
router.get('/:id', async (req, res, next) => {
    try {
        const { rows } = await query(
            `SELECT s.*,
        ST_Y(s.location::geometry) AS lat,
        ST_X(s.location::geometry) AS lng,
        u.name AS donor_name, u.badge_level AS donor_badge, u.avatar_url AS donor_avatar,
        (SELECT json_agg(c) FROM (
          SELECT c.id, c.status, c.window_type, c.created_at,
                 cu.name AS claimant_name
          FROM claims c JOIN users cu ON cu.id = c.claimant_id
          WHERE c.surplus_id = s.id AND c.status != 'cancelled'
        ) c) AS claims
       FROM surplus_items s
       JOIN users u ON u.id = s.donor_id
       WHERE s.id = $1`,
            [req.params.id]
        );
        if (!rows.length) return res.status(404).json({ error: 'Surplus item not found' });
        await query('UPDATE surplus_items SET view_count = view_count + 1 WHERE id = $1', [req.params.id]);
        res.json(rows[0]);
    } catch (err) {
        next(err);
    }
});

// POST /api/surplus — create
router.post(
    '/',
    authenticate,
    requireRole('donor', 'charity', 'admin'),
    upload.array('photos', 5),
    [
        body('title').trim().isLength({ min: 3, max: 200 }),
        body('quantityKg').isFloat({ min: 0.1 }),
        body('category').isIn(['produce', 'bakery', 'dairy', 'prepared_food', 'canned_goods', 'beverages', 'frozen', 'other']),
        body('lat').isFloat(),
        body('lng').isFloat(),
        body('pickupStart').isISO8601(),
        body('pickupEnd').isISO8601(),
        body('expiresAt').isISO8601(),
    ],
    async (req, res, next) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

            const {
                title, description, category, quantityKg, quantityDesc,
                lat, lng, locationLabel, exactLocation,
                pickupStart, pickupEnd, expiresAt,
            } = req.body;

            const photos = (req.files || []).map(f => `/uploads/${f.filename}`);

            const charityWindowEnd = new Date(Date.now() + CHARITY_WINDOW * 60 * 1000).toISOString();
            const trustedWindowEnd = new Date(Date.now() + (CHARITY_WINDOW + TRUSTED_WINDOW) * 60 * 1000).toISOString();

            const { rows } = await query(
                `INSERT INTO surplus_items
         (donor_id, title, description, category, quantity_kg, quantity_desc, photos,
          location, location_label, exact_location, pickup_start, pickup_end, expires_at,
          charity_window_end, trusted_window_end)
         VALUES ($1,$2,$3,$4,$5,$6,$7,
                 ST_SetSRID(ST_MakePoint($8,$9),4326),$10,$11,$12,$13,$14,$15,$16)
         RETURNING id, title, status, created_at`,
                [
                    req.user.id, title, description || null, category,
                    parseFloat(quantityKg), quantityDesc || null, photos,
                    parseFloat(lng), parseFloat(lat), locationLabel || null,
                    exactLocation === 'true', pickupStart, pickupEnd, expiresAt,
                    charityWindowEnd, trustedWindowEnd,
                ]
            );

            // Broadcast via Socket.IO
            try {
                getIO().emit('surplus:new', { id: rows[0].id, lat, lng, title, category });
            } catch (_) { }

            // Notify nearby users (async, don't await)
            notifyNearbyUsers(parseFloat(lat), parseFloat(lng), rows[0]).catch(console.error);

            res.status(201).json(rows[0]);
        } catch (err) {
            next(err);
        }
    }
);

// PATCH /api/surplus/:id — update own post
router.patch('/:id', authenticate, async (req, res, next) => {
    try {
        const { rows } = await query('SELECT donor_id FROM surplus_items WHERE id = $1', [req.params.id]);
        if (!rows.length) return res.status(404).json({ error: 'Not found' });
        if (rows[0].donor_id !== req.user.id && req.user.role !== 'admin') {
            return res.status(403).json({ error: 'Forbidden' });
        }

        const allowed = ['title', 'description', 'quantity_kg', 'quantity_desc', 'pickup_start', 'pickup_end', 'expires_at'];
        const updates = [];
        const values = [];
        let idx = 1;
        for (const key of allowed) {
            const bodyKey = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
            if (req.body[bodyKey] !== undefined) {
                updates.push(`${key} = $${idx}`);
                values.push(req.body[bodyKey]);
                idx++;
            }
        }
        if (!updates.length) return res.status(400).json({ error: 'No fields to update' });
        values.push(req.params.id);
        const { rows: updated } = await query(
            `UPDATE surplus_items SET ${updates.join(', ')} WHERE id = $${idx} RETURNING id, title, status`,
            values
        );
        res.json(updated[0]);
    } catch (err) {
        next(err);
    }
});

// DELETE /api/surplus/:id
router.delete('/:id', authenticate, async (req, res, next) => {
    try {
        const { rows } = await query('SELECT donor_id FROM surplus_items WHERE id = $1', [req.params.id]);
        if (!rows.length) return res.status(404).json({ error: 'Not found' });
        if (rows[0].donor_id !== req.user.id && req.user.role !== 'admin') {
            return res.status(403).json({ error: 'Forbidden' });
        }
        await query("UPDATE surplus_items SET status = 'removed' WHERE id = $1", [req.params.id]);
        try { getIO().emit('surplus:removed', { id: req.params.id }); } catch (_) { }
        res.json({ message: 'Removed' });
    } catch (err) {
        next(err);
    }
});

module.exports = router;
