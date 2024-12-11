import json
import pprint

from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.osmo.constants import MSG_TYPE_EXECUTE_CONTRACT
from staketaxcsv.osmo import denoms as denoms_osmo


class MsgInfoOsmo(MsgInfoIBC):

    def __init__(self, wallet_address, msg_index, message, log, lcd_node):
        super().__init__(wallet_address, msg_index, message, log, lcd_node)
        self.events_by_type = self._events_by_type()
        self.execute_contract_message = self._execute_contract_message()
        self.events_as_dict = self._events_as_dict(self.events)

    def amount_currency_single(self, amount_raw, currency_raw):
        return denoms_osmo.amount_currency_from_raw(amount_raw, currency_raw, self.lcd_node)

    def _execute_contract_message(self):
        if self.msg_type == MSG_TYPE_EXECUTE_CONTRACT:
            m = self.message
            if "msg" in m:
                return m["msg"]
            elif "msg__@stringify" in m:
                msg_str = m["msg__@stringify"]
                if isinstance(msg_str, str):
                    return json.loads(msg_str)
                elif isinstance(msg_str, list):
                    msg_str = "".join(msg_str)
                    return json.loads(msg_str)
                else:
                    raise Exception("unable to handle msg__@stringify in _execute_contract_message()")

        return {}

    def _events_as_dict(self, events):
        """ Returns event log element, converting attributes lists into dicts """
        out = []

        for event in events:
            attributes, event_type = event["attributes"], event["type"]
            item = {
                "event_type": event_type,
            }

            for i, kv in enumerate(attributes):
                k, v = kv["key"], kv["value"]

                if k == "_contract_address" and i > 0:
                    # start new item if attributes list has multiple actions (i.e. _contract_address elements)
                    out.append(item)
                    item = {
                        "event_type": event_type,
                    }

                item[k] = v

            out.append(item)
        return out

    def print(self):
        super().print()
        print("\n\texecute_contract_message:")
        pprint.pprint(self.execute_contract_message)
        print("\n\tevents_as_dict:")
        pprint.pprint(self.events_as_dict)
