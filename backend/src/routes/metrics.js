const express = require('express');
const { query } = require('../config/db');
const { authenticate } = require('../middleware/auth');

const router = express.Router();

// GET /api/metrics/platform — overall impact stats
router.get('/platform', async (req, res, next) => {
    try {
        const { rows } = await query(`
      SELECT
        COUNT(DISTINCT p.id)::int AS total_pickups,
        COALESCE(SUM(p.kg_redistributed), 0) AS total_kg,
        COUNT(DISTINCT s.donor_id)::int AS total_donors,
        COUNT(DISTINCT p.claimant_id)::int AS total_recipients,
        COUNT(DISTINCT s.id)::int AS total_posts,
        ROUND(
          COUNT(DISTINCT p.id)::numeric / NULLIF(COUNT(DISTINCT s.id), 0) * 100, 1
        ) AS success_rate_pct
      FROM surplus_items s
      LEFT JOIN pickup_logs p ON p.claim_id IN (
        SELECT id FROM claims WHERE surplus_id = s.id AND status = 'completed'
      )
    `);
        res.json(rows[0]);
    } catch (err) { next(err); }
});

// GET /api/metrics/user — current user's personal stats
router.get('/user', authenticate, async (req, res, next) => {
    try {
        const { rows } = await query(
            `SELECT
         u.successful_pickups,
         u.kg_redistributed,
         u.badge_level,
         (SELECT COUNT(*) FROM surplus_items WHERE donor_id = u.id)::int AS posts_count,
         (SELECT COUNT(*) FROM claims WHERE claimant_id = u.id AND status = 'completed')::int AS claims_completed
       FROM users u WHERE u.id = $1`,
            [req.user.id]
        );
        res.json(rows[0]);
    } catch (err) { next(err); }
});

// GET /api/metrics/timeseries — kg per day (last 30 days)
router.get('/timeseries', async (req, res, next) => {
    try {
        const { rows } = await query(`
      SELECT
        DATE(confirmed_at) AS date,
        COALESCE(SUM(kg_redistributed), 0) AS kg
      FROM pickup_logs
      WHERE confirmed_at >= NOW() - INTERVAL '30 days'
      GROUP BY DATE(confirmed_at)
      ORDER BY date ASC
    `);
        res.json({ data: rows });
    } catch (err) { next(err); }
});

// GET /api/metrics/categories — breakdown by category
router.get('/categories', async (req, res, next) => {
    try {
        const { rows } = await query(`
      SELECT
        s.category,
        COUNT(s.id)::int AS count,
        COALESCE(SUM(p.kg_redistributed), 0) AS kg
      FROM surplus_items s
      LEFT JOIN claims c ON c.surplus_id = s.id AND c.status = 'completed'
      LEFT JOIN pickup_logs p ON p.claim_id = c.id
      GROUP BY s.category
      ORDER BY kg DESC
    `);
        res.json({ data: rows });
    } catch (err) { next(err); }
});

// GET /api/metrics/leaderboard
router.get('/leaderboard', async (req, res, next) => {
    try {
        const { rows } = await query(`
      SELECT name, badge_level, successful_pickups, kg_redistributed
      FROM users
      WHERE successful_pickups > 0
      ORDER BY kg_redistributed DESC
      LIMIT 20
    `);
        res.json({ leaderboard: rows });
    } catch (err) { next(err); }
});

module.exports = router;
