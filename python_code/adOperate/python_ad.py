from ldap3 import Server, Connection, ALL
server = Server('192.168.100.192')
conn = Connection(server)
conn.bind()
server.info
