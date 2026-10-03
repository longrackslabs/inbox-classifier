# eBay Auto-Ship: Design Doc

## Problem

When a nozzle sells on eBay, George manually checks for the sale, prints a packing list, buys a USPS label through eBay's UI, and prints it. This is a candidate for automation.

## Goal

Detect eBay sales automatically, generate a USPS shipping label and packing list, and print both to a Rollo thermal printer on the Linux box — with a confirmation gate to control postage spend.

## Iteration Plan

### Iteration 1: Detect + Label + Packing List (with confirmation)

- Poll eBay Fulfillment API every 5 minutes from Linux box (192.168.254.99)
- When a new order is detected:
  1. Fetch order details (buyer address, items, SKUs, quantities, total)
  2. Generate a packing list PDF (item names, SKUs, quantities, buyer address)
  3. Generate a USPS shipping label via EasyPost API
  4. **Hold for confirmation** — notify George (email or stdout log), wait for explicit `ship confirm <order_id>` command
  5. On confirm → print packing list + shipping label to Rollo via `lpr`
- Track processed orders to avoid duplicates (JSONL log, same pattern as inbox-classifier classifications)

### Iteration 2: Full Auto (future)

- Remove confirmation gate
- Add safeguards: daily spend cap, anomaly detection (unusual weight, address, etc.)
- Sale → label + packing list printed automatically

## Architecture

### Runtime

- Python service on Linux box, same pattern as inbox-classifier
- Polling loop: check for new orders → process → sleep → repeat
- Logs to stdout and `~/.ebay-shipper/service.log`
- Orders logged to `~/.ebay-shipper/orders.jsonl`

### Sale Detection

- **eBay Fulfillment API** (REST): `GET /sell/fulfillment/v1/order`
- Filter by `creationdate` to find orders since last poll
- Reuse existing `longracks_msp` eBay app (same client ID/secret as ebay-mcp)
- Separate refresh token for ebay-shipper (independently revocable)
- Scope needed: `https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly`
- No public endpoint needed — outbound polling from behind NAT

### Label Generation

- **EasyPost** Python SDK (`pip install easypost`)
- 50,000 free labels (lifetime) — decades at current volume
- Commercial USPS rates
- Ship method: USPS Parcel Select (matching current method)
- Parcel dimensions: 9x6x1 in, weight varies by order (3oz per nozzle, ~9oz for bundle)
- Returns label as PDF or ZPL — use ZPL for direct Rollo printing

### Packing List

- Generated from order data (no external service needed)
- Content: order ID, date, buyer name/address, line items with SKU and quantity, order total
- Format: PDF (reportlab) or plain text, printed to Rollo
- Prints before the shipping label so it's on top when you grab the stack

### Printing

- Rollo thermal label printer connected to Linux box via USB
- Print via CUPS/`lpr`: `lpr -P Rollo -o raw label.zpl` (ZPL) or `lpr -P Rollo label.pdf` (PDF)
- 4x6 inch labels

### Confirmation Flow (Iteration 1)

- New order detected → service logs it and marks as "pending_confirmation"
- Notification: log message + optional email via existing Gmail API credentials
- George runs: `ebay-shipper confirm <order_id>` (CLI command)
- Service picks up confirmation → prints label + packing list
- Alternative: confirm via a simple local web UI (stretch goal)

### Configuration

- `~/.ebay-shipper/config.env` or environment variables:
  - `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `EBAY_REFRESH_TOKEN`
  - `EASYPOST_API_KEY`
  - `PRINTER_NAME` (CUPS printer name for Rollo)
  - `FROM_NAME`, `FROM_ADDRESS`, `FROM_CITY`, `FROM_STATE`, `FROM_ZIP`
  - `POLL_INTERVAL_SECONDS` (default: 300)

### Parcel Presets

Since all items ship in the same 9x6x1 padded envelope:

| SKU Pattern | Weight (oz) |
|-------------|-------------|
| NZ-*MM (single) | 3 |
| NZ-BNDL-* (bundle) | 9 |

Weight is calculated from line items, not hardcoded per order.

## Tech Stack

- Python 3.x (match inbox-classifier)
- `easypost` — label generation
- `reportlab` — packing list PDF generation
- `requests` or `httpx` — eBay Fulfillment API calls
- `lpr` — printing via CUPS

## New Repo or Same Repo?

Separate repo: `longrackslabs/ebay-shipper`. Different domain from email classification, different deployment config, different credentials. Same Linux box, same service pattern.

## What This Does NOT Cover

- eBay message/communication automation
- Inventory management (handled by lri workflow)
- Returns processing
- Multi-carrier support (USPS only for now)

## Setup Prerequisites

1. **Rollo printer** — verify it's set up in CUPS on the Linux box
2. **eBay OAuth** — reuse `longracks_msp` app, add `sell.fulfillment.readonly` scope, generate separate refresh token for ebay-shipper
3. **EasyPost account** — create account, get API key
