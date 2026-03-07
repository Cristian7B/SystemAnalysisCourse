const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT) || 587,
    secure: false,
    auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS,
    },
});

const sendEmail = async ({ to, subject, html }) => {
    try {
        const info = await transporter.sendMail({
            from: `"Food Rescue" <${process.env.EMAIL_FROM}>`,
            to,
            subject,
            html,
        });
        console.log('Email sent:', info.messageId);
        return info;
    } catch (err) {
        console.error('Email error:', err.message);
    }
};

module.exports = { sendEmail };
