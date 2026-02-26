import json
import logging
import requests
from base64 import b64encode

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('qpay', 'QPay')],
        ondelete={'qpay': 'set default'},
    )
    qpay_base_url = fields.Char(
        string='QPay Base URL',
        default='https://merchant.qpay.mn',
        required_if_provider='qpay',
    )
    qpay_username = fields.Char(
        string='QPay Username',
        required_if_provider='qpay',
        groups='base.group_system',
    )
    qpay_password = fields.Char(
        string='QPay Password',
        required_if_provider='qpay',
        groups='base.group_system',
    )
    qpay_invoice_code = fields.Char(
        string='QPay Invoice Code',
        required_if_provider='qpay',
    )

    _qpay_token_cache = {}

    def _qpay_get_token(self):
        self.ensure_one()
        cache_key = self.id
        cached = self._qpay_token_cache.get(cache_key)
        if cached:
            return cached

        url = f'{self.qpay_base_url}/v2/auth/token'
        credentials = b64encode(
            f'{self.qpay_username}:{self.qpay_password}'.encode()
        ).decode()
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json',
        }
        response = requests.post(url, headers=headers, timeout=30)
        response.raise_for_status()
        token = response.json().get('access_token')
        self._qpay_token_cache[cache_key] = token
        return token

    def _qpay_make_request(self, endpoint, payload=None, method='POST'):
        self.ensure_one()
        token = self._qpay_get_token()
        url = f'{self.qpay_base_url}{endpoint}'
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        response = requests.request(
            method, url, headers=headers,
            data=json.dumps(payload) if payload else None,
            timeout=30,
        )
        if response.status_code == 401:
            self._qpay_token_cache.pop(self.id, None)
            token = self._qpay_get_token()
            headers['Authorization'] = f'Bearer {token}'
            response = requests.request(
                method, url, headers=headers,
                data=json.dumps(payload) if payload else None,
                timeout=30,
            )
        response.raise_for_status()
        return response.json()

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, **kwargs
        )
        currency = self.env['res.currency'].browse(currency_id)
        if currency and currency.name != 'MNT':
            providers = providers.filtered(lambda p: p.code != 'qpay')
        return providers
