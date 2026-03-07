const webpush = require('web-push');

webpush.setVapidDetails(
    process.env.VAPID_SUBJECT,
    process.env.VAPID_PUBLIC_KEY,
    process.env.VAPID_PRIVATE_KEY
);

const sendPush = async (subscription, payload) => {
    try {
        await webpush.sendNotification(subscription, JSON.stringify(payload));
    } catch (err) {
        if (err.statusCode === 410) {
            // Subscription expired — could remove from DB here
            console.warn('Push subscription expired:', err.endpoint);
        } else {
            console.error('Push error:', err.message);
        }
    }
};

module.exports = { sendPush, webpush };
