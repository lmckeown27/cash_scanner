# CASH Token Transaction Tracker

This project contains two separate Python scripts for tracking CASH token transactions on the Aptos blockchain.

## Scripts

### 1. `historical_cash_scanner.py`
- **Purpose**: Scans historical transactions for CASH token activity
- **Scope**: Last 100,000 transactions
- **Duration**: One-time scan (completes and stops)
- **Output**: Detailed report of all historical CASH transactions found

### 2. `realtime_cash_monitor.py`
- **Purpose**: Monitors for new CASH token transactions in real-time
- **Scope**: Live monitoring from current blockchain state
- **Duration**: Continuous monitoring (runs until stopped)
- **Output**: Immediate alerts when new CASH transactions are detected

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running Both Scripts Simultaneously

**Option 1: Multiple Terminal Windows**
```bash
# Terminal 1 - Start real-time monitoring
python realtime_cash_monitor.py

# Terminal 2 - Start historical scanning
python historical_cash_scanner.py
```

**Option 2: Background Processing**
```bash
# Start real-time monitor in background
python realtime_cash_monitor.py &

# Start historical scanner in foreground
python historical_cash_scanner.py
```

**Option 3: Parallel Execution**
```bash
# Run both simultaneously
python realtime_cash_monitor.py & python historical_cash_scanner.py &
```

### Individual Script Usage

**Real-time Monitoring:**
```bash
python realtime_cash_monitor.py
```
- Starts monitoring immediately
- Press `Ctrl+C` to stop
- Shows live CASH transaction alerts

**Historical Scanning:**
```bash
python historical_cash_scanner.py
```
- Scans last 100,000 transactions
- Completes automatically
- Shows comprehensive historical report

## Features

### Both Scripts Include:
- ✅ Multiple Aptos node support
- ✅ Rate limiting protection
- ✅ Detailed transaction analysis
- ✅ Progress tracking (every 1,000 transactions)
- ✅ Comprehensive error handling
- ✅ SSL certificate bypass for development

### Real-time Monitor Features:
- ⚡ Immediate live monitoring
- 🔥 Instant CASH transaction alerts
- 📊 Real-time batch summaries
- 🛑 Graceful stop with Ctrl+C

### Historical Scanner Features:
- 📚 Comprehensive historical scan
- 📈 Progress tracking
- 📋 Detailed transaction reports
- 🎯 Complete analysis summary

## Output Examples

### Real-time Alert:
```
🔥 REAL-TIME CASH TRANSACTION DETECTED!
  📅 Transaction Time: 2024-01-15 14:36:10.987654
  🔗 Txn Hash: 0xabcdef1234567890...
  👤 Sender: 0x1234567890abcdef...
  📋 Version: 3005809455
  ⚡ Type: LIVE TRANSACTION
  📊 Total Transactions Analyzed: 1,500
  💰 Total CASH Swaps Found: 1
```

### Historical Report:
```
💰 HISTORICAL CASH TRANSACTION FOUND!
  📅 Transaction Time: 2024-01-15 14:25:30.123456
  🔗 Txn Hash: 0x1234567890abcdef...
  👤 Sender: 0x567890abcdef1234...
  📋 Version: 3005789001
  📊 Transactions Analyzed: 15,000
  💰 CASH Swaps Found: 1
```

## Configuration

### CASH Token Address:
The scripts are configured to track:
```
0x61ed8b048636516b4eaf4c74250fa4f9440d9c3e163d96aeb863fe658a4bdc67::CASH::CASH
```

### Aptos Nodes:
Multiple nodes are tested for reliability:
- https://fullnode.mainnet.aptoslabs.com
- https://aptos-mainnet.pontem.wallet
- Additional fallback nodes

## Notes

- Both scripts can run simultaneously without conflicts
- Each script uses independent network connections
- Rate limiting is handled gracefully
- Scripts are optimized for reliability over speed
- Historical scanner processes ~20-50 transactions/second
- Real-time monitor checks for new transactions every 5 seconds 