{
    'name': 'QPay Payment Provider',
    'version': '1.0.1',
    'category': 'Accounting/Payment Providers',
    'summary': 'QPay V2 payment integration for Odoo',
    'description': 'Accept payments via QPay V2 API. Supports QR code payments and bank app deep links.',
    'author': 'QPay SDK',
    'website': 'https://github.com/qpay-sdk/qpay-odoo',
    'license': 'LGPL-3',
    'depends': ['payment'],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_qpay_templates.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
}
