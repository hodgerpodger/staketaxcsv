from algo.api_algoindexer import AlgoIndexerAPI

# TODO Strong candidate for dynamodb cache
known_assets = {
    0: {
        "name": "Algorand",
        "unit-name": "ALGO",
        "decimals": 6,
    },
    312769: {
        "name": "Tether USDt",
        "unit-name": "USDt",
        "decimals": 6,
    },
    31566704: {
        "name": "USDC",
        "unit-name": "USDC",
        "decimals": 6,
    },
    465865291: {
        "name": "STBL",
        "unit-name": "STBL",
        "decimals": 6,
    },
    27165954: {
        "name": "Planets",
        "unit-name": "PLANET",
        "decimals": 6,
    },
    226701642: {
        "name": "Yieldly",
        "unit-name": "YLDY",
        "decimals": 6,
    },
    287867876: {
        "name": "Opulous",
        "unit-name": "OPUL",
        "decimals": 10,
    },
    359342000: {
        "name": "Tinyman Pool YLDY-ALGO",
        "unit-name": "TM1POOL",
        "decimals": 6,
    },
    384303832: {
        "name": "AKITA INU TOKEN",
        "unit-name": "AKITA",
        "decimals": 0,
    },
    386192725: {
        "name": "goBTC",
        "unit-name": "goBTC",
        "decimals": 8,
    },
    386195940: {
        "name": "goETH",
        "unit-name": "goETH",
        "decimals": 8,
    },
    552655440: {
        "name": "TinymanPool1.1 YLDY-ALGO",
        "unit-name": "TMPOOL11",
        "decimals": 6,
    },
}


class Asset:
    def __init__(self, id, amount=0):
        if id < 0:
            raise ValueError("id must be greater than zero")
        self._id = id
        params = None
        if id in known_assets:
            params = known_assets[id]
        else:
            params = AlgoIndexerAPI.get_asset(id)
            known_assets[id] = {key: params[key] for key in ["name", "unit-name", "decimals"]}
        if params is None:
            raise ValueError("invalid asset id")
        self._decimals = params["decimals"]
        self._ticker = params["unit-name"]
        self._amount = float(amount) / float(10 ** self._decimals)

    @property
    def amount(self):
        return self._amount

    @property
    def ticker(self):
        return self._ticker

    @property
    def decimals(self):
        return self._decimals

    def __add__(self, other):
        if type(other) == int:
            return Asset(self._id, self._amount + (float(other) / float(10 ** self._decimals)))
        return Asset(self._id, self._amount + other.amount)

    def __iadd__(self, other):
        if type(other) == int:
            self._amount += float(other) / float(10 ** self._decimals)
        else:
            self._amount += other.amount
        return self

    def __float__(self):
        return self.amount

    def __str__(self):
        return "{{:.{}f}}".format(self.decimals).format(self.amount)

    def zero(self):
        return self._amount == 0


class Algo(Asset):
    def __init__(self, amount=0):
        super().__init__(0, amount)
