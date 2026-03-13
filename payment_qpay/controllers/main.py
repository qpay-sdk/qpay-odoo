import json
import logging

from werkzeug.wrappers import Response

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class QPayController(http.Controller):

    @http.route(
        '/payment/qpay/webhook',
        type='http', auth='public', methods=['GET'], csrf=False,
    )
    def qpay_webhook(self, **kw):
        qpay_payment_id = kw.get('qpay_payment_id')
        _logger.info('QPay webhook received: qpay_payment_id=%s', qpay_payment_id)

        if not qpay_payment_id:
            _logger.warning('QPay webhook: missing qpay_payment_id')
            return Response('SUCCESS', status=200, content_type='text/plain')

        # Find all QPay transactions that are pending/draft
        txs = request.env['payment.transaction'].sudo().search([
            ('provider_code', '=', 'qpay'),
            ('state', 'in', ['draft', 'pending']),
            ('provider_reference', '!=', False),
        ])

        # Check each transaction's invoice via QPay API to find the matching one
        for tx in txs:
            provider = tx.provider_id
            try:
                result = provider._qpay_make_request('/v2/payment/check', {
                    'object_type': 'INVOICE',
                    'object_id': tx.provider_reference,
                    'offset': {'page_number': 1, 'page_limit': 100},
                })
                rows = result.get('rows', [])
                # Check if the payment_id matches any row
                for row in rows:
                    if str(row.get('payment_id')) == str(qpay_payment_id):
                        _logger.info(
                            'QPay webhook: payment %s matched tx %s',
                            qpay_payment_id, tx.reference,
                        )
                        tx._set_done()
                        return Response('SUCCESS', status=200, content_type='text/plain')
            except Exception as e:
                _logger.error(
                    'QPay webhook: check failed for tx %s: %s',
                    tx.reference, e,
                )

        _logger.warning(
            'QPay webhook: no matching transaction for payment_id %s',
            qpay_payment_id,
        )
        return Response('SUCCESS', status=200, content_type='text/plain')

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
