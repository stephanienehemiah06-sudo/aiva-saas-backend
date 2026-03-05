# Booking Integration Contract (AI + Manual Calendar)

## Goal
Prevent double-bookings when two channels attempt the same slot:
- AI chat booking flow
- Manual website calendar flow

Both must use the same server-side booking rules.

## Single Source of Truth
- Final booking write must go through one backend path (`POST /bookings/create`) or a shared booking service function.
- Frontend checks are advisory only.
- Server decides availability at booking time.

## Slot Identity
A slot is uniquely identified by:
- `technician_id`
- `date` (ISO)
- `start_time` (HH:mm)
- `timezone` (IANA, e.g. `Africa/Lagos`)

If duration varies by service, backend must block overlapping intervals, not just exact start times.

## Required Fields (Create Booking)
```json
{
  "technician_id": 12,
  "service_id": 4,
  "client_name": "Jane Doe",
  "client_phone": "+2348012345678",
  "client_email": "jane@example.com",
  "date": "2026-03-01",
  "time": "14:00",
  "timezone": "Africa/Lagos",
  "source": "ai"
}
```

`source` values:
- `ai`
- `website`

## Conflict/Locking Rules
- Backend must perform atomic check-and-create.
- Use DB-level protection (unique index or transaction lock strategy).
- Treat these statuses as slot-blocking (agree explicitly):
  - Recommended: `pending`, `payment_sent`, `confirmed`, `paid`
- Optional hold policy:
  - if `pending`, expire after X minutes if unpaid.

## Standard Error Contract
When slot is taken, return:
- HTTP `409`
- body:
```json
{
  "code": "SLOT_UNAVAILABLE",
  "message": "This time slot is no longer available",
  "next_available": ["14:30", "15:00", "15:30"]
}
```

## Availability Endpoint Contract
Calendar + AI should read from same endpoint:
- `GET /availability/slots?technician_id=12&date=2026-03-01&timezone=Africa/Lagos`

Response should return only currently bookable slots.

## AI Behavior Requirements
If booking create returns conflict (`409 SLOT_UNAVAILABLE`):
1. Tell client slot was just taken.
2. Offer `next_available` alternatives.
3. Ask client to choose one.
4. Retry booking with new selected slot.

## Manual Calendar Behavior Requirements
- Disable unavailable slots from `GET /availability/slots`.
- On submit, still handle `409 SLOT_UNAVAILABLE` (race condition-safe).
- Show user friendly message and refresh available slots.

## Idempotency
- Support `Idempotency-Key` header for retries.
- Same key + payload should not create duplicates.

## Observability (Recommended)
Log per booking attempt:
- `request_id`
- `source` (`ai`/`website`)
- `technician_id`
- slot tuple
- result (`created`/`conflict`)

## Ready-to-Implement Checklist
- [ ] Shared backend booking create logic
- [ ] Shared availability endpoint used by both channels
- [ ] Conflict response standardized to `409 SLOT_UNAVAILABLE`
- [ ] DB-level uniqueness/locking enabled
- [ ] `source` persisted and visible in dashboard
- [ ] AI fallback reply for conflicts implemented
- [ ] Manual calendar conflict fallback implemented
