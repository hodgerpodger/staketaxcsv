"""
Tests for cosmosplus processor, specifically for handling transactions without logs
"""

import unittest
from unittest.mock import MagicMock, patch

from staketaxcsv.common.ibc.MsgInfoIBC import MsgInfoIBC
from staketaxcsv.common.ibc.processor import txinfo
from staketaxcsv.common.ibc.TxInfoIBC import TxInfoIBC
from staketaxcsv.common.ibc.util_ibc import group_events_by_msg_index


class TestCosmosPlusNoLogs(unittest.TestCase):
    """Test handling of transactions without logs (using events instead)."""

    def test_group_events_by_msg_index(self):
        """Test that events are correctly grouped by msg_index."""
        events = [
            {
                "type": "coin_received",
                "attributes": [
                    {"key": "receiver", "value": "addr1"},
                    {"key": "amount", "value": "1000unym"},
                    {"key": "msg_index", "value": "0"},
                ],
            },
            {
                "type": "coin_spent",
                "attributes": [
                    {"key": "spender", "value": "addr2"},
                    {"key": "amount", "value": "1000unym"},
                    {"key": "msg_index", "value": "0"},
                ],
            },
            {
                "type": "coin_received",
                "attributes": [
                    {"key": "receiver", "value": "addr3"},
                    {"key": "amount", "value": "500unym"},
                    {"key": "msg_index", "value": "1"},
                ],
            },
            {
                "type": "transfer",
                "attributes": [
                    {"key": "recipient", "value": "addr1"},
                    {"key": "sender", "value": "addr2"},
                    {"key": "amount", "value": "1000unym"},
                    # No msg_index
                ],
            },
        ]

        result = group_events_by_msg_index(events)

        self.assertEqual(len(result), 2)
        self.assertIn(0, result)
        self.assertIn(1, result)
        self.assertEqual(len(result[0]), 2)  # 2 events for msg_index 0
        self.assertEqual(len(result[1]), 1)  # 1 event for msg_index 1

    def test_txinfo_with_logs(self):
        """Test that txinfo works normally when logs are present."""
        elem = {
            "txhash": "TEST123",
            "timestamp": "2025-01-01T00:00:00Z",
            "code": 0,
            "tx": {
                "body": {
                    "messages": [
                        {
                            "@type": "/cosmos.bank.v1beta1.MsgSend",
                            "from_address": "addr1",
                            "to_address": "addr2",
                            "amount": [{"denom": "unym", "amount": "1000"}],
                        }
                    ],
                    "memo": "test",
                },
                "auth_info": {"fee": {"amount": [{"denom": "unym", "amount": "500"}]}},
            },
            "logs": [
                {
                    "msg_index": 0,
                    "events": [
                        {
                            "type": "coin_spent",
                            "attributes": [
                                {"key": "spender", "value": "addr1"},
                                {"key": "amount", "value": "1000unym"},
                            ],
                        },
                        {
                            "type": "coin_received",
                            "attributes": [
                                {"key": "receiver", "value": "addr2"},
                                {"key": "amount", "value": "1000unym"},
                            ],
                        },
                    ],
                }
            ],
        }

        result = txinfo("addr2", elem, "generic", "https://test.node")

        self.assertIsInstance(result, TxInfoIBC)
        self.assertEqual(result.txid, "TEST123")
        self.assertEqual(len(result.msgs), 1)
        self.assertEqual(result.msgs[0].msg_type, "MsgSend")

    def test_txinfo_without_logs_with_events(self):
        """Test that txinfo falls back to events when logs are missing."""
        elem = {
            "txhash": "TEST456",
            "timestamp": "2025-01-01T00:00:00Z",
            "code": 0,
            "tx": {
                "body": {
                    "messages": [
                        {
                            "@type": "/cosmos.bank.v1beta1.MsgSend",
                            "from_address": "addr1",
                            "to_address": "addr2",
                            "amount": [{"denom": "unym", "amount": "1000"}],
                        }
                    ],
                    "memo": "test",
                },
                "auth_info": {"fee": {"amount": [{"denom": "unym", "amount": "500"}]}},
            },
            "logs": [],  # Empty logs
            "events": [
                {
                    "type": "coin_spent",
                    "attributes": [
                        {"key": "spender", "value": "addr1"},
                        {"key": "amount", "value": "1000unym"},
                        {"key": "msg_index", "value": "0"},
                    ],
                },
                {
                    "type": "coin_received",
                    "attributes": [
                        {"key": "receiver", "value": "addr2"},
                        {"key": "amount", "value": "1000unym"},
                        {"key": "msg_index", "value": "0"},
                    ],
                },
            ],
        }

        result = txinfo("addr2", elem, "generic", "https://test.node")

        self.assertIsInstance(result, TxInfoIBC)
        self.assertEqual(result.txid, "TEST456")
        self.assertEqual(len(result.msgs), 1)
        self.assertEqual(result.msgs[0].msg_type, "MsgSend")

    def test_txinfo_without_logs_and_events(self):
        """Test that txinfo handles case with neither logs nor events."""
        elem = {
            "txhash": "TEST789",
            "timestamp": "2025-01-01T00:00:00Z",
            "code": 0,
            "tx": {
                "body": {
                    "messages": [
                        {
                            "@type": "/cosmos.bank.v1beta1.MsgSend",
                            "from_address": "addr1",
                            "to_address": "addr2",
                            "amount": [{"denom": "unym", "amount": "1000"}],
                        }
                    ],
                    "memo": "test",
                },
                "auth_info": {"fee": {"amount": [{"denom": "unym", "amount": "500"}]}},
            },
            "logs": [],  # Empty logs
            # No events key
        }

        result = txinfo("addr2", elem, "generic", "https://test.node")

        self.assertIsInstance(result, TxInfoIBC)
        self.assertEqual(result.txid, "TEST789")
        # When neither logs nor events are present, no msgs are created
        # This is the expected behavior - the transaction will be treated as having no processable messages
        self.assertEqual(len(result.msgs), 0)

    def test_txinfo_multiple_messages_no_logs(self):
        """Test handling multiple messages without logs."""
        elem = {
            "txhash": "TEST_MULTI",
            "timestamp": "2025-01-01T00:00:00Z",
            "code": 0,
            "tx": {
                "body": {
                    "messages": [
                        {
                            "@type": "/cosmos.bank.v1beta1.MsgSend",
                            "from_address": "addr1",
                            "to_address": "addr2",
                            "amount": [{"denom": "unym", "amount": "1000"}],
                        },
                        {
                            "@type": "/cosmos.bank.v1beta1.MsgSend",
                            "from_address": "addr1",
                            "to_address": "addr3",
                            "amount": [{"denom": "unym", "amount": "2000"}],
                        },
                    ],
                    "memo": "test",
                },
                "auth_info": {"fee": {"amount": [{"denom": "unym", "amount": "500"}]}},
            },
            "logs": [],
            "events": [
                {
                    "type": "coin_spent",
                    "attributes": [
                        {"key": "spender", "value": "addr1"},
                        {"key": "amount", "value": "1000unym"},
                        {"key": "msg_index", "value": "0"},
                    ],
                },
                {
                    "type": "coin_received",
                    "attributes": [
                        {"key": "receiver", "value": "addr2"},
                        {"key": "amount", "value": "1000unym"},
                        {"key": "msg_index", "value": "0"},
                    ],
                },
                {
                    "type": "coin_spent",
                    "attributes": [
                        {"key": "spender", "value": "addr1"},
                        {"key": "amount", "value": "2000unym"},
                        {"key": "msg_index", "value": "1"},
                    ],
                },
                {
                    "type": "coin_received",
                    "attributes": [
                        {"key": "receiver", "value": "addr3"},
                        {"key": "amount", "value": "2000unym"},
                        {"key": "msg_index", "value": "1"},
                    ],
                },
            ],
        }

        result = txinfo("addr1", elem, "generic", "https://test.node")

        self.assertIsInstance(result, TxInfoIBC)
        self.assertEqual(result.txid, "TEST_MULTI")
        self.assertEqual(len(result.msgs), 2)
        self.assertEqual(result.msgs[0].msg_type, "MsgSend")
        self.assertEqual(result.msgs[1].msg_type, "MsgSend")


if __name__ == "__main__":
    unittest.main()
