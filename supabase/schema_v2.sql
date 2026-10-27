-- RollWatch accounts v2 (WhatsApp sign-in). Run in the Supabase SQL editor; safe to re-run.
-- Rows are keyed by the E.164 phone number. RLS is on with NO policies: only the API's
-- service-role key (server-side) can read or write. No API keys are ever stored here.

create table if not exists public.wa_saved_checks (
  phone text not null,
  claim_id text not null,
  claim_text text not null,
  overall text not null,
  created_at timestamptz not null default now(),
  primary key (phone, claim_id)
);

create table if not exists public.wa_watched_booths (
  phone text not null,
  booth_id text not null,
  created_at timestamptz not null default now(),
  primary key (phone, booth_id)
);

alter table public.wa_saved_checks enable row level security;
alter table public.wa_watched_booths enable row level security;
