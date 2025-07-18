import httpx
import os
import re

import odoo_api
from httpx import Response

META_API_URL = os.getenv("META_API_URL", "")
META_PAGE_ACCESS_TOKEN = os.getenv("META_PAGE_ACCESS_TOKEN", "")

phone_pattern = re.compile(r'^\+?\d+$')


async def parse_leadgen(webhook_body: dict) -> dict:
    lead = {
        'description': '',
    }
    leadgen_id: int = webhook_body['entry'][0]['changes'][0]['value']['leadgen_id']

    async with httpx.AsyncClient() as client:
        leadgen_response: Response = await client.get(
            f'{META_API_URL}/{leadgen_id}?access_token={META_PAGE_ACCESS_TOKEN}&fields=campaign_name,field_data')
        if leadgen_response.status_code != 200:
            raise httpx.HTTPStatusError(f"Failed to fetch leadgen data: {leadgen_response.text}",
                                        request=leadgen_response.request, response=leadgen_response)
        leadgen_body: dict = leadgen_response.json()

        campaign_name = leadgen_body.get('campaign_name', '')
        campaign_id = await odoo_api.create_campaign_if_does_not_exist(campaign_name)
        lead['campaign_id'] = campaign_id

        field_data = leadgen_body.get('field_data', [])

        while len(field_data) > 0:
            field = field_data.pop(0)
            name = field['name']
            value = field['values'][0]

            if name == 'email':
                lead['email_from'] = value
            elif name == 'phone':
                telefono = value.replace(' ', '').replace('-', '')
                lead['phone'] = telefono if phone_pattern.match(telefono) else ''
            elif name == 'first_name':
                lead['partner_nombres'] = value
            elif name == 'last_name':
                lead['partner_apellido_paterno'] = value
            elif 'medio_de_contacto' in name:
                medio_contacto_id = await odoo_api.search_read_underscored_lowered('crm.espol.medio.contacto', value)
                if medio_contacto_id != -1:
                    lead['medio_contacto_id'] = medio_contacto_id
                else:
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'fuente':
                fuente_id = await odoo_api.search_read_underscored_lowered('crm.espol.fuente', value)
                if fuente_id != -1:
                    lead['fuente_id'] = fuente_id
                else:
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'canal_contacto':
                canal_contacto_id = await odoo_api.search_read_underscored_lowered('crm.espol.canal.contacto', value)
                if canal_contacto_id != -1:
                    lead['canal_contacto_id'] = canal_contacto_id
                else:
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'periodo':
                periodo_id = await odoo_api.search_read_underscored_lowered('crm.espol.periodo', value)
                if periodo_id != -1:
                    lead['periodo_id'] = periodo_id
                else:
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'evento':
                lead['evento'] = value
            elif 'maestr' in name or 'grado' in name:
                tipo_programa_id = await odoo_api.search_read_underscored_lowered('crm.espol.tipo.programa',
                                                                                  'postgrado')
                if tipo_programa_id != -1:
                    lead['tipo_programa_id'] = tipo_programa_id

                postgrado_id = await odoo_api.search_read_underscored_lowered('crm.espol.programa.postgrado', value)
                if postgrado_id != -1:
                    lead['postgrado_id'] = postgrado_id
                else:
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'vendedor':
                lead['user_id'] = False
            else:
                lead['description'] += f"{name}: {value} \n "

        return lead
