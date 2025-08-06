# Rate Limiting Configuration

## Environment Variables

Add these to your `.env` file to configure Nancy's rate limiting:

```bash
# Daily rate limiting (default: 100 queries per user per day)
DAILY_RATE_LIMIT=100

# Set to a lower number for testing or cost control
# DAILY_RATE_LIMIT=50

# Set to 0 to disable rate limiting (not recommended for production)
# DAILY_RATE_LIMIT=0
```

## How it Works

- **In-Memory Storage**: Rate limits are stored in memory, reset on bot restart
- **Per-User Tracking**: Each Slack user has their own daily quota
- **UTC Day Boundary**: Quotas reset at midnight UTC
- **Automatic Cleanup**: Old entries are automatically removed
- **Admin Override**: Restart the bot to reset all quotas

## Rate Limit Behavior

1. **Normal Usage**: Users see no changes until they approach their limit
2. **Warning at 90%**: Users get a warning when they have 10% remaining
3. **Quota Exceeded**: Users see a friendly message explaining the limit
4. **Keep Cooking**: Also counts against the user's quota
5. **Grace Period**: No rate limiting during the first turn (conversation start)

## User Experience

**When quota is exceeded:**
```
🚫 Daily Limit Reached

You've used your 100 daily Nancy interactions. Your quota resets at midnight UTC.

Need more access? Contact your administrator or try again tomorrow!
```

**When quota is low (≤10 remaining):**
User sees normal response, but logs show a warning for admin monitoring.

## Admin Monitoring

Rate limit events are logged with INFO and WARNING levels:
- `✅ User rate limit check passed: 45/100 used`
- `⚠️ User has 5 queries remaining today`
- `🚫 Rate limit exceeded for user: 100/100`

## Testing

Use the test script to verify rate limiting:
```bash
python test_rate_limiter.py
```

## Production Recommendations

- **Start Conservative**: Begin with 50-100 queries per day
- **Monitor Usage**: Watch logs for patterns and adjust as needed
- **User Communication**: Inform users about the limits upfront
- **Admin Contact**: Provide clear escalation path for limit increases
