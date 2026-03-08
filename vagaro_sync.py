"""
Vagaro API Client — Focus Fitness
Syncs clients from Vagaro into local data/clients.json for marketing use.

Setup:
  1. Contact Vagaro Enterprise Sales to enable API access ($10/month)
     https://support.vagaro.com/hc/en-us/categories/34949493949851
  2. In your Vagaro dashboard: Settings → Developers → APIs & Webhooks
  3. Generate your API token and add it to your .env file:
       VAGARO_API_TOKEN=your_token_here
  4. Run: python3 vagaro_sync.py --sync

Usage:
  python3 vagaro_sync.py --sync          # Pull all clients from Vagaro
  python3 vagaro_sync.py --summary       # Show client database summary
  python3 vagaro_sync.py --segment       # Show client segments
  python3 vagaro_sync.py --export csv    # Export to CSV for Mailchimp etc.
"""

import json
import os
import sys
import csv
import argparse
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR     = Path(__file__).parent / "data"
CLIENTS_FILE = DATA_DIR / "clients.json"
EXPORTS_DIR  = Path(__file__).parent / "exports"
DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# ── Vagaro API config ─────────────────────────────────────────────────────────
VAGARO_API_BASE = "https://api.vagaro.com/v1"
VAGARO_TOKEN    = os.environ.get("VAGARO_API_TOKEN", "")
PAGE_SIZE       = 100   # max records per page


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(endpoint: str, params: dict = None) -> dict:
    """Make an authenticated GET request to the Vagaro API."""
    if not VAGARO_TOKEN:
        raise RuntimeError(
            "VAGARO_API_TOKEN not set. Export it or add it to your .env file.\n"
            "  export VAGARO_API_TOKEN=your_token_here"
        )
    url = f"{VAGARO_API_BASE}/{endpoint.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {VAGARO_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Vagaro API error {e.code}: {body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


# ── Client sync ───────────────────────────────────────────────────────────────

def fetch_all_clients(verbose: bool = True) -> list[dict]:
    """
    Pull the full client list from Vagaro, handling pagination.
    Returns a list of normalized client dicts.
    """
    all_clients = []
    page = 1

    while True:
        if verbose:
            print(f"  Fetching page {page}...", end="\r", flush=True)

        response = _get("customers", params={"pageSize": PAGE_SIZE, "page": page})

        # Vagaro returns data in different shapes — handle both list and paged object
        if isinstance(response, list):
            batch = response
            has_more = len(batch) == PAGE_SIZE
        elif isinstance(response, dict):
            batch = response.get("data") or response.get("customers") or response.get("items") or []
            total  = response.get("total") or response.get("totalCount") or 0
            has_more = len(all_clients) + len(batch) < total
        else:
            batch = []
            has_more = False

        for raw in batch:
            all_clients.append(_normalize(raw))

        if not has_more or not batch:
            break
        page += 1

    return all_clients


def _normalize(raw: dict) -> dict:
    """Normalize a raw Vagaro customer record into a consistent shape."""
    return {
        "id":          raw.get("customerId") or raw.get("id") or "",
        "first_name":  raw.get("customerFirstName") or raw.get("firstName") or "",
        "last_name":   raw.get("customerLastName") or raw.get("lastName") or "",
        "email":       (raw.get("email") or "").lower().strip(),
        "phone":       raw.get("mobilePhone") or raw.get("phone") or raw.get("dayPhone") or "",
        "address":     _build_address(raw),
        "created_at":  raw.get("createdDate") or raw.get("createdAt") or "",
        "last_visit":  raw.get("lastVisitDate") or raw.get("lastVisit") or "",
        "total_visits":raw.get("totalVisits") or raw.get("visitCount") or 0,
        "total_spent": raw.get("totalSpent") or raw.get("lifetimeValue") or 0.0,
        "tags":        raw.get("tags") or [],
        "active":      raw.get("active", True),
        "notes":       raw.get("notes") or "",
        "synced_at":   datetime.now().isoformat(),
    }


