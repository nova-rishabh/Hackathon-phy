"""RollWatch data contracts: the single source of truth (docs/TRD.md §3).

Only Rishabh changes this file. Every other module imports from here; the web
types are generated from the JSON Schemas that `python -m contracts.export` writes.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- shared enums

Lang = Literal["hi", "en", "pa", "bn", "mr", "ta", "te"]
RollVersion = Literal["v1", "v2"]
Gender = Literal["M", "F", "T"]
RelationType = Literal["father", "husband", "mother", "other"]
FlagType = Literal[
    "deletion_spike", "addition_spike", "duplicate_cluster", "impossible_age",
    "relation_conflict", "oversized_household", "gender_ratio_swing",
]
StoryCode = Literal["death_registered", "hostel_moveout", "boundary_change", "duplicate_cleanup", "unexplained"]
Outcome = Literal["unusual", "likely_benign", "mixed"]
Band = Literal["low", "medium", "high"]
Verdict = Literal["verified", "disputed", "unprovable"]
ClaimTool = Literal[
    "deletion_count", "deletion_rate", "addition_count", "duplicate_count", "age_distribution",
    "gender_ratio", "compare_booths", "story_shares", "unanswerable",
]
ReviewStatus = Literal["open", "benign", "escalated"]
CitizenStatus = Literal["present", "modified", "not_in_new_list", "not_found"]
ReasonCategory = Literal["shifted", "death_registered", "duplicate_cleanup", "boundary_change", "unexplained", "none"]


# ---------------------------------------------------------------- roll data

class RollRow(BaseModel):
    """One elector in one roll version (roll_v1.parquet / roll_v2.parquet).

    voter_id is stable for the same person across v1 and v2; duplicates get
    DIFFERENT ids; modified records keep their id.
    """
    voter_id: str = Field(pattern=r"^SBD\d{7}$")
    roll_version: RollVersion
    ward_id: str = Field(pattern=r"^W\d{2}$")
    booth_id: str = Field(pattern=r"^B\d{3}$")
    serial_no: int
    house_no: str
    name_dev: str
    name_lat: str
    relation_type: RelationType
    relation_name_dev: str
    relation_name_lat: str
    age: int
    gender: Gender


class DeathRecord(BaseModel):
    booth_id: str
    house_no: str
    name_lat: str
    age: int
    date: str  # ISO date


class HostelRecord(BaseModel):
    booth_id: str
    house_no: str
    capacity: int
    academic_year_end: str  # ISO date


class BoundaryChange(BaseModel):
    change_id: str
    from_booth: str
    to_booth: str
    house_from: int
    house_to: int
    effective_date: str


class Planting(BaseModel):
    """One entry of the PRIVATE answer key (private/answer_key.json). The engine never reads this."""
    plant_id: str
    type: FlagType | Literal["hostel_moveout", "boundary_change", "mass_death"]
    is_benign: bool
    booth_id: str
    voter_ids: list[str]
    note: str = ""


# ---------------------------------------------------------------- engine output

class Metrics(BaseModel):
    observed: float
    expected: float | None = None
    n: int
    p_value: float | None = None
    q_value: float | None = None
    unit: str = "records"


class Scope(BaseModel):
    level: Literal["booth", "household", "record"]
    booth_id: str
    house_no: str | None = None
    voter_ids: list[str] = []  # never rendered in auditor views


class Story(BaseModel):
    code: StoryCode
    label: str
    count: int
    share: float
    ci_lo: float
    ci_hi: float
    evidence: str


class Residual(BaseModel):
    count: int
    expected_background: float
    p_value: float
    significant: bool


class StoryResult(BaseModel):
    booth_id: str
    removed_total: int
    stories: list[Story]
    residual: Residual
    context_used: list[Literal["death_register", "hostel_list", "boundary_changes", "duplicates"]]
    outcome: Outcome


class Card(BaseModel):
    found: str
    why_unusual: str
    innocent_explanations: list[str]
    confidence_text: str
    lang: Literal["en", "hi"]
    source: Literal["llm", "template"]


class GuardResult(BaseModel):
    passed: bool
    blocked_terms: list[str] = []
    rewritten: bool = False


class Review(BaseModel):
    status: ReviewStatus = "open"
    ts: str | None = None
    hash: str | None = None


class Flag(BaseModel):
    flag_id: str  # sha256(type+scope+evidence)[:12]
    type: FlagType
    scope: Scope
    metrics: Metrics
    reason_codes: list[str]
    stories: StoryResult | None = None
    confidence: float = Field(ge=0, le=1)
    confidence_band: Band
    confidence_n: int
    likely_benign: bool
    needs_human_review: Literal[True] = True
    card: Card | None = None
    guard: GuardResult | None = None
    review: Review = Review()


# ---------------------------------------------------------------- claims

class ClaimInput(BaseModel):
    text: str
    source: Literal["text", "image"]
    lang: Lang


class EvidencePoint(BaseModel):
    label: str
    value: float


class Evidence(BaseModel):
    series: list[EvidencePoint] = []
    note: str = ""


class SubClaim(BaseModel):
    id: str
    text: str
    tool: ClaimTool
    params: dict[str, str | int | float] = {}
    query_shown: str
    claimed_value: float | None = None
    computed_value: float | None = None
    tolerance: float = 0.15
    verdict: Verdict
    reason: str
    evidence: Evidence = Evidence()
    confidence: float = Field(ge=0, le=1)
    settle_with: str | None = None


class Mirror(BaseModel):
    claim_text: str
    sub_claim_verdicts: list[Verdict]
    identical_treatment: bool


class ClaimVerdict(BaseModel):
    claim_id: str
    input: ClaimInput
    normalized_claim: str
    sub_claims: list[SubClaim]
    overall: Literal["verified", "disputed", "unprovable", "mixed"]
    confidence: float = Field(ge=0, le=1)
    mirror: Mirror | None = None
    card_png: str | None = None
    guard: GuardResult
    cached: bool = False


# ---------------------------------------------------------------- API I/O

class Health(BaseModel):
    ok: bool
    demo_mode: bool
    versions: dict[str, str]


class Totals(BaseModel):
    v1: int
    v2: int
    added: int
    deleted: int
    modified: int


class BoothSummary(BaseModel):
    booth_id: str
    ward_id: str
    n_v1: int
    n_v2: int
    del_rate: float
    expected_del_rate: float
    q_value: float | None
    flag_count: int
    outcome: Outcome | Literal["normal"]


class Overview(BaseModel):
    totals: Totals
    booths: list[BoothSummary]


class FlagList(BaseModel):
    items: list[Flag]
    total: int


class StoryToggleRequest(BaseModel):
    context_on: list[Literal["death_register", "hostel_list", "boundary_changes", "duplicates"]]


class EngineRunResult(BaseModel):
    flags_total: int
    by_type: dict[str, int]
    runtime_ms: int


class TypeScore(BaseModel):
    type: str
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float


class ReliabilityBin(BaseModel):
    bin_lo: float
    bin_hi: float
    mean_conf: float
    frac_true: float
    n: int


class Miss(BaseModel):
    plant_id: str
    type: str
    why: str


class EvalResult(BaseModel):
    planted_anomalies: int
    planted_decoys: int
    found: int
    decoys_cleared: int
    by_type: list[TypeScore]
    benign_fp_rate: float
    reliability: list[ReliabilityBin]
    misses: list[Miss]


class RuleCard(BaseModel):
    rule_id: str
    what: str
    fires_on_benign_rate: float
    innocent_explanations: list[str]
    resolves_with: str


class SearchMatch(BaseModel):
    voter_id: str
    name_dev: str
    name_lat: str
    booth_id: str
    status_v2: CitizenStatus
    score: float


class SearchResult(BaseModel):
    matches: list[SearchMatch]
    query_normalized: str


class CitizenAsk(BaseModel):
    text: str | None = None
    audio_b64: str | None = None
    lang: Lang | None = None
    channel: Literal["web", "telegram", "whatsapp"]


class CitizenAnswer(BaseModel):
    lang: Lang
    transcript: str | None = None
    answer_text: str
    answer_audio_url: str | None = None
    match: SearchMatch | None = None
    status: CitizenStatus
    reason_category: ReasonCategory
    next_steps: list[str]
    confidence: float = Field(ge=0, le=1)
    guard: GuardResult


class ClaimCheckRequest(BaseModel):
    text: str | None = None
    image_b64: str | None = None
    mirror: bool = True


class ReviewRequest(BaseModel):
    status: Literal["benign", "escalated"]
    note: str = ""


class ReviewResponse(BaseModel):
    review: Review
    audit_hash: str


class AuditEntry(BaseModel):
    ts: str
    flag_id: str
    action: str
    hash: str
    prev_hash: str | None


class GuardLogItem(BaseModel):
    ts: str
    surface: Literal["flag_card", "claim", "citizen", "bot"]
    blocked_terms: list[str]
    rewritten: bool
    fell_back_to_template: bool


class GuardLog(BaseModel):
    checked: int
    blocked: int
    rewritten: int
    items: list[GuardLogItem]


# ---------------------------------------------------------------- Organizations, RBAC & API Keys
OrgRole = Literal["owner", "admin", "auditor", "reviewer", "viewer"]
OrgTier = Literal["free", "pro", "enterprise"]


class QuotaInfo(BaseModel):
    checks_limit: int = 1000
    checks_used: int = 0
    max_seats: int = 5
    seats_used: int = 1
    rate_limit_per_min: int = 60
    pdf_ingest: bool = True


class OrgMember(BaseModel):
    member_id: str
    email: str
    role: OrgRole
    joined_at: str


class ApiKeyItem(BaseModel):
    key_id: str
    name: str
    prefix: str
    last4: str
    role: OrgRole = "auditor"
    scopes: list[str] = ["audit:read", "audit:write", "search"]
    created_at: str
    expires_at: str | None = None
    is_active: bool = True
    last_used_at: str | None = None


class Organization(BaseModel):
    id: str
    name: str
    slug: str
    tier: OrgTier = "pro"
    quotas: QuotaInfo = QuotaInfo()
    created_at: str


class CreateOrgRequest(BaseModel):
    name: str
    slug: str | None = None
    tier: OrgTier = "pro"
    admin_email: str = "admin@rollwatch.org"


class AddMemberRequest(BaseModel):
    email: str
    role: OrgRole = "auditor"


class CreateKeyRequest(BaseModel):
    name: str
    role: OrgRole = "auditor"
    scopes: list[str] = ["audit:read", "audit:write", "search"]
    expires_in_days: int | None = 90


class CreateKeyResponse(BaseModel):
    key_id: str
    name: str
    token: str  # Plaintext key shown once upon creation
    role: OrgRole
    scopes: list[str]
    created_at: str
    expires_at: str | None


# Everything the exporter writes to contracts/schemas/ (and on to web/lib/types.ts).
EXPORTED: list[type[BaseModel]] = [
    RollRow, DeathRecord, HostelRecord, BoundaryChange, Planting,
    Flag, StoryResult, ClaimVerdict,
    Health, Overview, FlagList, StoryToggleRequest, EngineRunResult, EvalResult, RuleCard,
    SearchResult, CitizenAsk, CitizenAnswer, ClaimCheckRequest, ReviewRequest, ReviewResponse,
    AuditEntry, GuardLog,
    Organization, QuotaInfo, OrgMember, ApiKeyItem, CreateOrgRequest, AddMemberRequest,
    CreateKeyRequest, CreateKeyResponse,
]

