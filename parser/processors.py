import re
import odoo_api

VALID_PHONE_PATTERN = re.compile(r'^\+?\d+$')


def process_email(lead: dict, value: str) -> bool:
    lead['email_from'] = value
    return True


def process_phone(lead: dict, value: str) -> bool:
    telefono = value.replace(' ', '').replace('-', '')
    if VALID_PHONE_PATTERN.match(telefono):
        lead['phone'] = telefono.replace('+', '')
    else:
        lead['phone'] = ''
    return True


def process_name(lead: dict, value: str) -> bool:
    lead['partner_nombres'] = value
    return True


def process_last_name(lead: dict, value: str) -> bool:
    lead['partner_apellido_paterno'] = value
    return True


async def process_contact_method(lead: dict, value: str) -> bool:
    medio_contacto_id = await odoo_api.search_read_underscored_lowered('crm.espol.medio.contacto', value)

    found = medio_contacto_id != -1
    if found:
        lead['medio_contacto_id'] = medio_contacto_id

    return found


async def process_source(lead: dict, value: str) -> bool:
    fuente_id = await odoo_api.search_read_underscored_lowered('crm.espol.fuente', value)

    found = fuente_id != -1
    if found:
        lead['fuente_id'] = fuente_id

    return found


async def process_contact_channel(lead: dict, value: str) -> bool:
    canal_contacto_id = await odoo_api.search_read_underscored_lowered('crm.espol.canal.contacto', value)

    found = canal_contacto_id != -1
    if found:
        lead['canal_contacto_id'] = canal_contacto_id

    return found


async def process_period(lead: dict, value: str) -> bool:
    periodo_id = await odoo_api.search_read_underscored_lowered('crm.espol.periodo', value)

    found = periodo_id != -1
    if found:
        lead['periodo_id'] = periodo_id

    return found


def process_event(lead: dict, value: str) -> bool:
    lead['evento'] = value
    return True


async def process_postgrado(lead: dict, value: str) -> bool:
    tipo_programa_id = await odoo_api.search_read_underscored_lowered('crm.espol.tipo.programa',
                                                                      'postgrado')
    if tipo_programa_id != -1:
        lead['tipo_programa_id'] = tipo_programa_id

    postgrado_id = await odoo_api.search_read_underscored_lowered('crm.espol.programa.postgrado', value)

    found = postgrado_id != -1
    if found:
        lead['postgrado_id'] = postgrado_id

    return found


async def process_curso(lead: dict, value: str) -> bool:
    tipo_programa_id = await odoo_api.search_read_underscored_lowered('crm.espol.tipo.programa',
                                                                      'educacion_continua')
    if tipo_programa_id != -1:
        lead['tipo_programa_id'] = tipo_programa_id

    curso_id = await odoo_api.search_read_underscored_lowered('crm.espol.programa.educacion.continua',
                                                              value)
    found = curso_id != -1
    if found:
        lead['curso_id'] = curso_id

    return found


async def process_city(lead: dict, value: str) -> bool:
    ciudad_id = await odoo_api.search_read_underscored_lowered('predefined.city', value)
    found = ciudad_id != -1
    if found:
        lead['partner_predefined_city_id'] = ciudad_id

    return found


def process_salesman(lead: dict, value: str) -> bool:
    lead['user_id'] = False
    return True


FIELD_PROCESSORS = {
    'email': process_email,
    'correo': process_email,
    'phone': process_phone,
    'telefono': process_phone,
    'celular': process_phone,
    'full_name': process_name,
    'nombre_completo': process_name,
    'first_name': process_name,
    'nombre': process_name,
    'last_name': process_last_name,
    'apellido': process_last_name,
    'medio_de_contacto': process_contact_method,
    'preferido': process_contact_method,
    'fuente': process_source,
    'source': process_source,
    'canal_contacto': process_contact_channel,
    'periodo': process_period,
    'evento': process_event,
    'maestr': process_postgrado,
    'grado': process_postgrado,
    'curso': process_curso,
    'diplomado': process_curso,
    'ciudad': process_city,
    'city': process_city,
    'vendedor': process_salesman,
}
