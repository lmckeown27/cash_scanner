import asyncio
from aptos_sdk.async_client import RestClient
import json

NODE_URL = "https://fullnode.mainnet.aptoslabs.com"
CASH_TOKEN_TYPE = "0x61ed8b048636516b4eaf4c74250fa4f9440d9c3e163d96aeb863fe658a4bdc67::CASH::CASH"

client = RestClient(NODE_URL)

async def is_cash_swap_event(event):
    event_type = event.get("type", "")
    return "swap" in event_type.lower() and CASH_TOKEN_TYPE in event_type

async def get_latest_version():
    ledger_info = await client.info()
    return int(ledger_info["ledger_version"])

async def scan_cash_swaps(poll_interval=5):
    print("🚀 Scanning for CASH swaps using aptos-sdk (async)...")
    last_version = await get_latest_version()
    swaps_found = 0

    while True:
        try:
            latest_version = await get_latest_version()
            # Scan new transactions since last check
            for version in range(last_version + 1, latest_version + 1):
                txn = await client.transaction_by_version(version)
                if txn["type"] == "user_transaction":
                    for event in txn.get("events", []):
                        if await is_cash_swap_event(event):
                            swaps_found += 1
                            print(f"\n💰 CASH SWAP #{swaps_found}")
                            print(f"  Txn Hash: {txn['hash']}")
                            print(f"  Sender: {txn['sender']}")
                            print(f"  Timestamp: {txn['timestamp']}")
                            print(f"  Event Type: {event['type']}")
                            print(f"  Event Data: {json.dumps(event['data'], indent=2)}")
            last_version = latest_version
            await asyncio.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(scan_cash_swaps(poll_interval=5)) 