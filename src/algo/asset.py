from algo.api_algoindexer import AlgoIndexerAPI


class Asset:
    asset_list = {
        0: {
            "name": "Algorand",
            "unit-name": "ALGO",
            "decimals": 6,
        }
    }
    indexer = AlgoIndexerAPI()

    def __init__(self, id, amount=0):
        if id < 0:
            raise ValueError("Asset id must be greater than zero")
        if int(amount) < 0:
            raise ValueError("Asset amount cannot be negative")

        self._id = id
        if id in self.asset_list:
            params = self.asset_list[id]
        else:
            params = self.indexer.get_asset(id)
            self.asset_list[id] = {key: params[key] for key in ["name", "unit-name", "decimals"]}
        if params is None:
            raise ValueError("invalid asset id")
        self._decimals = params["decimals"]
        # Remove non-ascii characters from the name
        self._ticker = params["unit-name"].encode('ascii', 'ignore').decode('ascii')
        self._uint_amount = int(amount)

    @classmethod
    def load_assets(cls, assets):
        for asset in assets:
            id = asset["asset-id"]
            cls.asset_list[id] = {key: asset[key] for key in ["name", "unit-name", "decimals"]}

    @property
    def id(self):
        return self._id

    @property
    def amount(self):
        return float(self._uint_amount) / float(10 ** self._decimals)

    @property
    def uint_amount(self):
        return self._uint_amount

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
