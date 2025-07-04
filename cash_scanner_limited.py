import requests
import time
import json
from datetime import datetime

# Configuration
CASH_TOKEN_TYPE = "0x61ed8b048636516b4eaf4c74250fa4f9440d9c3e163d96aeb863fe658a4bdc67::CASH::CASH"
LIQUIDSWAP_ACCOUNT = "0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12"
NODE_URL = "https://fullnode.mainnet.aptoslabs.com"

def get_liquidswap_events(start_sequence=0, limit=100):
    """Get events from Liquidswap account"""
    try:
        url = f"{NODE_URL}/accounts/{LIQUIDSWAP_ACCOUNT}/events?start={start_sequence}&limit={limit}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting events: {e}")
        return []

def get_transaction_details(version):
    """Get transaction details by version"""
    try:
        url = f"{NODE_URL}/transactions/by_version/{version}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error getting transaction: {e}")
        return None

def is_cash_related_event(event):
    """Check if event involves CASH token"""
    event_str = json.dumps(event, default=str)
    return CASH_TOKEN_TYPE in event_str

def is_swap_event(event):
    """Check if event is a swap"""
    event_type = event.get("type", "")
    return "swap" in event_type.lower()

def process_swap_event(event):
    """Process a swap event and extract relevant information"""
    try:
        # Get transaction details
        txn = get_transaction_details(event["version"])
        if not txn:
            return None
        
        # Extract event data
        event_data = event.get("data", {})
        
        swap_info = {
            "transaction_hash": txn["hash"],
            "version": event["version"],
            "timestamp": txn["timestamp"],
            "sender": txn["sender"],
            "event_type": "swap",
            "event_data": event_data,
            "gas_used": txn.get("gas_used", 0),
            "success": txn.get("success", True)
        }
        
        return swap_info
    except Exception as e:
        print(f"Error processing swap event: {e}")
        return None

def calculate_price_info(swap_info):
    """Calculate price and volume from swap data"""
    try:
        event_data = swap_info["event_data"]
        
        # Extract amounts (convert from octas to actual amounts)
        apt_in = int(event_data.get("y_in", 0)) / 100000000  # APT has 8 decimals
        cash_out = int(event_data.get("x_out", 0)) / 100000000  # CASH has 8 decimals
        
        # Calculate price
        price = apt_in / cash_out if cash_out > 0 else 0
        
        return {
            "apt_amount": apt_in,
            "cash_amount": cash_out,
            "price_apt_per_cash": price,
            "price_cash_per_apt": 1/price if price > 0 else 0
        }
    except Exception as e:
        print(f"Error calculating price: {e}")
        return None

def scan_cash_transactions_limited(target_count=10, max_attempts=100):
    """Scan for a specific number of CASH transactions"""
    
    last_sequence = 0
    swaps_found = 0
    attempts = 0
    
    print("🚀 Starting Limited CASH Token Transaction Scanner")
    print(f"📊 Token: {CASH_TOKEN_TYPE}")
    print(f"🏦 DEX: Liquidswap ({LIQUIDSWAP_ACCOUNT})")
    print(f"🎯 Target: {target_count} CASH swaps")
    print(f"🔄 Max attempts: {max_attempts}")
    print("=" * 60)
    
    while swaps_found < target_count and attempts < max_attempts:
        try:
            attempts += 1
            print(f"\n📡 Attempt {attempts}/{max_attempts} - Looking for events (sequence: {last_sequence})")
            
            # Get new events
            events = get_liquidswap_events(last_sequence, 100)
            
            if events:
                print(f"   Found {len(events)} events")
                
                for event in events:
                    # Check if it's a CASH-related swap
                    if is_cash_related_event(event) and is_swap_event(event):
                        swap_info = process_swap_event(event)
                        
                        if swap_info:
                            swaps_found += 1
                            
                            # Calculate price info
                            price_info = calculate_price_info(swap_info)
                            
                            # Display results
                            print(f"\n💰 CASH SWAP #{swaps_found}/{target_count}")
                            print(f"   Hash: {swap_info['transaction_hash']}")
                            print(f"   Sender: {swap_info['sender']}")
                            print(f"   Timestamp: {datetime.fromtimestamp(int(swap_info['timestamp'])/1000000)}")
                            
                            if price_info:
                                print(f"   APT Amount: {price_info['apt_amount']:.6f} APT")
                                print(f"   CASH Amount: {price_info['cash_amount']:.6f} CASH")
                                print(f"   Price: {price_info['price_apt_per_cash']:.8f} APT per CASH")
                                print(f"   Price: {price_info['price_cash_per_apt']:.8f} CASH per APT")
                            
                            print(f"   Gas Used: {swap_info['gas_used']}")
                            print("-" * 40)
                            
                            # Check if we've reached our target
                            if swaps_found >= target_count:
                                print(f"\n🎉 Target reached! Found {swaps_found} CASH swaps")
                                return
                    
                    # Update sequence number
                    last_sequence = max(last_sequence, event["sequence_number"] + 1)
            else:
                print("   No new events found")
            
            # Wait before next poll
            print("   Waiting 5 seconds...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print(f"\n🛑 Scanner stopped by user")
            print(f"📈 CASH swaps found: {swaps_found}/{target_count}")
            return
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(10)
    
    # Final summary
    print(f"\n🏁 Scan completed!")
    print(f"📈 CASH swaps found: {swaps_found}/{target_count}")
    print(f"🔄 Total attempts: {attempts}")
    
    if swaps_found < target_count:
        print(f"⚠️  Could not find {target_count} swaps within {max_attempts} attempts")
    else:
        print(f"✅ Successfully found {target_count} CASH swaps!")

if __name__ == "__main__":
    # You can change these parameters
    TARGET_SWAPS = 5  # Number of CASH swaps to find
    MAX_ATTEMPTS = 50  # Maximum number of polling attempts
    
    scan_cash_transactions_limited(TARGET_SWAPS, MAX_ATTEMPTS) 