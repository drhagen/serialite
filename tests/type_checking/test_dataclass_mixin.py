from dataclasses import dataclass
from typing import assert_type

from serialite import SerializableMixin, StringSerializer, field


@dataclass(frozen=True, kw_only=True, slots=True)
class UserProfile(SerializableMixin):
    age: int
    name: str = "anonymous"
    nickname: str = field(serializer=StringSerializer())


profile = UserProfile.from_data({"age": 30, "nickname": "ace"}).unwrap()
assert_type(profile, UserProfile)
assert_type(profile.age, int)
assert_type(profile.name, str)
assert_type(profile.nickname, str)
assert_type(profile.to_data(), dict)
