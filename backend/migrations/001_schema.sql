-- ============================================================
-- Food Waste Redistribution Platform — Database Schema
-- Requires: PostgreSQL 15 + PostGIS 3.3
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── USERS ────────────────────────────────────────────────────
CREATE TYPE user_role AS ENUM (
  'donor',
  'charity',
  'trusted_collector',
  'general_recipient',
  'admin'
);

CREATE TYPE badge_level AS ENUM (
  'newcomer',
  'helper',
  'champion',
  'hero'
);

CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name            VARCHAR(120) NOT NULL,
  email           VARCHAR(255) NOT NULL UNIQUE,
  password_hash   TEXT NOT NULL,
  role            user_role NOT NULL DEFAULT 'general_recipient',
  badge_level     badge_level NOT NULL DEFAULT 'newcomer',
  avatar_url      TEXT,
  phone           VARCHAR(30),
  bio             TEXT,
  is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
  is_banned       BOOLEAN NOT NULL DEFAULT FALSE,
  push_subscription JSONB,
  refresh_token   TEXT,
  successful_pickups INTEGER NOT NULL DEFAULT 0,
  kg_redistributed NUMERIC(10, 2) NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role  ON users (role);

-- ── ORGANIZATIONS ────────────────────────────────────────────
CREATE TABLE organizations (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name            VARCHAR(200) NOT NULL,
  description     TEXT,
  document_url    TEXT,
  website         TEXT,
  verified_at     TIMESTAMPTZ,
  verified_by     UUID REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_org_user ON organizations (user_id);

-- ── SURPLUS ITEMS ─────────────────────────────────────────────
CREATE TYPE surplus_status AS ENUM (
  'available',
  'claimed',
  'completed',
  'expired',
  'removed'
);

CREATE TYPE surplus_category AS ENUM (
  'produce',
  'bakery',
  'dairy',
  'prepared_food',
  'canned_goods',
  'beverages',
  'frozen',
  'other'
);

CREATE TABLE surplus_items (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  donor_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title           VARCHAR(200) NOT NULL,
  description     TEXT,
  category        surplus_category NOT NULL DEFAULT 'other',
  quantity_kg     NUMERIC(8, 2) NOT NULL,
  quantity_desc   VARCHAR(200),
  photos          TEXT[] DEFAULT '{}',
  location        GEOMETRY(POINT, 4326) NOT NULL,
  location_label  VARCHAR(300),
  exact_location  BOOLEAN NOT NULL DEFAULT FALSE,
  pickup_start    TIMESTAMPTZ NOT NULL,
  pickup_end      TIMESTAMPTZ NOT NULL,
  expires_at      TIMESTAMPTZ NOT NULL,
  charity_window_end     TIMESTAMPTZ,
  trusted_window_end     TIMESTAMPTZ,
  status          surplus_status NOT NULL DEFAULT 'available',
  view_count      INTEGER NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_surplus_location ON surplus_items USING GIST (location);
CREATE INDEX idx_surplus_status   ON surplus_items (status);
CREATE INDEX idx_surplus_donor    ON surplus_items (donor_id);
CREATE INDEX idx_surplus_expires  ON surplus_items (expires_at);
CREATE INDEX idx_surplus_category ON surplus_items (category);

-- ── CLAIMS ────────────────────────────────────────────────────
CREATE TYPE claim_status AS ENUM (
  'pending',
  'confirmed',
  'completed',
  'cancelled',
  'no_show'
);

CREATE TYPE claim_window AS ENUM (
  'charity',
  'trusted_collector',
  'general'
);

CREATE TABLE claims (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  surplus_id      UUID NOT NULL REFERENCES surplus_items(id) ON DELETE CASCADE,
  claimant_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status          claim_status NOT NULL DEFAULT 'pending',
  window_type     claim_window NOT NULL,
  notes           TEXT,
  confirmed_at    TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  cancelled_at    TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (surplus_id, claimant_id)
);

CREATE INDEX idx_claims_surplus  ON claims (surplus_id);
CREATE INDEX idx_claims_claimant ON claims (claimant_id);
CREATE INDEX idx_claims_status   ON claims (status);

-- ── NOTIFICATIONS ─────────────────────────────────────────────
CREATE TYPE notification_type AS ENUM (
  'surplus_posted',
  'claim_received',
  'claim_confirmed',
  'claim_cancelled',
  'pickup_reminder',
  'window_opened',
  'badge_earned',
  'verification_approved',
  'verification_rejected',
  'user_banned',
  'post_removed'
);

CREATE TABLE notifications (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type            notification_type NOT NULL,
  title           VARCHAR(200) NOT NULL,
  body            TEXT NOT NULL,
  payload         JSONB DEFAULT '{}',
  is_read         BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifs_user    ON notifications (user_id);
CREATE INDEX idx_notifs_unread  ON notifications (user_id, is_read) WHERE is_read = FALSE;

-- ── PICKUP LOGS ───────────────────────────────────────────────
CREATE TABLE pickup_logs (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  claim_id        UUID NOT NULL UNIQUE REFERENCES claims(id) ON DELETE CASCADE,
  donor_id        UUID NOT NULL REFERENCES users(id),
  claimant_id     UUID NOT NULL REFERENCES users(id),
  kg_redistributed NUMERIC(8, 2) NOT NULL,
  notes           TEXT,
  confirmed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pickup_donor    ON pickup_logs (donor_id);
CREATE INDEX idx_pickup_claimant ON pickup_logs (claimant_id);

-- ── MODERATION LOGS ───────────────────────────────────────────
CREATE TYPE moderation_action AS ENUM (
  'verify_org',
  'reject_org',
  'remove_post',
  'ban_user',
  'unban_user',
  'warn_user',
  'upgrade_role'
);

CREATE TABLE moderation_logs (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  admin_id        UUID NOT NULL REFERENCES users(id),
  action          moderation_action NOT NULL,
  target_type     VARCHAR(50) NOT NULL,
  target_id       UUID NOT NULL,
  note            TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mod_admin  ON moderation_logs (admin_id);
CREATE INDEX idx_mod_target ON moderation_logs (target_id);

-- ── PUSH SUBSCRIPTIONS ────────────────────────────────────────
CREATE TABLE push_subscriptions (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  endpoint        TEXT NOT NULL UNIQUE,
  p256dh          TEXT NOT NULL,
  auth            TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_push_user ON push_subscriptions (user_id);

-- ── AUTO-TIMESTAMP TRIGGER ────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_surplus_updated_at
  BEFORE UPDATE ON surplus_items
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── INITIAL ADMIN USER ────────────────────────────────────────
-- Password: Admin1234! (bcrypt hash — change in production)
INSERT INTO users (name, email, password_hash, role, badge_level, is_verified)
VALUES (
  'Platform Admin',
  'admin@foodwaste.app',
  '$2a$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/k4/TnJu',
  'admin',
  'hero',
  TRUE
) ON CONFLICT DO NOTHING;
