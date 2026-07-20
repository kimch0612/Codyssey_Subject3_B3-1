"""Redis-style command parsing, validation, and output formatting."""

import shlex

from mini_redis import OutOfMemoryError


class CommandProcessor:
    """Translate one input line into one MiniRedis operation."""

    INTEGER_ERROR = "(error) ERR value is not an integer or out of range"
    OOM_ERROR = "(error) OOM command not allowed when used_memory > 'maxmemory'"

    def __init__(self, redis):
        self.redis = redis

    def execute(self, line):
        """Execute one command and return its printable result."""
        try:
            arguments = shlex.split(line)
        except ValueError:
            return "(error) ERR syntax error"

        if not arguments:
            return None

        command = arguments[0].upper()
        try:
            if command == "SET":
                return self._set(arguments)
            if command == "GET":
                return self._get(arguments)
            if command == "DEL":
                return self._delete(arguments)
            if command == "EXISTS":
                return self._exists(arguments)
            if command == "DBSIZE":
                return self._dbsize(arguments)
            if command == "KEYS":
                return self._keys(arguments)
            if command == "CONFIG":
                return self._config(arguments)
            if command == "INFO":
                return self._info(arguments)
            if command == "EXPIRE":
                return self._expire(arguments)
            if command == "TTL":
                return self._ttl(arguments)
        except OutOfMemoryError:
            return self.OOM_ERROR

        return "(error) ERR unknown command '{}'".format(arguments[0])

    def _set(self, arguments):
        if len(arguments) != 3:
            return self._wrong_arguments("SET")
        self.redis.set(arguments[1], arguments[2])
        return "OK"

    def _get(self, arguments):
        if len(arguments) != 2:
            return self._wrong_arguments("GET")
        value = self.redis.get(arguments[1])
        if value is None:
            return "(nil)"
        return self._quote(value)

    def _delete(self, arguments):
        if len(arguments) != 2:
            return self._wrong_arguments("DEL")
        return self._integer(1 if self.redis.delete(arguments[1]) else 0)

    def _exists(self, arguments):
        if len(arguments) != 2:
            return self._wrong_arguments("EXISTS")
        return self._integer(1 if self.redis.exists(arguments[1]) else 0)

    def _dbsize(self, arguments):
        if len(arguments) != 1:
            return self._wrong_arguments("DBSIZE")
        return self._integer(self.redis.dbsize())

    def _keys(self, arguments):
        if len(arguments) != 1:
            return self._wrong_arguments("KEYS")
        keys = self.redis.keys()
        if not keys:
            return "(empty array)"
        return "\n".join(self._quote(key) for key in keys)

    def _config(self, arguments):
        if len(arguments) != 4:
            return self._wrong_arguments("CONFIG")
        if arguments[1].upper() != "SET" or arguments[2].lower() != "maxmemory":
            return "(error) ERR syntax error"

        byte_limit = self._parse_integer(arguments[3])
        if byte_limit is None or byte_limit < 0:
            return self.INTEGER_ERROR
        self.redis.config_set_maxmemory(byte_limit)
        return "OK"

    def _info(self, arguments):
        if len(arguments) != 2:
            return self._wrong_arguments("INFO")
        if arguments[1].lower() != "memory":
            return "(error) ERR syntax error"

        used_memory, maxmemory, evicted_keys = self.redis.info_memory()
        return "\n".join(
            (
                "used_memory:{}".format(used_memory),
                "maxmemory:{}".format(maxmemory),
                "evicted_keys:{}".format(evicted_keys),
            )
        )

    def _expire(self, arguments):
        if len(arguments) != 3:
            return self._wrong_arguments("EXPIRE")
        seconds = self._parse_integer(arguments[2])
        if seconds is None:
            return self.INTEGER_ERROR
        return self._integer(1 if self.redis.expire(arguments[1], seconds) else 0)

    def _ttl(self, arguments):
        if len(arguments) != 2:
            return self._wrong_arguments("TTL")
        return self._integer(self.redis.ttl(arguments[1]))

    @staticmethod
    def _parse_integer(value):
        try:
            return int(value, 10)
        except ValueError:
            return None

    @staticmethod
    def _integer(value):
        return "(integer) {}".format(value)

    @staticmethod
    def _quote(value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return '"{}"'.format(escaped)

    @staticmethod
    def _wrong_arguments(command):
        return "(error) ERR wrong number of arguments for '{}' command".format(
            command
        )

