import io
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class Varint:
    """
    Constructs the integer encoded as a base 128 varint from a stream of bytes.
    """
    _varint: int
    _shift: int

    def __init__(self):
        self._varint = 0
        self._shift = 0

    @property
    def byte_size(self) -> int:
        return int((self._shift + (8 - (self._shift % 8))) / 8)

    @property
    def value(self) -> int:
        return self._varint

    def from_bytes(self, byte_stream: io.BytesIO) -> None:
        while True:
            byte = byte_stream.read(1)
            if byte == b"":
                raise EOFError("unexpected end of byte sequence while parsing varint")

            # single byte, so byte order doesn't matter
            byte = int.from_bytes(byte, sys.byteorder)

            # add this byte's data into the varint
            self._varint |= (byte & 0x7f) << self._shift
            self._shift += 7

            # if the most significant bit is set, there is another byte to read for this varint
            if not byte & 0x80:
                break


class ProtobufWireType(Enum):
    VARINT = 0
    FIXED_64_BIT = 1
    LENGTH_DELIMITED = 2
    FIXED_32_BIT = 5

    # start group and end group wire types are deprecated and not supported
    START_GROUP = 3
    END_GROUP = 4


@dataclass
class ProtobufParserFrame:
    field_number: int
    end_of_field_offset: Optional[int]


class ProtobufParserStack:

    _stack: List[ProtobufParserFrame]
    _field_path: str

    def __init__(self):
        self._stack = []
        self._field_path = ""

    @property
    def field_path(self) -> str:
        if not self._field_path:
            self._make_field_path()

        return self._field_path

    def push_frame(self, field_number: int, end_of_field_offset: Optional[int]) -> None:
        frame = ProtobufParserFrame(field_number=field_number, end_of_field_offset=end_of_field_offset)
        self._stack.append(frame)
        self._clear_field_path()

    def update_frame(self, end_of_field_offset: int) -> None:
        if not self._stack:
            raise RuntimeError("no stack frame to update")

        self._stack[-1].end_of_field_offset = end_of_field_offset

    def peek_frame(self) -> Optional[ProtobufParserFrame]:
        if not self._stack:
            return None

        return self._stack[-1]

    def pop_frame(self) -> ProtobufParserFrame:
        self._clear_field_path()
        return self._stack.pop()

    def _make_field_path(self) -> None:
        self._field_path = ":".join([str(frame.field_number) for frame in self._stack])

    def _clear_field_path(self) -> None:
        self._field_path = ""


class ProtobufParserMessageAction(Enum):
    SKIP = 0
    PARSE_AS_MESSAGE = 1
    PARSE_AS_BYTES = 2


class ProtobufParserCallback(ABC):

    @abstractmethod
    def on_length_delimited_field(self, field_number: int, field_path: str) -> ProtobufParserMessageAction:
        """
        Callback function to tell the protobuf parser how to act when it finds a
        length delimited field.
        """
        raise NotImplementedError()

    @abstractmethod
    def on_field(self, wire_type: ProtobufWireType, field_number: int, field_value: bytes, field_path: str) -> None:
        """
        Callback function when a new field that isn't a message is found.
        The value is passed as bytes and up to the user to determine how to decode it.
        The field_path is a colon delimited string of the field numbers this field is a child of.
        """
        raise NotImplementedError()


class CosmosTransactionFeeExtractor(ProtobufParserCallback):
    """
    A protobuf parser callback that extracts the fee for a transaction from the AuthInfo message object of the protobuf
    structure defined here: https://github.com/cosmos/cosmos-sdk/blob/main/proto/cosmos/tx/v1beta1/tx.proto.
    """

    coin_message_base_path: str = "2:2:1"
    coin_denom_path: str = f"{coin_message_base_path}:1"
    coin_amount_path: str = f"{coin_message_base_path}:2"

    _fee_denom: Optional[str]
    _fee_amount: Optional[str]

    def __init__(self):
        self._fee_denom = None
        self._fee_amount = None

    @property
    def fee_denom(self) -> Optional[str]:
        return self._fee_denom

    @property
    def fee_amount(self) -> Optional[str]:
        return self._fee_amount

    def on_length_delimited_field(self, field_number: int, field_path: str) -> ProtobufParserMessageAction:
        if not field_path:
            raise RuntimeError(f"unexpected empty field path while processing protobuf data")

        if field_path in (self.coin_denom_path, self.coin_amount_path):
            return ProtobufParserMessageAction.PARSE_AS_BYTES

        if self.coin_message_base_path.startswith(field_path):
            return ProtobufParserMessageAction.PARSE_AS_MESSAGE

        return ProtobufParserMessageAction.SKIP

    def on_field(self, wire_type: ProtobufWireType, field_number: int, field_value: bytes, field_path: str) -> None:
        if field_path == self.coin_denom_path:
            self._fee_denom = field_value.decode("utf-8")
        elif field_path == self.coin_amount_path:
            self._fee_amount = field_value.decode("utf-8")


