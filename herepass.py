"""
Copyright (c) 2022 Nader G. Zeid

This file is part of HerePass.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with HerePass. If not, see <https://www.gnu.org/licenses/gpl.html>.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from typing import Literal, Optional, Union

import ujson
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes
from pydantic import BaseModel, Extra, Field, StrictBytes, constr

herepass_version = "1.0.0"


class ConfiguredModel(BaseModel):
    class Config:
        validate_assignment = True
        extra = Extra.forbid
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prepare()

    def prepare(self):
        pass

    def has_sync(self, attribute):
        pass

    def get_sync(self, attribute):
        pass

    def set_sync(self, attribute):
        pass

    def has(self, attribute):
        output = hasattr(self, attribute)
        self.has_sync(attribute)
        return output

    def get(self, attribute):
        output = getattr(self, attribute)
        self.get_sync(attribute)
        return output

    def set(self, attribute, value):
        setattr(self, attribute, value)
        self.set_sync(attribute)
        return getattr(self, attribute)


class Scrypt(ConfiguredModel):
    passphrase: StrictBytes
    salt: StrictBytes
    key_length: Literal[32] = 32
    cost: Literal[1048576] = 1048576  # 2^20
    block_size: Literal[8] = 8
    parallelization: Literal[1] = 1
    key: Optional[StrictBytes]

    def on_change(self):
        self.key = scrypt(
            self.passphrase,
            self.salt,
            self.key_length,
            self.cost,
            self.block_size,
            self.parallelization,
        )

    def prepare(self):
        self.on_change()

    def set_sync(self, attribute):
        self.on_change()


class AESGCM(ConfiguredModel):
    key_derivation: Scrypt
    nonce: StrictBytes = Field(..., min_length=16, max_length=16)
    mac_length: Literal[16] = 16
    decrypted: Optional[StrictBytes]
    encrypted: Optional[StrictBytes]
    digest: Optional[StrictBytes]

    def on_change(self):
        if self.decrypted is None:
            if self.digest is None:
                raise TypeError("Missing digest!")
            if self.encrypted is None:
                raise TypeError("Missing encrypted!")
            cipher = AES.new(
                self.key_derivation.key,
                AES.MODE_GCM,
                nonce=self.nonce,
                mac_len=self.mac_length,
            )
            self.decrypted = cipher.decrypt_and_verify(self.encrypted, self.digest)
        else:
            if self.decrypted is None:
                raise TypeError("Missing decrypted!")
            cipher = AES.new(
                self.key_derivation.key,
                AES.MODE_GCM,
                nonce=self.nonce,
                mac_len=self.mac_length,
            )
            output = cipher.encrypt_and_digest(self.decrypted)
            self.encrypted = output[0]
            self.digest = output[1]

    def prepare(self):
        self.on_change()

    def set_sync(self, attribute):
        self.on_change()


class GroupListener(ABC):
    @abstractmethod
    def sync(self):
        pass


def group_cascade_listener(data):
    if data.listener and isinstance(data, Group):
        sets_of_entries = [data.entries]
        while sets_of_entries:
            current_entries = sets_of_entries.pop()
            for i in current_entries:
                i.listener = data.listener
                if isinstance(i, Group):
                    sets_of_entries.append(i.entries)


def group_cascade_delete(data):
    if isinstance(data, Group):
        sets_of_entries = [data.entries]
        while sets_of_entries:
            current_entries = sets_of_entries.pop()
            for i in current_entries:
                i.deleted = data.deleted
                if isinstance(i, Group):
                    sets_of_entries.append(i.entries)


def group_prepare(data):
    right_now = datetime.now(timezone.utc)
    if not data.created:
        data.created = right_now
    if not data.updated:
        data.updated = right_now
    group_cascade_listener(data)


def matches_phrase(search_words, words):
    for search_word in search_words:
        assert type(search_word) is str
        missing = True
        for word in words:
            assert type(word) is str
            if word.startswith(search_word):
                missing = False
                break
        if missing:
            return False
    return True


def group_set_sync(data, attribute):
    if attribute == "listener":
        group_cascade_listener(data)
    else:
        data.updated = datetime.now(timezone.utc)
        if attribute == "deleted":
            group_cascade_delete(data)
    if data.listener:
        data.listener.sync()


class Entry(ConfiguredModel):
    label: constr(strict=True, min_length=1)
    content: constr(strict=True, min_length=1)
    secret: bool
    created: Optional[datetime]
    updated: Optional[datetime]
    deleted: Optional[datetime]
    listener: Optional[GroupListener]

    def prepare(self):
        group_prepare(self)

    def set_sync(self, attribute):
        group_set_sync(self, attribute)

    def get_key(self):
        deleted_code = "1" if self.deleted else "0"
        type_code = "0"
        secret_code = "1" if self.secret else "0"
        return deleted_code + ":" + type_code + ":" + secret_code + ":" + self.label

    def portable_dict(self):
        output = self.dict()
        del output["listener"]
        if output["created"]:
            output["created"] = output["created"].isoformat()
        if output["updated"]:
            output["updated"] = output["updated"].isoformat()
        if output["deleted"]:
            output["deleted"] = output["deleted"].isoformat()
        return output


class Group(ConfiguredModel):
    label: constr(strict=True, min_length=1)
    description: Optional[constr(strict=True, min_length=1)]
    created: Optional[datetime]
    updated: Optional[datetime]
    deleted: Optional[datetime]
    listener: Optional[GroupListener]
    entries: list[Union[Group, Entry]]

    def prepare(self):
        group_prepare(self)

    def set_sync(self, attribute):
        group_set_sync(self, attribute)

    def add_group(self, label, description):
        new_group = Group(label=label, description=description, entries=[])
        self.entries.append(new_group)
        self.set_sync("listener")
        return new_group

    def add_entry(self, label, content, secret):
        new_entry = Entry(label=label, content=content, secret=secret)
        self.entries.append(new_entry)
        self.set_sync("listener")
        return new_entry

    def get_key(self):
        deleted_code = "1" if self.deleted else "0"
        type_code = "1"
        secret_code = "0"
        return deleted_code + ":" + type_code + ":" + secret_code + ":" + self.label

    def sort_entries(self):
        self.entries.sort(key=lambda entry: entry.get_key())
        for entry in self.entries:
            if isinstance(entry, Group):
                entry.sort_entries()

    def search(self, search_phrase):
        search_words = search_phrase.lower().split()
        output = []
        for entry in self.entries:
            if isinstance(entry, Group):
                suboutput = entry.search(search_phrase)
                for matched in suboutput:
                    matched.insert(0, self)
                output.extend(suboutput)
        words = self.label.lower().split()
        if matches_phrase(search_words, words):
            output.append([self])
        elif self.description:
            words = self.description.lower().split()
            if matches_phrase(search_words, words):
                output.append([self])
        return output

    def purge_deleted(self, seconds_ago, current_time=None):
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        i = 0
        skip_to = 0
        leng = len(self.entries)
        while i < leng:
            if skip_to > i:
                self.entries[i], self.entries[skip_to] = (
                    self.entries[skip_to],
                    self.entries[i],
                )
            deleted_at = self.entries[i].deleted
            if deleted_at:
                deleted_for = (current_time - deleted_at).total_seconds()
                if deleted_for > seconds_ago:
                    skip_to += 1
                    leng -= 1
                    continue
            if isinstance(self.entries[i], Group):
                self.entries[i].purge_deleted(seconds_ago, current_time)
            i += 1
            skip_to += 1
        if i != skip_to:
            leng = i - skip_to
            del self.entries[leng:]

    def portable_dict(self):
        output = self.dict()
        del output["listener"]
        if output["created"]:
            output["created"] = output["created"].isoformat()
        if output["updated"]:
            output["updated"] = output["updated"].isoformat()
        if output["deleted"]:
            output["deleted"] = output["deleted"].isoformat()
        sets_of_entries = [output["entries"]]
        while sets_of_entries:
            current_entries = sets_of_entries.pop()
            for i in current_entries:
                del i["listener"]
                if i["created"]:
                    i["created"] = i["created"].isoformat()
                if i["updated"]:
                    i["updated"] = i["updated"].isoformat()
                if i["deleted"]:
                    i["deleted"] = i["deleted"].isoformat()
                if "entries" in i:
                    sets_of_entries.append(i["entries"])
        return output


class HerePass(GroupListener):
    # self.group
    # self.encrypter

    def create(self, passphrase):
        self.group = Group(label="New", entries=[], listener=self)
        salt = get_random_bytes(16)
        key_derivation = Scrypt(passphrase=passphrase.encode("utf-8"), salt=salt)
        nonce = get_random_bytes(16)
        self.encrypter = AESGCM(
            key_derivation=key_derivation,
            nonce=nonce,
            decrypted=ujson.dumps(self.group.portable_dict()).encode(),
        )

    def sync(self):
        self.group.purge_deleted(86400)
        self.group.sort_entries()
        self.encrypter.set(
            "decrypted", ujson.dumps(self.group.portable_dict()).encode()
        )

    def to_encrypted_json(self):
        encrypter = self.encrypter
        nonce = get_random_bytes(16)
        encrypter.set("nonce", nonce)
        key_derivation = encrypter.get("key_derivation")
        kd_dict = {"class": type(key_derivation).__name__}
        if key_derivation.has("salt"):
            kd_dict["salt"] = b64encode(key_derivation.get("salt")).decode("utf-8")
        if key_derivation.has("key_length"):
            kd_dict["key_length"] = key_derivation.get("key_length")
        if key_derivation.has("cost"):
            kd_dict["cost"] = key_derivation.get("cost")
        if key_derivation.has("block_size"):
            kd_dict["block_size"] = key_derivation.get("block_size")
        if key_derivation.has("parallelization"):
            kd_dict["parallelization"] = key_derivation.get("parallelization")
        en_dict = {"class": type(encrypter).__name__, "key_derivation": kd_dict}
        if encrypter.has("nonce"):
            en_dict["nonce"] = b64encode(encrypter.get("nonce")).decode("utf-8")
        if encrypter.has("mac_length"):
            en_dict["mac_length"] = encrypter.get("mac_length")
        if encrypter.has("digest"):
            en_dict["digest"] = b64encode(encrypter.get("digest")).decode("utf-8")
        if encrypter.has("encrypted"):
            en_dict["encrypted"] = b64encode(encrypter.get("encrypted")).decode("utf-8")
        data = {"encrypter": en_dict}
        return ujson.dumps(data).encode()

    def from_encrypted_json(self, passphrase, data):
        assert type(passphrase) is str
        data = ujson.loads(data)
        assert type(data) is dict
        encrypter = data["encrypter"]
        class_map = {"Scrypt": Scrypt, "AESGCM": AESGCM}
        b64_list = [
            "salt",
            "nonce",
            "digest",
            "encrypted",
        ]
        key_derivation = encrypter["key_derivation"]
        encrypter["key_derivation"] = None
        key_derivation_class = class_map[key_derivation.pop("class")]
        encrypter_class = class_map[encrypter.pop("class")]
        encrypter.pop("key_derivation")
        for b64_key in b64_list:
            for key in encrypter:
                if key == b64_key:
                    encrypter[key] = b64decode(encrypter[key])
            for key in key_derivation:
                if key == b64_key:
                    key_derivation[key] = b64decode(key_derivation[key])
        key_derivation["passphrase"] = passphrase.encode("utf-8")
        encrypter["key_derivation"] = key_derivation_class.parse_obj(key_derivation)
        self.encrypter = encrypter_class.parse_obj(encrypter)
        data.clear()
        group = ujson.loads(self.encrypter.get("decrypted"))
        assert isinstance(group, dict)
        group["listener"] = self
        self.group = Group.parse_obj(group)
