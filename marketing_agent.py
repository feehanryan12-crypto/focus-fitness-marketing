"""
Focus Fitness Marketing Agent
Levittown, PA | Strength Training | No Bullshit.

Powered by Claude Opus 4.6 with adaptive thinking + web search.
Run: python3 marketing_agent.py
"""

import json
import os
import sys
import threading
import time
import itertools
from datetime import datetime
from pathlib import Path
import anthropic
import vagaro_sync

# ── Paths ────────────────────────────────────────────────────────────────────
REPO_DIR   = Path(__file__).parent
PLANS_DIR  = REPO_DIR / "plans"
DATA_DIR   = REPO_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.json"
PLANS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ── ANSI colors ───────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
DIM    = "\033[2m"

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Business context ──────────────────────────────────────────────────────────
BUSINESS = {
    "name": "Focus Fitness",
    "location": "Levittown, PA",
    "zip_codes": ["19054", "19055", "19056", "19057", "19058"],
    "nearby": ["Bristol PA", "Fairless Hills PA", "Tullytown PA", "Penndel PA"],
    "services": ["personal training", "group strength classes"],
    "focus": "strength training",
    "brand_voice": "No bullshit. Efficient hard work. No gimmicks.",
    "target_age": "25–60",
    "monthly_budget": 200,
    "usp": "Real strength training in Levittown with zero gimmicks. You work hard, you get results.",
}

SYSTEM_PROMPT = f"""You are an elite marketing strategist and direct-response copywriter specializing in local fitness businesses.
You have 20+ years of experience across digital advertising, brand building, social media, email marketing,
community-based marketing, and retention strategy. You have helped hundreds of independent gyms, personal
trainers, and strength coaches grow their businesses from scratch with tight budgets.

Your client is {BUSINESS['name']} in {BUSINESS['location']}.
- Services: {', '.join(BUSINESS['services'])}
- Focus: {BUSINESS['focus']}
- Brand voice: {BUSINESS['brand_voice']}
- Target audience: Adults {BUSINESS['target_age']} in Levittown who want to get genuinely stronger
- Monthly marketing budget: ${BUSINESS['monthly_budget']}
- Nearby areas to target: {', '.join(BUSINESS['nearby'])}

Your deep expertise includes:
- Facebook & Instagram ad strategy, targeting, and copywriting
- Google Business Profile optimization and local SEO
- Direct response copywriting (headlines, hooks, CTAs, email, SMS)
- Content calendars and organic social media strategy
- Email drip sequences and SMS follow-up systems
- Referral and retention programs
- Seasonal promotions and campaign planning
- Competitor and market analysis (use web search when relevant)
- Brand positioning for independent gyms against big-box competitors
- Pricing strategy and value ladders
- Community building and word-of-mouth amplification
- ROI tracking and budget allocation

You think like a performance marketer but write like a human being.
You always match the client's voice: direct, confident, no fluff.
When you use tools, combine their outputs into cohesive, actionable recommendations.
Never recommend spending money the client doesn't have.
Prioritize high-ROI, low-cost tactics first.
Use web search when you need current competitor info, local market data, or industry trends.
"""


# ── Persistence helpers ───────────────────────────────────────────────────────

def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            data = json.loads(HISTORY_FILE.read_text())
            # Keep last 40 messages to avoid context overflow
            return data[-40:] if len(data) > 40 else data
        except Exception:
            return []
    return []


def save_history(history: list) -> None:
    try:
        HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str))
    except Exception:
        pass


# ── Spinner ───────────────────────────────────────────────────────────────────

class Spinner:
    def __init__(self, message: str = "Thinking"):
        self._msg = message
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        for frame in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
            if self._stop.is_set():
                break
            sys.stdout.write(f"\r{DIM}{frame} {self._msg}...{RESET}")
            sys.stdout.flush()
            time.sleep(0.08)
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        self._thread.join()


# ── Tool functions ────────────────────────────────────────────────────────────

def generate_ad_copy(platform: str, goal: str, tone: str = "direct and confident", offer: str = "free first class") -> str:
    copies = {
        "Facebook": [
            f"Tired of gyms full of machines you don't need and trainers who don't push you?\n\n"
            f"Focus Fitness in Levittown is different.\n\n"
            f"We do one thing: make you stronger. No cardio bunny classes. No mirror selfie crowd. "
            f"Just real barbells and people who show up to work.\n\n"
            f"👉 {offer.capitalize()}. Limited spots. DM us or click below.",

            f"Most gyms sell you a membership. We sell you results.\n\n"
            f"Strength training for adults who are serious about getting stronger — "
            f"in Levittown, 10 minutes from your front door.\n\n"
            f"Personal training & group classes. No gimmicks.\n\n"
            f"➡ {offer.capitalize()} — no credit card, no commitment.",

            f"Here's the truth most gyms won't tell you:\n\n"
            f"Cardio won't make you strong. Machines won't make you strong. "
            f"A program that actually progresses you will.\n\n"
            f"That's Focus Fitness. Levittown, PA.\n\n"
            f"→ {offer.capitalize()}. No BS, no upsells.",
        ],
        "Instagram": [
            f"Strong is not a look. It's a lifestyle.\n\n"
            f"Strength training in Levittown, PA 📍\n"
            f"Personal training + group classes.\n\n"
            f"DM us for your {offer}.",

            f"You don't need more motivation. You need a coach and a barbell.\n\n"
            f"Levittown, PA 📍 | No gimmicks. No machines. No mirrors.\n\n"
            f"First class free → link in bio.",

            f"We're not for everyone.\n\n"
            f"We're for people who want to actually get stronger.\n\n"
            f"📍 Levittown PA | Strength training done right\n"
            f"→ {offer.capitalize()}. DM us.",
        ],
        "Google": [
            f"Strength Training Levittown PA | Personal Trainer | {offer.capitalize()} | Focus Fitness",
            f"Personal Trainer Near Me Levittown | Real Results, No Gimmicks | {offer.capitalize()}",
            f"Best Gym Levittown PA | Strength Classes & Personal Training | Focus Fitness",
        ],
    }
    result = {
        "platform": platform,
        "goal": goal,
        "offer": offer,
        "ad_copies": copies.get(platform, copies["Facebook"]),
        "ab_test_tip": "Run 2 variations simultaneously for 7 days. Kill the loser, double the winner's budget.",
        "pro_tip": "Facebook: use Lead Ads (instant form) so prospects never leave the app. Always follow up within 1 hour.",
    }
    return json.dumps(result, indent=2)


