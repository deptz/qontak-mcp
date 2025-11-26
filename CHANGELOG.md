# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-26

### Added

- **Initial open source release** of Qontak MCP Server
- **Deals Tools** (8 tools):
  - `get_deal_template`: Get deal field definitions and schema
  - `get_required_fields_for_deal`: **Dynamically discover required fields** for specific pipeline/stage combinations
  - `list_deals`: List deals with filtering and pagination
  - `get_deal`: Get single deal details by ID
  - `create_deal`: Create new deals with dynamic required field support
  - `update_deal`: Update existing deals
  - `get_deal_timeline`: View deal activity timeline
  - `get_deal_stage_history`: Track stage changes with history
- **Tickets Tools** (7 tools):
  - `get_ticket_template`: Get ticket field definitions and schema
  - `get_required_fields_for_ticket`: **Dynamically discover required fields** for specific pipelines
  - `list_tickets`: List tickets with filtering and pagination
  - `get_ticket`: Get single ticket details by ID
  - `create_ticket`: Create new tickets with dynamic required field support
  - `update_ticket`: Update existing tickets
  - `get_ticket_pipelines`: View available pipelines and stages
- **Tasks Tools** (8 tools):
  - `get_task_template`: Get task field definitions and schema
  - `get_required_fields_for_task`: **Dynamically discover required fields** with proper categorization (required vs optional)
  - `list_tasks`: List tasks with filtering and pagination
  - `get_task`: Get single task details by ID
  - `create_task`: Create new tasks with support for commonly required fields (`crm_task_status_id`, `detail`, `next_step`)
  - `update_task`: Update existing tasks
  - `list_task_categories`: View available task categories
  - `create_task_category`: Create new task categories
- **Token Storage Backends**:
  - `env`: In-memory storage for local development
  - `redis`: Redis-based storage for dev/staging
  - `vault`: HashiCorp Vault storage for production
- **Dynamic Field Discovery**:
  - **Zero hardcoded field values** - all required fields discovered at runtime from API templates
  - Automatic detection of required vs optional fields for each resource type
  - Pipeline and stage-specific requirements for deals and tickets
  - Proper categorization of standard fields vs custom fields
- **Security Features**:
  - Rate limiting with token bucket algorithm (per-user and global limits)
  - Structured security logging with sensitive data redaction
  - Comprehensive input validation using Pydantic models
  - Multi-tenant support via optional user_id parameter
- **Comprehensive Testing**:
  - 437+ unit tests covering all functionality
  - 34 integration tests with full API validation
  - 100% dynamic field discovery verified in tests
