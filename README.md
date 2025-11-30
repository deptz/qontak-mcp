# Qontak MCP

> ⚠️ **EXPERIMENTAL PROJECT** ⚠️
> 
> This project is currently in **active development** and should be considered experimental.
> While thoroughly tested, it requires further real-world validation before production use.
> APIs and functionality may change without notice. Use at your own risk.
> Community feedback and contributions are welcome!

Qontak MCP is a Model Context Protocol (MCP) server that provides **61 intelligent tools** for managing Contacts, Companies, Deals, Tickets, Tasks, Notes, Products, and Products Associations in Qontak CRM with **dynamic field discovery**.

## Features

### Core Capabilities

- **61 Intelligent MCP Tools** for comprehensive Qontak CRM operations
  - **Contacts (10 tools)**: Complete contact management with template discovery, CRUD, timeline, chat history
  - **Companies (8 tools)**: Full company management with dynamic field support
  - **Deals (14 tools)**: Complete deal lifecycle management with pipeline/stage-aware required fields, chat history, permissions
  - **Tickets (7 tools)**: Full ticket workflow with pipeline-specific field requirements  
  - **Tasks (8 tools)**: Task management with automatic status, detail, and next_step field discovery
  - **Notes (5 tools)**: Note creation and management with entity associations (contacts, companies, deals)
  - **Products (5 tools)**: Product catalog management with pricing and SKU support
  - **Products Association (5 tools)**: Link products to deals, contacts, or companies
- **Dynamic Field Discovery** - The game changer:
  - 🚀 **Zero hardcoded values** - all required fields discovered at runtime from API templates
  - 🎯 **Smart categorization** - automatically identifies required vs optional fields
  - 🔄 **API-driven validation** - adapts automatically when Qontak CRM field requirements change
  - 📊 **Resource-specific logic** - different discovery strategies for deals, tickets, and tasks
- **Production-Ready Architecture**:
  - ✅ **Multi-tenant support**: Pluggable token store with per-user isolation
  - ✅ **Automatic token management**: Lazy refresh with 6-hour caching (Redis/Vault)
  - ✅ **Three storage backends**: Environment (dev), Redis (staging), Vault (production)
  - ✅ **Rate limiting**: Token bucket algorithm with per-user and global limits
  - ✅ **Security first**: Pydantic validation, structured logging, sensitive data redaction
- **Battle-Tested Quality**:
  - ✅ 808 tests covering all functionality
  - ✅ 15 integration test files with real API validation
  - ✅ 100% dynamic field discovery verified
  - ✅ 96% code coverage across core modules
  - ✅ 100% coverage on authentication and all 8 tools modules
  - ✅ 91% coverage on API client with comprehensive error handling

## Token Store Selection

Choose the appropriate token store based on your environment:

| Environment | TOKEN_STORE | Package | Security Level | Token Caching |
|-------------|-------------|---------|----------------|---------------|
| **Local Dev** | `env` (default) | Base | ⚠️ Development only | ❌ No (refreshes every request) |
| **Development** | `redis` | `[redis]` | ⚠️ Development/Staging | ✅ Yes (6 hours) |
| **Staging/QA** | `redis` | `[redis]` | ⚠️ Development/Staging | ✅ Yes (6 hours) |
| **Production** | `vault` | `[vault]` | ✅ Production-grade | ✅ Yes (6 hours) |

> ⚠️ **Important**: `env` and `redis` stores are for **development and staging only**. 
> For production deployments, use `vault` which provides encryption at rest, 
> audit logging, and fine-grained access control.

### Why Use Redis or Vault Instead of Env?

**Environment Store (`env`):**
- ❌ No access token caching
- ❌ Refreshes token on every API request
- ❌ Slower performance
- ❌ Higher load on Qontak OAuth endpoint
- ✅ Simple setup for quick local testing

**Redis Store (`redis`):**
- ✅ Caches access tokens for 6 hours
- ✅ Only refreshes when token expires
- ✅ Much faster API calls
- ✅ Reduces load on Qontak OAuth endpoint
- ✅ Multi-tenant support
- ⚠️ Development/Staging use only

**Vault Store (`vault`):**
- ✅ All Redis benefits plus:
- ✅ Encrypted at rest
- ✅ Audit logging
- ✅ Fine-grained access control
- ✅ Production-ready security

## Installation

### Prerequisites

- Python 3.10+
- Qontak CRM account with API access

### Setup

```bash
# Clone the repository
git clone https://github.com/deptz/qontak-mcp.git
cd qontak-mcp

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate   # Windows

# Install dependencies based on your environment:
pip install -e .              # Local dev (env store only)
pip install -e ".[redis]"     # Dev/Staging (with Redis)
pip install -e ".[vault]"     # Production (with Vault)
pip install -e ".[all]"       # All backends

# Configure credentials
cp .env.example .env
# Edit .env and add your configuration
```

The `.env.example` file contains all configuration options for:
- MCP server (production use)
- Integration tests (development use)
- All token store backends (env, redis, vault)