def build_content_calendar(month: str, posts_per_week: int = 4, platforms: str = "Instagram, Facebook") -> str:
    all_themes = [
        ("Monday",    "Mindset/Hook",    "Bold statement or uncomfortable truth about fitness that stops the scroll"),
        ("Tuesday",   "Training Clip",   "15-30 sec raw video: member hitting a PR, coach cueing a lift, class energy"),
        ("Wednesday", "Education",       "Teach one thing: 'Why the deadlift beats the leg press' or 'The only 3 lifts you need'"),
        ("Thursday",  "Social Proof",    "Member milestone, testimonial, before/after, or PR board update"),
        ("Friday",    "Behind the Scenes", "Coach setup, class recap, day-in-the-life — builds culture and trust"),
        ("Saturday",  "Offer/CTA",       "Direct push: free first class, current promo, or referral program reminder"),
        ("Sunday",    "Engagement",      "Question, poll, or challenge: 'What's your current deadlift PR?' or 'Tag someone who needs this'"),
    ]
    weekly_plan = all_themes[:posts_per_week]
    return json.dumps({
        "month": month,
        "platforms": platforms,
        "posts_per_week": posts_per_week,
        "weekly_content_themes": [{"day": t[0], "theme": t[1], "idea": t[2]} for t in weekly_plan],
        "monthly_arc": {
            "week_1": "Introduce/reintroduce — who you are and what you stand for",
            "week_2": "Education — teach your audience why strength training is the answer",
            "week_3": "Social proof — results, member stories, PRs",
            "week_4": "Conversion — push hard on your free first class offer",
        },
        "hashtag_sets": {
            "local": "#LevittownPA #LevittownFitness #BristolPA #FairlessHills #BucksCountyFitness",
            "niche": "#StrengthTraining #Powerlifting #BarbelTraining #GetStrong #LiftHeavy",
            "broad": "#Fitness #PersonalTrainer #GymLife #FitLife #WorkoutMotivation",
        },
        "rules": [
            "Raw > polished. Your phone camera is fine. Authenticity wins.",
            "Stories daily. Feed posts 4x/week. Reels 1-2x/week.",
            "Reply to every comment within 2 hours — the algorithm rewards it.",
            "Never post without a CTA. Every post should have a next step.",
        ],
    }, indent=2)


def analyze_audience(segment: str = "primary") -> str:
    segments = {
        "primary": {
            "name": "The Lapsed Athlete (35–55)",
            "demographics": "Adults 35–55, Levittown/Bucks County, $60K–$120K HHI, homeowners",
            "psychographics": [
                "Was athletic in their 20s, let it slip",
                "Tired of spinning their wheels at commercial gyms",
                "Wants real results, not entertainment or social fitness",
                "Values efficiency — wants a 45-minute session that actually does something",
                "Skeptical of fitness trends, fads, and supplements",
                "Motivated by measurable progress (weight on the bar)",
            ],
            "pain_points": [
                "Doesn't know how to program strength training correctly",
                "Has tried and quit big-box gyms multiple times",
                "Busy — kids, job, commute — can't waste time on ineffective workouts",
                "Slightly intimidated by barbell gyms but won't admit it",
            ],
            "best_channels": ["Facebook Ads", "Google Search", "Word of mouth from friends"],
            "messaging_that_works": "Stop wasting time. Get strong. We show you exactly how.",
            "messaging_to_avoid": "Transformation photos, before/afters (too salesy for this demo)",
        },
        "secondary": {
            "name": "Young Professional (25–35)",
            "demographics": "Adults 25–35, Levittown area, commuters, $45K–$80K income",
            "psychographics": [
                "Was athletic in high school or college, fell off in their mid-20s",
                "Wants to look and feel strong — not skinny, not bulky",
                "Social — will bring friends if they love the culture",
                "Instagram-active, influenced by strength/lifting content",
                "Values community and belonging as much as results",
            ],
            "pain_points": [
                "Expensive Planet Fitness membership they never use",
                "Needs accountability and a coach to actually show up",
                "Doesn't know how to start barbell training safely",
            ],
            "best_channels": ["Instagram Ads", "Referrals", "Organic social"],
            "messaging_that_works": "The gym you've been looking for. No machines. No mirrors. Just progress.",
        },
        "tertiary": {
            "name": "Over-50 New Starter (50–65)",
            "demographics": "Adults 50–65, Levittown, often recently motivated by health scare or doctor's advice",
            "psychographics": [
                "Was told strength training is important for bone density, metabolism, longevity",
                "Nervous about injury, needs to trust the coach completely",
                "Responds to authority and expertise",
                "Very loyal once they commit — low churn",
            ],
            "pain_points": [
                "Scared of 'hardcore' gym culture",
                "Has real physical limitations (knees, back)",
                "Doesn't know where to start",
            ],
            "best_channels": ["Google Search", "Facebook", "Doctor referrals", "Community boards"],
            "messaging_that_works": "Strength training designed for real people. Safe, coached, and effective.",
        },
    }
    if segment == "all":
        return json.dumps(segments, indent=2)
    return json.dumps(segments.get(segment, segments["primary"]), indent=2)


def create_offer(goal: str, season: str = "general", budget_sensitive: bool = True) -> str:
    offers = {
        "get new members": [
            {
                "name": "Free First Class",
                "description": "Walk in, try a group class or PT session free. No signup, no card.",
                "why_it_works": "Removes all risk. Most people who try once come back.",
                "cost": "$0",
                "promote_via": "Facebook/Instagram Lead Ads, Google Business, word of mouth",
            },
            {
                "name": "Bring a Friend Week",
                "description": "Any current member can bring one guest free for a full week.",
                "why_it_works": "Warm referrals convert at 5x the rate of cold ads.",
                "cost": "$0",
                "promote_via": "Text/DM all current members, announce in class",
            },
            {
                "name": "30-Day Commitment Challenge",
                "description": "First month $99 (vs. $149) if they attend 12+ sessions in 30 days.",
                "why_it_works": "Creates habit. Members who hit 12 sessions in month 1 almost never quit.",
                "cost": "$50 revenue reduction — offset by lifetime value",
                "promote_via": "Facebook Ads → landing page or Lead Ad form",
            },
        ],
        "retain current members": [
            {
                "name": "PR Board + Milestone Rewards",
                "description": "Public PR board. At 50/100/200 sessions: free shirt, free month, public shoutout.",
                "why_it_works": "Gamification creates emotional investment. Stopping feels like losing progress.",
                "cost": "Shirt ~$15, free month ~$149 — tiny vs. member LTV",
            },
            {
                "name": "Check-in Text",
                "description": "Text any member who misses 2+ sessions: 'Hey [name], missed you this week. Everything ok?'",
                "why_it_works": "Personal outreach stops churn before it starts. Most gyms never do this.",
                "cost": "$0 — 2 minutes of your time",
            },
        ],
        "reactivate lapsed members": [
            {
                "name": "Win-Back Offer",
                "description": "Text or email lapsed members: 'We miss you. Come back for 2 weeks free, no questions asked.'",
                "why_it_works": "They already know you. Re-acquisition cost is 5x lower than new member acquisition.",
                "cost": "2 weeks free (~$70 value)",
            },
        ],
    }
    return json.dumps({
        "goal": goal,
        "season": season,
        "recommended_offers": offers.get(goal, offers["get new members"]),
        "golden_rule": "Zero friction to claim. Zero risk to the prospect. Never require a card for a trial.",
    }, indent=2)


