import simplejson.errors
import logging

from staketaxcsv.common.ibc import api_lcd_v1, api_lcd_v2


LCD_V2_MIN_VERSION = "0.46.0"


class NodeVersions:

    # node url -> cosmos sdk version
    versions = {}


def get_txs_pages_count(node, address, max_txs, **kwargs):
    if _version_ge(_node_version(node), LCD_V2_MIN_VERSION):
        return api_lcd_v2.get_txs_pages_count(node, address, max_txs, **kwargs)
    else:
        return api_lcd_v1.get_txs_pages_count(node, address, max_txs, **kwargs)


def get_txs_all(node, address, max_txs, progress=None, **kwargs):
    if _version_ge(_node_version(node), LCD_V2_MIN_VERSION):
        return api_lcd_v2.get_txs_all(node, address, max_txs, progress=progress, **kwargs)
    else:
        return api_lcd_v1.get_txs_all(node, address, max_txs, progress=progress, **kwargs)


def make_lcd_api(node):
    """ Returns a LcdAPI object (i.e. LcdAPI_v2(..) or LcdAPI_v1(..)) """
    if _version_ge(_node_version(node), LCD_V2_MIN_VERSION):
        return api_lcd_v2.LcdAPI_v2(node)
    else:
        return api_lcd_v1.LcdAPI_v1(node)


def _node_version(node):
    """ Returns cosmos sdk version of lcd node (i.e. "0.45.1") """
    if node in NodeVersions.versions:
        return NodeVersions.versions[node]

    try:
        version = api_lcd_v1.LcdAPI_v1(node).cosmos_sdk_version()
        logging.info("cosmos sdk version: %s", version)
    except simplejson.errors.JSONDecodeError as e:
        logging.error("Unable to determine cosmos sdk version.  Returning dummy version 0.1.1.  "
                      "Suggest using explicit LcdAPI like api_lcd_v1 or api_lcd_v2 instead.  ")
        version = "0.1.1"
    NodeVersions.versions[node] = version
    return version


# Output: "0.45.13" >= 2.1.1: False"
def _version_ge(version1, version2):
    version1_parts = [int(part) for part in version1.split('.')]
    version2_parts = [int(part) for part in version2.split('.')]

    return version1_parts >= version2_parts
