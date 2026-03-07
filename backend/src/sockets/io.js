let _io = null;

const setIO = (io) => { _io = io; };
const getIO = () => {
    if (!_io) throw new Error('Socket.IO not initialized');
    return _io;
};

const initSockets = (io) => {
    setIO(io);
    io.on('connection', (socket) => {
        console.log(`Socket connected: ${socket.id}`);

        // Join user-specific room for targeted notifications
        socket.on('join:user', (userId) => {
            socket.join(`user:${userId}`);
        });

        // Join map region room (e.g., 'map:40.7_-74.0')
        socket.on('join:map', (region) => {
            socket.join(`map:${region}`);
        });

        socket.on('disconnect', () => {
            console.log(`Socket disconnected: ${socket.id}`);
        });
    });
};

module.exports = { initSockets, getIO, setIO };
