import asyncio
import aiohttp
import json
import ssl
import time
from datetime import datetime

# Multiple reliable Aptos nodes - Historical scanner uses different nodes
NODE_URLS = [
    "https://aptos-mainnet.pontem.wallet",
    "https://fullnode.mainnet.aptoslabs.com",
    "https://aptos-mainnet.pontem.wallet/v1",
    "https://fullnode.mainnet.aptoslabs.com/v1"
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
    print("🔍 Testing Aptos nodes for historical scanner...")
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

async def scan_historical_cash_transactions():
    """Scan historically for all CASH transactions"""
    print("🚀 HISTORICAL CASH TRANSACTION SCANNER")
    print("📚 Scanning past CASH transactions...")
    print("=" * 60)
    
    # Find a working node
    try:
        working_node = await find_working_node()
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Get current version
    try:
        current_version = await get_latest_version(working_node)
        print(f"📊 Current ledger version: {current_version}")
    except Exception as e:
        print(f"❌ Failed to get current version: {e}")
        return

    # Scan last 100,000 transactions for historical data
    historical_start = max(0, current_version - 100000)
    print(f"📅 Scanning transactions from {historical_start} to {current_version}")
    print(f"📊 Total transactions to scan: {current_version - historical_start + 1:,}")
    print("=" * 60)
    
    cash_transactions = []
    transactions_checked = 0
    swaps_in_current_batch = 0
    last_summary_time = time.time()
    summary_interval = 5  # seconds
    
    for version in range(historical_start, current_version + 1):
        try:
            txn = await get_transaction(working_node, version)
            
            if txn:
                transactions_checked += 1
                
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
                    cash_transactions.append(cash_txn_info)
                    
                    print(f"💰 HISTORICAL CASH TRANSACTION FOUND!")
                    print(f"  📅 Transaction Time: {transaction_time}")
                    print(f"  🔗 Txn Hash: {txn['hash']}")
                    print(f"  👤 Sender: {txn.get('sender', 'unknown')}")
                    print(f"  📋 Version: {version}")
                    print(f"  📊 Transactions Analyzed: {transactions_checked:,}")
                    print(f"  💰 CASH Swaps Found: {len(cash_transactions)}")
                    print(f"  📚 Type: HISTORICAL TRANSACTION")
                    
                    # Show CASH-related events with detailed formatting
                    events = txn.get('events', [])
                    cash_events_found = 0
                    for i, event in enumerate(events):
                        if CASH_TOKEN_TYPE in event.get('type', ''):
                            cash_events_found += 1
                            print(f"  📊 Event {cash_events_found}: {event['type']}")
                            print(f"  📊 Event Data: {json.dumps(event['data'], indent=4)}")
                    
                    # Show payload information if it contains CASH token
                    payload = txn.get('payload', {})
                    if payload:
                        function = payload.get('function', '')
                        if CASH_TOKEN_TYPE in function:
                            print(f"  🔧 Function: {function}")
                        
                        type_arguments = payload.get('type_arguments', [])
                        for arg in type_arguments:
                            if CASH_TOKEN_TYPE in arg:
                                print(f"  🔧 Type Argument: {arg}")
                    
                    print("-" * 60)
                
                # Report progress every 5 seconds
                current_time = time.time()
                if current_time - last_summary_time >= summary_interval:
                    print(f"📊 BATCH SUMMARY: Analyzed {transactions_checked:,} transactions")
                    print(f"💰 CASH Swaps in this batch: {swaps_in_current_batch}")
                    print(f"💰 Total CASH Swaps found: {len(cash_transactions)}")
                    print(f"📈 Progress: {transactions_checked:,} / {current_version - historical_start + 1:,} transactions")
                    print(f"📊 Completion: {(transactions_checked / (current_version - historical_start + 1) * 100):.1f}%")
                    print("-" * 40)
                    swaps_in_current_batch = 0  # Reset for next batch
                    last_summary_time = current_time
                
                # Add small delay to avoid rate limiting
                if transactions_checked % 50 == 0:
                    await asyncio.sleep(0.5)  # Increased delay for historical scanner
            else:
                # Count attempted transactions even if they don't exist
                transactions_checked += 1
                
                # Report progress every 5 seconds (including failed attempts)
                current_time = time.time()
                if current_time - last_summary_time >= summary_interval:
                    print(f"📊 BATCH SUMMARY: Analyzed {transactions_checked:,} transactions")
                    print(f"💰 CASH Swaps in this batch: {swaps_in_current_batch}")
                    print(f"💰 Total CASH Swaps found: {len(cash_transactions)}")
                    print(f"📈 Progress: {transactions_checked:,} / {current_version - historical_start + 1:,} transactions")
                    print(f"📊 Completion: {(transactions_checked / (current_version - historical_start + 1) * 100):.1f}%")
                    print("-" * 40)
                    swaps_in_current_batch = 0  # Reset for next batch
                    last_summary_time = current_time
                    
        except Exception as e:
            # Count attempted transactions even if they fail
            transactions_checked += 1
            
            # Report progress every 5 seconds (including failed attempts)
            current_time = time.time()
            if current_time - last_summary_time >= summary_interval:
                print(f"📊 BATCH SUMMARY: Analyzed {transactions_checked:,} transactions")
                print(f"💰 CASH Swaps in this batch: {swaps_in_current_batch}")
                print(f"💰 Total CASH Swaps found: {len(cash_transactions)}")
                print(f"📈 Progress: {transactions_checked:,} / {current_version - historical_start + 1:,} transactions")
                print(f"📊 Completion: {(transactions_checked / (current_version - historical_start + 1) * 100):.1f}%")
                print("-" * 40)
                swaps_in_current_batch = 0  # Reset for next batch
                last_summary_time = current_time
    
    # Final Summary
    print("\n" + "=" * 60)
    print("🎯 HISTORICAL SCAN COMPLETE")
    print("=" * 60)
    print(f"📊 Total transactions analyzed: {transactions_checked:,}")
    print(f"💰 Total CASH transactions found: {len(cash_transactions)}")
    
    if cash_transactions:
        print(f"\n📋 HISTORICAL CASH TRANSACTION DETAILS:")
        for i, txn in enumerate(cash_transactions, 1):
            print(f"  #{i}: {txn['timestamp']} - Version {txn['version']} - {txn['hash'][:20]}...")
    else:
        print("❌ No CASH transactions found in historical scan")
    
    print("✅ Historical scanner completed!")

if __name__ == "__main__":
    asyncio.run(scan_historical_cash_transactions()) 