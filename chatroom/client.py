import socket
import sys
import utils
import select

class Client(object):

    def __init__(self, name, address, port):

        """
        chat client
        :param name: client name
        :param address: remote address
        :param port: remote port
        """
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()
        self.buffer = ''
        self.fdList = [self.socket, sys.stdin]

        try:
            self.socket.connect((self.address, self.port))
        except:
            print(utils.CLIENT_CANNOT_CONNECT.format(self.address, self.port))
            sys.exit()

        try:
            self.socket.send(self.name.ljust(utils.MESSAGE_LENGTH))
        except:
            print(utils.CLIENT_SERVER_DISCONNECTED.format(self.address, self.port))
            sys.exit()

        sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX)
        sys.stdout.flush()

        hasPrefix = True
        while True:
            ready_to_read, ready_to_write, in_error = select.select(self.fdList,[],[])
            for fd in ready_to_read:
                if fd == self.socket:
                    data = self.socket.recv(utils.MESSAGE_LENGTH)
                    if not data:
                        print('\r' + utils.CLIENT_SERVER_DISCONNECTED.format(self.address, self.port))
                        sys.exit()
                    else:
                        self.buffer += data
                        if len(self.buffer) >= utils.MESSAGE_LENGTH:
                            if hasPrefix:
                                sys.stdout.write(utils.CLIENT_WIPE_ME + '\r')
                                hasPrefix = False
                            showbuf = self.buffer.strip()
                            if self.buffer != '':
                                sys.stdout.write(showbuf + '\n')
                                sys.stdout.flush()
                            self.buffer = ''
                else:
                    msg_to_send = sys.stdin.readline()
                    self.socket.send(msg_to_send.ljust(utils.MESSAGE_LENGTH))
                    hasPrefix = False
                if hasPrefix == False:
                    sys.stdout.write(utils.CLIENT_MESSAGE_PREFIX)
                    sys.stdout.flush()
                    hasPrefix = True

if __name__ == '__main__':
    args = sys.argv
    if len(args) != 4:
        print("Usage: python client.py name remote_addr remote_port")
        sys.exit()
    client = Client(args[1], args[2], args[3])