def write_google_business_post(topic: str, include_cta: bool = True) -> str:
    posts = {
        "strength tip": (
            "The #1 mistake people make at the gym: too much variety, not enough consistency.\n\n"
            "At Focus Fitness in Levittown, we build your strength on the fundamentals — "
            "squat, deadlift, press, row. We progress them every week.\n\n"
            "Show up. Work hard. Get stronger. That's the whole program.\n\n"
            "📍 Levittown, PA | Personal Training & Group Classes\n"
            "First class free — call or DM us to schedule."
        ),
        "member result": (
            "New PR at Focus Fitness Levittown 💪\n\n"
            "One of our members hit a new personal best on the deadlift this week — "
            "after just 8 weeks of coaching. No magic, no gimmicks. Just showing up and working.\n\n"
            "If you're in Levittown and want to actually get stronger, your first class is on us."
        ),
        "offer": (
            "New to Focus Fitness? Your first class is free.\n\n"
            "We offer personal training and group strength classes in Levittown, PA.\n\n"
            "No mirrors. No machines. No fluff. Just a coach, a barbell, and a plan.\n\n"
            "Message us or call to claim your free session. Spots are limited."
        ),
        "class schedule": (
            "Updated class schedule now live at Focus Fitness Levittown!\n\n"
            "New time slots available to fit around your work schedule.\n\n"
            "Strength training. Small groups. Real coaching.\n\n"
            "📞 Call or DM us to reserve your spot."
        ),
        "why strength training": (
            "Why strength training beats everything else as you get older:\n\n"
            "→ Builds bone density\n"
            "→ Boosts metabolism\n"
            "→ Improves posture and reduces joint pain\n"
            "→ Increases energy and confidence\n\n"
            "Focus Fitness | Levittown, PA\n"
            "Personal training & group classes. First class free."
        ),
    }
    return json.dumps({
        "post_content": posts.get(topic, posts["strength tip"]),
        "cta_button": "Call now" if include_cta else None,
        "character_count": len(posts.get(topic, posts["strength tip"])),
        "seo_tips": [
            "Post minimum once per week — Google ranks active profiles higher.",
            "Always include 'Levittown' and 'PA' naturally in the text.",
            "Add a photo to every post — 3x more views.",
            "Respond to every Google review within 24 hours.",
            "Use the 'What's New' post type for evergreen content.",
        ],
    }, indent=2)


def plan_facebook_ad_campaign(objective: str, duration_days: int = 30, monthly_budget: int = 120) -> str:
    daily = round(monthly_budget / 30, 2)
    return json.dumps({
        "objective": objective,
        "platform": "Facebook + Instagram (same campaign, Meta Ads Manager)",
        "budget": {
            "monthly_total": f"${monthly_budget}",
            "daily": f"${daily}",
            "split": {
                "cold_prospecting": f"${round(monthly_budget * 0.7)} — new people who don't know you",
                "warm_retargeting": f"${round(monthly_budget * 0.3)} — people who've interacted with your page/ads",
            },
        },
        "targeting": {
            "locations": BUSINESS["zip_codes"] + BUSINESS["nearby"],
            "radius": "5 miles from Levittown center",
            "age_range": "28–58",
            "interests": [
                "Weightlifting", "Strength training", "Powerlifting",
                "Barbell training", "Physical fitness", "CrossFit",
                "Men's Health magazine", "Muscle & Fitness",
            ],
            "lookalike_audience": "Upload your current member list to Meta → create 1% lookalike audience in PA",
            "exclusions": "Exclude people who already liked your page (unless retargeting campaign)",
        },
        "creative_plan": [
            {"week": "1-2", "format": "Video 15-30s", "content": "Raw training footage — real lifts, real people, no music overlay needed"},
            {"week": "3-4", "format": "Single image", "content": "PR board, member milestone, or strong headline text overlay on gym photo"},
        ],
        "ad_copy_formula": "Pain → Agitation → Solution → CTA. Example: 'Tired of going to the gym and not getting stronger? [agitate] → Focus Fitness [solution] → First class free [CTA]'",
        "testing": "Always run 2 ad variations. After 7 days, pause the loser. Scale the winner.",
        "kpis": {
            "cost_per_lead": "$5–$15 (good), under $5 (great), over $20 (pause and retest)",
            "ctr": "1.5%+ feed, 3%+ stories",
            "lead_to_trial_rate": "30%+ (if lower, fix your follow-up speed)",
        },
        "rules": [
            "Use Lead Ads (instant form) — never send people to a website they'll abandon.",
            "Follow up every lead within 1 hour. Every hour you wait, conversion drops 10x.",
            "Never boost posts. Always use Ads Manager for targeting control.",
            "Monday/Tuesday ads are cheaper — CPMs spike on weekends.",
        ],
    }, indent=2)


def write_referral_program(reward_type: str = "free month") -> str:
    return json.dumps({
        "program_name": "Bring Your People",
        "tagline": "Get stronger together.",
        "mechanism": {
            "step_1": "Current member refers a friend",
            "step_2": "Friend completes their first paid month",
            "step_3": "BOTH get rewarded",
        },
        "rewards": {
            "referrer": f"One free month ({reward_type}) — $149 value",
            "new_member": "First month at 50% off",
            "why_double_sided": "Double-sided rewards increase referral rates 3x vs. one-sided. The new member has more reason to sign up.",
        },
        "launch_plan": [
            "1. Announce verbally in every class this week.",
            "2. Text every current member: 'Hey [name] — we launched a referral program. Refer a friend who joins, you both get a free month. That's it.'",
            "3. Post to Instagram + Facebook stories (not just feed).",
            "4. Put a simple sign at the gym entrance.",
        ],
        "tracking": "Spreadsheet: member name | referred friend | date joined | reward given. Keep it simple.",
        "who_to_ask_first": "Your 5 most enthusiastic members. Ask them personally. A warm ask converts 10x better than a mass text.",
        "pro_tip": "Run 'Bring a Friend Week' quarterly — any member can bring a guest free for 7 days. Low commitment = high conversion.",
    }, indent=2)


