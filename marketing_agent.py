"""
Focus Fitness Marketing Agent
Levittown, PA | Strength Training | No Bullshit.

An expert marketing agent powered by Claude Opus 4.6.
Run it and ask it anything about your marketing.
"""

import json
import os
import anthropic
from anthropic import beta_tool
from datetime import datetime

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── Business context injected into every tool call ──────────────────────────
BUSINESS = {
    "name": "Focus Fitness",
    "location": "Levittown, PA",
    "zip_codes": ["19054", "19055", "19056", "19057", "19058"],
    "services": ["personal training", "group strength classes"],
    "focus": "strength training",
    "brand_voice": "No bullshit. Efficient hard work. No gimmicks.",
    "target_age": "25–60",
    "monthly_budget": 200,
    "usp": "Real strength training in Levittown with zero gimmicks. You work hard, you get results.",
}

SYSTEM_PROMPT = f"""You are an elite marketing strategist and copywriter specializing in local fitness businesses.
You have 20+ years of experience across digital advertising, brand building, social media, direct response copywriting,
and community-based marketing. You have helped hundreds of independent gyms, personal trainers, and strength coaches
grow their businesses from scratch.

Your client is {BUSINESS['name']} in {BUSINESS['location']}.
- Services: {', '.join(BUSINESS['services'])}
- Focus: {BUSINESS['focus']}
- Brand voice: {BUSINESS['brand_voice']}
- Target audience: Adults {BUSINESS['target_age']} in Levittown who want to get genuinely stronger
- Monthly marketing budget: ${BUSINESS['monthly_budget']}

Your expertise includes:
- Facebook & Instagram ad strategy and copywriting
- Google Business Profile optimization
- Local SEO
- Direct response copywriting (headlines, hooks, CTAs)
- Content calendars and organic social media strategy
- Email and SMS marketing
- Referral and retention programs
- Seasonal promotions and campaign planning
- Competitor and market analysis
- Brand positioning for independent gyms
- Pricing strategy
- Community building and word-of-mouth amplification

You think like a performance marketer but write like a human being.
You always match the client's voice: direct, confident, no fluff.
When you use tools, you combine their outputs into a cohesive, actionable recommendation.
You never recommend spending money the client doesn't have.
You prioritize high-ROI, low-cost tactics first.
"""


# ── Tools ────────────────────────────────────────────────────────────────────

@beta_tool
def generate_ad_copy(
    platform: str,
    goal: str,
    tone: str = "direct and confident",
    offer: str = "free first class",
) -> str:
    """
    Generate high-converting ad copy for a specific platform.

    Args:
        platform: The ad platform — e.g. 'Facebook', 'Instagram', 'Google'.
        goal: What the ad should achieve — e.g. 'get new members', 'promote group class', 'build brand awareness'.
        tone: The tone of the copy — e.g. 'direct and confident', 'motivational', 'no-nonsense'.
        offer: The lead magnet or offer to include — e.g. 'free first class', '20% off first month'.
    """
    variations = {
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
        ],
        "Instagram": [
            f"Strong is not a look. It's a lifestyle.\n\n"
            f"@focusfitness_levittown — strength training that actually works.\n"
            f"Link in bio → {offer}.",

            f"You don't need more motivation. You need a coach and a barbell.\n\n"
            f"Levittown, PA 📍 | Personal training + group classes\n"
            f"DM us for your {offer}.",
        ],
        "Google": [
            f"Strength Training in Levittown PA | No Fluff, Real Results",
            f"Personal Trainer Levittown PA | {offer.capitalize()} | Focus Fitness",
        ],
    }
    copies = variations.get(platform, variations["Facebook"])
    result = {
        "platform": platform,
        "goal": goal,
        "offer": offer,
        "ad_copies": copies,
        "notes": (
            f"Use the copy that matches your current goal: {goal}. "
            f"A/B test both versions for 7 days and keep the one with more clicks/leads. "
            f"Always include a clear call-to-action."
        ),
    }
    return json.dumps(result, indent=2)


