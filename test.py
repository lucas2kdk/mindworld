from mcstatus import MinecraftServer

def main():
    # Replace 'localhost' with your server's address if it's not running locally
    server = MinecraftServer.lookup("localhost:25565")
    
    try:
        # 'status' is used to get a list of players and server information
        status = server.status()
        print(f"The server has {status.players.online} players and replied in {status.latency} ms")
        
        # 'query' is used to get more detailed information, but it needs to be enabled in the server.properties file
        query = server.query()
        print(f"The server has the following players online: {', '.join(query.players.names)}")
        
    except Exception as e:
        print(f"Could not connect to server: {e}")

if __name__ == "__main__":
    main()
