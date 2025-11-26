# Integration Tests

This directory contains integration tests that hit the real Qontak CRM API. These tests are **excluded from default pytest runs** and must be executed manually.

## ⚠️ Important Notes

- **These tests use real API calls** and will create actual resources in your Qontak CRM instance
- **Deals cannot be deleted** via API - they will remain in your CRM after tests complete
- **Tasks and Tickets are automatically cleaned up** after each test
- All test resources use the naming pattern: `INTEGRATION_TEST_{timestamp}_{uuid}`
- A JSON log file (`integration_test_resources.json`) is created after test completion

## 🚀 Setup

### 1. Install Dependencies

```bash
# Install with Redis support for token caching
pip install -e ".[dev,redis]"
```

### 2. Start Redis (for Token Caching)

Redis is used to cache access tokens so they don't need to be refreshed on every test run. Access tokens are valid for 6 hours and will only be refreshed when expired.

```bash
# Option 1: Using Docker
docker run -d -p 6379:6379 redis:alpine

# Option 2: Using Homebrew (macOS)
brew install redis
brew services start redis

# Option 3: Using apt (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 3. Configure Environment

**Option A: Using .env file (Recommended)**

The main `.env.example` file in the project root contains all configuration options:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and set your refresh token
# QONTAK_REFRESH_TOKEN=your_actual_refresh_token_here

# Optional: Customize Redis settings (defaults work for local development)
# REDIS_URL=redis://localhost:6379/0
# REDIS_KEY_PREFIX=qontak:test:tokens:
```

**Option B: Using environment variables**

```bash
export QONTAK_REFRESH_TOKEN=your_actual_refresh_token_here

# Optional Redis configuration (defaults work for local development)
# export REDIS_URL=redis://localhost:6379/0
# export REDIS_KEY_PREFIX=qontak:test:tokens:
```

### 4. Get Your Refresh Token

1. Sign in to your Qontak CRM account
2. Navigate to: **https://crm.qontak.com/crm/api_token/**
3. Create a new token or copy an existing refresh token
4. Add it to your `.env` file or export it as shown above

### How Token Caching Works

- **First run**: Uses refresh token to get access token, stores in Redis
- **Subsequent runs**: Reuses cached access token (valid for 6 hours)
- **After 6 hours**: Automatically refreshes access token using refresh token
- **Result**: Much faster test execution, fewer API calls to Qontak

## 🧪 Running Tests

### Run All Integration Tests

```bash
pytest -m integration_manual -v -s
```

The `-s` flag shows print statements for better visibility of test progress.

### Run Specific Test Modules

```bash
# Run only Deal tests
pytest tests/integration/test_deals_integration.py -m integration_manual -v -s

# Run only Task tests
pytest tests/integration/test_tasks_integration.py -m integration_manual -v -s

# Run only Ticket tests
pytest tests/integration/test_tickets_integration.py -m integration_manual -v -s

# Run end-to-end workflow tests
pytest tests/integration/test_end_to_end.py -m integration_manual -v -s
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/integration/test_deals_integration.py::TestDealCRUD -m integration_manual -v -s

# Run a specific test function
pytest tests/integration/test_tasks_integration.py::TestTaskCRUD::test_create_and_get_task -m integration_manual -v -s
```

## 📊 Test Coverage

### Deals (11 tools)
- ✅ `get_deal_template` - Get field template
- ✅ `get_required_fields_for_deal` - Get required fields for pipeline/stage
- ✅ `list_pipelines` - List deal pipelines
- ✅ `get_pipeline` - Get specific pipeline
- ✅ `list_pipeline_stages` - List stages for pipeline
- ✅ `list_deals` - List deals with pagination
- ✅ `get_deal` - Get specific deal
- ✅ `create_deal` - Create new deal
- ✅ `update_deal` - Update existing deal
- ✅ `get_deal_timeline` - Get deal activity timeline
- ✅ `get_deal_stage_history` - Get deal stage change history

### Tasks (9 tools)
- ✅ `get_task_template` - Get field template
- ✅ `get_required_fields_for_task` - Get required fields
- ✅ `list_task_categories` - List categories
- ✅ `create_task_category` - Create new category
- ✅ `delete_task_category` - Delete category
- ✅ `list_tasks` - List tasks with pagination
- ✅ `get_task` - Get specific task
- ✅ `create_task` - Create new task
- ✅ `update_task` - Update existing task
- ✅ `delete_task` - Delete task

### Tickets (9 tools)
- ✅ `get_ticket_template` - Get field template
- ✅ `get_required_fields_for_ticket` - Get required fields for pipeline
- ✅ `list_ticket_pipelines_and_stages` - List pipelines and stages
- ✅ `list_tickets` - List tickets with pagination
- ✅ `get_ticket` - Get specific ticket
- ✅ `create_ticket` - Create new ticket
- ✅ `update_ticket` - Update existing ticket
- ✅ `delete_ticket` - Delete ticket