def diagnose_marketing(area: str) -> str:
    diagnoses = {
        "low leads": {
            "root_causes": [
                "No compelling reason to try you over a cheaper gym",
                "Google Business not fully optimized — you're invisible in local search",
                "Ads targeting too broad, wrong age, or wrong message",
                "No follow-up system — leads fall through the cracks",
                "No referral program — your happiest members aren't working for you",
            ],
            "fix_this_week": [
                "Check your Google Business — complete profile, add 5 recent photos, post something",
                "Text every current member asking for one referral",
                "Launch a Facebook Lead Ad with the free first class offer targeting Levittown zip codes",
            ],
            "fix_this_month": [
                "Set up a lead response workflow: inquiry → call/text within 1 hour → book free trial → follow up 24hrs later",
                "Get 10 Google reviews (text members a direct link to your review page)",
                "Launch the referral program formally",
            ],
        },
        "high churn": {
            "root_causes": [
                "Members aren't seeing progress — no visible tracking system",
                "No community — members train alongside strangers, not a tribe",
                "No check-in when they start missing sessions",
                "Price objection — no mid-tier option between intro and full price",
            ],
            "fix_this_week": [
                "Create a PR board — even a whiteboard creates emotional investment in staying",
                "Call out every PR in class. Post them on social. Make progress visible.",
                "Text every member who's missed 2+ sessions: 'Hey, missed you — everything ok?'",
            ],
        },
        "low ad roi": {
            "root_causes": [
                "Boosting posts instead of using Ads Manager (kills targeting precision)",
                "No A/B testing — running one ad and hoping",
                "Follow-up too slow — leads go cold in under an hour",
                "Landing in wrong audience — too broad, too old/young, wrong geography",
            ],
            "fix_this_week": [
                "Kill all boosted posts. Move everything to Ads Manager.",
                "Run 2 ad variations simultaneously — different headlines, same offer",
                "Set a phone alarm to check and respond to leads every 2 hours during business hours",
            ],
        },
        "weak social media": {
            "root_causes": [
                "Posting quotes and stock photos instead of real training footage",
                "No consistent schedule — followers forget you exist",
                "Every post is an ad — no value, no reason to follow",
                "No call to action — people don't know what to do next",
            ],
            "fix_this_week": [
                "Film 3 clips today during your next session. 15 seconds each, no editing.",
                "Post one now with: 'This is what we do. First class free. DM us.'",
                "Set phone reminders: post Mon/Wed/Fri/Sat — no exceptions for 30 days",
            ],
        },
        "pricing": {
            "market_rates": {
                "group_class_membership": "$120–$160/month unlimited",
                "personal_training": "$65–$95/session, or $250–$320/month (4 sessions)",
                "intro_package": "$79–$129 for 2-3 sessions",
            },
            "recommendation": (
                "Group membership: $139/month unlimited. "
                "PT: $79/session or $299/month (4 sessions). "
                "Intro offer: $99 for 2 sessions — low barrier, high commitment signal."
            ),
            "principle": "Price for the result, not the time. You're not selling 45-minute sessions. You're selling a stronger body.",
        },
    }
    return json.dumps(diagnoses.get(area, {
        "message": f"No preset diagnosis for '{area}'. Describe the problem in more detail and I'll give you a direct recommendation.",
    }), indent=2)


def write_email_sequence(trigger: str, num_emails: int = 3, goal: str = "convert to member") -> str:
    sequences = {
        "new_inquiry": [
            {
                "email": 1,
                "timing": "Immediately (within 5 minutes of inquiry)",
                "subject": "Your free class at Focus Fitness — here's what to know",
                "body": (
                    "Hey [Name],\n\n"
                    "Thanks for reaching out. Your first class at Focus Fitness is free — no credit card, no commitment.\n\n"
                    "Here's what to expect:\n"
                    "→ Show up 10 minutes early\n"
                    "→ Wear comfortable clothes and sneakers\n"
                    "→ We'll go over your goals and get you started on the right movements\n\n"
                    "Classes run [TIMES]. Which works best for you this week?\n\n"
                    "Just reply to this email or text me at [PHONE].\n\n"
                    "— [Coach Name]\n"
                    "Focus Fitness, Levittown"
                ),
            },
            {
                "email": 2,
                "timing": "Day 2 (if no reply)",
                "subject": "Still have a spot for you",
                "body": (
                    "Hey [Name],\n\n"
                    "Just following up — I still have your free class held.\n\n"
                    "A lot of people are nervous their first time in a strength gym. That's normal. "
                    "We coach every movement from scratch, regardless of your experience level.\n\n"
                    "What's a good time this week?\n\n"
                    "— [Coach Name]"
                ),
            },
            {
                "email": 3,
                "timing": "Day 5 (final follow-up)",
                "subject": "Last chance for your free class",
                "body": (
                    "Hey [Name],\n\n"
                    "I don't want to keep blowing up your inbox — but I also don't want you to miss out.\n\n"
                    "Your free class offer stands through [DATE]. After that I'll release the spot.\n\n"
                    "If the timing isn't right or you have questions, just reply — no pressure.\n\n"
                    "— [Coach Name]"
                ),
            },
        ],
        "post_trial": [
            {
                "email": 1,
                "timing": "Same day, 2 hours after trial class",
                "subject": "How'd it go?",
                "body": (
                    "Hey [Name],\n\n"
                    "Great having you in today. How are you feeling?\n\n"
                    "I think you'd be a great fit here. If you want to keep going, "
                    "I'd love to get you started on a proper program.\n\n"
                    "Membership is $139/month — no contracts, cancel anytime. "
                    "Or grab a 4-session intro package at $99 if you want to try it out first.\n\n"
                    "What do you want to do?\n\n"
                    "— [Coach Name]"
                ),
            },
            {
                "email": 2,
                "timing": "Day 3 (if no decision)",
                "subject": "Quick question",
                "body": (
                    "Hey [Name],\n\n"
                    "What's holding you back?\n\n"
                    "I ask because most people who try one class tell me they loved it but then get busy. "
                    "I get it. Life happens.\n\n"
                    "If it's timing, cost, or anything else — just tell me. "
                    "I'd rather work something out than lose you to a gym that won't give you the same results.\n\n"
                    "— [Coach Name]"
                ),
            },
            {
                "email": 3,
                "timing": "Day 7",
                "subject": "Offer expires Friday",
                "body": (
                    "Hey [Name],\n\n"
                    "Last one from me. Your intro pricing ($99 for 4 sessions) is good through Friday.\n\n"
                    "If now's not the time, no worries — the door's always open.\n\n"
                    "— [Coach Name]"
                ),
            },
        ],
        "lapsed_member": [
            {
                "email": 1,
                "timing": "30 days after last visit",
                "subject": "We miss you at Focus Fitness",
                "body": (
                    "Hey [Name],\n\n"
                    "Haven't seen you in a while — just wanted to check in.\n\n"
                    "No judgment here. Life gets in the way. "
                    "But I know how hard you worked when you were coming in, and I'd love to have you back.\n\n"
                    "Come back for 2 weeks free — no questions asked. Your membership picks back up after.\n\n"
                    "Just reply and we'll set it up.\n\n"
                    "— [Coach Name]"
                ),
            },
        ],
    }
    emails = sequences.get(trigger, sequences["new_inquiry"])[:num_emails]
    return json.dumps({
        "trigger": trigger,
        "goal": goal,
        "sequence": emails,
        "rules": [
            "Speed matters most on email 1. Under 5 minutes = 2x conversion rate.",
            "Short emails win. 100 words beats 400 words every time.",
            "Always end with one clear question or one clear next step — not both.",
            "Use their first name. Be direct. Write like a human, not a business.",
        ],
    }, indent=2)