class ProtobufParser:
    """
    A protobuf parser to parse protobuf data without a .proto file.
    Most useful to extract data when you know the .proto file the data is based on, but you don't want to load it
    into an application.

    Implements the encoding described here: https://developers.google.com/protocol-buffers/docs/encoding.
    """

    _buffer: io.BytesIO
    _buffer_size: int
    _callback: ProtobufParserCallback

    def __init__(self, protobuf_bytes: bytes, callback: ProtobufParserCallback):
        self._buffer = io.BytesIO(protobuf_bytes)
        self._buffer_size = len(protobuf_bytes)
        self._callback = callback

    def parse(self) -> None:
        parser_stack: ProtobufParserStack = ProtobufParserStack()
        while self._buffer.tell() < self._buffer_size:
            # get the next field key
            wire_type, field_number = self._get_field_key()

            # get the field value
            parser_stack.push_frame(field_number=field_number, end_of_field_offset=None)
            field_value, parse_embedded_message, embedded_message_length = self._get_field_value(wire_type, field_number, parser_stack)
            if parse_embedded_message:
                parser_stack.update_frame(end_of_field_offset=self._buffer.tell() + embedded_message_length)
                continue

            # callback the application with any values found
            if field_value is not None:
                self._callback.on_field(wire_type, field_number, field_value, parser_stack.field_path)

            # cleanup
            parser_stack.pop_frame()
            while frame := parser_stack.peek_frame():
                if frame.end_of_field_offset != self._buffer.tell():
                    break

                parser_stack.pop_frame()

    def _get_field_key(self) -> Tuple[ProtobufWireType, int]:
        field_key = self._read_varint().value

        wire_type = field_key & 0x07
        field_number = field_key >> 3

        return ProtobufWireType(wire_type), field_number

    def _get_field_value(self, wire_type: ProtobufWireType, field_number: int, parser_stack: ProtobufParserStack) -> Tuple[Optional[bytes], bool, int]:
        if wire_type == ProtobufWireType.START_GROUP or wire_type == ProtobufWireType.END_GROUP:
            raise NotImplementedError("The start and end group wire types are deprecated and not supported")

        parse_embedded_message = False
        embedded_message_length = None

        if wire_type == ProtobufWireType.VARINT:
            field_value = self._parse_varint_value()
        elif wire_type == ProtobufWireType.FIXED_64_BIT:
            field_value = self._parse_fixed_64_bit_value()
        elif wire_type == ProtobufWireType.LENGTH_DELIMITED:
            field_value, parse_embedded_message, embedded_message_length = self._parse_length_delimited_value(field_number, parser_stack)
        elif wire_type == ProtobufWireType.FIXED_32_BIT:
            field_value = self._parse_fixed_32_bit_value()
        else:
            raise RuntimeError(f"Unknown wire type found [{wire_type}")

        return field_value, parse_embedded_message, embedded_message_length

    def _parse_varint_value(self) -> bytes:
        varint = self._read_varint()
        return varint.value.to_bytes(varint.byte_size, "little")

    def _parse_length_delimited_value(self, field_number: int, parser_stack: ProtobufParserStack) -> Tuple[Optional[bytes], bool, int]:
        # get the length
        field_value_length = self._read_varint().value

        # see what the user wants us to do
        action = self._callback.on_length_delimited_field(field_number, parser_stack.field_path)

        # see if we should read the field_value
        field_value = None
        if action in [ProtobufParserMessageAction.SKIP, ProtobufParserMessageAction.PARSE_AS_BYTES]:
            temp_value = self._read_bytes(field_value_length)
            if action == ProtobufParserMessageAction.PARSE_AS_BYTES:
                field_value = temp_value

        return field_value, action == ProtobufParserMessageAction.PARSE_AS_MESSAGE, field_value_length

    def _parse_fixed_64_bit_value(self) -> bytes:
        return self._read_bytes(8)

    def _parse_fixed_32_bit_value(self) -> bytes:
        return self._read_bytes(4)

    def _read_varint(self) -> Varint:
        varint = Varint()
        varint.from_bytes(self._buffer)

        return varint

    def _read_bytes(self, size: int) -> bytes:
        bytes_read = self._buffer.read(size)
        if bytes_read == b"":
            raise EOFError("unexpected end of byte sequence while reading protobuf")

        return bytes_read
