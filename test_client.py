from client import KVClient

client = KVClient([5000, 5001, 5002])

print(client.put("name", "Mukesh"))
print(client.read("name"))
print(client.batch_put([("city", "Pune"), ("country", "India")]))
print(client.range_read("a", "z"))
print(client.delete("name"))
