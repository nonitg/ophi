-- Every past preauth a clinic sent and Sun Life's answer: the source Laya and LightGBM train from, the Past
-- outcomes page lists, and similar-request links draw on. One table for all clinics; each clinic sees only
-- its own rows. Member IDs are hashed before they get here.

create schema if not exists outcomes;

create table if not exists outcomes.clinic (
  clinic_id  text primary key,
  name       text not null
);

create table if not exists outcomes.past_request (
  preauth_id       text primary key,
  clinic_id        text not null references outcomes.clinic (clinic_id),
  source           text not null,  -- the export folder it came from
  procedure_code   text not null,
  tooth_fdi        smallint,
  tooth_class      text,
  age_band         text not null,
  channel          text not null,
  submitted_on     date not null,
  decided_on       date,
  status           text not null check (status in ('approved', 'denied')),
  reason_code      text,
  reason_category  text,
  letter           text,           -- Sun Life's explanation of benefits, verbatim
  followup_type    text,
  followup_outcome text,
  sent             jsonb not null, -- the request as the clinic sent it
  decision         jsonb not null,
  followup         jsonb,
  -- the engine's reading plus raw values (training_set.features); null outside the crown pack
  features         jsonb,
  pack_version     text,
  -- synthetic answer key: note-question labels for training only, never shown to a clinic
  truth            jsonb,
  ingested_at      timestamptz not null default now()
);
create index if not exists past_request_clinic_idx on outcomes.past_request (clinic_id, status, submitted_on desc);
create index if not exists past_request_reason_idx on outcomes.past_request (reason_code);

alter table outcomes.clinic enable row level security;
alter table outcomes.past_request enable row level security;

-- A signed-in clinic user reads its own clinic's rows (clinic_id in app_metadata), never the answer key.
-- Guarded so the same file runs on plain Postgres in tests, where Supabase's auth roles don't exist.
do $$
begin
  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    grant usage on schema outcomes to authenticated;
    grant select on outcomes.clinic to authenticated;
    grant select (preauth_id, clinic_id, source, procedure_code, tooth_fdi, tooth_class, age_band, channel, submitted_on,
                  decided_on, status, reason_code, reason_category, letter, followup_type, followup_outcome, sent, decision,
                  followup, features, pack_version, ingested_at) on outcomes.past_request to authenticated;
    drop policy if exists own_clinic on outcomes.past_request;
    create policy own_clinic on outcomes.past_request for select to authenticated
      using (clinic_id = (select auth.jwt() -> 'app_metadata' ->> 'clinic_id'));
    drop policy if exists own_clinic on outcomes.clinic;
    create policy own_clinic on outcomes.clinic for select to authenticated
      using (clinic_id = (select auth.jwt() -> 'app_metadata' ->> 'clinic_id'));
  end if;
end $$;
