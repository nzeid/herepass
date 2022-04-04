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

from base64 import b64encode
from datetime import datetime, timedelta, timezone

import pytest
import ujson
from Crypto.Random import get_random_bytes

from herepass import (
    AESGCM,
    ConfiguredModel,
    Entry,
    Group,
    GroupListener,
    HerePass,
    Scrypt,
)


@pytest.fixture
def passphrase_bytes_1():
    return b64encode(get_random_bytes(10))


@pytest.fixture
def passphrase_1(passphrase_bytes_1):
    return passphrase_bytes_1.decode("utf-8")


@pytest.fixture
def passphrase_bytes_2():
    # Length 11 so as never to match passphrase_bytes_1:
    return b64encode(get_random_bytes(11))


@pytest.fixture
def passphrase_2(passphrase_bytes_2):
    return passphrase_bytes_2.decode("utf-8")


@pytest.fixture
def salt16():
    return get_random_bytes(16)


@pytest.fixture
def scrypt(passphrase_bytes_1, salt16):
    return Scrypt(passphrase=passphrase_bytes_1, salt=salt16)


@pytest.fixture
def nonce16():
    return get_random_bytes(16)


@pytest.fixture
def encrypt_this_1():
    return get_random_bytes(50)


@pytest.fixture
def encrypt_this_2():
    # Length 51 so as never to match encrypt_this_1:
    return get_random_bytes(51)


def test_configured_model():
    class TestModel(ConfiguredModel):
        prepared: bool = False
        has_synced: bool = False
        get_synced: bool = False
        set_synced: bool = False

        def prepare(self):
            self.prepared = True

        def has_sync(self, attribute):
            self.has_synced = True

        def get_sync(self, attribute):
            self.get_synced = True

        def set_sync(self, attribute):
            self.set_synced = True

    test_model = TestModel()
    assert test_model.prepared
    assert not test_model.has_synced
    assert not test_model.get_synced
    assert not test_model.set_synced
    test_model.has("prepared")
    assert test_model.prepared
    assert test_model.has_synced
    assert not test_model.get_synced
    assert not test_model.set_synced
    test_model.get("prepared")
    assert test_model.prepared
    assert test_model.has_synced
    assert test_model.get_synced
    assert not test_model.set_synced
    test_model.set("prepared", False)
    assert not test_model.prepared
    assert test_model.has_synced
    assert test_model.get_synced
    assert test_model.set_synced


def test_scrypt(passphrase_bytes_1, passphrase_bytes_2, salt16, scrypt):
    scrypt1 = Scrypt.parse_obj({"passphrase": passphrase_bytes_1, "salt": salt16})
    scrypt2 = Scrypt(
        passphrase=passphrase_bytes_1,
        salt=salt16,
        key_length=32,
        cost=1048576,
        block_size=8,
        parallelization=1,
    )
    scrypt3 = Scrypt.parse_obj(
        {
            "passphrase": passphrase_bytes_1,
            "salt": salt16,
            "key_length": 32,
            "cost": 1048576,
            "block_size": 8,
            "parallelization": 1,
        }
    )
    assert scrypt.get("key") == scrypt1.get("key")
    assert scrypt.get("key") == scrypt2.get("key")
    assert scrypt.get("key") == scrypt3.get("key")
    scrypt1.set("passphrase", passphrase_bytes_2)
    assert scrypt.get("key") != scrypt1.get("key")
    scrypt2.set("passphrase", passphrase_bytes_2)
    assert scrypt.get("key") != scrypt2.get("key")
    assert scrypt1.get("key") == scrypt2.get("key")