def write_sms_templates(stage: str) -> str:
    templates = {
        "initial_inquiry": [
            "Hey [Name], it's [Coach] from Focus Fitness! Got your message. Your first class is free — when works this week? 💪",
            "Hi [Name]! [Coach] here from Focus Fitness Levittown. Still have a spot open for your free class — Tue at 6pm or Sat at 9am work for you?",
        ],
        "trial_reminder": [
            "Hey [Name] — just a reminder your free class is tomorrow at [TIME]. Wear comfy clothes, show up 10 min early. See you there! — [Coach]",
            "Reminder: Focus Fitness free class today at [TIME]. 📍 [ADDRESS]. Any questions just text back. — [Coach]",
        ],
        "trial_followup": [
            "Hey [Name], great having you in today! How are you feeling? Ready to get started? — [Coach] at Focus Fitness",
            "Hey [Name]! [Coach] here. Loved having you in. If you're ready to commit, I've got a spot for you. Just reply YES and I'll send details.",
        ],
        "no_show": [
            "Hey [Name], missed you today at Focus Fitness. Everything ok? Still want to get you in for your free class — any day this week work? — [Coach]",
        ],
        "lapsed_reactivation": [
            "Hey [Name], it's [Coach] from Focus Fitness. Missed seeing you. Come back for 2 weeks free — no strings attached. Interested? Just reply YES.",
        ],
        "referral_ask": [
            "Hey [Name]! Quick favor — know anyone in Levittown who wants to get stronger? Send them our way and you both get a free month. Just have them mention your name 💪",
        ],
    }
    return json.dumps({
        "stage": stage,
        "templates": templates.get(stage, templates["initial_inquiry"]),
        "rules": [
            "Text within 5 minutes of any inquiry. After 1 hour, response rates drop by 80%.",
            "Keep it under 160 characters when possible (one SMS segment).",
            "Always identify yourself by name AND gym — they may not have your number saved.",
            "One CTA per text. Don't ask multiple questions.",
            "9am–8pm only. Never text before 8am or after 9pm.",
        ],
    }, indent=2)


def calculate_roi(
    monthly_ad_spend: float,
    leads_per_month: int,
    trial_rate_pct: float,
    close_rate_pct: float,
    avg_monthly_revenue: float,
    avg_lifespan_months: float,
) -> str:
    trials = leads_per_month * (trial_rate_pct / 100)
    new_members = trials * (close_rate_pct / 100)
    revenue_per_member = avg_monthly_revenue * avg_lifespan_months
    monthly_revenue_from_ads = new_members * avg_monthly_revenue
    cac = monthly_ad_spend / new_members if new_members > 0 else float("inf")
    ltv = revenue_per_member
    ltv_cac_ratio = ltv / cac if cac > 0 else 0
    monthly_roi_pct = ((monthly_revenue_from_ads - monthly_ad_spend) / monthly_ad_spend * 100) if monthly_ad_spend > 0 else 0
    payback_months = cac / avg_monthly_revenue if avg_monthly_revenue > 0 else float("inf")

    if ltv_cac_ratio >= 3:
        assessment = "STRONG — scale up ad spend"
    elif ltv_cac_ratio >= 1.5:
        assessment = "DECENT — optimize conversion rates before scaling"
    else:
        assessment = "WEAK — fix follow-up speed and close rate before spending more"

    return json.dumps({
        "inputs": {
            "monthly_ad_spend": f"${monthly_ad_spend}",
            "leads_per_month": leads_per_month,
            "trial_rate": f"{trial_rate_pct}%",
            "close_rate": f"{close_rate_pct}%",
            "avg_monthly_revenue_per_member": f"${avg_monthly_revenue}",
            "avg_member_lifespan": f"{avg_lifespan_months} months",
        },
        "results": {
            "trials_per_month": round(trials, 1),
            "new_members_per_month": round(new_members, 1),
            "customer_acquisition_cost_CAC": f"${round(cac, 2)}",
            "lifetime_value_LTV": f"${round(ltv, 2)}",
            "ltv_to_cac_ratio": round(ltv_cac_ratio, 2),
            "monthly_revenue_from_ads": f"${round(monthly_revenue_from_ads, 2)}",
            "monthly_roi": f"{round(monthly_roi_pct, 1)}%",
            "payback_period": f"{round(payback_months, 1)} months",
        },
        "assessment": assessment,
        "biggest_lever": (
            "Trial-to-member close rate is usually the #1 lever — "
            "improve follow-up speed (under 1 hour) and your close rate often doubles."
            if close_rate_pct < 40
            else "Focus on increasing leads — your conversion funnel is working well."
        ),
    }, indent=2)


def respond_to_review(rating: int, sentiment: str, review_text: str) -> str:
    if rating >= 4 or sentiment == "positive":
        response = (
            f"Thank you so much [Reviewer Name] — this means a lot to us! "
            f"Comments like this are why we do what we do. "
            f"Keep showing up and keep getting stronger. "
            f"See you in the gym! — [Coach Name], Focus Fitness Levittown"
        )
        tips = [
            "Like and reply to every positive review within 24 hours.",
            "Thank them specifically for what they mentioned.",
            "Keep it short — 2-4 sentences. Don't oversell.",
        ]
    elif rating <= 2 or sentiment == "negative":
        response = (
            f"Hi [Reviewer Name], thank you for the feedback — I take this seriously. "
            f"I'd like to understand what happened and make it right. "
            f"Please reach out to me directly at [PHONE/EMAIL] so we can talk. "
            f"— [Coach Name], Focus Fitness Levittown"
        )
        tips = [
            "Never argue or get defensive in a public review response.",
            "Move the conversation offline immediately.",
            "A professional, calm response to a negative review impresses future customers more than a 5-star review.",
            "After resolving it, politely ask them to update their review.",
        ]
    else:
        response = (
            f"Thanks for the feedback [Reviewer Name] — we appreciate you sharing your experience. "
            f"We're always working to improve. If there's anything specific we can do better, "
            f"please reach out at [PHONE]. Hope to see you back soon! "
            f"— [Coach Name], Focus Fitness Levittown"
        )
        tips = [
            "For neutral reviews, acknowledge and invite them back.",
            "Ask what you could have done better — shows you care.",
        ]
    return json.dumps({
        "review_rating": rating,
        "review_text": review_text,
        "suggested_response": response,
        "character_count": len(response),
        "tips": tips,
        "why_reviews_matter": "93% of people read reviews before choosing a local business. Responding to all reviews — especially negative ones — increases trust.",
    }, indent=2)


