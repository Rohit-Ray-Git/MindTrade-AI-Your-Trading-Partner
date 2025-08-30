"""
Delta Exchange API Integration
Handles authentication, trade fetching, and data synchronization
"""

import os
import hmac
import hashlib
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
import httpx
from loguru import logger

from models.dal import TradeDAL, get_db_session
from models.models import Trade

class DeltaExchangeAPI:
    """Delta Exchange API client for trade synchronization"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize Delta Exchange API client"""
        self.api_key = api_key or os.getenv("DELTA_API_KEY")
        self.api_secret = api_secret or os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange"
        
        if not self.api_key or not self.api_secret:
            logger.warning("Delta Exchange API credentials not configured")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Delta Exchange API client initialized")
    
    def _generate_signature(self, method: str, timestamp: str, request_path: str, body: str = "") -> str:
        """Generate HMAC signature for Delta Exchange API"""
        try:
            message = method + timestamp + request_path + body
            signature = hmac.new(
                self.api_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            return signature
        except Exception as e:
            logger.error(f"Error generating signature: {e}")
            raise
    
    def _get_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        """Get headers with authentication for API requests"""
        timestamp = str(int(time.time()))
        signature = self._generate_signature(method, timestamp, request_path, body)
        
        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json"
        }
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if not self.enabled:
            return None
        
        try:
            endpoint = "/v2/profile"
            headers = self._get_headers("GET", endpoint)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Account info retrieved successfully")
                    return data
                else:
                    logger.error(f"Failed to get account info: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    async def get_fills(self, 
                       start_time: Optional[datetime] = None, 
                       end_time: Optional[datetime] = None,
                       product_symbol: Optional[str] = None,
                       page_size: int = 100) -> List[Dict[str, Any]]:
        """Get trading fills (executed orders) from Delta Exchange"""
        if not self.enabled:
            logger.warning("Delta Exchange API not enabled")
            return []
        
        try:
            endpoint = "/v2/orders/history/fills"
            
            # Build query parameters
            params = {
                "page_size": min(page_size, 1000)  # API limit
            }
            
            if start_time:
                params["start_time"] = int(start_time.timestamp())
            if end_time:
                params["end_time"] = int(end_time.timestamp())
            if product_symbol:
                params["product_symbol"] = product_symbol
            
            # Convert params to query string
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_endpoint = f"{endpoint}?{query_string}"
            
            headers = self._get_headers("GET", full_endpoint)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{full_endpoint}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    fills = data.get("result", [])
                    logger.info(f"Retrieved {len(fills)} fills from Delta Exchange")
                    return fills
                elif response.status_code == 401:
                    logger.error("Delta Exchange API authentication failed")
                    return []
                else:
                    logger.error(f"Failed to get fills: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting fills: {e}")
            return []
    
    async def get_products(self) -> List[Dict[str, Any]]:
        """Get available trading products"""
        try:
            # This is a public endpoint, no authentication required
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/products",
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get("result", [])
                    logger.info(f"Retrieved {len(products)} products")
                    return products
                else:
                    logger.error(f"Failed to get products: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
    
    def _process_fills_to_trades(self, fills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process Delta Exchange fills into trade format"""
        trades = []
        
        try:
            # Group fills by order ID to reconstruct complete trades
            order_groups = {}
            for fill in fills:
                order_id = fill.get("order_id")
                if order_id not in order_groups:
                    order_groups[order_id] = []
                order_groups[order_id].append(fill)
            
            # Process each order group
            for order_id, order_fills in order_groups.items():
                try:
                    # Sort fills by timestamp
                    order_fills.sort(key=lambda x: x.get("created_at", 0))
                    
                    # Calculate trade metrics
                    total_quantity = sum(float(fill.get("size", 0)) for fill in order_fills)
                    total_notional = sum(float(fill.get("size", 0)) * float(fill.get("price", 0)) for fill in order_fills)
                    avg_price = total_notional / total_quantity if total_quantity > 0 else 0
                    
                    first_fill = order_fills[0]
                    last_fill = order_fills[-1]
                    
                    # Extract trade information
                    symbol = first_fill.get("product", {}).get("symbol", "UNKNOWN")
                    side = first_fill.get("side", "").upper()  # "buy" or "sell"
                    direction = "LONG" if side == "BUY" else "SHORT"
                    
                    # Calculate fees
                    total_fees = sum(float(fill.get("commission", 0)) for fill in order_fills)
                    
                    # Create trade record
                    trade_data = {
                        "external_id": f"delta_{order_id}",
                        "exchange": "Delta Exchange",
                        "symbol": symbol,
                        "direction": direction,
                        "entry_price": avg_price,
                        "exit_price": avg_price,  # For now, treat as single fill
                        "quantity": total_quantity,
                        "fees": total_fees,
                        "entry_time": datetime.fromtimestamp(first_fill.get("created_at", 0) / 1000),
                        "exit_time": datetime.fromtimestamp(last_fill.get("created_at", 0) / 1000),
                        "raw_data": {
                            "order_id": order_id,
                            "fills": order_fills,
                            "fill_count": len(order_fills)
                        }
                    }
                    
                    trades.append(trade_data)
                    
                except Exception as e:
                    logger.error(f"Error processing order {order_id}: {e}")
                    continue
            
            logger.info(f"Processed {len(fills)} fills into {len(trades)} trades")
            return trades
            
        except Exception as e:
            logger.error(f"Error processing fills to trades: {e}")
            return []
    
    async def sync_trades(self, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Synchronize trades from Delta Exchange to local database"""
        if not self.enabled:
            return {
                "success": False,
                "error": "Delta Exchange API not configured",
                "imported_count": 0,
                "skipped_count": 0
            }
        
        try:
            # Default to last 30 days if no date range specified
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            logger.info(f"Syncing trades from {start_date} to {end_date}")
            
            # Get fills from Delta Exchange
            fills = await self.get_fills(start_date, end_date)
            
            if not fills:
                return {
                    "success": True,
                    "message": "No fills found for the specified period",
                    "imported_count": 0,
                    "skipped_count": 0
                }
            
            # Process fills into trades
            trade_data_list = self._process_fills_to_trades(fills)
            
            # Import trades to database
            db = get_db_session()
            trade_dal = TradeDAL(db)
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for trade_data in trade_data_list:
                try:
                    # Check if trade already exists (by external_id)
                    existing_trade = db.query(Trade).filter(
                        Trade.external_id == trade_data["external_id"]
                    ).first()
                    
                    if existing_trade:
                        skipped_count += 1
                        logger.debug(f"Trade {trade_data['external_id']} already exists, skipping")
                        continue
                    
                    # Calculate P&L (for now, assume breakeven since we don't have exit data)
                    trade_data["pnl"] = -trade_data["fees"]  # Only fees as loss
                    trade_data["stop_price"] = None
                    trade_data["target_price"] = None
                    
                    # Create trade
                    trade = trade_dal.create_trade(trade_data)
                    imported_count += 1
                    logger.info(f"Imported trade: {trade.symbol} - {trade.direction}")
                    
                except Exception as e:
                    error_msg = f"Error importing trade {trade_data.get('external_id', 'unknown')}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue
            
            db.close()
            
            result = {
                "success": True,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "total_fills": len(fills),
                "total_trades": len(trade_data_list),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
            if errors:
                result["errors"] = errors
            
            logger.info(f"Sync completed: {imported_count} imported, {skipped_count} skipped")
            return result
            
        except Exception as e:
            logger.error(f"Error syncing trades: {e}")
            return {
                "success": False,
                "error": str(e),
                "imported_count": 0,
                "skipped_count": 0
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and authentication"""
        if not self.enabled:
            return {
                "success": False,
                "error": "API credentials not configured"
            }
        
        try:
            # Test with account info endpoint
            account_info = await self.get_account_info()
            
            if account_info:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "account_id": account_info.get("id"),
                    "email": account_info.get("email")
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to retrieve account information"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }

class DeltaExchangeSync:
    """Higher-level synchronization manager"""
    
    def __init__(self):
        """Initialize sync manager"""
        self.api = DeltaExchangeAPI()
        self.last_sync = None
    
    async def auto_sync(self, hours_back: int = 24) -> Dict[str, Any]:
        """Perform automatic sync for recent trades"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        result = await self.api.sync_trades(start_time, end_time)
        
        if result.get("success"):
            self.last_sync = datetime.now()
        
        return result
    
    async def full_sync(self, days_back: int = 90) -> Dict[str, Any]:
        """Perform full historical sync"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        result = await self.api.sync_trades(start_time, end_time)
        
        if result.get("success"):
            self.last_sync = datetime.now()
        
        return result
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        return {
            "api_enabled": self.api.enabled,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "credentials_configured": bool(self.api.api_key and self.api.api_secret)
        }
