import unittest

from staketaxcsv.common.address import from_pubkey_to_bech32
from staketaxcsv.common.ibc.processor import _wallet_is_fee_payer

# Real secp256k1 signer pubkeys taken from Osmosis cosmwasmpool fixtures.
#   KEEPER  signs the batch-claim txs (e.g. 1BC7CE7F); it is osmo1wsrn579...
#   OWNER   osmo1q8709... is the limit-order owner; it signs place/cancel itself
#           (e.g. 8C69A594) but does NOT sign the keeper-settled claims.
KEEPER_PUBKEY = {
    "@type": "/cosmos.crypto.secp256k1.PubKey",
    "key": "Aw7wH5hJllHMLeFPLaI49PHDBR4YS5LBvGCRiFwVL1Gj",
}
OWNER_PUBKEY = {
    "@type": "/cosmos.crypto.secp256k1.PubKey",
    "key": "A55+LLJASGp7ZAvQwj1iVos8zT5wp/O3EhO2XMm32iyA",
}
OWNER = "osmo1q8709l2656zjtg567xnrxjr6j35a2pvwhxxms2"
KEEPER = "osmo1wsrn579cg2hddq7ejpfgtutdqangdwx7rfumpf"


class TestFeePayer(unittest.TestCase):

    def test_from_pubkey_to_bech32_secp256k1(self):
        self.assertEqual(from_pubkey_to_bech32("osmo", KEEPER_PUBKEY), KEEPER)
        self.assertEqual(from_pubkey_to_bech32("osmo", OWNER_PUBKEY), OWNER)

    def test_from_pubkey_to_bech32_unhandled_returns_none(self):
        # ethsecp256k1, multisig, empty and malformed keys are not derivable -> None
        self.assertIsNone(from_pubkey_to_bech32(
            "inj", {"@type": "/injective.crypto.v1beta1.ethsecp256k1.PubKey", "key": "AAAA"}))
        self.assertIsNone(from_pubkey_to_bech32(
            "osmo", {"@type": "/cosmos.crypto.multisig.LegacyAminoPubKey"}))
        self.assertIsNone(from_pubkey_to_bech32("osmo", {}))
        self.assertIsNone(from_pubkey_to_bech32("osmo", None))

    def test_owner_is_not_payer_of_keeper_settled_claim(self):
        # No explicit payer/granter -> first signer pays. Signer is the keeper,
        # so the order owner did not pay this fee.
        auth_info = {
            "fee": {"amount": [{"denom": "uosmo", "amount": "10000"}], "payer": "", "granter": ""},
            "signer_infos": [{"public_key": KEEPER_PUBKEY}],
        }
        self.assertFalse(_wallet_is_fee_payer(OWNER, auth_info))
        self.assertTrue(_wallet_is_fee_payer(KEEPER, auth_info))

    def test_owner_is_payer_of_own_tx(self):
        auth_info = {
            "fee": {"amount": [{"denom": "uosmo", "amount": "1285"}], "payer": "", "granter": ""},
            "signer_infos": [{"public_key": OWNER_PUBKEY}],
        }
        self.assertTrue(_wallet_is_fee_payer(OWNER, auth_info))

    def test_explicit_payer_and_granter_precedence(self):
        # Explicit fee.payer wins over the signer.
        self.assertTrue(_wallet_is_fee_payer(
            OWNER, {"fee": {"payer": OWNER}, "signer_infos": [{"public_key": KEEPER_PUBKEY}]}))
        self.assertFalse(_wallet_is_fee_payer(
            OWNER, {"fee": {"payer": KEEPER}, "signer_infos": [{"public_key": OWNER_PUBKEY}]}))
        # feegrant: the granter pays.
        self.assertTrue(_wallet_is_fee_payer(
            OWNER, {"fee": {"granter": OWNER}, "signer_infos": [{"public_key": KEEPER_PUBKEY}]}))
        self.assertFalse(_wallet_is_fee_payer(
            OWNER, {"fee": {"granter": KEEPER}, "signer_infos": [{"public_key": OWNER_PUBKEY}]}))

    def test_undeterminable_falls_back_to_prior_behavior(self):
        # No signer_infos, or an unhandled key type -> attribute to wallet (old behavior).
        self.assertTrue(_wallet_is_fee_payer(OWNER, {"fee": {}, "signer_infos": []}))
        self.assertTrue(_wallet_is_fee_payer(
            OWNER, {"fee": {}, "signer_infos": [
                {"public_key": {"@type": "/cosmos.crypto.multisig.LegacyAminoPubKey"}}]}))


if __name__ == "__main__":
    unittest.main()