def plan_seasonal_campaign(season: str, goal: str = "new members") -> str:
    campaigns = {
        "new_year": {
            "window": "Dec 26 – Jan 31",
            "why": "Highest fitness intent of the year. People are making resolutions.",
            "angle": "Not a resolution. A decision. Most gyms are selling motivation. Sell results.",
            "offer": "January special: first month $99 (reg $139). Offer expires Jan 15.",
            "channels": "Facebook/Instagram Ads ($100), flyers at local businesses ($20), Google Business posts",
            "copy_hook": "Resolutions fail. Strength doesn't. Start 2026 the right way.",
            "urgency": "Hard deadline Jan 15. Say it in every post and ad.",
        },
        "spring": {
            "window": "March 1 – April 30",
            "why": "People start thinking about summer. High motivation to look and feel better.",
            "angle": "12 weeks to summer. Start now.",
            "offer": "Spring Challenge: commit to 3x/week for 12 weeks. Track every lift. Show up.",
            "channels": "Instagram Ads, organic content (transformation progress updates)",
            "copy_hook": "Summer is 12 weeks away. That's enough time to get genuinely stronger. We'll show you how.",
        },
        "back_to_school": {
            "window": "Aug 15 – Sep 15",
            "why": "Kids are back in school. Parents have their mornings and afternoons back.",
            "angle": "You got your time back. Use it.",
            "offer": "September Strong Start: Join in September, skip the signup fee.",
            "channels": "Facebook Ads (target parents 30–50), local Facebook groups",
            "copy_hook": "The kids are back in school. You finally have time. Don't waste it.",
        },
        "summer": {
            "window": "June – August",
            "why": "Lower intent than Jan/spring, but good for retention and referrals.",
            "angle": "Summer Bring-a-Friend campaign. Outdoor training content.",
            "offer": "Summer Referral Blitz: refer a friend who joins, you both get 2 weeks free.",
            "channels": "Organic social, member texts, in-gym signage",
            "copy_hook": "Summer Strong. Bring your people.",
        },
        "holiday": {
            "window": "Nov 15 – Dec 24",
            "why": "Gift cards, New Year's pre-sell, and keeping current members engaged through the holidays.",
            "angle": "Gift strength. And get ahead of January before prices go up.",
            "offer": "Gift cards + pre-sell January memberships at January pricing in December.",
            "channels": "Email to current members, organic social, Google Business",
            "copy_hook": "The best gift you can give someone is strength. Gift cards available now.",
        },
    }
    campaign = campaigns.get(season, campaigns["new_year"])
    campaign["goal"] = goal
    campaign["season"] = season
    campaign["budget_suggestion"] = {
        "ads": "$80–$100",
        "print_flyers": "$20–$30",
        "total": "$100–$130 (leaving buffer from $200 monthly budget)",
    }
    return json.dumps(campaign, indent=2)


def save_output(title: str, content: str) -> str:
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{timestamp}_{safe_title}.md"
    filepath = PLANS_DIR / filename
    filepath.write_text(f"# {title}\n\n*Saved: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*\n\n{content}\n")
    return json.dumps({
        "saved": True,
        "file": str(filepath),
        "message": f"Saved to plans/{filename}",
    }, indent=2)


# ── Vagaro tools ─────────────────────────────────────────────────────────────

def vagaro_sync_clients() -> str:
    """Pull the full client list from Vagaro and save it locally."""
    try:
        summary = vagaro_sync.sync(verbose=False)
        return json.dumps({
            "status": "success",
            "total_clients": summary["total"],
            "with_email": summary["with_email"],
            "with_phone": summary["with_phone"],
            "segments": summary["segments"],
            "message": f"Synced {summary['total']} clients from Vagaro. {summary['with_email']} have email, {summary['with_phone']} have phone.",
        }, indent=2)
    except RuntimeError as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "setup_instructions": [
                "1. Contact Vagaro Enterprise Sales to enable API access ($10/month)",
                "   https://support.vagaro.com/hc/en-us/categories/34949493949851",
                "2. In Vagaro dashboard: Settings → Developers → APIs & Webhooks",
                "3. Generate your API token",
                "4. Set environment variable: export VAGARO_API_TOKEN=your_token_here",
                "5. Try again",
            ],
        }, indent=2)


def vagaro_get_segments() -> str:
    """Show how clients are segmented (active, at-risk, lapsed, lost, etc.)."""
    clients = vagaro_sync._load_local()
    if not clients:
        return json.dumps({"error": "No clients synced yet. Use vagaro_sync_clients first."})

    segs = vagaro_sync.segment_clients(clients)
    result = {
        "total_clients": len(clients),
        "segments": {},
    }
    for seg_name, members in segs.items():
        result["segments"][seg_name] = {
            "count": len(members),
            "description": {
                "active_recent":  "Visited in the last 30 days — your most engaged members",
                "at_risk":        "Last visit 31-90 days ago — follow up NOW before they leave",
                "lapsed":         "Last visit 91-365 days ago — win-back candidates",
                "lost":           "No visit in over 1 year — long-shot win-back",
                "never_visited":  "In system but no visits recorded — may be leads who never converted",
                "high_value":     "Top 20% by total spend — treat these people like gold",
                "no_email":       "No email on file — can only reach by phone",
                "no_phone":       "No phone on file — can only reach by email",
            }.get(seg_name, ""),
            "sample": [
                f"{c['first_name']} {c['last_name']} | {c.get('email','no email')} | last visit: {(c.get('last_visit') or 'unknown')[:10]}"
                for c in members[:5]
            ],
        }
    return json.dumps(result, indent=2)


def vagaro_generate_outreach(segment_name: str, channel: str, template_name: str, limit: int = 0) -> str:
    """
    Generate personalized email or SMS messages for a client segment.

    Args:
        segment_name: 'active_recent', 'at_risk', 'lapsed', 'lost', 'never_visited', 'high_value'
        channel: 'email' or 'sms'
        template_name: 'win_back', 'referral_ask', 'check_in', 'new_promo'
        limit: max number of messages to generate (0 = all)
    """
    result = json.loads(vagaro_sync.generate_outreach(segment_name, channel, template_name, limit))
    if "error" in result:
        return json.dumps(result, indent=2)

    # Add compliance reminders
    result["compliance_notes"] = {
        "email": [
            "CAN-SPAM: Every email must include your physical address and an unsubscribe link.",
            "These are existing clients — sending to them is generally permitted under CAN-SPAM business relationship exemption.",
            "Honor all unsubscribe requests within 10 business days.",
        ],
        "sms": [
            "TCPA WARNING: You must have explicit written opt-in consent before sending marketing SMS.",
            "If clients opted in when they signed up with Vagaro, you're covered — verify this.",
            "Every SMS must include: 'Reply STOP to opt out'.",
            "Recommended SMS hours: 9am–8pm local time only.",
            "Consider using a service like Twilio, SimpleTexting, or Podium to manage SMS campaigns with compliance built in.",
        ],
    }.get(channel, [])

    result["next_steps"] = {
        "email": "Copy these messages into Mailchimp, Constant Contact, or your email provider. Import the CSV export for bulk sending.",
        "sms": "Copy these into SimpleTexting, Podium, or Twilio. Always verify SMS consent before sending.",
    }.get(channel, "")

    return json.dumps(result, indent=2)


