import asyncio
import os
from telethon import TelegramClient
from telethon.tl.functions.account import CheckUsernameRequest
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, UsernameInvalidError

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["SESSION"]
CHUNK = os.environ.get("CHUNK", "1")

HANDLES_FILE = f"handles_{CHUNK}.txt"
AVAILABLE_FILE = f"available_{CHUNK}.txt"

async def main():
    if not os.path.exists(HANDLES_FILE):
        print(f"No file {HANDLES_FILE}, skipping.")
        return

    with open(HANDLES_FILE) as f:
        handles = [l.strip() for l in f if l.strip()]

    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.connect()

    found = []
    print(f"Checking {len(handles)} handles (chunk {CHUNK})...")

    for i, handle in enumerate(handles):
        try:
            result = await client(CheckUsernameRequest(handle))
            if result:
                found.append(handle)
                with open(AVAILABLE_FILE, "a") as f:
                    f.write(handle + "\n")
                print(f"[✓ AVAILABLE] @{handle} ({len(found)} found)")
            else:
                print(f"[✗] @{handle}")

        except FloodWaitError as e:
            print(f"Rate limited, waiting {e.seconds}s...")
            await asyncio.sleep(e.seconds + 5)
            continue
        except UsernameInvalidError:
            print(f"[SKIP] @{handle}")
        except Exception as e:
            print(f"[ERROR] @{handle}: {e}")

        await asyncio.sleep(4)

    print(f"\nDone! {len(found)} available in chunk {CHUNK}")
    await client.disconnect()

asyncio.run(main())