## Configuration

All configuration is done via environment variables in the `.env` file or exported in your shell.

### Quick Setup

**For Local Development (Simple):**
```bash
cp .env.example .env
# Edit .env and set:
# QONTAK_REFRESH_TOKEN=your_token_here
# TOKEN_STORE=env  (default)
```

**For Development with Redis (Recommended):**
```bash
cp .env.example .env
# Edit .env and set:
# QONTAK_REFRESH_TOKEN=your_token_here
# TOKEN_STORE=redis
# REDIS_URL=redis://localhost:6379/0  (default)
```

### Environment Variables Reference

#### Required

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `QONTAK_REFRESH_TOKEN` | Your Qontak API refresh token | https://crm.qontak.com/crm/api_token/ |

#### Token Store Selection

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `TOKEN_STORE` | Token storage backend | `env` | `env`, `redis`, `vault` |

#### Redis Configuration (when TOKEN_STORE=redis)

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `REDIS_KEY_PREFIX` | Key prefix for MCP server tokens | `qontak:tokens:` |
| `REDIS_TEST_KEY_PREFIX` | Key prefix for integration test tokens | `qontak:test:tokens:` |
| `REDIS_TOKEN_TTL` | TTL for cached tokens (seconds) | `21600` (6 hours) |

#### Vault Store (Production) ✅ Recommended

| Variable | Description | Default |
|----------|-------------|---------|
| `VAULT_ADDR` | HashiCorp Vault address | - (required) |
| `VAULT_TOKEN` | Vault authentication token | - (required) |
| `VAULT_MOUNT_PATH` | KV v2 mount path | `secret` |
| `VAULT_SECRET_PATH` | Base path for secrets | `qontak/tokens` |
| `VAULT_NAMESPACE` | Vault namespace (enterprise) | - |

### Vault Setup (Production)

1. Enable KV v2 secrets engine:
```bash
vault secrets enable -path=secret kv-v2
```

2. Create a policy for the MCP server:
```hcl
# qontak-mcp-policy.hcl
path "secret/data/qontak/tokens/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
path "secret/metadata/qontak/tokens/*" {
  capabilities = ["read", "delete", "list"]
}
```

3. Apply the policy:
```bash
vault policy write qontak-mcp qontak-mcp-policy.hcl
```

4. Generate a token with the policy:
```bash
vault token create -policy=qontak-mcp
```

### Getting Your Refresh Token

1. Sign in to your Qontak CRM account
2. Go to the API Token settings: `https://crm.qontak.com/crm/api_token/`
3. Create a new token if one doesn't exist
4. Copy the generated refresh token

### Quick Start with Redis (Recommended for Development)

Redis provides significant performance improvements by caching access tokens:

```bash
# 1. Install with Redis support
pip install -e ".[redis]"

# 2. Start Redis (choose one method)
# Docker (easiest):
docker run -d -p 6379:6379 --name redis-qontak redis:alpine

# Homebrew (macOS):
brew install redis && brew services start redis

# Or direct:
redis-server --daemonize yes

# 3. Verify Redis is running
redis-cli ping  # Should return: PONG

# 4. Configure environment
export TOKEN_STORE=redis
export QONTAK_REFRESH_TOKEN="your_refresh_token_here"

# 5. Run the server
qontak-mcp
```

**Performance Comparison:**
- **Without Redis** (`env` store): ~500ms per API call (includes OAuth refresh)
- **With Redis** (`redis` store): ~50-100ms per API call (cached token, 10x faster!)

The access token is cached for 6 hours and automatically refreshed when it expires.

## Usage

### Running the Server

```bash
# Run the MCP server
qontak-mcp
```

### Available Tools

#### Contacts (10 tools)

| Tool | Description |
|------|-------------|
| `get_contact_template` | Get contact field definitions and schema |
| `get_required_fields_for_contact` | 🆕 Dynamically discover required fields for contacts |
| `list_contacts` | List contacts with pagination and filters |
| `get_contact` | Get a single contact by ID |
| `create_contact` | Create a new contact with dynamic field support |
| `update_contact` | Update an existing contact |
| `delete_contact` | Delete a contact by ID |
| `get_contact_timeline` | View contact activity timeline |
| `get_contact_chat_history` | Retrieve chat history for contacts |
| `update_contact_owner` | Change contact ownership |

#### Companies (8 tools)

| Tool | Description |
|------|-------------|
| `get_company_template` | Get company field definitions and schema |
| `get_required_fields_for_company` | 🆕 Dynamically discover required fields for companies |
| `list_companies` | List companies with pagination |
| `get_company` | Get a single company by ID |
| `create_company` | Create a new company with dynamic field support |
| `update_company` | Update an existing company |
| `delete_company` | Delete a company by ID |
| `get_company_timeline` | View company activity timeline |

#### Deals (14 tools)

