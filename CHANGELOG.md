# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-11-30

### Added

- **Contact Tools** (10 tools):
  - `get_contact_template`: Get contact field definitions and schema
  - `get_required_fields_for_contact`: Dynamically discover required fields for contacts
  - `list_contacts`: List contacts with pagination
  - `get_contact`: Get single contact details by ID
  - `create_contact`: Create new contacts with dynamic field support
  - `update_contact`: Update existing contacts
  - `delete_contact`: Delete contacts by ID
  - `get_contact_timeline`: View contact activity timeline
  - `get_contact_chat_history`: Retrieve chat history for contacts
  - `update_contact_owner`: Change contact ownership

- **Company Tools** (8 tools):
  - `get_company_template`: Get company field definitions and schema
  - `get_required_fields_for_company`: Dynamically discover required fields for companies
  - `list_companies`: List companies with pagination
  - `get_company`: Get single company details by ID
  - `create_company`: Create new companies with dynamic field support
  - `update_company`: Update existing companies
  - `delete_company`: Delete companies by ID
  - `get_company_timeline`: View company activity timeline

- **Note Tools** (5 tools):
  - `list_notes`: List notes with filtering by contact/company/deal
  - `get_note`: Get single note details by ID
  - `create_note`: Create notes associated with contacts, companies, or deals
  - `update_note`: Update existing notes
  - `delete_note`: Delete notes by ID

- **Product Tools** (5 tools):
  - `list_products`: List products with pagination
  - `get_product`: Get single product details by ID
  - `create_product`: Create new products with pricing and SKU
  - `update_product`: Update existing products
  - `delete_product`: Delete products by ID

- **Products Association Tools** (5 tools):
  - `list_products_associations`: List product associations with pagination
  - `get_products_association`: Get single product association details by ID
  - `create_products_association`: Link products to deals, contacts, or companies
  - `update_products_association`: Update existing product associations
  - `delete_products_association`: Delete product associations by ID

- **Deal Extensions** (5 tools):
  - `get_deal_chat_history`: Retrieve chat history for deals
  - `get_deal_real_creator`: Get original creator of a deal
  - `get_deal_full_field`: Get deal with complete field information
  - `get_deal_permissions`: Check user permissions for deals
  - `update_deal_owner`: Change deal ownership

### Enhanced

- **API Coverage**: Expanded from 23 tools to 61 tools (165% increase)
- **Category Coverage**: Added 5 new categories (Contacts, Companies, Notes, Products, Products Association)
- **Complete Deal Support**: Added 5 missing deal tools for 100% deal API coverage
- **Client Methods**: Added 50+ new QontakClient methods for all new endpoints
- **Pydantic Models**: Added comprehensive validation models for all new tools
- **Test Coverage**: Created 10 new test files with 50+ unit and integration tests

### Summary

- **Total Tools**: 61 (up from 23)
- **Total Categories**: 8 (Contacts, Companies, Deals, Tasks, Tickets, Notes, Products, Products Association)
- **API Coverage**: 95% of available Qontak CRM API endpoints (67/70 endpoints)
- **New Tools**: 38
- **Test Files**: 15 total (10 unit test files, 5 integration test files)

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
