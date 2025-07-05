import asyncio
import aiohttp
import json
import ssl
from datetime import datetime

# Multiple reliable Aptos nodes - Real-time monitor uses different nodes
NODE_URLS = [
    "https://fullnode.mainnet.aptoslabs.com",
    "https://aptos-mainnet.pontem.wallet",
    "https://fullnode.mainnet.aptoslabs.com/v1",
    "https://aptos-mainnet.pontem.wallet/v1"
]

CASH_TOKEN_TYPE = "0x61ed8b048636516b4eaf4c74250fa4f9440d9c3e163d96aeb863fe658a4bdc67::CASH::CASH"

# Create SSL context that bypasses certificate issues
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def test_node_connectivity(node_url):
    """Test if a node is responding"""
    try:
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(f"{node_url}/v1", ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    if "ledger_version" in data:
                        return True, data["ledger_version"]
            
            async with session.get(f"{node_url}/", ssl=False) as response:
                if response.status == 200:
                    return True, None
                    
    except Exception as e:
        return False, None
    
    return False, None

async def find_working_node():
    """Find a working Aptos node"""
    print("🔍 Testing Aptos nodes for real-time monitor...")
    for i, node_url in enumerate(NODE_URLS, 1):
        print(f"  {i}/{len(NODE_URLS)} Testing: {node_url}")
        is_working, ledger_version = await test_node_connectivity(node_url)
        
        if is_working:
            print(f"✅ Found working node: {node_url}")
            if ledger_version:
                print(f"📊 Current ledger version: {ledger_version}")
            return node_url
    
    raise Exception("No working nodes found")

async def get_latest_version(node_url):
    """Get the latest ledger version from a node"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=15)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(f"{node_url}/v1", ssl=False) as response:
                    if response.status == 200:
                        data = await response.json()
                        return int(data.get("ledger_version", 0))
                    elif response.status == 429:
                        wait_time = (attempt + 1) * 5  # Progressive backoff
                        print(f"⚠️  Rate limited (HTTP 429). Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (attempt + 1) * 2
            print(f"⚠️  Error getting version (attempt {attempt + 1}/{max_retries}). Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    raise Exception("Failed to get latest version after all retries")

async def get_transaction(node_url, version):
    """Get a specific transaction by version"""
    try:
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(f"{node_url}/v1/transactions/by_version/{version}", ssl=False) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                elif response.status == 429:
                    await asyncio.sleep(3)
                    return None
                else:
                    return None
                    
    except Exception as e:
        return None

def is_cash_related_transaction(txn):
    """Check if a transaction involves CASH token"""
    if not txn or txn.get("type") != "user_transaction":
        return False
    
    # Check events for CASH token
    events = txn.get("events", [])
    for event in events:
        event_type = event.get("type", "")
        if CASH_TOKEN_TYPE in event_type:
            return True
    
    # Check payload for CASH token
    payload = txn.get("payload", {})
    if payload:
        # Check function calls
        function = payload.get("function", "")
        if CASH_TOKEN_TYPE in function:
            return True
        
        # Check type arguments
        type_arguments = payload.get("type_arguments", [])
        for arg in type_arguments:
            if CASH_TOKEN_TYPE in arg:
                return True
    
    return False

async def monitor_realtime_cash_transactions():
    """Monitor for new CASH transactions in real-time"""
    print("🚀 REAL-TIME CASH TRANSACTION MONITOR")
    print("⚡ Monitoring for live CASH transactions...")
    print("=" * 60)
    
    # Find a working node
    try:
        working_node = await find_working_node()
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Get current version to start monitoring from
    try:
        start_version = await get_latest_version(working_node)
        print(f"📊 Starting real-time monitoring from version: {start_version}")
    except Exception as e:
        print(f"❌ Failed to get current version: {e}")
        return

    print("📡 REAL-TIME MONITORING ACTIVE")
    print("💡 Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    last_checked_version = start_version
    realtime_transactions = []
    total_transactions_analyzed = 0
    swaps_in_current_batch = 0
    batch_size = 1000
    
    while True:
        try:
            # Get current latest version
            current_version = await get_latest_version(working_node)
            
            if current_version > last_checked_version:
                new_transactions_count = current_version - last_checked_version
                print(f"📈 New transactions detected: {last_checked_version + 1} to {current_version} ({new_transactions_count} transactions)")
                
                # Check new transactions
                for version in range(last_checked_version + 1, current_version + 1):
                    try:
                        txn = await get_transaction(working_node, version)
                        
                        if txn:
                            total_transactions_analyzed += 1
                            
                            if is_cash_related_transaction(txn):
                                transaction_time = datetime.fromtimestamp(int(txn['timestamp']) / 1000000)
                                swaps_in_current_batch += 1
                                
                                cash_txn_info = {
                                    'version': version,
                                    'timestamp': transaction_time,
                                    'hash': txn['hash'],
                                    'sender': txn.get('sender', 'unknown'),
                                    'events': txn.get('events', []),
                                    'payload': txn.get('payload', {})
                                }
                                realtime_transactions.append(cash_txn_info)
                                
                                print(f"🔥 REAL-TIME CASH TRANSACTION DETECTED!")
                                print(f"  📅 Transaction Time: {transaction_time}")
                                print(f"  🔗 Txn Hash: {txn['hash']}")
                                print(f"  👤 Sender: {txn.get('sender', 'unknown')}")
                                print(f"  📋 Version: {version}")
                                print(f"  ⚡ Type: LIVE TRANSACTION")
                                print(f"  📊 Total Transactions Analyzed: {total_transactions_analyzed:,}")
                                print(f"  💰 Total CASH Swaps Found: {len(realtime_transactions)}")
                                
                                # Show CASH-related events
                                events = txn.get('events', [])
                                for i, event in enumerate(events):
                                    if CASH_TOKEN_TYPE in event.get('type', ''):
                                        print(f"  📊 Event {i+1}: {event['type']}")
                                        print(f"  📊 Event Data: {json.dumps(event['data'], indent=4)}")
                                
                                print("=" * 60)
                        
                        # Report progress every 1,000 transactions
                        if total_transactions_analyzed % batch_size == 0:
                            print(f"📊 REAL-TIME BATCH SUMMARY: Analyzed {total_transactions_analyzed:,} transactions")
                            print(f"💰 CASH Swaps in this batch: {swaps_in_current_batch}")
                            print(f"💰 Total CASH Swaps found: {len(realtime_transactions)}")
                            print("-" * 40)
                            swaps_in_current_batch = 0  # Reset for next batch
                            
                    except Exception as e:
                        continue
                
                last_checked_version = current_version
            else:
                print(f"⏳ No new transactions. Current version: {current_version}")
            
            # Wait before next check
            await asyncio.sleep(10)  # Increased delay for real-time monitor
            
        except KeyboardInterrupt:
            print("\n🛑 Real-time monitoring stopped by user")
            print(f"📊 Final real-time analysis: {total_transactions_analyzed:,} transactions analyzed")
            break
        except Exception as e:
            print(f"⚠️  Error in real-time monitoring: {e}")
            await asyncio.sleep(10)
            continue
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎯 REAL-TIME MONITORING SUMMARY")
    print("=" * 60)
    print(f"📊 Total transactions analyzed: {total_transactions_analyzed:,}")
    print(f"💰 Total CASH transactions found: {len(realtime_transactions)}")
    
    if realtime_transactions:
        print(f"\n📋 REAL-TIME CASH TRANSACTION DETAILS:")
        for i, txn in enumerate(realtime_transactions, 1):
            print(f"  #{i}: {txn['timestamp']} - Version {txn['version']} - {txn['hash'][:20]}...")
    else:
        print("❌ No CASH transactions found during real-time monitoring")
    
    print("✅ Real-time monitor completed!")

if __name__ == "__main__":
    asyncio.run(monitor_realtime_cash_transactions()) 