@beta_tool
def build_content_calendar(
    month: str,
    posts_per_week: int = 4,
    platforms: str = "Instagram, Facebook",
) -> str:
    """
    Build a monthly social media content calendar with post ideas and themes.

    Args:
        month: The target month, e.g. 'March 2026'.
        posts_per_week: How many posts per week to plan, typically 3-5.
        platforms: Comma-separated list of platforms to include.
    """
    themes = [
        ("Monday", "Motivation/Mindset", "Short tip or quote about why strength matters more than cardio"),
        ("Tuesday", "Training Content", "Clip or photo of a member doing a big lift (with permission)"),
        ("Wednesday", "Education", "'Why we train X movement' — teach something real about strength"),
        ("Thursday", "Social Proof", "Member result, testimonial, or transformation story"),
        ("Friday", "Community", "Behind the scenes — coach setup, class recap, gym culture"),
        ("Saturday", "Offer/CTA", "Remind followers about free first class or current promotion"),
        ("Sunday", "Engagement", "Question for followers: 'What's your favorite lift?' or poll"),
    ]
    weekly_plan = themes[:posts_per_week]
    calendar = {
        "month": month,
        "platforms": platforms,
        "posts_per_week": posts_per_week,
        "weekly_themes": [
            {"day": t[0], "theme": t[1], "post_idea": t[2]} for t in weekly_plan
        ],
        "monthly_campaigns": [
            "Week 1 — Launch/Re-introduce: Who we are and what we stand for",
            "Week 2 — Education week: 4 posts teaching strength training fundamentals",
            "Week 3 — Social proof week: Member stories and results",
            "Week 4 — Offer week: Push the free first class CTA hard",
        ],
        "content_tips": [
            "Film every session if possible — raw, real footage outperforms polished stock photos.",
            "Stories get 3x the engagement of feed posts on Instagram — use them daily.",
            "Tag Levittown in every post. Local hashtags boost organic reach.",
            "Reply to every comment within 2 hours — the algorithm rewards engagement.",
        ],
    }
    return json.dumps(calendar, indent=2)


@beta_tool
def analyze_audience(
    segment: str = "primary",
) -> str:
    """
    Analyze the target audience segments for Focus Fitness.

    Args:
        segment: Which audience segment to analyze — 'primary', 'secondary', or 'all'.
    """
    segments = {
        "primary": {
            "name": "Levittown Strength Seeker (35–55)",
            "demographics": "Adults 35–55, Levittown PA, household income $60K–$120K",
            "psychographics": [
                "Tired of spinning their wheels at commercial gyms",
                "Want real results, not entertainment",
                "Value efficiency — 45-minute sessions that actually work",
                "Skeptical of fad diets and trendy fitness classes",
                "Motivated by progress they can measure (weight on the bar)",
            ],
            "pain_points": [
                "Don't know how to program strength training correctly",
                "Intimidated by powerlifting/barbell gyms",
                "Busy schedule — can't commit to hour-long classes",
                "Have tried and quit big-box gyms before",
            ],
            "best_channels": ["Facebook Ads", "Google Search", "Word of mouth"],
            "best_message": "Stop wasting time. Get strong. We'll show you exactly how.",
        },
        "secondary": {
            "name": "Young Professional (25–35)",
            "demographics": "Adults 25–35, commuters, first job, athletic background",
            "psychographics": [
                "Athletic in high school/college, fell out of shape",
                "Want to look and feel strong, not skinny",
                "Social — will bring friends if they like the culture",
                "Instagram-active, influenced by strength accounts",
            ],
            "pain_points": [
                "Expensive big-box gym memberships not worth it",
                "Need accountability and coaching",
                "Don't know where to start with barbell training",
            ],
            "best_channels": ["Instagram Ads", "TikTok (organic)", "Referrals"],
            "best_message": "The gym you've been looking for. No machines. No mirrors. Just progress.",
        },
    }
    if segment == "all":
        result = segments
    else:
        result = segments.get(segment, segments["primary"])
    return json.dumps(result, indent=2)


