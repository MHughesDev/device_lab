# skills/backend/service-repository-pattern.md

<!-- CROSS-REFERENCES -->
<!-- - Related rules: .cursor/rules/apps-api.md, PYTHON_PROCEDURES.md §6 -->
<!-- - Related procedure: docs/procedures/scaffold-domain-module.md -->

**Purpose:** [FULL SKILL] How to implement service and repository layers correctly: separation of concerns, transaction boundaries, interface contracts. Per spec §26.4 item 56.

## Purpose

One paragraph. The service/repository pattern is the primary architectural boundary in this codebase. Services contain business rules; repositories contain persistence logic. Violations (queries in services, business logic in repositories, or both in routers) create untestable, brittle code. This skill makes the boundaries concrete and testable.

## When to Invoke

- When implementing any new business operation
- When a router function is growing with business logic
- When a service function starts containing SQL queries
- When writing tests and needing to mock dependencies

## Prerequisites

PYTHON_PROCEDURES.md §6 (Domain Separation), §4 (Dependency Injection), §14 (Persistence) all read.

## Relevant Files/Areas

- `apps/api/app/<module>/service.py` — business logic layer
- `apps/api/app/<module>/router.py` — transport layer (thin)
- `apps/api/app/<module>/models.py` — persistence layer definitions
- `apps/api/app/database.py` — session management

## Step-by-Step Method

Numbered steps:
1. **Router** (transport layer): receives request, calls service, returns response. No logic.
   ```python
   @router.post("/invoices", response_model=InvoiceResponse)
   async def create_invoice(
       body: CreateInvoiceRequest,
       service: InvoiceService = Depends(get_invoice_service),
       current_user: User = Depends(get_current_user),
   ) -> InvoiceResponse:
       return await service.create_invoice(body, user_id=current_user.id)
   ```
2. **Service** (business layer): validates business rules, orchestrates, owns transactions.
   ```python
   class InvoiceService:
       def __init__(self, session: AsyncSession) -> None:
           self._session = session

       async def create_invoice(self, data: CreateInvoiceRequest, user_id: UUID) -> InvoiceResponse:
           # Business rule: user must have active account
           # Business rule: amount must be positive
           # Call repository for persistence
           async with self._session.begin():
               invoice = await self._create_invoice_record(data, user_id)
           return InvoiceResponse.model_validate(invoice)
   ```
3. **Repository** (persistence layer — if separate): builds queries, returns domain objects.
   ```python
   async def get_invoice_by_id(session: AsyncSession, invoice_id: UUID, tenant_id: UUID) -> Invoice | None:
       result = await session.execute(
           select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
       )
       return result.scalar_one_or_none()
   ```
4. **Dependency injection**: wire service in dependencies.py
   ```python
   def get_invoice_service(session: AsyncSession = Depends(get_db)) -> InvoiceService:
       return InvoiceService(session=session)
   ```

## Command Examples

`make typecheck` (verify DI wiring), `make test` (verify layer isolation via mocks)

## Validation Checklist

- [ ] Router has no business logic (no if/else on domain state)
- [ ] Service has no raw SQL (uses repository functions or ORM queries only)
- [ ] Transactions managed in service layer (`async with session.begin()`)
- [ ] Repository returns domain objects, not raw rows
- [ ] Service is unit testable with mocked session/repository

## Common Failure Modes

- **Logic in router**: router has `if invoice.status == "paid": raise ...` → untestable via unit test. Fix: move to service.
- **Query in service**: service has `await session.execute(select(Invoice).where(...))` directly → service is tied to DB schema. Fix: move to repository function.
- **Transaction in repository**: repository commits → service loses control of transaction boundary. Fix: always commit in service, never in repository.

## Handoff Expectations

Layer separation verified, tests cover service logic in isolation, transaction boundaries documented.

## Related Procedures

docs/procedures/scaffold-domain-module.md

## Related Prompts

prompts/implementation_agent.md

## Related Rules

.cursor/rules/apps-api.md (dependency injection rules), PYTHON_PROCEDURES.md §6 and §14
