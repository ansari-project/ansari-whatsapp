# Observability with Sentry in ansari-whatsapp

This document explains how we use Sentry for error tracking and performance monitoring in the ansari-whatsapp service.

---

## What is Observability?

Observability is the ability to understand what's happening inside your application by examining its outputs. For production services, this typically includes:

- **Error Tracking**: Capturing and analyzing exceptions that occur in production
- **Performance Monitoring**: Measuring response times, API calls, and identifying bottlenecks
- **Context Correlation**: Linking errors to specific requests and users for easier debugging

In ansari-whatsapp, we use Sentry to capture errors with contextual information that helps us quickly diagnose and fix issues in production.

---

## Our Error Categorization Strategy

We categorize errors using Sentry tags to make them easy to filter and analyze. Every captured error includes an `error_type` tag that indicates which component failed.

### The Four Error Types

**1. webhook_processing_failure**
- **What it means**: Error occurred while parsing or validating the incoming WhatsApp webhook from Meta
- **Where it's captured**: `app/main.py` - webhook endpoint
- **Common causes**: Malformed JSON payload, unexpected webhook structure, signature verification issues
- **Example scenario**: Meta sends a webhook with a new field structure we haven't seen before

**2. backend_timeout**
- **What it means**: The ansari-backend service took too long to respond (timeout exceeded)
- **Where it's captured**: `services/whatsapp_conversation_manager.py` - message processing
- **Common causes**: Backend overload, slow AI model response, database query taking too long
- **Example scenario**: User sends a complex question that takes 30+ seconds to generate a response

**3. message_processing_failure**
- **What it means**: Error occurred while processing the user's message (excluding timeouts)
- **Where it's captured**: `services/whatsapp_conversation_manager.py` - message processing
- **Common causes**: Network errors, invalid backend API response, unexpected exceptions
- **Example scenario**: Backend returns a 500 error due to an internal bug

**4. meta_api_failure**
- **What it means**: Meta's WhatsApp API returned a 5xx server error
- **Where it's captured**: `services/meta_api_service_real.py` - Meta API calls
- **Common causes**: Meta service outage, API rate limiting, temporary infrastructure issues
- **Example scenario**: Meta's API is experiencing downtime and returns 503 Service Unavailable

---

## Why These Categories?

This categorization allows us to quickly identify:
- **Which component is failing**: Webhook parsing vs backend communication vs Meta API
- **Who's responsible**: Our code vs backend service vs Meta's infrastructure
- **Severity and urgency**: Timeouts might need infrastructure scaling, while webhook failures might indicate breaking API changes

---

## How to Use Sentry UI

### Filtering by Error Type

When you visit the Sentry dashboard for ansari-whatsapp:

1. Navigate to **Issues** tab
2. Click on the **Filter** dropdown
3. Select **Tags** → **error_type**
4. Choose one of the four error types

Example: Filtering by `error_type:backend_timeout` shows all instances where the backend didn't respond in time.

### Understanding Error Patterns

**Scenario: High Volume of One Error Type**

If you see many `backend_timeout` errors:
- **Insight**: The backend service is likely overloaded or experiencing performance issues
- **Action**: Check backend infrastructure, scale up resources, or investigate slow queries

If you see many `meta_api_failure` errors:
- **Insight**: Meta's infrastructure is having issues (not our fault)
- **Action**: Check Meta's status page, wait for their service to recover

**Scenario: Isolated Errors**

If you see occasional `message_processing_failure` errors:
- **Insight**: Specific edge cases or rare bugs in our code
- **Action**: Review the stacktrace and context to identify the root cause

### Reading Error Context

Each captured error includes:
- **request_id**: Unique identifier for the HTTP request (useful for correlating with CloudWatch logs)
- **user_id**: Database UUID of the WhatsApp user (allows tracking errors for specific users)
- **Stacktrace**: Full call stack showing exactly where the error occurred
- **Additional context**: API status codes, endpoint names, timestamps

Example: You see a `meta_api_failure` error with context:
```
status_code: 503
endpoint: send_message
request_id: abc-123-def-456
```

This tells you:
- Meta's API returned 503 (Service Unavailable)
- The failure happened while trying to send a message
- You can search CloudWatch logs for `request_id=abc-123-def-456` to see the full request timeline

---

## Privacy and Security

We never capture phone numbers directly in Sentry. All error tracking follows these principles:

- **No PII**: `send_default_pii=False` ensures no personal data (IP addresses, phone numbers) is sent
- **request_id and user_id only**: We use internal identifiers for correlation, not phone numbers
- **Masked data**: When debugging context requires phone information, we mask it (e.g., `+1234***`)

---

## Sampling for Cost Control

In production, we only capture 20% of performance traces to reduce costs:

```python
traces_sample_rate=0.2  # Production: 20% of transactions traced
profiles_sample_rate=0.2  # Production: 20% of profiled transactions
```

In staging, we capture 100% for full visibility during testing:

```python
traces_sample_rate=1.0  # Staging: 100% of transactions traced
profiles_sample_rate=1.0  # Staging: 100% of profiled transactions
```

This means:
- **Errors are always captured** (100% of exceptions are sent)
- **Performance traces are sampled** (only a subset is sent to reduce volume)

---

## When Errors Are Not Captured

Some errors are intentionally filtered out using the `before_send` function:

- `HTTP exception: 401` - Authentication failures (expected, noisy)
- `HTTP exception: 403` - Permission errors (expected, noisy)

These are logged normally but not sent to Sentry because they're expected operational events, not bugs.

---

## Relationship with CloudWatch Logs

Sentry and CloudWatch serve different but complementary purposes:

**CloudWatch Logs:**
- Store ALL logs (debug, info, warning, error)
- Queryable by `request_id` and `user_id`
- Show the complete timeline of a request
- Used for tracing and debugging

**Sentry:**
- Captures ONLY errors and performance data
- Groups similar errors together
- Provides stacktraces and alerting
- Used for error tracking and monitoring

**How they work together:**
1. Sentry captures an error with `request_id: abc-123`
2. You view the error in Sentry dashboard
3. You copy the `request_id` and search CloudWatch logs:
   ```sql
   fields @timestamp, level, text
   | filter request_id = "abc-123"
   | sort @timestamp asc
   ```
4. CloudWatch shows the full request timeline (what happened before/after the error)

---

## Summary

Observability in ansari-whatsapp is built on:
- **Four error type tags** for easy categorization
- **Context-rich error captures** with request_id and user_id
- **Privacy-safe tracking** (no phone numbers or PII)
- **Cost-optimized sampling** (20% in production, 100% in staging)
- **Integration with CloudWatch** for full request tracing

When investigating production issues:
1. Start with Sentry to identify error patterns and filter by type
2. Use request_id to correlate with CloudWatch logs for detailed timeline
3. Analyze context (status codes, endpoints) to determine root cause
4. Take action based on which component is failing