@beta_tool
def create_offer(
    goal: str,
    season: str = "general",
    budget_sensitive: bool = True,
) -> str:
    """
    Design a promotional offer or lead magnet to attract new members.

    Args:
        goal: What the offer is trying to achieve — e.g. 'get new members', 'retain current members', 'reactivate lapsed members'.
        season: The time of year or context — e.g. 'January', 'summer', 'back to school', 'general'.
        budget_sensitive: Whether the offer must be free or very low cost to fulfill.
    """
    offers = {
        "get new members": [
            {
                "name": "Free First Class",
                "description": "Walk in, try a group class or personal training session for free. No signup, no credit card.",
                "why_it_works": "Removes all risk. 80% of people who try once come back.",
                "cost_to_you": "$0 (your time)",
                "how_to_promote": "Facebook/Instagram ads, Google Business, word of mouth",
            },
            {
                "name": "Bring a Friend Week",
                "description": "Every current member can bring one guest for free for an entire week.",
                "why_it_works": "Turns members into recruiters. Warm referrals convert at 5x cold leads.",
                "cost_to_you": "$0",
                "how_to_promote": "Text/email existing members, post in class",
            },
            {
                "name": "30-Day New Member Challenge",
                "description": "First month at a reduced rate ($99 instead of $149) if they attend at least 12 sessions.",
                "why_it_works": "Creates commitment and habit. Members who hit 12 sessions almost never quit.",
                "cost_to_you": "~$50 revenue reduction, offset by retention",
                "how_to_promote": "Facebook ads targeting Levittown, landing page",
            },
        ],
        "retain current members": [
            {
                "name": "Loyalty Milestone Rewards",
                "description": "Hit 50, 100, 200 sessions — get a shirt, a free month, public recognition.",
                "why_it_works": "Gamification keeps attendance high and creates social proof.",
                "cost_to_you": "Shirt (~$15), 1 free month (~$149 value) — worth it for lifetime retention",
            },
        ],
    }
    result = {
        "goal": goal,
        "season": season,
        "recommended_offers": offers.get(goal, offers["get new members"]),
        "golden_rule": (
            "The best offer has zero friction to claim and zero risk to the prospect. "
            "Never require a credit card upfront for a trial. "
            "Your close rate on free trials is your real marketing metric — track it."
        ),
    }
    return json.dumps(result, indent=2)


@beta_tool
def write_google_business_post(
    topic: str,
    include_cta: bool = True,
) -> str:
    """
    Write a Google Business Profile post to boost local search visibility.

    Args:
        topic: The topic of the post — e.g. 'new class schedule', 'member result', 'strength tip', 'offer'.
        include_cta: Whether to include a call-to-action button suggestion.
    """
    posts = {
        "strength tip": (
            "The #1 mistake people make at the gym: too much variety, not enough consistency.\n\n"
            "At Focus Fitness in Levittown, we build your strength on a foundation of "
            "the big compound movements — squat, deadlift, press, row.\n\n"
            "Show up. Work hard. Get stronger. Simple as that.\n\n"
            "📍 Levittown, PA | Personal Training & Group Classes\n"
            "First class is free — call or message us to schedule."
        ),
        "member result": (
            "Another member PR at Focus Fitness 💪\n\n"
            "This week, one of our members hit a new personal best on the deadlift after just 8 weeks of coaching.\n\n"
            "No gimmicks. No complicated programming. Just consistent hard work and expert coaching.\n\n"
            "If you're in Levittown and ready to actually get stronger, come try a class on us.\n"
            "First session is free."
        ),
        "offer": (
            "New to Focus Fitness? Your first class is free.\n\n"
            "We offer personal training and group strength classes right here in Levittown, PA.\n\n"
            "No mirrors. No machines. No fluff. Just a coach, a barbell, and a plan that works.\n\n"
            "Spots are limited — message us or call to claim your free session."
        ),
        "new class schedule": (
            "Updated class schedule now live at Focus Fitness Levittown!\n\n"
            "We've added [TIME] slots to make it easier for you to train around your schedule.\n\n"
            "Strength training. Small groups. Real results.\n\n"
            "📞 Call or DM us to reserve your spot."
        ),
    }
    content = posts.get(topic, posts["strength tip"])
    result = {
        "post_content": content,
        "cta_button": "Call now" if include_cta else None,
        "posting_tips": [
            "Post once per week minimum to stay active in Google's local algorithm.",
            "Always include 'Levittown' and 'PA' naturally in the text for local SEO.",
            "Add a photo to every post — posts with photos get 3x more views.",
            "Respond to every Google review within 24 hours.",
        ],
    }
    return json.dumps(result, indent=2)


