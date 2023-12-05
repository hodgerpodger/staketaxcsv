import boto3
import logging
import os

STAGE = os.environ.get("STAGE")
DYNAMO_TABLE_CACHE = "prod_cache" if STAGE == "prod" else "dev_cache"
FIELD_TERRA_CURRENCY_ADDRESSES = "terra_currency_addresses"
FIELD_TERRA_DECIMALS = "terra_decimals"
FIELD_TERRA_LP_CURRENCY_ADDRESSES = "terra_lp_currency_addresses"
FIELD_IBC_ADDRESSES = "ibc_addresses"
FIELD_KOINLY_NULL_MAP = "koinly_null_map"
FIELD_OSMO_EXPONENTS = "osmo_exponents"
FIELD_LUNA2_CONTRACTS = "luna2_contracts"
FIELD_LUNA2_CURRENCY_ADDRESSES = "luna2_currency_addresses"
FIELD_LUNA2_LP_CURRENCY_ADDRESSES = "luna2_lp_currency_addresses"


class Cache:

    dynamodb = None
    table = None

    def __init__(self):
        if not Cache.dynamodb:
            Cache.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            Cache.table = Cache.dynamodb.Table(DYNAMO_TABLE_CACHE)

    def _set_overwrite(self, field_name, data):
        response = Cache.table.put_item(
            Item={
                'field': field_name,
                'data': data
            }
        )
        logging.info("Updated %s ", field_name, extra={"response": response})

    def _set_merge(self, field_name, data):
        prev_data = self._get(field_name)
        prev_data.update(data)

        self._set_overwrite(field_name, prev_data)

    def _get(self, field_name):
        response = Cache.table.get_item(
            Key={'field': field_name}
        )

        if "Item" not in response:
            logging.warning("_get(): Unable to retrieve for field_name=%s", field_name)

            return {}
        item = response['Item']
        logging.info("Retrieved %s data.", field_name)
        data = item['data']
        return data

    def set_terra_currency_addresses(self, data):
        # Remove entries where no symbol was found or empty attribute
        data = {k: v for k, v in data.items() if (k and v)}

        return self._set_merge(FIELD_TERRA_CURRENCY_ADDRESSES, data)

    def get_terra_currency_addresses(self):
        return self._get(FIELD_TERRA_CURRENCY_ADDRESSES)

    def set_terra_lp_currency_addresses(self, data):
        # Remove entries where no symbol was found or empty attribute
        data = {k: v for k, v in data.items() if (k and v)}

        return self._set_merge(FIELD_TERRA_LP_CURRENCY_ADDRESSES, data)

    def get_terra_lp_currency_addresses(self):
        return self._get(FIELD_TERRA_LP_CURRENCY_ADDRESSES)

    def set_terra_decimals(self, data):
        # Remove entries with empty attribute
        data = {k: v for k, v in data.items() if k}

        return self._set_merge(FIELD_TERRA_DECIMALS, data)

    def get_terra_decimals(self):
        return self._get(FIELD_TERRA_DECIMALS)

    def get_luna2_contracts(self):
        return self._get(FIELD_LUNA2_CONTRACTS)

    def set_luna2_contracts(self, data):
        # Remove entries where no symbol was found or empty attribute
        data = {k: v for k, v in data.items() if (k and v)}

        return self._set_merge(FIELD_LUNA2_CONTRACTS, data)

    def get_luna2_currency_addresses(self):
        return self._get(FIELD_LUNA2_CURRENCY_ADDRESSES)

    def set_luna2_currency_addresses(self, data):
        # Remove entries where no symbol was found or empty attribute
        data = {k: v for k, v in data.items() if (k and v)}

        return self._set_merge(FIELD_LUNA2_CURRENCY_ADDRESSES, data)

    def get_luna2_lp_currency_addresses(self):
        return self._get(FIELD_LUNA2_LP_CURRENCY_ADDRESSES)

    def set_luna2_lp_currency_addresses(self, data):
        # Remove entries where no symbol was found or empty attribute
        data = {k: v for k, v in data.items() if (k and v)}

        return self._set_merge(FIELD_LUNA2_LP_CURRENCY_ADDRESSES, data)

    def set_ibc_addresses(self, data):
        # Remove entries where no symbol was found
        data = {k: v for k, v in data.items() if not v.startswith("ibc/")}

        return self._set_merge(FIELD_IBC_ADDRESSES, data)

    def get_ibc_addresses(self):
        return self._get(FIELD_IBC_ADDRESSES)

    def set_koinly_null_map(self, data):
        return self._set_overwrite(FIELD_KOINLY_NULL_MAP, data)

    def get_koinly_null_map(self):
        val = self._get(FIELD_KOINLY_NULL_MAP)
        if val:
            return val
        else:
            return []

    def set_osmo_exponents(self, data):
        return self._set_merge(FIELD_OSMO_EXPONENTS, data)

    def get_osmo_exponents(self):
        return self._get(FIELD_OSMO_EXPONENTS)
