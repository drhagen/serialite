from dataclasses import dataclass
from typing import assert_type

from serialite import Errors, Result, Serializable, StringSerializer, field, serializable


@serializable
@dataclass(frozen=True, kw_only=True, slots=True)
class UserProfile(Serializable):
    age: int
    name: str = "anonymous"
    nickname: str = field(serializer=StringSerializer())


# Success
result = UserProfile.from_data({"age": 30, "nickname": "ace"})
assert_type(result, Result[UserProfile])

profile = result.unwrap()
assert_type(profile, UserProfile)
assert_type(profile.age, int)
assert_type(profile.name, str)
assert_type(profile.nickname, str)

# Failure
result = UserProfile.from_data({})
assert_type(result, Result[UserProfile])

errors = result.failure()
assert_type(errors, Errors)


@serializable(hide_default=False)
@dataclass(frozen=True, kw_only=True, slots=True)
class ShownDefaults(Serializable):
    age: int
    name: str = "anonymous"


shown = ShownDefaults.from_data({"age": 30})
assert_type(shown, Result[ShownDefaults])
assert_type(shown.unwrap(), ShownDefaults)
assert_type(shown.unwrap().name, str)


@serializable()
@dataclass(frozen=True, kw_only=True, slots=True)
class EmptyParens(Serializable):
    age: int


assert_type(EmptyParens.from_data({"age": 30}).unwrap(), EmptyParens)