@beta_tool
def plan_facebook_ad_campaign(
    objective: str,
    duration_days: int = 30,
    monthly_budget: int = 120,
) -> str:
    """
    Build a complete Facebook/Instagram ad campaign plan with targeting, budget allocation, and creative guidance.

    Args:
        objective: The campaign objective — e.g. 'lead generation', 'brand awareness', 'event promotion'.
        duration_days: How long to run the campaign.
        monthly_budget: Total monthly budget in dollars for Facebook/Instagram ads.
    """
    daily_budget = round(monthly_budget / 30, 2)
    campaign = {
        "objective": objective,
        "platform": "Facebook + Instagram (same campaign)",
        "budget": {
            "monthly": monthly_budget,
            "daily": daily_budget,
            "allocation": {
                "prospecting_new_leads": f"${round(monthly_budget * 0.7)} (70%) — cold audience targeting",
                "retargeting": f"${round(monthly_budget * 0.3)} (30%) — people who visited your profile/website",
            },
        },
        "targeting": {
            "locations": BUSINESS["zip_codes"] + ["Bristol PA", "Fairless Hills PA", "Tullytown PA"],
            "radius": "5 miles around Levittown",
            "age": "28–58",
            "interests": [
                "Weightlifting",
                "Strength training",
                "Powerlifting",
                "Barbell training",
                "Physical fitness",
                "CrossFit (people who want something better)",
            ],
            "exclude": ["Planet Fitness employees", "Gold's Gym employees"],
            "lookalike": "Upload your current member list to Facebook to build a lookalike audience",
        },
        "ad_formats": [
            {
                "format": "Short video (15–30 sec)",
                "when": "Week 1–2",
                "content": "Raw training footage — a member hitting a big lift, coach cueing, real gym energy",
                "why": "Video builds trust and stops the scroll",
            },
            {
                "format": "Single image",
                "when": "Week 3–4",
                "content": "Before/after transformation or member PR milestone with short headline",
                "why": "Images are cheaper per click and good for retargeting",
            },
        ],
        "testing_plan": "Run 2 ad variations simultaneously. After 7 days, kill the lower performer and double budget on the winner.",
        "kpis": {
            "cost_per_lead_target": "$5–$15",
            "click_through_rate_target": "1.5%+",
            "lead_to_trial_conversion_target": "30%+",
        },
        "pro_tips": [
            "Never boost posts — always use Ads Manager for real targeting control.",
            "Use Facebook Lead Ads (instant form) so prospects never leave the app.",
            "Follow up every lead within 1 hour — speed to contact is the #1 conversion factor.",
            f"Start ads on Monday or Tuesday — CPMs are lower early in the week.",
        ],
    }
    return json.dumps(campaign, indent=2)


@beta_tool
def write_referral_program(
    reward_type: str = "free month",
) -> str:
    """
    Design a referral program to turn current members into recruiters.

    Args:
        reward_type: What reward to offer referrers — e.g. 'free month', 'discount', 'cash', 'swag'.
    """
    program = {
        "program_name": "Bring Your People",
        "tagline": "You get stronger together. So do we.",
        "how_it_works": [
            "Step 1: Current member refers a friend who joins.",
            "Step 2: Friend completes their first paid month.",
            "Step 3: Both the member AND the new joiner get the reward.",
        ],
        "reward": {
            "type": reward_type,
            "referrer_gets": "One free month of membership ($149 value)",
            "new_member_gets": "First month at 50% off",
            "why_both": "Double-sided rewards increase referral rates by 3x vs. one-sided.",
        },
        "how_to_launch": [
            "Announce it in class verbally this week.",
            "Text all current members with a 2-sentence message: "
            "'Hey [name], we just launched a referral program. Bring a friend who signs up and you both get a free month. Simple.'",
            "Post it on Instagram and Facebook stories.",
            "Put a small sign at the front of the gym.",
        ],
        "tracking": "Keep a simple spreadsheet: member name, friend name, date referred, date joined, reward given.",
        "pro_tip": (
            "Your best customers are your best salespeople. "
            "Ask your 5 most enthusiastic members personally — word of mouth from a trusted friend "
            "converts at 5–10x the rate of any ad."
        ),
    }
    return json.dumps(program, indent=2)


