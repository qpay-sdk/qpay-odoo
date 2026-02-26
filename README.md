# QPay Payment Provider for Odoo

[![CI](https://github.com/qpay-sdk/qpay-odoo/actions/workflows/ci.yml/badge.svg)](https://github.com/qpay-sdk/qpay-odoo/actions)

QPay V2 payment integration for Odoo 17+.

## Installation

1. Copy `payment_qpay/` to your Odoo addons directory
2. Update apps list: **Settings → Apps → Update Apps List**
3. Install **QPay Payment Provider**

## Configuration

Go to **Invoicing → Configuration → Payment Providers → QPay**:

| Setting | Description |
|---------|-------------|
| Base URL | `https://merchant.qpay.mn` |
| Username | QPay merchant username |
| Password | QPay merchant password |
| Invoice Code | Your invoice code |

## How It Works

1. Customer selects QPay at checkout
2. Invoice created via QPay V2 API
3. QR code and bank deep links displayed
4. Customer pays via bank app
5. Webhook confirms payment → transaction marked as done
6. Client-side polling also checks payment status

## License

LGPL-3
