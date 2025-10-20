#!/usr/bin/env python -3.8
"""Test script for MT5 Trade Sync Service"""

def test_sync_service():
    """Test the sync service directly"""
    try:
        print("Testing MT5 Trade Sync Service...")

        # Import the service
        from services.sync_mt5_trades_service import MT5TradeSyncService, mt5_trade_sync
        print("Service imported successfully")

        # Try to create a new instance
        test_service = MT5TradeSyncService()
        print("Service instance created successfully")

        # Check MT5 connection
        mt5_connected = test_service._check_mt5_connection()
        print(f"MT5 Connected: {mt5_connected}")

        # Try to get status
        status = test_service.get_status()
        print(f"Service Status: {status}")

        # Try sync now (should handle MT5 being disconnected gracefully)
        print("Attempting sync_now()...")
        result = test_service.sync_now()
        print(f"Sync result: {result}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sync_service()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
