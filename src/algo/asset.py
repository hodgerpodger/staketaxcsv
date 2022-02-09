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
            raise ValueError("Asset id must be greater than zero")
        if int(amount) < 0:
            raise ValueError("Asset amount cannot be negative")

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
        self._uint_amount = int(amount)

    @property
    def id(self):
        return self._id

    @property
    def amount(self):
        return float(self._uint_amount) / float(10 ** self._decimals)

    @property
    def ticker(self):
        return self._ticker

    @property
    def decimals(self):
        return self._decimals

    def __add__(self, other):
        if type(other) == int:
            if other < 0:
                raise ValueError("Amounts cannot be negative")
            return Asset(self._id, self._uint_amount + other)

        if not isinstance(other, Asset):
            raise TypeError("Invalid argument")

        if self._id != other.id:
            raise ValueError("Cannot add different assets")

        return Asset(self._id, self._uint_amount + other._uint_amount)

    def __iadd__(self, other):
        if type(other) == int:
            if other < 0:
                raise ValueError("Amounts cannot be negative")
            self._uint_amount += other
        else:
            if not isinstance(other, Asset):
                raise TypeError("Invalid argument")
            if self._id != other.id:
                raise ValueError("Cannot add different assets")
            self._uint_amount += other._uint_amount

        return self

    def __sub__(self, other):
        if type(other) == int:
            if other < 0:
                raise ValueError("Amounts cannot be negative")
            if self._uint_amount < other:
                raise ValueError("Asset amount cannot be negative")
            return Asset(self._id, self._uint_amount - other)

        if not isinstance(other, Asset):
            raise TypeError("Invalid argument")
        if self._id != other.id:
            raise ValueError("Cannot substruct different assets")
        if self._uint_amount < other._uint_amount:
            raise ValueError("Asset amount cannot be negative")

        return Asset(self._id, self._uint_amount - other._uint_amount)

    def __isub__(self, other):
        if type(other) == int:
            if other < 0:
                raise ValueError("Amounts cannot be negative")
            if self._uint_amount < other:
                raise ValueError("Asset amount cannot be negative")
            self._uint_amount -= other
        else:
            if not isinstance(other, Asset):
                raise TypeError("Invalid argument")
            if self._id != other.id:
                raise ValueError("Cannot substruct different assets")
            if self._uint_amount < other._uint_amount:
                raise ValueError("Asset amount cannot be negative")
            self._uint_amount -= other._uint_amount

        return self

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            raise TypeError("Invalid argument")
        if other < 0:
            raise ValueError("Asset amount cannot be negative")

        return Asset(self._id, self._uint_amount * other)

    def __float__(self):
        return self.amount

    def __str__(self):
        return "{{:.{}f}}".format(self.decimals).format(self.amount)

    def zero(self):
        return self._uint_amount == 0


class Algo(Asset):
    def __init__(self, amount=0):
        super().__init__(0, amount)
