import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'qpay':
            return res

        provider = self.provider_id
        payload = {
            'invoice_code': provider.qpay_invoice_code,
            'sender_invoice_no': self.reference,
            'amount': self.amount,
            'callback_url': f'{self.get_base_url()}/payment/qpay/webhook',
            'invoice_description': self.reference,
            'invoice_receiver_code': self.partner_id.email or '',
        }
        try:
            invoice_data = provider._qpay_make_request('/v2/invoice', payload)
        except Exception as e:
            raise ValidationError(
                _('QPay invoice creation failed: %s', str(e))
            )

        self.provider_reference = invoice_data.get('invoice_id')

        return {
            'qpay_invoice_id': invoice_data.get('invoice_id'),
            'qpay_qr_text': invoice_data.get('qr_text', ''),
            'qpay_qr_image': invoice_data.get('qr_image', ''),
            'qpay_qpay_short_url': invoice_data.get('qPay_shortUrl', ''),
            'qpay_urls': invoice_data.get('urls', []),
            'api_url': f'{self.get_base_url()}/payment/qpay/check',
        }

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(
            provider_code, notification_data
        )
        if provider_code != 'qpay':
            return tx

        reference = notification_data.get('sender_invoice_no')
        if not reference:
            raise ValidationError(
                _('QPay: No reference found in notification data.')
            )
        tx = self.search([
            ('reference', '=', reference),
            ('provider_code', '=', 'qpay'),
        ])
        if not tx:
            raise ValidationError(
                _('QPay: No transaction found matching reference %s.', reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'qpay':
            return

        invoice_id = self.provider_reference
        if not invoice_id:
            self._set_error(_('QPay: Missing invoice ID.'))
            return

        provider = self.provider_id
        try:
            result = provider._qpay_make_request('/v2/payment/check', {
                'object_type': 'INVOICE',
                'object_id': invoice_id,
                'offset': {'page_number': 1, 'page_limit': 100},
            })
        except Exception as e:
            self._set_error(_('QPay payment check failed: %s', str(e)))
            return

        rows = result.get('rows', [])
        if rows:
            self._set_done()
        else:
            self._set_pending()