def _build_address(raw: dict) -> str:
    parts = [
        raw.get("streetAddress") or raw.get("address") or "",
        raw.get("city") or "",
        raw.get("regionCode") or raw.get("state") or "",
        raw.get("postalCode") or raw.get("zip") or "",
    ]
    return ", ".join(p for p in parts if p)


def sync(verbose: bool = True) -> dict:
    """Full sync: fetch from Vagaro, save to local file. Returns summary."""
    if verbose:
        print("Connecting to Vagaro API...")

    clients = fetch_all_clients(verbose=verbose)

    # Merge with existing data to preserve any local notes
    existing = _load_local()
    existing_map = {c["id"]: c for c in existing}
    for c in clients:
        if c["id"] in existing_map:
            # Preserve local notes, merge remote data
            local = existing_map[c["id"]]
            c["notes"] = c["notes"] or local.get("notes", "")

    _save_local(clients)
    summary = _summarize(clients)

    if verbose:
        print(f"\n✓ Synced {len(clients)} clients from Vagaro")
        print(f"  With email:  {summary['with_email']}")
        print(f"  With phone:  {summary['with_phone']}")
        print(f"  Active:      {summary['active']}")
        print(f"  Saved to:    {CLIENTS_FILE}")

    return summary


# ── Local storage ─────────────────────────────────────────────────────────────

def _load_local() -> list[dict]:
    if CLIENTS_FILE.exists():
        try:
            return json.loads(CLIENTS_FILE.read_text())
        except Exception:
            return []
    return []


def _save_local(clients: list[dict]) -> None:
    CLIENTS_FILE.write_text(json.dumps(clients, indent=2, default=str))


# ── Segmentation ──────────────────────────────────────────────────────────────

def segment_clients(
    clients: Optional[list[dict]] = None,
    inactive_days: int = 30,
) -> dict[str, list[dict]]:
    """
    Split clients into named segments for targeted marketing.

    Segments:
      active_recent   — visited within last 30 days (most engaged)
      at_risk         — last visit 31–90 days ago (save them)
      lapsed          — last visit 91–365 days ago (win-back candidates)
      lost            — last visit over 1 year ago (long-shot win-back)
      never_visited   — in system but no visits recorded
      no_email        — no email on file (can't email them)
      no_phone        — no phone on file (can't text them)
      high_value      — top 20% by total spend
    """
    if clients is None:
        clients = _load_local()

    now = datetime.now()

    def days_since(date_str: str) -> Optional[int]:
        if not date_str:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return (now - datetime.strptime(date_str[:10], fmt[:10])).days
            except ValueError:
                continue
        return None

    # Sort clients by spend to find top 20%
    spenders = sorted(
        [c for c in clients if float(c.get("total_spent") or 0) > 0],
        key=lambda c: float(c.get("total_spent") or 0),
        reverse=True,
    )
    top_20_pct_cutoff = int(len(spenders) * 0.2)
    high_value_ids = {c["id"] for c in spenders[:max(1, top_20_pct_cutoff)]}

    segments: dict[str, list[dict]] = {
        "active_recent":  [],
        "at_risk":        [],
        "lapsed":         [],
        "lost":           [],
        "never_visited":  [],
        "no_email":       [],
        "no_phone":       [],
        "high_value":     [],
    }

    for c in clients:
        if not c.get("active", True):
            continue

        if c["id"] in high_value_ids:
            segments["high_value"].append(c)

        if not c.get("email"):
            segments["no_email"].append(c)
            continue  # can't email them — still check phone

        if not c.get("phone"):
            segments["no_phone"].append(c)

        last = days_since(c.get("last_visit"))
        if last is None:
            segments["never_visited"].append(c)
        elif last <= 30:
            segments["active_recent"].append(c)
        elif last <= 90:
            segments["at_risk"].append(c)
        elif last <= 365:
            segments["lapsed"].append(c)
        else:
            segments["lost"].append(c)

    return segments


def _summarize(clients: list[dict]) -> dict:
    segs = segment_clients(clients)
    return {
        "total":          len(clients),
        "with_email":     sum(1 for c in clients if c.get("email")),
        "with_phone":     sum(1 for c in clients if c.get("phone")),
        "active":         sum(1 for c in clients if c.get("active", True)),
        "synced_at":      datetime.now().isoformat(),
        "segments": {k: len(v) for k, v in segs.items()},
    }