@beta_tool
def diagnose_marketing(
    area: str,
) -> str:
    """
    Diagnose a specific marketing problem and give a direct recommendation.

    Args:
        area: The marketing area to diagnose — e.g. 'low leads', 'high churn', 'low ad ROI', 'weak social media', 'pricing'.
    """
    diagnoses = {
        "low leads": {
            "likely_causes": [
                "No clear lead magnet or offer (why would someone try you vs. a big gym?)",
                "Not enough local visibility — Google Business not optimized",
                "Ads targeting too broad or wrong age group",
                "No follow-up system for people who inquire but don't book",
            ],
            "fix_this_week": [
                "Audit your Google Business Profile — make sure it's complete, has photos, and has an active post",
                "Create a Facebook/Instagram lead ad with the free first class offer targeting Levittown zip codes",
                "Text or DM every current member asking them to refer one person",
            ],
            "fix_this_month": [
                "Set up a simple lead follow-up workflow: inquiry → text/call within 1 hour → book free trial",
                "Get 10 Google reviews from current members (email them a direct link to your review page)",
                "Launch the referral program",
            ],
        },
        "high churn": {
            "likely_causes": [
                "Members not seeing clear progress — no tracking system",
                "No community feel — members don't know each other",
                "Price objection — no value ladder between intro and full membership",
            ],
            "fix_this_week": [
                "Start tracking every member's key lifts — even a simple whiteboard PR board creates emotional investment",
                "Celebrate every PR publicly (post it, call it out in class)",
                "Check in with any member who has missed 2+ sessions in a row",
            ],
        },
        "weak social media": {
            "likely_causes": [
                "Posting stock photos or motivational quotes instead of real content",
                "Inconsistent posting schedule",
                "No clear call to action in posts",
            ],
            "fix_this_week": [
                "Film 3 short clips of real training today — 15 seconds each, no editing needed",
                "Post one today with the caption: 'This is what we do at Focus Fitness Levittown. First class free.'",
                "Set a phone reminder to post every Monday, Wednesday, Friday, and Saturday",
            ],
        },
        "pricing": {
            "benchmark": "Local independent gym PT rates: $60–$100/session. Group: $25–$40/class. Monthly memberships: $99–$179.",
            "recommendation": (
                "For a no-frills strength gym in Levittown: "
                "Group class membership $129–$149/month unlimited, "
                "PT starting at $75/session or $280/month (4 sessions). "
                "Offer a 2-session intro package at $99 to lower the barrier."
            ),
            "pricing_principle": "Price for the value, not the cost. People pay for results and accountability, not just gym access.",
        },
    }
    result = diagnoses.get(area, {
        "message": f"I don't have a canned diagnosis for '{area}', but here's what I'd do: "
                   "describe the problem in more detail and I'll give you a direct recommendation.",
    })
    return json.dumps(result, indent=2)


# ── Agent loop ────────────────────────────────────────────────────────────────

TOOLS = [
    generate_ad_copy,
    build_content_calendar,
    analyze_audience,
    create_offer,
    write_google_business_post,
    plan_facebook_ad_campaign,
    write_referral_program,
    diagnose_marketing,
]


def run_agent(user_message: str, conversation_history: list | None = None) -> tuple[str, list]:
    """
    Run one turn of the marketing agent.
    Returns (assistant_reply, updated_history).
    """
    if conversation_history is None:
        conversation_history = []

    conversation_history.append({"role": "user", "content": user_message})

    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        thinking={"type": "adaptive"},
        tools=TOOLS,
        messages=conversation_history,
    )

    # Collect the full response by iterating the runner
    final_message = None
    for message in runner:
        final_message = message

    if final_message is None:
        return "No response generated.", conversation_history

    # Extract text from the response
    reply_text = ""
    for block in final_message.content:
        if hasattr(block, "text"):
            reply_text += block.text

    # Append assistant reply to history for multi-turn support
    conversation_history.append({
        "role": "assistant",
        "content": reply_text or "[No text response]",
    })

    return reply_text, conversation_history


def main():
    print("\n" + "=" * 60)
    print("  FOCUS FITNESS MARKETING AGENT")
    print("  Levittown, PA | Strength Training | No Bullshit.")
    print("=" * 60)
    print("\nAsk me anything about your marketing.")
    print("Examples:")
    print("  - Write me a Facebook ad for new members")
    print("  - Build a content calendar for April")
    print("  - Design a referral program")
    print("  - I'm not getting enough leads. What do I do?")
    print("  - Plan my Facebook ad campaign for the month")
    print("\nType 'quit' to exit.\n")

    history = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Go get 'em. No excuses.")
            break

        print("\nAgent: ", end="", flush=True)
        reply, history = run_agent(user_input, history)
        print(reply)
        print()


if __name__ == "__main__":
    main()
