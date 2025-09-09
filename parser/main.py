import httpx
import os

import odoo_api
from httpx import Response

from parser.processors import FIELD_PROCESSORS

META_API_URL = os.getenv("META_API_URL", "")
META_ACCESS_TOKENS = os.getenv("META_PAGE_ACCESS_TOKENS", "invalid_page_id:invalid_token")
tokens_map = {}
for token_pair in META_ACCESS_TOKENS.split(','):
    page_id, token = token_pair.strip().split(':')
    tokens_map[page_id] = token

META_ADSETS_MAPPING = os.getenv("META_ADSETS_MAPPING", "")
adsets_map = {}
for mapping_pair in META_ADSETS_MAPPING.split(','):
    adset_name, postgrado_name = mapping_pair.strip().split(':')
    adsets_map[adset_name] = postgrado_name


async def parse_leadgen(webhook_body: dict) -> dict:
    lead = {
        'description': '',
    }
    leadgen_id: int = webhook_body['entry'][0]['changes'][0]['value']['leadgen_id']
    page_id: int = webhook_body['entry'][0]['changes'][0]['value']['page_id']

    async with (httpx.AsyncClient() as client):
        leadgen_response: Response = await client.get(
            f'{META_API_URL}/{leadgen_id}?access_token={tokens_map[page_id]}&fields=campaign_name,field_data,form_id,adset_name')
        if leadgen_response.status_code != 200:
            raise httpx.HTTPStatusError(f"Failed to fetch leadgen data: {leadgen_response.text}",
                                        request=leadgen_response.request, response=leadgen_response)
        leadgen_body: dict = leadgen_response.json()

        campaign_name = leadgen_body.get('campaign_name', '')
        form_id = leadgen_body.get('form_id', '')
        adset_name = leadgen_body.get('adset_name', '')

        if campaign_name:
            campaign_id = await odoo_api.create_campaign_if_does_not_exist(campaign_name)
            lead['campaign_id'] = campaign_id
        else:
            form_response: Response = await client.get(
                f'{META_API_URL}/{form_id}?access_token={tokens_map[page_id]}&fields=name')
            if form_response.status_code != 200:
                raise httpx.HTTPStatusError(f"Failed to fetch form data: {form_response.text}",
                                            request=form_response.request, response=form_response)
            form_body: dict = form_response.json()
            form_name = form_body.get('name', '')
            if form_name:
                campaign_id = await odoo_api.create_campaign_if_does_not_exist(form_name)
                lead['campaign_id'] = campaign_id

        fuente_id = await odoo_api.search_read_underscored_lowered('crm.espol.fuente', 'meta')
        if fuente_id != -1:
            lead['fuente_id'] = fuente_id

        field_data = leadgen_body.get('field_data', [])

        while len(field_data) > 0:
            field = field_data.pop(0)
            name = field['name'].lower()
            value = field['values'][0]

            matched_processor = False

            for key, processor in FIELD_PROCESSORS.items():
                if key in name:
                    matched_processor = await processor(lead, value)
                    break
            if not matched_processor:
                lead['description'] += f"{name}: {value} \n "

        if adset_name:
            lead['description'] += f"adset_name: {adset_name} \n "
            if 'postgrado_id' not in lead:
                for adset_key, postgrado_name in adsets_map.items():
                    if adset_key in adset_name:
                        await FIELD_PROCESSORS['grado'](lead, postgrado_name)
                        break

        return lead