# ── Outreach generation ───────────────────────────────────────────────────────

EMAIL_TEMPLATES = {
    "win_back": {
        "subject": "We miss you at Focus Fitness, {first_name}",
        "body": (
            "Hey {first_name},\n\n"
            "It's been a while since we've seen you at Focus Fitness — "
            "just wanted to check in and see how you're doing.\n\n"
            "No judgment here. Life gets in the way. But I know how hard you worked "
            "when you were coming in, and I'd love to have you back.\n\n"
            "Come back for 2 weeks free — no strings attached. "
            "Your membership picks back up after.\n\n"
            "Just reply to this email and we'll set it up.\n\n"
            "— [Coach Name]\n"
            "Focus Fitness, Levittown PA\n"
            "[PHONE] | [EMAIL]"
        ),
    },
    "referral_ask": {
        "subject": "Quick favor, {first_name}",
        "body": (
            "Hey {first_name},\n\n"
            "Quick one — do you know anyone in Levittown who's been thinking about "
            "getting stronger but hasn't pulled the trigger yet?\n\n"
            "Send them our way. If they sign up, you both get a free month. Simple.\n\n"
            "Just have them mention your name when they reach out.\n\n"
            "Thanks for being part of Focus Fitness 💪\n\n"
            "— [Coach Name]\n"
            "Focus Fitness, Levittown PA"
        ),
    },
    "new_promo": {
        "subject": "Something new at Focus Fitness, {first_name}",
        "body": (
            "Hey {first_name},\n\n"
            "[INSERT PROMO/NEWS HERE]\n\n"
            "As always — if you have questions or want to schedule, "
            "just reply or text us at [PHONE].\n\n"
            "— [Coach Name]\n"
            "Focus Fitness, Levittown PA"
        ),
    },
    "check_in": {
        "subject": "Checking in, {first_name}",
        "body": (
            "Hey {first_name},\n\n"
            "Haven't seen you in a bit — everything ok?\n\n"
            "If something's come up or you have questions about your program, "
            "just reply. We're here.\n\n"
            "— [Coach Name]\n"
            "Focus Fitness, Levittown PA"
        ),
    },
}

SMS_TEMPLATES = {
    "win_back": (
        "Hey {first_name}, it's [Coach] from Focus Fitness! "
        "Missed seeing you — come back for 2 weeks free, no strings. "
        "Interested? Just reply YES."
    ),
    "referral_ask": (
        "Hey {first_name}! [Coach] here. Know anyone in Levittown who wants to get stronger? "
        "Send them our way — you both get a free month. Just have them mention your name 💪"
    ),
    "check_in": (
        "Hey {first_name}, [Coach] from Focus Fitness. Missed you this week — everything ok? "
        "Let me know if you need anything."
    ),
    "promo": (
        "Hey {first_name}! [Coach] at Focus Fitness — [INSERT OFFER]. "
        "Reply STOP to opt out."
    ),
}


