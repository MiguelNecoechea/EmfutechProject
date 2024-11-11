from Backend.BackendServer import BackendServer
if __name__ == "__main__":
    server = BackendServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Keyboard interrupt received")
    finally:
        server.cleanup()
        