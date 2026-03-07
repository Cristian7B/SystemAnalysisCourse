require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

async function migrate() {
    const pool = new Pool({ connectionString: process.env.DATABASE_URL });
    const migrationsDir = path.join(__dirname, '../../migrations');
    const files = fs.readdirSync(migrationsDir).filter(f => f.endsWith('.sql')).sort();

    console.log(`Running ${files.length} migration(s)...`);
    for (const file of files) {
        const sql = fs.readFileSync(path.join(migrationsDir, file), 'utf8');
        console.log(`  → ${file}`);
        await pool.query(sql);
    }
    console.log('Migrations complete.');
    await pool.end();
}

migrate().catch(err => {
    console.error('Migration failed:', err.message);
    process.exit(1);
});
