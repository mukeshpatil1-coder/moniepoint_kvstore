from store.kv import KeyValueStore

def test_put_and_read():
    kv = KeyValueStore()
    kv.put("a", "1")
    kv.put("b", "2")
    assert kv.read("a") == "1"
    assert kv.read("b") == "2"

def test_delete():
    kv = KeyValueStore()
    kv.put("x", "123")
    kv.delete("x")
    assert kv.read("x") is None

def test_batch_put():
    kv = KeyValueStore()
    kv.batch_put([("k1", "v1"), ("k2", "v2")])
    assert kv.read("k1") == "v1"
    assert kv.read("k2") == "v2"