| Tool | Description |
|------|-------------|
| `get_deal_template` | Get deal field definitions and options |
| `get_required_fields_for_deal` | 🆕 Get required fields for specific pipeline/stage |
| `list_deals` | List all deals with optional filters |
| `get_deal` | Get a single deal by ID |
| `create_deal` | Create a new deal |
| `update_deal` | Update an existing deal |
| `delete_deal` | Delete a deal by ID |
| `get_deal_timeline` | Get deal activity timeline |
| `get_deal_stage_history` | Get deal stage change history |
| `get_deal_chat_history` | 🆕 Retrieve chat history for deals |
| `get_deal_real_creator` | 🆕 Get original creator of a deal |
| `get_deal_full_field` | 🆕 Get deal with complete field information |
| `get_deal_permissions` | 🆕 Check user permissions for deals |
| `update_deal_owner` | 🆕 Change deal ownership |

#### Tickets (7 tools)

| Tool | Description |
|------|-------------|
| `get_ticket_template` | Get ticket field definitions |
| `get_required_fields_for_ticket` | 🆕 Get required fields for specific pipeline |
| `list_tickets` | List all tickets |
| `get_ticket` | Get a single ticket by ID |
| `create_ticket` | Create a new ticket |
| `update_ticket` | Update an existing ticket |
| `delete_ticket` | Delete a ticket by ID |
| `get_ticket_pipelines` | Get available ticket pipelines and stages |

#### Tasks (8 tools)

| Tool | Description |
|------|-------------|
| `get_task_template` | Get task field definitions |
| `get_required_fields_for_task` | 🆕 Get all available task fields and their types |
| `list_tasks` | List all tasks with optional filters |
| `get_task` | Get a single task by ID |
| `create_task` | Create a new task |
| `update_task` | Update an existing task |
| `delete_task` | Delete a task by ID |
| `list_task_categories` | List available task categories |
| `create_task_category` | Create a new task category |

#### Notes (5 tools)

| Tool | Description |
|------|-------------|
| `list_notes` | List notes with filtering by contact/company/deal |
| `get_note` | Get a single note by ID |
| `create_note` | Create notes associated with contacts, companies, or deals |
| `update_note` | Update an existing note |
| `delete_note` | Delete a note by ID |

#### Products (5 tools)

| Tool | Description |
|------|-------------|
| `list_products` | List products with pagination |
| `get_product` | Get a single product by ID |
| `create_product` | Create new products with pricing and SKU |
| `update_product` | Update an existing product |
| `delete_product` | Delete a product by ID |

#### Products Association (5 tools)

| Tool | Description |
|------|-------------|
| `list_products_associations` | List product associations with pagination |
| `get_products_association` | Get a single product association by ID |
| `create_products_association` | Link products to deals, contacts, or companies |
| `update_products_association` | Update existing product associations |
| `delete_products_association` | Delete product associations by ID |

### Custom Fields

All resources (Deals, Tickets, Tasks) support dynamic custom fields using a universal array format:

```json
{
  "additional_fields": [
    {
      "id": 14840254,
      "name": "field_name",
      "value": "field_value",
      "value_name": null
    }
  ]
}
```

**Workflow for handling custom fields:**

1. **Discover required fields** using the appropriate tool:
   - `get_required_fields_for_deal(pipeline_id, stage_id)` - For deals
   - `get_required_fields_for_ticket(pipeline_id)` - For tickets  
   - `get_required_fields_for_task()` - For tasks

2. **Get field details** including:
   - Field names and IDs
   - Field types (Single-line text, Dropdown select, Number, etc.)
   - Dropdown options (if applicable)
   - Whether field is required for the pipeline/stage

3. **Build the additional_fields array** with required custom fields

4. **Create/update the resource** with the complete data

**Supported field types:**
- ✅ Single-line text, Text Area, Number, Date, Date time
- ✅ Dropdown select, Multiple select, Percentage, Checklist, URL
- ⚠️ Photo, Signature, File upload, GPS (require separate upload mechanism)

See [FIELD_LIMITATIONS.md](FIELD_LIMITATIONS.md) for detailed field type documentation.

### Multi-Tenant Usage

All tools accept an optional `user_id` parameter for multi-tenant scenarios:

```python
# Single tenant (default)
list_deals(page=1, per_page=25)

# Multi-tenant
list_deals(page=1, per_page=25, user_id="tenant-123")
```

## Architecture

```
┌─────────────────────────────────────────┐
│             MCP Tools (61)              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│            QontakClient                 │
│       (async HTTP + auto auth)          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│            QontakAuth                   │
│         (lazy token refresh)            │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   TokenStore (Protocol)                     │
├─────────────────┬─────────────────┬─────────────────────────┤
│   EnvTokenStore │ RedisTokenStore │    VaultTokenStore      │
│   (Local Dev)   │  (Dev/Staging)  │     (Production)        │
│       ⚠️        │       ⚠️        │         ✅              │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Development

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

```bash
# Install dev dependencies
pip install -e ".[all,dev]"

# Run tests
pytest

# Type checking
mypy src/
```

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