def test_aesgcm(scrypt, nonce16, encrypt_this_1, encrypt_this_2):
    en1 = AESGCM(key_derivation=scrypt, nonce=nonce16, decrypted=encrypt_this_1)
    en2 = AESGCM.parse_obj(
        {"key_derivation": scrypt, "nonce": nonce16, "decrypted": encrypt_this_1}
    )
    en3 = AESGCM(
        key_derivation=scrypt, nonce=nonce16, mac_length=16, decrypted=encrypt_this_1
    )
    en4 = AESGCM.parse_obj(
        {
            "key_derivation": scrypt,
            "nonce": nonce16,
            "mac_length": 16,
            "decrypted": encrypt_this_1,
        }
    )
    encrypted = en1.get("encrypted")
    digest = en1.get("digest")
    assert encrypted == en2.get("encrypted")
    assert digest == en2.get("digest")
    assert encrypted == en3.get("encrypted")
    assert digest == en3.get("digest")
    assert encrypted == en4.get("encrypted")
    assert digest == en4.get("digest")
    en5 = AESGCM(
        key_derivation=scrypt, nonce=nonce16, encrypted=encrypted, digest=digest
    )
    en6 = AESGCM.parse_obj(
        {
            "key_derivation": scrypt,
            "nonce": nonce16,
            "encrypted": encrypted,
            "digest": digest,
        }
    )
    en7 = AESGCM(
        key_derivation=scrypt,
        nonce=nonce16,
        mac_length=16,
        encrypted=encrypted,
        digest=digest,
    )
    en8 = AESGCM.parse_obj(
        {
            "key_derivation": scrypt,
            "nonce": nonce16,
            "mac_length": 16,
            "encrypted": encrypted,
            "digest": digest,
        }
    )
    assert en5.get("decrypted") == encrypt_this_1
    assert en6.get("decrypted") == encrypt_this_1
    assert en7.get("decrypted") == encrypt_this_1
    assert en8.get("decrypted") == encrypt_this_1
    en1.set("decrypted", encrypt_this_2)
    assert encrypted != en1.get("encrypted")
    en2.set("decrypted", encrypt_this_2)
    assert encrypted != en2.get("encrypted")
    assert en1.get("encrypted") == en2.get("encrypted")
    assert en1.get("digest") == en2.get("digest")


