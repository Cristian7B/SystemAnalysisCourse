const errorHandler = (err, req, res, next) => {
    console.error(`[Error] ${req.method} ${req.path}:`, err.message);

    if (err.code === '23505') {
        return res.status(409).json({ error: 'Duplicate entry', detail: err.detail });
    }
    if (err.code === '23503') {
        return res.status(400).json({ error: 'Referenced record not found' });
    }
    if (err.type === 'entity.too.large') {
        return res.status(413).json({ error: 'Payload too large' });
    }

    const status = err.status || 500;
    res.status(status).json({
        error: err.message || 'Internal server error',
        ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
    });
};

module.exports = { errorHandler };
