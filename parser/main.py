import httpx
import os
import re

import odoo_api
from httpx import Response

META_API_URL = os.getenv("META_API_URL", "")
META_ACCESS_TOKENS = os.getenv("META_PAGE_ACCESS_TOKENS", "invalid_page_id:invalid_token")
tokens_map = {}
for token_pair in META_ACCESS_TOKENS.split(','):
    page_id, token = token_pair.strip().split(':')
    tokens_map[page_id] = token

phone_pattern = re.compile(r'^\+?\d+$')


async def parse_leadgen(webhook_body: dict) -> dict:
    lead = {
        'description': '',
    }
    leadgen_id: int = webhook_body['entry'][0]['changes'][0]['value']['leadgen_id']
    page_id: int = webhook_body['entry'][0]['changes'][0]['value']['page_id']

    async with httpx.AsyncClient() as client:
        leadgen_response: Response = await client.get(
            f'{META_API_URL}/{leadgen_id}?access_token={tokens_map[page_id]}&fields=campaign_name,field_data,form_id')
        if leadgen_response.status_code != 200:
            raise httpx.HTTPStatusError(f"Failed to fetch leadgen data: {leadgen_response.text}",
                                        request=leadgen_response.request, response=leadgen_response)
        leadgen_body: dict = leadgen_response.json()

        campaign_name = leadgen_body.get('campaign_name', '')
        form_id = leadgen_body.get('form_id', '')

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
            name = field['name']
            value = field['values'][0]

            if name == 'email' or 'correo' in name:
                lead['email_from'] = value
            elif name == 'phone' or 'celular' in name or 'fono' in name:
                telefono = value.replace(' ', '').replace('-', '')
                if phone_pattern.match(telefono):
                    lead['phone'] = telefono
                else:
                    lead['phone'] = ''
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'first_name' or 'nombre' in name:
                lead['partner_nombres'] = value
            elif name == 'last_name' or 'apellido' in name:
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
            elif 'name' == 'curso' or 'curso' in name:
                tipo_programa_id = await odoo_api.search_read_underscored_lowered('crm.espol.tipo.programa',
                                                                                  'educacion_continua')
                if tipo_programa_id != -1:
                    lead['tipo_programa_id'] = tipo_programa_id

                curso_id = await odoo_api.search_read_underscored_lowered('crm.espol.programa.educacion.continua', value)
                if curso_id != -1:
                    lead['curso_id'] = curso_id
                else:
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'city' or 'ciudad' in name:
                ciudad_id = await odoo_api.search_read_underscored_lowered('predefined.city', value)
                if ciudad_id != -1:
                    lead['partner_predefined_city_id'] = ciudad_id
                else:
                    lead['description'] += f"{name}: {value} \n "
            elif name == 'vendedor':
                lead['user_id'] = False
            else:
                lead['description'] += f"{name}: {value} \n "

        return lead