def test_group():
    class TestHandler(GroupListener):
        def __init__(self):
            self.count = 0

        def sync(self):
            self.count += 1

    th = TestHandler()
    right_now = datetime.now(timezone.utc)
    en1 = Entry(label="enl1", content="ens1", secret=True)
    en2 = Entry(label="enl2", content="ens2", secret=False, listener=th)
    en3 = Entry.parse_obj({"label": "enl3", "content": "ens3", "secret": True})
    en4 = Entry.parse_obj(
        {"label": "enl4", "content": "ens4", "secret": False, "listener": th}
    )
    assert th.count == 0
    assert (
        en1.get("label") == "enl1"
        and en1.get("content") == "ens1"
        and en1.get("secret") is True
    )
    assert en1.get("created") > right_now and en1.get("created") == en1.get("updated")
    assert (
        en2.get("label") == "enl2"
        and en2.get("content") == "ens2"
        and en2.get("secret") is False
        and en2.get("listener") == th
    )
    assert en2.get("created") > right_now and en2.get("created") == en2.get("updated")
    assert (
        en3.get("label") == "enl3"
        and en3.get("content") == "ens3"
        and en3.get("secret") is True
    )
    assert en3.get("created") > right_now and en3.get("created") == en3.get("updated")
    assert (
        en4.get("label") == "enl4"
        and en4.get("content") == "ens4"
        and en4.get("secret") is False
        and en4.get("listener") == th
    )
    assert en4.get("created") > right_now and en4.get("created") == en4.get("updated")
    en1.set("label", "enl1_s")
    assert th.count == 0
    assert en1.get("label") == "enl1_s"
    assert en1.get("created") < en1.get("updated")
    en2.set("content", "ens1_s")
    assert th.count == 1
    assert en2.get("content") == "ens1_s"
    assert en2.get("created") < en2.get("updated")
    en3.set("secret", False)
    assert th.count == 1
    assert en3.get("secret") is False
    assert en3.get("created") < en3.get("updated")
    right_now = datetime.now(timezone.utc)
    gr1 = Group(label="grl1", description="gro1", entries=[])
    assert th.count == 1
    assert (
        gr1.get("label") == "grl1"
        and gr1.get("description") == "gro1"
        and len(gr1.get("entries")) == 0
    )
    assert gr1.get("created") > right_now and gr1.get("created") == gr1.get("updated")
    gr1.set("label", "grl1_s")
    assert th.count == 1
    assert gr1.get("label") == "grl1_s"
    assert gr1.get("created") < gr1.get("updated")
    gr2 = Group(label="grl2", listener=th, entries=[gr1])
    assert th.count == 1
    assert (
        gr2.get("label") == "grl2"
        and gr2.get("description") is None
        and len(gr2.get("entries")) == 1
    )
    assert gr2.get("created") > right_now and gr2.get("created") == gr2.get("updated")
    assert ujson.dumps(gr2.get("entries")[0].portable_dict()) == ujson.dumps(
        gr1.portable_dict()
    )
    # So... Pydantic does some kind of shallow copy on these nested
    # containers so you gotta be careful.
    assert gr2.get("entries")[0].get("listener") == th
    right_now = datetime.now(timezone.utc)
    gr3 = Group.parse_obj(
        {
            "label": "grl3_1",
            "listener": th,
            "entries": [
                {
                    "label": "grl3_2",
                    "description": "gro3_2",
                    "entries": [
                        {"label": "grl3_3", "content": "grs3_3", "secret": True}
                    ],
                }
            ],
        }
    )
    assert th.count == 1
    gr3_2 = gr3.get("entries")[0]
    assert gr3_2.get("label") == "grl3_2" and gr3_2.get("description") == "gro3_2"
    assert gr3_2.get("created") > right_now and gr3_2.get("created") == gr3_2.get(
        "updated"
    )
    assert gr3_2.get("listener") == th
    gr3_3 = gr3.get("entries")[0].get("entries")[0]
    assert gr3_3.get("label") == "grl3_3" and gr3_3.get("content") == "grs3_3"
    assert gr3_3.get("created") > right_now and gr3_3.get("created") == gr3_3.get(
        "updated"
    )
    assert gr3_3.get("listener") == th
    gr3_2.set("description", "gro3_2_s")
    assert th.count == 2
    assert gr3_2.get("description") == "gro3_2_s"
    assert gr3_2.get("created") < gr3_2.get("updated")
    right_now = datetime.now(timezone.utc)
    gr3_4 = gr3.add_group("grl3_4", "gro3_4")
    assert th.count == 3
    len(gr3.get("entries")) == 2
    assert gr3.get("created") == gr3.get("updated")
    assert (
        gr3_4.get("label") == "grl3_4"
        and gr3_4.get("description") == "gro3_4"
        and len(gr3_4.get("entries")) == 0
    )
    assert gr3_4.get("created") > right_now and gr3_4.get("created") == gr3_4.get(
        "updated"
    )
    assert ujson.dumps(gr3.get("entries")[1].portable_dict()) == ujson.dumps(
        gr3_4.portable_dict()
    )
    assert gr3.get("entries")[1].get("listener") == th
    grc3_2 = gr3_2.get("created")
    gru3_2 = gr3_2.get("updated")
    right_now = datetime.now(timezone.utc)
    gr3_5 = gr3_2.add_entry("grl3_5", "grs3_5", False)
    len(gr3_2.get("entries")) == 2
    assert th.count == 4
    assert gr3_2.get("created") == grc3_2 and gr3_2.get("updated") == gru3_2
    assert (
        gr3_5.get("label") == "grl3_5"
        and gr3_5.get("content") == "grs3_5"
        and gr3_5.get("secret") is False
    )
    assert gr3_5.get("created") > right_now and gr3_5.get("created") == gr3_5.get(
        "updated"
    )
    assert ujson.dumps(
        gr3.get("entries")[0].get("entries")[1].portable_dict()
    ) == ujson.dumps(gr3_5.portable_dict())
    assert gr3.get("entries")[0].get("entries")[1].get("listener") == th
    gr3.get("entries")[0].get("entries")[1].set("deleted", True)
    assert th.count == 5
    assert not gr3_2.get("deleted")
    assert gr3_2.get("created") == grc3_2 and gr3_2.get("updated") == gru3_2
    assert gr3_5.get("created") < gr3_5.get("updated")
    assert not gr3.get("deleted")
    assert not gr3_2.get("deleted")
    assert not gr3_3.get("deleted")
    assert not gr3_4.get("deleted")
    assert gr3_5.get("deleted")
    grc3_4 = gr3_4.get("created")
    gru3_4 = gr3_4.get("updated")
    gr3.set("deleted", True)
    assert th.count == 6
    assert gr3.get("created") < gr3.get("updated")
    assert gr3_4.get("created") == grc3_4
    assert gr3_4.get("updated") == gru3_4
    assert gr3.get("deleted")
    assert gr3_2.get("deleted")
    assert gr3_3.get("deleted")
    assert gr3_4.get("deleted")
    assert gr3_5.get("deleted")
    # Sorting:
    grs1 = Group.parse_obj(
        {
            "label": "grs1",
            "description": "grs1_d",
            "entries": [
                {
                    "label": "grs3",
                    "description": "grs3_d",
                    "entries": [
                        {"label": "en2", "content": "en2_c", "secret": True},
                        {"label": "en1", "content": "en1_c", "secret": True},
                        {"label": "en1", "content": "en1_c", "secret": False},
                    ],
                },
                {
                    "label": "grs2",
                    "description": "grs2_d",
                    "entries": [],
                    "deleted": right_now,
                },
                {
                    "label": "grs2",
                    "description": "grs2_d",
                    "entries": [],
                },
                {"label": "en3", "content": "en3_c", "secret": True},
                {"label": "en3", "content": "en3_c", "secret": False},
                {"label": "en2", "content": "en2_c", "secret": False},
            ],
        }
    )
    grs1.sort_entries()
    grs1 = grs1.portable_dict()
    all_entries = [grs1]
    while all_entries:
        current_entry = all_entries.pop()
        del current_entry["created"]
        del current_entry["updated"]
        if current_entry["deleted"]:
            current_entry["deleted"] = "deleted"
        if "entries" in current_entry:
            all_entries += current_entry["entries"]
    # The sorted result:
    grs1_r = {
        "label": "grs1",
        "description": "grs1_d",
        "deleted": None,
        "entries": [
            {"label": "en2", "content": "en2_c", "secret": False, "deleted": None},
            {"label": "en3", "content": "en3_c", "secret": False, "deleted": None},
            {"label": "en3", "content": "en3_c", "secret": True, "deleted": None},
            {"label": "grs2", "description": "grs2_d", "deleted": None, "entries": []},
            {
                "label": "grs3",
                "description": "grs3_d",
                "deleted": None,
                "entries": [
                    {
                        "label": "en1",
                        "content": "en1_c",
                        "secret": False,
                        "deleted": None,
                    },
                    {
                        "label": "en1",
                        "content": "en1_c",
                        "secret": True,
                        "deleted": None,
                    },
                    {
                        "label": "en2",
                        "content": "en2_c",
                        "secret": True,
                        "deleted": None,
                    },
                ],
            },
            {
                "label": "grs2",
                "description": "grs2_d",
                "deleted": "deleted",
                "entries": [],
            },
        ],
    }
    assert ujson.dumps(grs1) == ujson.dumps(grs1_r)


