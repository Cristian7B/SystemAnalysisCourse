const { query } = require('../config/db');
const { notifyUser } = require('./notificationService');

const BADGE_THRESHOLDS = {
    newcomer: 0,
    helper: 5,
    champion: 20,
    hero: 50,
};

const checkAndUpgradeBadge = async (userId) => {
    try {
        const { rows } = await query(
            'SELECT successful_pickups, badge_level, role FROM users WHERE id = $1',
            [userId]
        );
        if (!rows.length) return;
        const { successful_pickups, badge_level, role } = rows[0];

        let newBadge = badge_level;
        if (successful_pickups >= BADGE_THRESHOLDS.hero) newBadge = 'hero';
        else if (successful_pickups >= BADGE_THRESHOLDS.champion) newBadge = 'champion';
        else if (successful_pickups >= BADGE_THRESHOLDS.helper) newBadge = 'helper';

        if (newBadge !== badge_level) {
            await query('UPDATE users SET badge_level = $1 WHERE id = $2', [newBadge, userId]);

            // Auto-upgrade role: helper → trusted_collector if currently general_recipient
            if (newBadge === 'champion' && role === 'general_recipient') {
                await query("UPDATE users SET role = 'trusted_collector' WHERE id = $1", [userId]);
            }

            await notifyUser(userId, {
                type: 'badge_earned',
                title: `🏅 New Badge: ${newBadge.charAt(0).toUpperCase() + newBadge.slice(1)}!`,
                body: `You've earned the "${newBadge}" badge for ${successful_pickups} successful pickups. Keep it up!`,
                payload: { badge: newBadge },
            });
        }
    } catch (err) {
        console.error('checkAndUpgradeBadge error:', err.message);
    }
};

module.exports = { checkAndUpgradeBadge, BADGE_THRESHOLDS };
