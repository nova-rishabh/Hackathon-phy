-- RollWatch accounts. Run once in the Supabase SQL editor.
-- Stores only: saved claim checks and watched booths per user. No API keys are ever stored here.

create table if not exists public.saved_checks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade default auth.uid(),
  claim_id text not null,
  claim_text text not null,
  overall text not null,
  created_at timestamptz not null default now()
);
create index if not exists saved_checks_user_idx on public.saved_checks (user_id, created_at desc);

create table if not exists public.watched_booths (
  user_id uuid not null references auth.users (id) on delete cascade default auth.uid(),
  booth_id text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, booth_id)
);

alter table public.saved_checks enable row level security;
alter table public.watched_booths enable row level security;

drop policy if exists "own saved_checks select" on public.saved_checks;
drop policy if exists "own saved_checks insert" on public.saved_checks;
drop policy if exists "own saved_checks delete" on public.saved_checks;
create policy "own saved_checks select" on public.saved_checks for select to authenticated using (auth.uid() = user_id);
create policy "own saved_checks insert" on public.saved_checks for insert to authenticated with check (auth.uid() = user_id);
create policy "own saved_checks delete" on public.saved_checks for delete to authenticated using (auth.uid() = user_id);

drop policy if exists "own watched_booths select" on public.watched_booths;
drop policy if exists "own watched_booths insert" on public.watched_booths;
drop policy if exists "own watched_booths delete" on public.watched_booths;
create policy "own watched_booths select" on public.watched_booths for select to authenticated using (auth.uid() = user_id);
create policy "own watched_booths insert" on public.watched_booths for insert to authenticated with check (auth.uid() = user_id);
create policy "own watched_booths delete" on public.watched_booths for delete to authenticated using (auth.uid() = user_id);

grant select, insert, delete on public.saved_checks to authenticated;
grant select, insert, delete on public.watched_booths to authenticated;