### Special Features Tested
- ✅ Custom fields (array format for Tasks/Tickets, dict format for Deals)
- ✅ GPS/Location fields with lat/long coordinates
- ✅ Single ID associations (Tasks: `crm_deal_id`, Deals: `contact_id`)
- ✅ Array associations (Tickets: `crm_task_ids`, `crm_lead_ids`, `crm_product_ids`)
- ✅ Cross-module workflows (Deal → Task → Ticket)
- ✅ Field discovery and dynamic testing
- ✅ Retry logic with exponential backoff
- ✅ Resource tracking and cleanup

## 📄 Resource Logging

After tests complete, a comprehensive log is written to `integration_test_resources.json`:

```json
{
  "deals": [
    {
      "id": 12345,
      "name": "INTEGRATION_TEST_20251126_143022_a3b4c5d6",
      "test_function": "test_create_and_get_deal",
      "timestamp": "2025-11-26T14:30:22",
      "status": "created",
      "pipeline_id": 1,
      "stage_id": 2
    }
  ],
  "tasks": [
    {
      "id": 67890,
      "name": "INTEGRATION_TEST_TASK_20251126_143025_b5c6d7e8",
      "test_function": "test_create_and_get_task",
      "timestamp": "2025-11-26T14:30:25",
      "status": "deleted",
      "due_date": "2025-12-03"
    }
  ],
  "tickets": [...],
  "workflows": [...],
  "metadata": {
    "test_session_start": "2025-11-26T14:30:00",
    "test_session_end": "2025-11-26T14:35:00",
    "exit_status": 0,
    "total_resources_created": 15
  }
}
```

### Log Contents

- **deals**: All created deals (remain in CRM - no delete endpoint)
- **tasks**: Created tasks with deletion status
- **tickets**: Created tickets with deletion status
- **categories**: Created task categories with deletion status
- **workflows**: End-to-end workflow relationships
- **metadata**: Session information and statistics

## 🧹 Cleanup

### Automatic Cleanup
- ✅ **Tasks**: Automatically deleted after each test
- ✅ **Tickets**: Automatically deleted after each test
- ✅ **Categories**: Deleted when created for testing

### Manual Cleanup Required
- ⚠️ **Deals**: Cannot be deleted via API - must be cleaned up manually

### How to Clean Up Deals

1. Open the `integration_test_resources.json` file
2. Find all deals with `"status": "created"`
3. In Qontak CRM web interface:
   - Go to Deals section
   - Filter by name starting with `INTEGRATION_TEST_`
   - Manually delete unwanted deals

**Tip**: Use the naming pattern to quickly identify test data:
- Format: `INTEGRATION_TEST_{YYYYMMDD}_{HHMMSS}_{uuid}`
- Example: `INTEGRATION_TEST_20251126_143022_a3b4c5d6`

## 🔍 Troubleshooting

### Authentication Errors

```
Authentication error (fail fast): 401 Unauthorized
```

**Solution**: Check your `QONTAK_REFRESH_TOKEN` in `.env` file:
- Ensure it's a valid refresh token (not access token)
- Verify token hasn't expired
- Get a new token from https://crm.qontak.com/crm/api_token/

### Rate Limiting

```
⏳ Retryable error (attempt 1/3): 429 Too Many Requests
```

**Solution**: The tests include automatic retry with exponential backoff. Wait for retries to complete.

If rate limiting persists:
- Run fewer tests at once
- Add delays between test runs
- Check your API rate limits in Qontak CRM settings

### No Pipelines/Stages Found

```
AssertionError: No pipelines available
```

**Solution**: Your Qontak CRM account needs at least:
- One deal pipeline with stages
- One ticket pipeline with stages
- Verify in the CRM web interface under Settings

### Missing Custom Fields

Some tests will skip if custom fields aren't available:

```
⚠️  No GPS location field found in task template - skipping
```

This is normal - not all CRM instances have all field types configured.

## 📚 Related Documentation

- **[FIELD_LIMITATIONS.md](../../FIELD_LIMITATIONS.md)**: Field type limitations and special handling
- **[README.md](../../README.md)**: Main project documentation
- **[CONTRIBUTING.md](../../CONTRIBUTING.md)**: Development guidelines

## 🛡️ Security Notes

- Never commit `.env` file with real tokens
- Tokens in `.env.example` are placeholders only
- Use environment-specific tokens (dev/staging, not production)
- Rotate tokens regularly
- Review `integration_test_resources.json` before committing (contains resource IDs)

## 💡 Best Practices

1. **Run tests in a test/staging environment** - not production
2. **Review created resources** - check `integration_test_resources.json` after tests
3. **Clean up regularly** - manually delete test deals periodically
4. **Monitor API usage** - integration tests count toward rate limits
5. **Keep tokens secure** - never share or commit real tokens

## 🆘 Getting Help

If you encounter issues:

1. Check this README for troubleshooting steps
2. Review test output and error messages
3. Check `integration_test_resources.json` for resource details
4. Open an issue on GitHub with:
   - Test command used
   - Error message and stack trace
   - Relevant portions of `integration_test_resources.json` (remove sensitive IDs)

---

**Happy Testing! 🚀**