def generate_outreach(
    segment_name: str,
    channel: str,
    template_name: str,
    limit: int = 0,
) -> dict:
    """
    Generate personalized email or SMS messages for a client segment.

    Args:
        segment_name: e.g. 'lapsed', 'at_risk', 'active_recent'
        channel: 'email' or 'sms'
        template_name: e.g. 'win_back', 'referral_ask', 'check_in', 'new_promo'
        limit: max messages to generate (0 = all)

    Returns:
        dict with 'messages' list, 'segment_count', 'skipped' (no contact info), etc.
    """
    clients = _load_local()
    if not clients:
        return {"error": "No clients synced yet. Run sync() first."}

    segments = segment_clients(clients)
    segment = segments.get(segment_name, [])

    if not segment:
        return {"error": f"Segment '{segment_name}' is empty or doesn't exist."}

    if channel == "email":
        templates = EMAIL_TEMPLATES
        contact_field = "email"
    else:
        templates = SMS_TEMPLATES
        contact_field = "phone"

    template = templates.get(template_name)
    if not template:
        return {"error": f"Template '{template_name}' not found for {channel}."}

    messages = []
    skipped  = []
    batch    = segment[:limit] if limit else segment

    for client in batch:
        contact = client.get(contact_field, "")
        if not contact:
            skipped.append(f"{client['first_name']} {client['last_name']} (no {contact_field})")
            continue

        ctx = {
            "first_name": client.get("first_name") or "there",
            "last_name":  client.get("last_name") or "",
            "email":      client.get("email") or "",
            "phone":      client.get("phone") or "",
        }

        if channel == "email":
            messages.append({
                "to_name":  f"{ctx['first_name']} {ctx['last_name']}".strip(),
                "to_email": contact,
                "subject":  template["subject"].format(**ctx),
                "body":     template["body"].format(**ctx),
            })
        else:
            messages.append({
                "to_name":  f"{ctx['first_name']} {ctx['last_name']}".strip(),
                "to_phone": contact,
                "message":  template.format(**ctx) if isinstance(template, str) else template.format(**ctx),
            })

    return json.dumps({
        "segment":       segment_name,
        "channel":       channel,
        "template":      template_name,
        "segment_total": len(segment),
        "generated":     len(messages),
        "skipped":       len(skipped),
        "skipped_names": skipped[:10],
        "messages":      messages,
    }, indent=2)


# ── CSV export ────────────────────────────────────────────────────────────────

def export_csv(segment_name: Optional[str] = None, filename: Optional[str] = None) -> str:
    """
    Export clients (or a segment) to CSV for Mailchimp, Constant Contact, etc.
    Returns the path to the exported file.
    """
    clients = _load_local()
    if not clients:
        raise RuntimeError("No clients synced. Run sync() first.")

    if segment_name:
        segments = segment_clients(clients)
        clients = segments.get(segment_name, [])
        if not clients:
            raise RuntimeError(f"Segment '{segment_name}' is empty.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    label     = segment_name or "all_clients"
    outfile   = EXPORTS_DIR / (filename or f"{timestamp}_{label}.csv")

    fields = ["first_name", "last_name", "email", "phone", "address",
              "last_visit", "total_visits", "total_spent", "tags"]

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for c in clients:
            row = dict(c)
            row["tags"] = ", ".join(c.get("tags") or [])
            writer.writerow(row)

    return str(outfile)


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_summary():
    clients = _load_local()
    if not clients:
        print("No clients synced yet. Run: python3 vagaro_sync.py --sync")
        return
    s = _summarize(clients)
    print(f"\n{'='*50}")
    print(f"  Focus Fitness Client Database")
    print(f"{'='*50}")
    print(f"  Total clients:   {s['total']}")
    print(f"  With email:      {s['with_email']}")
    print(f"  With phone:      {s['with_phone']}")
    print(f"  Last synced:     {s['synced_at'][:19]}")
    print(f"\n  Segments:")
    for seg, count in s["segments"].items():
        print(f"    {seg:<20} {count}")
    print()


def _print_segments():
    clients = _load_local()
    if not clients:
        print("No clients. Run --sync first.")
        return
    segs = segment_clients(clients)
    print(f"\nClient Segments:")
    for name, members in segs.items():
        print(f"\n  {name.upper()} ({len(members)})")
        for c in members[:5]:
            print(f"    • {c['first_name']} {c['last_name']} — {c.get('email','')} | last visit: {c.get('last_visit','?')[:10]}")
        if len(members) > 5:
            print(f"    ... and {len(members)-5} more")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vagaro client sync tool for Focus Fitness")
    parser.add_argument("--sync",    action="store_true", help="Pull all clients from Vagaro API")
    parser.add_argument("--summary", action="store_true", help="Show client database summary")
    parser.add_argument("--segment", action="store_true", help="Show client segments")
    parser.add_argument("--export",  metavar="SEGMENT",   help="Export segment to CSV (use 'all' for all clients)")
    args = parser.parse_args()

    if args.sync:
        sync()
    elif args.summary:
        _print_summary()
    elif args.segment:
        _print_segments()
    elif args.export:
        seg = None if args.export == "all" else args.export
        path = export_csv(segment_name=seg)
        print(f"Exported to: {path}")
    else:
        parser.print_help()
