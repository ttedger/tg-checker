import asyncio
import os
import time
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.account import CheckUsernameRequest
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, UsernameInvalidError, SessionPasswordNeededError

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["SESSION"]
CHUNK = os.environ.get("CHUNK", "1")

HANDLES_FILE = f"handles_{CHUNK}.txt"
AVAILABLE_FILE = f"available_{CHUNK}.txt"
LOG_FILE = f"log_{CHUNK}.txt"
MAX_FLOOD_WAIT = 1800  # 30 mins max wait

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

async def main():
    start_time = time.time()
    log("=" * 50)
    log(f"🚀 STARTING CHUNK {CHUNK}")
    log(f"📄 Handles file: {HANDLES_FILE}")
    log("=" * 50)

    # Check handles file exists
    if not os.path.exists(HANDLES_FILE):
        log(f"❌ ERROR: {HANDLES_FILE} not found!")
        return

    # Load handles
    with open(HANDLES_FILE) as f:
        handles = [l.strip() for l in f if l.strip()]
    log(f"📋 Loaded {len(handles)} handles to check")

    # Connect
    log("🔌 Connecting to Telegram...")
    try:
        client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
        await client.connect()
    except Exception as e:
        log(f"❌ Connection failed: {e}")
        return

    # Verify login
    try:
        me = await client.get_me()
        if me is None:
            log("❌ Session invalid — not logged in! Regenerate SESSION string.")
            return
        log(f"✅ Logged in as: {me.first_name} (@{me.username}) | ID: {me.id}")
    except Exception as e:
        log(f"❌ Auth check failed: {e}")
        return

    log(f"⏱️  Delay: 10s per handle")
    log(f"⏱️  Estimated time: {len(handles) * 10 // 60} mins")
    log("-" * 50)

    # Counters
    found = []
    taken = 0
    skipped = 0
    errors = 0
    flood_hits = 0

    for i, handle in enumerate(handles):
        # Progress every 50
        if i > 0 and i % 50 == 0:
            elapsed = int(time.time() - start_time)
            rate = i / (elapsed / 60)
            remaining = int((len(handles) - i) / rate) if rate > 0 else 0
            log(f"📊 PROGRESS: {i}/{len(handles)} | ✅ {len(found)} available | ⏱️ {elapsed//60}m elapsed | ~{remaining}m remaining")

        try:
            result = await client(CheckUsernameRequest(handle))

            if result:
                found.append(handle)
                # Save instantly
                with open(AVAILABLE_FILE, "a") as f:
                    f.write(handle + "\n")
                log(f"✅ AVAILABLE @{handle} — ({len(found)} total found)")
            else:
                taken += 1
                log(f"❌ taken    @{handle}")

        except FloodWaitError as e:
            flood_hits += 1
            wait = e.seconds
            log(f"⚠️  FLOOD WAIT #{flood_hits} — {wait}s ({wait//60} mins)")
            if wait > MAX_FLOOD_WAIT:
                log(f"🛑 Flood wait too long ({wait//60} mins) — stopping gracefully at handle {i}")
                break
            log(f"💤 Sleeping {wait}s then resuming...")
            await asyncio.sleep(wait + 5)
            continue

        except UsernameInvalidError:
            skipped += 1
            log(f"⚠️  SKIP (invalid) @{handle}")

        except Exception as e:
            errors += 1
            log(f"🔴 ERROR @{handle}: {e}")

        await asyncio.sleep(10)

    # Final summary
    elapsed_total = int(time.time() - start_time)
    log("=" * 50)
    log(f"🏁 CHUNK {CHUNK} COMPLETE")
    log("=" * 50)
    log(f"✅ Available:    {len(found)}")
    log(f"❌ Taken:        {taken}")
    log(f"⚠️  Skipped:      {skipped}")
    log(f"🔴 Errors:       {errors}")
    log(f"⚠️  Flood hits:   {flood_hits}")
    log(f"⏱️  Total time:   {elapsed_total//60}m {elapsed_total%60}s")
    log(f"💾 Saved to:     {AVAILABLE_FILE}")
    log(f"📝 Full log:     {LOG_FILE}")
    log("=" * 50)

    await client.disconnect()

asyncio.run(main())