import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class QPayController(http.Controller):

    @http.route(
        '/payment/qpay/webhook',
        type='json', auth='public', methods=['POST'], csrf=False,
    )
    def qpay_webhook(self):
        data = json.loads(request.httprequest.data)
        _logger.info('QPay webhook received: %s', data)

        tx = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
            'qpay', data
        )
        tx._handle_notification_data('qpay', data)
        return {'status': 'ok'}

    @http.route(
        '/payment/qpay/check',
        type='json', auth='public', methods=['POST'], csrf=False,
    )
    def qpay_check(self):
        data = json.loads(request.httprequest.data)
        invoice_id = data.get('invoice_id')
        if not invoice_id:
            return {'paid': False, 'error': 'Missing invoice_id'}

        tx = request.env['payment.transaction'].sudo().search([
            ('provider_reference', '=', invoice_id),
            ('provider_code', '=', 'qpay'),
        ], limit=1)

        if not tx:
            return {'paid': False, 'error': 'Transaction not found'}

        provider = tx.provider_id
        try:
            result = provider._qpay_make_request('/v2/payment/check', {
                'object_type': 'INVOICE',
                'object_id': invoice_id,
                'offset': {'page_number': 1, 'page_limit': 100},
            })
            rows = result.get('rows', [])
            if rows:
                tx._set_done()
                return {'paid': True}
            return {'paid': False}
        except Exception as e:
            _logger.error('QPay check failed: %s', e)
            return {'paid': False, 'error': str(e)}