def vagaro_export_csv(segment_name: str = "all") -> str:
    """
    Export a client segment to CSV for use with Mailchimp, Constant Contact, or SMS platforms.

    Args:
        segment_name: 'all', 'active_recent', 'at_risk', 'lapsed', 'lost', 'high_value', etc.
    """
    try:
        seg = None if segment_name == "all" else segment_name
        path = vagaro_sync.export_csv(segment_name=seg)
        clients = vagaro_sync._load_local()
        segs = vagaro_sync.segment_clients(clients)
        count = len(segs.get(segment_name, clients)) if segment_name != "all" else len(clients)
        return json.dumps({
            "status": "success",
            "file": path,
            "records_exported": count,
            "compatible_with": [
                "Mailchimp (import CSV under Audience → Import contacts)",
                "Constant Contact",
                "Klaviyo",
                "SimpleTexting (for SMS)",
                "Podium",
                "Any spreadsheet (Excel, Google Sheets)",
            ],
        }, indent=2)
    except RuntimeError as e:
        return json.dumps({"status": "error", "error": str(e)}, indent=2)


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOL_MAP = {
    "generate_ad_copy":          generate_ad_copy,
    "build_content_calendar":    build_content_calendar,
    "analyze_audience":          analyze_audience,
    "create_offer":              create_offer,
    "write_google_business_post": write_google_business_post,
    "plan_facebook_ad_campaign": plan_facebook_ad_campaign,
    "write_referral_program":    write_referral_program,
    "diagnose_marketing":        diagnose_marketing,
    "write_email_sequence":      write_email_sequence,
    "write_sms_templates":       write_sms_templates,
    "calculate_roi":             calculate_roi,
    "respond_to_review":         respond_to_review,
    "plan_seasonal_campaign":    plan_seasonal_campaign,
    "save_output":               save_output,
    # Vagaro CRM integration
    "vagaro_sync_clients":       vagaro_sync_clients,
    "vagaro_get_segments":       vagaro_get_segments,
    "vagaro_generate_outreach":  vagaro_generate_outreach,
    "vagaro_export_csv":         vagaro_export_csv,
}

# User-defined tool schemas (JSON schema format for the Messages API)
USER_TOOL_SCHEMAS = [
    {
        "name": "generate_ad_copy",
        "description": "Generate 2-3 high-converting ad copy variations for a specific platform (Facebook, Instagram, or Google).",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "Ad platform: 'Facebook', 'Instagram', or 'Google'"},
                "goal": {"type": "string", "description": "Ad objective, e.g. 'get new members', 'promote group class'"},
                "tone": {"type": "string", "description": "Tone of voice, default: 'direct and confident'"},
                "offer": {"type": "string", "description": "Lead magnet/offer, e.g. 'free first class'"},
            },
            "required": ["platform", "goal"],
        },
    },
    {
        "name": "build_content_calendar",
        "description": "Build a monthly social media content calendar with post ideas, themes, and hashtag sets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Target month, e.g. 'April 2026'"},
                "posts_per_week": {"type": "integer", "description": "Posts per week, typically 3-5"},
                "platforms": {"type": "string", "description": "Comma-separated platforms, e.g. 'Instagram, Facebook'"},
            },
            "required": ["month"],
        },
    },
    {
        "name": "analyze_audience",
        "description": "Get a deep profile of a target audience segment including demographics, psychographics, pain points, and messaging.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment": {"type": "string", "description": "'primary' (35-55), 'secondary' (25-35), 'tertiary' (50-65), or 'all'"},
            },
            "required": [],
        },
    },
    {
        "name": "create_offer",
        "description": "Design a promotional offer or lead magnet for a specific goal (new members, retention, or win-back).",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "'get new members', 'retain current members', or 'reactivate lapsed members'"},
                "season": {"type": "string", "description": "Time of year context, e.g. 'January', 'summer', 'general'"},
                "budget_sensitive": {"type": "boolean", "description": "Whether the offer must be free or low-cost to fulfill"},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "write_google_business_post",
        "description": "Write an SEO-optimized Google Business Profile post to improve local search visibility.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "'strength tip', 'member result', 'offer', 'class schedule', or 'why strength training'"},
                "include_cta": {"type": "boolean", "description": "Whether to include a CTA button suggestion"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "plan_facebook_ad_campaign",
        "description": "Build a complete Facebook/Instagram ad campaign plan with targeting, budget split, creative direction, and KPIs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "objective": {"type": "string", "description": "Campaign objective, e.g. 'lead generation', 'brand awareness'"},
                "duration_days": {"type": "integer", "description": "Campaign length in days"},
                "monthly_budget": {"type": "integer", "description": "Total monthly budget in dollars for FB/IG ads"},
            },
            "required": ["objective"],
        },
    },
    {
        "name": "write_referral_program",
        "description": "Design a referral program with rewards, launch plan, and tracking system to turn members into recruiters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reward_type": {"type": "string", "description": "Reward for referrers: 'free month', 'discount', 'cash', 'swag'"},
            },
            "required": [],
        },
    },
    {
        "name": "diagnose_marketing",
        "description": "Diagnose a specific marketing problem and get a prioritized list of fixes. Use when something isn't working.",
        "input_schema": {
            "type": "object",
            "properties": {
                "area": {"type": "string", "description": "'low leads', 'high churn', 'low ad roi', 'weak social media', or 'pricing'"},
            },
            "required": ["area"],
        },
    },
    {
        "name": "write_email_sequence",
        "description": "Write a multi-email follow-up sequence for leads, post-trial prospects, or lapsed members.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trigger": {"type": "string", "description": "'new_inquiry', 'post_trial', or 'lapsed_member'"},
                "num_emails": {"type": "integer", "description": "Number of emails in the sequence (2-5)"},
                "goal": {"type": "string", "description": "What the sequence should achieve"},
            },
            "required": ["trigger"],
        },
    },
    {
        "name": "write_sms_templates",
        "description": "Write SMS templates for each stage of the lead-to-member journey.",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {"type": "string", "description": "'initial_inquiry', 'trial_reminder', 'trial_followup', 'no_show', 'lapsed_reactivation', or 'referral_ask'"},
            },
            "required": ["stage"],
        },
    },
    {
        "name": "calculate_roi",
        "description": "Calculate marketing ROI, customer acquisition cost (CAC), lifetime value (LTV), and payback period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monthly_ad_spend": {"type": "number", "description": "Total monthly ad spend in dollars"},
                "leads_per_month": {"type": "integer", "description": "Number of leads generated per month"},
                "trial_rate_pct": {"type": "number", "description": "Percentage of leads who book a trial (0-100)"},
                "close_rate_pct": {"type": "number", "description": "Percentage of trials who become paying members (0-100)"},
                "avg_monthly_revenue": {"type": "number", "description": "Average monthly revenue per member in dollars"},
                "avg_lifespan_months": {"type": "number", "description": "Average member lifespan in months"},
            },
            "required": ["monthly_ad_spend", "leads_per_month", "trial_rate_pct", "close_rate_pct", "avg_monthly_revenue", "avg_lifespan_months"],
        },
    },
    {
        "name": "respond_to_review",
        "description": "Write a professional, on-brand response to a Google or Facebook review (positive, negative, or neutral).",
        "input_schema": {
            "type": "object",
            "properties": {
                "rating": {"type": "integer", "description": "Star rating 1-5"},
                "sentiment": {"type": "string", "description": "'positive', 'negative', or 'neutral'"},
                "review_text": {"type": "string", "description": "The text of the review"},
            },
            "required": ["rating", "sentiment", "review_text"],
        },
    },
    {
        "name": "plan_seasonal_campaign",
        "description": "Plan a marketing campaign around a specific season or fitness moment of the year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "season": {"type": "string", "description": "'new_year', 'spring', 'summer', 'back_to_school', or 'holiday'"},
                "goal": {"type": "string", "description": "What you want to achieve, e.g. 'new members', 'retention'"},
            },
            "required": ["season"],
        },
    },
    {
        "name": "save_output",
        "description": "Save a marketing plan, ad copy, or any output to a markdown file in the plans/ directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title for the file, e.g. 'April Content Calendar'"},
                "content": {"type": "string", "description": "The full content to save"},
            },
            "required": ["title", "content"],
        },
    },
    # ── Vagaro CRM ──
    {
        "name": "vagaro_sync_clients",
        "description": "Pull all clients from Vagaro and save them locally. Run this first before using other Vagaro tools. Requires VAGARO_API_TOKEN environment variable.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "vagaro_get_segments",
        "description": "Show how clients are grouped into segments: active, at-risk, lapsed, lost, high-value, etc. Use this to decide who to target for a campaign.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "vagaro_generate_outreach",
        "description": "Generate personalized email or SMS messages for a specific client segment. Returns ready-to-send messages with the client's first name merged in.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_name": {"type": "string", "description": "Segment to target: 'active_recent', 'at_risk', 'lapsed', 'lost', 'never_visited', or 'high_value'"},
                "channel":      {"type": "string", "description": "'email' or 'sms'"},
                "template_name":{"type": "string", "description": "'win_back', 'referral_ask', 'check_in', or 'new_promo'"},
                "limit":        {"type": "integer", "description": "Max messages to generate. 0 = all clients in segment."},
            },
            "required": ["segment_name", "channel", "template_name"],
        },
    },
    {
        "name": "vagaro_export_csv",
        "description": "Export a client segment to a CSV file compatible with Mailchimp, Constant Contact, or SMS platforms like SimpleTexting.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_name": {"type": "string", "description": "Segment to export: 'all', 'at_risk', 'lapsed', 'active_recent', 'high_value', etc."},
            },
            "required": [],
        },
    },
]

