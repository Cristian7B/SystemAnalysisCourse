const { query } = require('../config/db');
const { sendEmail } = require('../config/mailer');
const { sendPush } = require('../config/push');

// Send a notification to a single user
const notifyUser = async (userId, { type, title, body, payload = {} }) => {
    try {
        // Store in DB
        await query(
            `INSERT INTO notifications (user_id, type, title, body, payload)
       VALUES ($1, $2, $3, $4, $5)`,
            [userId, type, title, body, JSON.stringify(payload)]
        );

        // Fetch user for email + push
        const { rows } = await query(
            'SELECT email, push_subscription FROM users WHERE id = $1',
            [userId]
        );
        if (!rows.length) return;
        const user = rows[0];

        // Email
        sendEmail({
            to: user.email,
            subject: title,
            html: `
        <div style="font-family:sans-serif;max-width:600px;margin:auto">
          <div style="background:#22c55e;color:#fff;padding:24px;border-radius:12px 12px 0 0">
            <h2 style="margin:0">🍎 Food Rescue</h2>
          </div>
          <div style="padding:24px;background:#f9fafb;border-radius:0 0 12px 12px">
            <h3>${title}</h3>
            <p>${body}</p>
          </div>
        </div>`,
        }).catch(console.error);

        // Push
        const pushRows = await query(
            'SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = $1',
            [userId]
        );
        for (const sub of pushRows.rows) {
            sendPush({ endpoint: sub.endpoint, keys: { p256dh: sub.p256dh, auth: sub.auth } }, {
                title,
                body,
                payload,
            });
        }
    } catch (err) {
        console.error('notifyUser error:', err.message);
    }
};

// Notify charity users near a location when new surplus is posted
const notifyNearbyUsers = async (lat, lng, surplus) => {
    try {
        const { rows } = await query(
            `SELECT u.id FROM users u
       JOIN surplus_items s_ref ON TRUE
       WHERE u.role IN ('charity', 'trusted_collector', 'general_recipient')
         AND u.is_banned = FALSE
         AND s_ref.id = $1
       LIMIT 50`,
            [surplus.id]
        );
        // In practice you'd store user home location; simplified to notify recently active users
        const { rows: nearbyUsers } = await query(
            `SELECT DISTINCT u.id
       FROM users u
       WHERE u.role IN ('charity', 'trusted_collector')
         AND u.is_banned = FALSE
       LIMIT 30`
        );
        for (const user of nearbyUsers) {
            await notifyUser(user.id, {
                type: 'surplus_posted',
                title: '🍎 New Food Available Nearby',
                body: `"${surplus.title}" is available for pickup. Claim it before it expires!`,
                payload: { surplusId: surplus.id },
            });
        }
    } catch (err) {
        console.error('notifyNearbyUsers error:', err.message);
    }
};

module.exports = { notifyUser, notifyNearbyUsers };
