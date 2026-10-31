import os
import json
import asyncio
import subprocess
import edge_tts

VOICE = "en-US-ChristopherNeural"

SCENES = [
    {
        "id": "scene_01",
        "image": "scene_01_dashboard.png",
        "section": "01 / EXECUTIVE DASHBOARD",
        "title": "Real-Time Recurring Revenue Analytics",
        "narration": "Welcome to Brightloop Subscription Management and Recurring Billing Platform. In modern SaaS companies, recurring revenue tracking is often broken—leading to forgotten renewals, manual invoice errors, and delayed reporting. Brightloop provides a unified, enterprise-ready platform engineered with strict numeric precision, automated lifecycle billing, and an innovative AI Revenue Copilot."
    },
    {
        "id": "scene_02",
        "image": "scene_02_catalog.png",
        "section": "02 / PRODUCT CATALOG & PLANS",
        "title": "Dynamic Product Variants & Plan Rules",
        "narration": "Our catalog supports dynamic product variants and flexible billing rules. For instance, selecting the Odoo ERP Seat variant automatically adds five hundred sixty rupees to the base price. Plans feature configurable pause, close, and renewal policies tailored for modern enterprise SaaS contracts."
    },
    {
        "id": "scene_03",
        "image": "scene_03_subscriptions.png",
        "section": "03 / SUBSCRIPTION LIFECYCLE",
        "title": "Rigorous 5-State Lifecycle Engine",
        "narration": "Subscriptions follow a rigorous five-state lifecycle: Draft, Quotation, Confirmed, Active, and Closed. Here, Acme Private Limited is in Active status. Notice how our system computed the un-discounted totals: untaxed three thousand six hundred twenty rupees, tax six hundred fifty-one rupees, and total four thousand two hundred seventy-one rupees."
    },
    {
        "id": "scene_04",
        "image": "scene_04_invoices.png",
        "section": "04 / RECURRING BILLING ENGINE",
        "title": "Golden Vector Numeric Accuracy (₹3,844.44)",
        "narration": "On billing day, our engine automatically generates invoices with zero human intervention. Notice the mathematical precision: our discount engine detects the Volume ten percent discount and splits three hundred sixty-two rupees with largest-remainder allocation. GST eighteen percent is computed with strict half-up rounding, arriving at exactly three thousand eight hundred forty-four rupees and forty-four paise."
    },
    {
        "id": "scene_05",
        "image": "scene_05_payments.png",
        "section": "05 / PAYMENT ENGINE",
        "title": "Overpayment Guard & Instant Ledger Settlement",
        "narration": "Our payment engine prevents overpayment, seamlessly accommodates partial payments, records payment methods, and automatically transitions the invoice status to Paid once settled."
    },
    {
        "id": "scene_06",
        "image": "scene_06_ai_copilot.png",
        "section": "06 / AI REVENUE COPILOT",
        "title": "Autonomous Churn Risk & Health Scoring (0–100)",
        "narration": "For our hackathon innovation, we built the Brightloop AI Revenue Copilot. Instead of waiting for accounts to churn after missed renewals, our copilot tracks payment lag and subscription tenure to assign an autonomous Health Score from zero to one hundred and classify churn risk."
    },
    {
        "id": "scene_07",
        "image": "scene_07_smart_dunning.png",
        "section": "07 / SMART DUNNING GENERATOR",
        "title": "Tone-Adjusted AI Retention Notices",
        "narration": "With the Smart Dunning Generator, our AI drafts personalized tone-adjusted retention emails—from gentle reminders for recent slips to urgent notices for critical accounts, protecting recurring cashflow before revenue leakage occurs."
    },
    {
        "id": "scene_08",
        "image": "scene_08_time_travel.png",
        "section": "08 / TIME-TRAVEL BILLING ENGINE",
        "title": "Virtual Clock & Automated Catch-Up Billing",
        "narration": "Judges can test the platform interactively! Clicking Advance One Month advances our virtual clock to the next billing cycle. Running the billing engine instantly generates catch-up invoices with zero duplicate billing."
    },
    {
        "id": "scene_09",
        "image": "scene_09_customer_portal.png",
        "section": "09 / CUSTOMER SELF-SERVICE PORTAL",
        "title": "Independent Client Dashboard & Tax Receipts",
        "narration": "Customers get an isolated self-service portal to approve quotes, request pauses or renewals, and download compliant GST tax receipts at any time."
    },
    {
        "id": "scene_10",
        "image": "scene_10_architecture.png",
        "section": "10 / ARCHITECTURE & CONCLUSION",
        "title": "FastAPI + 100% Test Coverage + Production-Ready",
        "narration": "A unified platform built in Python and FastAPI with strict numeric decimal types, SQLite and PostgreSQL compatibility, and one hundred percent test coverage. Thank you for watching Brightloop!"
    }
]

async def generate_all_narration():
    base_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(base_dir, "output", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    print(f"🎙 Generating voiceovers using {VOICE}...")
    manifest = []
    
    for idx, scene in enumerate(SCENES, 1):
        out_audio = os.path.join(audio_dir, f"{scene['id']}.mp3")
        print(f"  [{idx}/{len(SCENES)}] Synthesizing: {scene['section']}...")
        
        communicate = edge_tts.Communicate(scene["narration"], VOICE, rate="+3%")
        await communicate.save(out_audio)
        
        # Get duration using ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            out_audio
        ]
        duration_str = subprocess.check_output(probe_cmd).decode().strip()
        speech_duration = float(duration_str)
        
        # Add 1.2s padding for natural pause and video pacing
        scene_duration = round(speech_duration + 1.2, 2)
        
        manifest.append({
            "id": scene["id"],
            "image": scene["image"],
            "section": scene["section"],
            "title": scene["title"],
            "speech_duration": speech_duration,
            "scene_duration": scene_duration,
            "audio_file": f"{scene['id']}.mp3"
        })
        print(f"     Duration: {speech_duration:.2f}s (scene: {scene_duration:.2f}s)")
        
    manifest_path = os.path.join(base_dir, "output", "scenes_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    total_time = sum(s["scene_duration"] for s in manifest)
    print(f"🎉 All voiceovers generated! Total estimated video length: {total_time:.1f}s ({total_time/60:.2f} minutes)")
    print(f"📄 Manifest written to: {manifest_path}")

if __name__ == "__main__":
    asyncio.run(generate_all_narration())
