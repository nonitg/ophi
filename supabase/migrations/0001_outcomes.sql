-- Past preauth outcomes + the engine's reading of each submission. De-identified: hashed member and
-- provider, age band only, no note text. Lives in its own schema so the Data API never exposes it;
-- RLS with no policies means only the service connection can read or write.

create schema if not exists outcomes;

create table outcomes.submission (
  preauth_id      text primary key,
  member_hash     text not null,
  provider_hash   text not null,
  code            text not null,
  tooth_fdi       smallint,
  age_band        text not null,
  channel         text not null,
  submitted_on    date not null,
  unmodelled_attachments text[] not null default '{}',
  -- null when the code is outside the pack: stored as an outcome, never assessed
  pack_version    text,
  pack_hash       text,
  verdict         text,
  ingested_at     timestamptz not null default now()
);

create table outcomes.requirement_result (
  preauth_id      text not null references outcomes.submission (preauth_id) on delete cascade,
  requirement_id  text not null,
  status          text not null,
  satisfied_via   text,
  primary key (preauth_id, requirement_id)
);
create index requirement_result_requirement_idx on outcomes.requirement_result (requirement_id);

create table outcomes.decision (
  preauth_id       text primary key references outcomes.submission (preauth_id) on delete cascade,
  status           text not null check (status in ('approved', 'denied')),
  reason_code      text,
  reason_category  text,
  followup_type    text,
  followup_outcome text
);

-- denial_map.yaml, loaded on every ingest so attribution uses the same bytes as the pack version
create table outcomes.denial_map (
  pack_version    text not null,
  reason_code     text not null,
  requirement_id  text,  -- null row = reviewed, no requirement covers this code
  unique nulls not distinct (pack_version, reason_code, requirement_id)
);

alter table outcomes.submission enable row level security;
alter table outcomes.requirement_result enable row level security;
alter table outcomes.decision enable row level security;
alter table outcomes.denial_map enable row level security;

-- For each requirement: denial rate when the engine found it missing vs when it did not.
-- "Missing" is `unsatisfied` only; undated-but-attached evidence is indeterminate and counts as present.
create view outcomes.v_requirement_denial_lift with (security_invoker = true) as
select
  r.requirement_id,
  s.pack_version,
  count(*) filter (where r.status = 'unsatisfied')                              as n_missing,
  count(*) filter (where r.status = 'unsatisfied' and d.status = 'denied')      as denied_missing,
  count(*) filter (where r.status <> 'unsatisfied')                             as n_present,
  count(*) filter (where r.status <> 'unsatisfied' and d.status = 'denied')     as denied_present
from outcomes.requirement_result r
join outcomes.submission s using (preauth_id)
join outcomes.decision d using (preauth_id)
where r.status <> 'not_applicable'
group by r.requirement_id, s.pack_version;

-- Denials the pack cannot explain: the reason maps to no requirement, the code is unknown to the map,
-- or no mapped requirement was found missing on the submission date (met, or evidence undated).
create view outcomes.v_pack_blind_spots with (security_invoker = true) as
select
  s.preauth_id, s.code, d.reason_code, d.reason_category, s.unmodelled_attachments,
  case
    when not exists (select 1 from outcomes.denial_map m where m.pack_version = s.pack_version and m.reason_code = d.reason_code)
      then 'unmapped_reason'
    when not exists (select 1 from outcomes.denial_map m where m.pack_version = s.pack_version and m.reason_code = d.reason_code and m.requirement_id is not null)
      then 'no_requirement'
    else 'mapped_gap_not_found'
  end as kind
from outcomes.submission s
join outcomes.decision d using (preauth_id)
where d.status = 'denied'
  and s.pack_version is not null
  and not exists (
    select 1 from outcomes.denial_map m
    join outcomes.requirement_result r on r.preauth_id = s.preauth_id and r.requirement_id = m.requirement_id
    where m.pack_version = s.pack_version and m.reason_code = d.reason_code and r.status = 'unsatisfied');