def test_group_search():
    test_group = Group.parse_obj(
        {
            "label": "First Second",
            "description": "Third Fourth",
            "entries": [
                {
                    "label": "Fifth Sixth",
                    "description": "Seventh Eighth",
                    "entries": [
                        {"label": "en2", "content": "en2_c", "secret": True},
                        {"label": "en1", "content": "en1_c", "secret": True},
                        {"label": "en1", "content": "en1_c", "secret": False},
                    ],
                },
                {
                    "label": "Thirteenth Fourteenth",
                    "description": "Fifteenth Sixteenth",
                    "entries": [
                        {
                            "label": "Ninth Tenth",
                            "description": "Eleventh Twelfth",
                            "entries": [],
                        }
                    ],
                },
                {"label": "Element Twice", "entries": []},
                {"label": "en3", "content": "en3_c", "secret": False},
                {"label": "en2", "content": "en2_c", "secret": False},
            ],
        }
    )
    first = test_group.search("fif six")
    assert len(first) == 2
    assert len(first[0]) == 2
    assert first[0][0] == test_group
    assert first[0][1] == test_group.entries[0]
    assert len(first[1]) == 2
    assert first[1][0] == test_group
    assert first[1][1] == test_group.entries[1]
    second = test_group.search("thir four")
    assert len(second) == 2
    assert len(second[0]) == 2
    assert second[0][0] == test_group
    assert second[0][1] == test_group.entries[1]
    assert len(second[1]) == 1
    assert second[1][0] == test_group
    third = test_group.search("el tw")
    assert len(third) == 2
    assert len(third[0]) == 3
    assert third[0][0] == test_group
    assert third[0][1] == test_group.entries[1]
    assert third[0][2] == test_group.entries[1].entries[0]
    assert len(third[1]) == 2
    assert third[1][0] == test_group
    assert third[1][1] == test_group.entries[2]
    fourth = test_group.search("el w")
    assert len(fourth) == 0
    fifth = test_group.search("n")
    assert len(fifth) == 1
    assert len(fifth[0]) == 3
    assert fifth[0][0] == test_group
    assert fifth[0][1] == test_group.entries[1]
    assert fifth[0][2] == test_group.entries[1].entries[0]
    sixth = test_group.search("for")
    assert len(sixth) == 0


