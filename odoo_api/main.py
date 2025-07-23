import os
import random
import httpx
from httpx import Response

ODOO_API_URL = os.getenv("ODOO_API_URL", "")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_ADMIN_ID = os.getenv("ODOO_ADMIN_ID", "")
ODOO_ADMIN_API_KEY = os.getenv("ODOO_ADMIN_API_KEY", "")


async def json_rpc(method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": random.randint(0, 1000000000),
    }
    async with httpx.AsyncClient() as client:
        reply: Response = await client.post(f'{ODOO_API_URL}', json=data)
        return reply.json()["result"]


async def call(*args):
    return await json_rpc("call", {"service": 'object', "method": 'execute',
                                   "args": (ODOO_DB, ODOO_ADMIN_ID, ODOO_ADMIN_API_KEY, *args)})


async def search_read_underscored_lowered(model: str, target_name: str):
    records = await call(model, 'search_read', [['id', '>', 0]], ['name'])
    filtered_records = list(filter(lambda x: x['name'].replace(' ', '_').lower() == target_name, records))
    if not filtered_records:
        filtered_records = list(filter(lambda x: x['name'].lower() == target_name.lower(), records))
        if not filtered_records:
            return -1
    return filtered_records[0]['id']


async def create_lead(body: dict):
    lead_id = await call('crm.lead', 'create', body)
    await call('crm.lead', 'remote_assign_salesman_if_possible', {'lead_id': lead_id})
    return lead_id


async def get_postgrados():
    return await call('crm.espol.programa.postgrado', 'search_read', [['id', '>', 0]], ['name'])


async def create_campaign_if_does_not_exist(name: str) -> int:
    campaigns = await call('utm.campaign', 'search_read', [['title', '=', name]], ['id'])
    if not campaigns:
        return await call('utm.campaign', 'create', {'title': name})
    return campaigns[0]['id']


async def update_lead(lead_id: int, values: dict):
    return await call('crm.lead', 'write', [lead_id], values)
