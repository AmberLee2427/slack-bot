"""
Simple in-memory rate limiter for Nancy bot.
Tracks daily usage per user with automatic cleanup.
"""

import time
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class DailyRateLimiter:
    def __init__(self, daily_limit: int = 100):
        """
        Initialize rate limiter with daily limit per user.
        
        Args:
            daily_limit: Maximum queries per user per day (default 100)
        """
        self.daily_limit = daily_limit
        # Format: {user_id: [(timestamp1, timestamp2, ...)]}
        self.user_usage = {}
        
        logger.info(f"Rate limiter initialized with daily limit: {daily_limit}")
    
    def _get_current_day_start(self) -> float:
        """Get timestamp for start of current UTC day"""
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return day_start.timestamp()
    
    def _cleanup_old_entries(self, user_id: str):
        """Remove entries older than 24 hours for a user"""
        if user_id not in self.user_usage:
            return
        
        day_start = self._get_current_day_start()
        
        # Keep only timestamps from today
        today_timestamps = [
            ts for ts in self.user_usage[user_id] 
            if ts >= day_start
        ]
        
        self.user_usage[user_id] = today_timestamps
        
        # Remove user entry if no usage today
        if not today_timestamps:
            del self.user_usage[user_id]
    
    def check_and_increment(self, user_id: str) -> tuple[bool, int, int]:
        """
        Check if user is within rate limit and increment usage.
        
        Args:
            user_id: Slack user ID
            
        Returns:
            tuple: (allowed: bool, used_today: int, remaining: int)
        """
        current_time = time.time()
        
        # Clean up old entries for this user
        self._cleanup_old_entries(user_id)
        
        # Get current usage count
        current_usage = len(self.user_usage.get(user_id, []))
        
        # Check if user would exceed limit
        if current_usage >= self.daily_limit:
            remaining = 0
            logger.warning(f"Rate limit exceeded for user {user_id}: {current_usage}/{self.daily_limit}")
            return False, current_usage, remaining
        
        # Add current timestamp to user's usage
        if user_id not in self.user_usage:
            self.user_usage[user_id] = []
        
        self.user_usage[user_id].append(current_time)
        new_usage = current_usage + 1
        remaining = self.daily_limit - new_usage
        
        logger.info(f"Rate limit check passed for user {user_id}: {new_usage}/{self.daily_limit} (remaining: {remaining})")
        return True, new_usage, remaining
    
    def get_user_stats(self, user_id: str) -> dict:
        """Get current usage stats for a user"""
        self._cleanup_old_entries(user_id)
        
        current_usage = len(self.user_usage.get(user_id, []))
        remaining = max(0, self.daily_limit - current_usage)
        
        return {
            "user_id": user_id,
            "used_today": current_usage,
            "daily_limit": self.daily_limit,
            "remaining": remaining,
            "reset_time": self._get_current_day_start() + 86400  # Next day start
        }
    
    def cleanup_all_users(self):
        """Clean up old entries for all users (call periodically)"""
        users_to_cleanup = list(self.user_usage.keys())
        
        for user_id in users_to_cleanup:
            self._cleanup_old_entries(user_id)
        
        logger.info(f"Cleaned up rate limiter. Active users: {len(self.user_usage)}")
    
    def get_all_stats(self) -> dict:
        """Get stats for all users (admin function)"""
        self.cleanup_all_users()
        
        stats = {}
        for user_id in self.user_usage:
            stats[user_id] = self.get_user_stats(user_id)
        
        return {
            "total_users": len(stats),
            "daily_limit": self.daily_limit,
            "users": stats
        }