def test_purge_deleted():
    test_group = Group.parse_obj(
        {
            "label": "First Second",
            "description": "Third Fourth",
            "entries": [
                {
                    "label": "Fifth Sixth",
                    "description": "Seventh Eighth",
                    "entries": [
                        {"label": "en2", "content": "en2_c", "secret": True},
                        {"label": "en1", "content": "en1_c", "secret": True},
                        {"label": "en1", "content": "en1_c", "secret": False},
                    ],
                },
                {
                    "label": "Thirteenth Fourteenth",
                    "description": "Fifteenth Sixteenth",
                    "entries": [
                        {
                            "label": "Ninth Tenth",
                            "description": "Eleventh Twelfth",
                            "entries": [],
                        }
                    ],
                },
                {"label": "Element Twice", "entries": []},
                {"label": "en3", "content": "en3_c", "secret": False},
                {"label": "en2", "content": "en2_c", "secret": False},
            ],
        }
    )
    changed_group = test_group.portable_dict()
    # Delete an entry and a subgroup:
    test_group.entries[3].set(
        "deleted", datetime.now(timezone.utc) - timedelta(seconds=6)
    )
    del changed_group["entries"][3]
    test_group.entries[1].set(
        "deleted", datetime.now(timezone.utc) - timedelta(seconds=7)
    )
    del changed_group["entries"][1]
    test_group.purge_deleted(4)
    assert ujson.dumps(test_group.portable_dict()) == ujson.dumps(changed_group)
    # Delete an entry:
    test_group.entries[0].entries[1].set(
        "deleted", datetime.now(timezone.utc) - timedelta(seconds=3)
    )
    test_group.purge_deleted(1)
    del changed_group["entries"][0]["entries"][1]
    assert ujson.dumps(test_group.portable_dict()) == ujson.dumps(changed_group)
    # Don't delete if it hasn't been long enough:
    test_group.entries[0].entries[1].set(
        "deleted", datetime.now(timezone.utc) - timedelta(seconds=1)
    )
    test_group.purge_deleted(3)
    changed_group["entries"][0]["entries"][1]["updated"] = (
        test_group.entries[0].entries[1].get("updated").isoformat()
    )
    changed_group["entries"][0]["entries"][1]["deleted"] = (
        test_group.entries[0].entries[1].get("deleted").isoformat()
    )
    assert ujson.dumps(test_group.portable_dict()) == ujson.dumps(changed_group)


