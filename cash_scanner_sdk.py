from aptos_sdk.client import RestClient
import time
import json

# Configuration
CASH_TOKEN_TYPE = "0x61ed8b048636516b4eaf4c74250fa4f9440d9c3e163d96aeb863fe658a4bdc67::CASH::CASH"
LIQUIDSWAP_ACCOUNT = "0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12"
NODE_URL = "https://fullnode.mainnet.aptoslabs.com"

client = RestClient(NODE_URL)

def get_liquidswap_swap_events(start_sequence=0, limit=100):
    """Get swap events from Liquidswap"""
    try:
        # Get all events from Liquidswap account
        events = client.get_account_events(
            account=LIQUIDSWAP_ACCOUNT,
            start=start_sequence,
            limit=limit
        )
        
        # Filter for swap events
        swap_events = []
        for event in events:
            if "swap" in str(event).lower():
                swap_events.append(event)
        return swap_events
    except Exception as e:
        print(f"Error getting swap events: {e}")
        return []

def is_cash_related_event(event_data):
    """Check if the event involves CASH token"""
    event_str = json.dumps(event_data, default=str)
    return CASH_TOKEN_TYPE in event_str

def process_swap_event(event):
    """Process a swap event and extract relevant information"""
    try:
        # Get transaction details via SDK
        txn = client.get_transaction_by_version(event["version"])
        
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

def scan_liquidswap_for_cash_transactions():
    """Main function to scan Liquidswap for CASH transactions"""
    
    # Track the last processed event sequence numbers
    last_swap_sequence = 0
    
    print(f"Starting to scan Liquidswap for CASH token transactions...")
    print(f"CASH Token Type: {CASH_TOKEN_TYPE}")
    print(f"Liquidswap Account: {LIQUIDSWAP_ACCOUNT}")
    print("Press Ctrl+C to stop scanning...")
    
    while True:
        try:
            # Get swap events
            swap_events = get_liquidswap_swap_events(last_swap_sequence, 100)
            for event in swap_events:
                if is_cash_related_event(event["data"]):
                    swap_info = process_swap_event(event)
                    if swap_info:
                        print(f"SWAP: {json.dumps(swap_info, indent=2)}")
                        
                        # Calculate and display price
                        try:
                            apt_in = int(swap_info["event_data"]["y_in"]) / 100000000
                            cash_out = int(swap_info["event_data"]["x_out"]) / 100000000
                            price = apt_in / cash_out if cash_out > 0 else 0
                            print(f"💰 Price: {price:.6f} APT per CASH")
                            print(f"📊 Volume: {apt_in:.2f} APT")
                        except:
                            pass
                last_swap_sequence = max(last_swap_sequence, event["sequence_number"] + 1)
            
            # Wait before next poll
            time.sleep(5)  # Poll every 5 seconds
            
        except KeyboardInterrupt:
            print("Scanning stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)  # Wait longer on error

if __name__ == "__main__":
    scan_liquidswap_for_cash_transactions() 