# Server-side tools (executed by the API, not client-side)
SERVER_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search"},
]

ALL_TOOLS = SERVER_TOOLS + USER_TOOL_SCHEMAS


# ── Streaming agentic loop ────────────────────────────────────────────────────

def run_agent(user_message: str, history: list) -> tuple[str, list]:
    """
    Stream one full agent turn (may include multiple tool call rounds).
    Prints text to terminal as it streams.
    Returns (full_reply_text, updated_history).
    """
    history.append({"role": "user", "content": user_message})
    full_reply = ""
    max_iterations = 10

    for iteration in range(max_iterations):
        current_block_type = None
        turn_text = ""

        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            tools=ALL_TOOLS,
            messages=history,
        ) as stream:
            for event in stream:
                etype = event.type

                if etype == "content_block_start":
                    cb = event.content_block
                    current_block_type = getattr(cb, "type", None)
                    if current_block_type == "tool_use":
                        print(f"\n{CYAN}🔧 {cb.name}{RESET}", flush=True)

                elif etype == "content_block_delta":
                    delta = event.delta
                    dtype = getattr(delta, "type", None)
                    if dtype == "text_delta" and current_block_type == "text":
                        print(delta.text, end="", flush=True)
                        turn_text += delta.text

                elif etype == "content_block_stop":
                    current_block_type = None

            response = stream.get_final_message()

        full_reply += turn_text

        # Append this assistant turn to history
        history.append({"role": "assistant", "content": response.content})

        stop = response.stop_reason

        if stop == "end_turn":
            break

        if stop == "pause_turn":
            # Server-side tool loop hit its limit — re-send to continue
            continue

        if stop == "tool_use":
            # Execute user-defined tools
            tool_results = []
            for block in response.content:
                btype = getattr(block, "type", None)
                if btype == "tool_use":
                    fn = TOOL_MAP.get(block.name)
                    if fn:
                        with Spinner(f"Running {block.name}"):
                            try:
                                result = fn(**block.input)
                            except Exception as exc:
                                result = json.dumps({"error": str(exc)})
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

            if tool_results:
                history.append({"role": "user", "content": tool_results})
            continue

        break  # unknown stop reason

    return full_reply, history


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}{'=' * 62}{RESET}")
    print(f"{BOLD}  FOCUS FITNESS MARKETING AGENT{RESET}")
    print(f"{DIM}  Levittown, PA | Strength Training | No Bullshit.{RESET}")
    print(f"{BOLD}{'=' * 62}{RESET}")
    print(f"\n{DIM}Plans saved to: {PLANS_DIR}{RESET}")
    print(f"{DIM}Type 'new' to clear history. Type 'quit' to exit.{RESET}\n")
    print(f"{YELLOW}What can I help you with?{RESET}")
    print(f"{DIM}Examples: 'Write a Facebook ad' | 'Build April's content calendar'")
    print(f"'What should I do about low leads?' | 'Plan my New Year campaign'")
    print(f"'Calculate my ROI: $120/mo ads, 20 leads, 40% trial, 50% close, $139/mo, 14 mo avg'{RESET}\n")

    history = load_history()
    if history:
        print(f"{DIM}(Resuming previous session — {len(history)} messages in memory){RESET}\n")

    while True:
        try:
            user_input = input(f"{GREEN}You:{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Go get 'em.{RESET}")
            break

        if not user_input:
            continue

        if user_input.lower() == "new":
            history = []
            save_history(history)
            print(f"{DIM}History cleared. Fresh start.{RESET}\n")
            continue

        if user_input.lower() in ("quit", "exit", "bye", "q"):
            print(f"{DIM}Go get 'em. No excuses.{RESET}")
            break

        print(f"\n{BOLD}Agent:{RESET} ", end="", flush=True)

        try:
            reply, history = run_agent(user_input, history)
            save_history(history)
        except anthropic.AuthenticationError:
            print(f"\n{YELLOW}Set your API key: export ANTHROPIC_API_KEY=your_key{RESET}")
        except anthropic.RateLimitError:
            print(f"\n{YELLOW}Rate limited — wait a moment and try again.{RESET}")
        except anthropic.APIError as exc:
            print(f"\n{YELLOW}API error: {exc}{RESET}")

        print("\n")


if __name__ == "__main__":
    main()