def test_storage_handler(passphrase_1, scrypt, nonce16, encrypt_this_1):
    sh1 = HerePass()
    sh1.create(passphrase_1)
    sh1_g1 = ujson.dumps(sh1.group.portable_dict()).encode()
    sh1_n1 = sh1.encrypter.get("nonce")
    sh1_d1 = sh1.encrypter.get("digest")
    sh1_e1 = sh1.encrypter.get("encrypted")
    sh1_ej1 = sh1.to_encrypted_json()
    sh1.from_encrypted_json(passphrase_1, sh1_ej1)
    sh1_g2 = ujson.dumps(sh1.group.portable_dict()).encode()
    sh1_n2 = sh1.encrypter.get("nonce")
    sh1_d2 = sh1.encrypter.get("digest")
    sh1_e2 = sh1.encrypter.get("encrypted")
    assert sh1_g1 == sh1_g2
    assert sh1_n1 != sh1_n2
    assert sh1_d1 != sh1_d2
    assert sh1_e1 != sh1_e2
    sh2 = HerePass()
    sh2.from_encrypted_json(passphrase_1, sh1_ej1)
    sh2_g1 = ujson.dumps(sh2.group.portable_dict()).encode()
    sh2_n1 = sh2.encrypter.get("nonce")
    sh2_d1 = sh2.encrypter.get("digest")
    sh2_e1 = sh2.encrypter.get("encrypted")
    assert sh1_g1 == sh2_g1
    assert sh1_n1 != sh2_n1
    assert sh1_d1 != sh2_d1
    assert sh1_e1 != sh2_e1
    sh1.group.set("description", "test_od")
    sh1_g3 = ujson.dumps(sh1.group.portable_dict()).encode()
    sh1_n3 = sh1.encrypter.get("nonce")
    sh1_d3 = sh1.encrypter.get("digest")
    sh1_e3 = sh1.encrypter.get("encrypted")
    assert sh1_n3 == sh1_n2
    assert sh1_d3 != sh1_d2
    assert sh1_e3 != sh1_e2
    sh2.group.add_entry("test_l", "test_s", True)
    sh2_g2 = ujson.dumps(sh2.group.portable_dict()).encode()
    sh2_n2 = sh2.encrypter.get("nonce")
    sh2_d2 = sh2.encrypter.get("digest")
    sh2_e2 = sh2.encrypter.get("encrypted")
    assert sh2_n2 == sh2_n1
    assert sh2_d2 != sh2_d1
    assert sh2_e2 != sh2_e1
    assert sh2_e2 != sh1_e3
    sh1_ej2 = sh1.to_encrypted_json()
    sh3 = HerePass()
    sh3.from_encrypted_json(passphrase_1, sh1_ej2)
    sh3_g = ujson.dumps(sh3.group.portable_dict()).encode()
    sh3_n = sh3.encrypter.get("nonce")
    sh3_d = sh3.encrypter.get("digest")
    sh3_e = sh3.encrypter.get("encrypted")
    assert sh1_g3 == sh3_g
    assert sh1_n3 != sh3_n
    assert sh1_d3 != sh3_d
    assert sh1_e3 != sh3_e
    sh2_ej1 = sh2.to_encrypted_json()
    sh4 = HerePass()
    sh4.from_encrypted_json(passphrase_1, sh2_ej1)
    sh4_g = ujson.dumps(sh4.group.portable_dict()).encode()
    sh4_n = sh4.encrypter.get("nonce")
    sh4_d = sh4.encrypter.get("digest")
    sh4_e = sh4.encrypter.get("encrypted")
    assert sh2_g2 == sh4_g
    assert sh2_n2 != sh4_n
    assert sh2_d2 != sh4_d
    assert sh2_e2 != sh4_e
