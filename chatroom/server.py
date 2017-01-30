import socket
import sys
import utils
import select

class Server(object):
    """
    chat server
    :param port: server port
    """
    def __init__(self, port):
        self.address = 'localhost'
        self.port = int(port)
        self.channels = {} # key : channel name, value : list of sock in this channel
        self.clients_name = {}  # key : client sock, value : client name
        self.clients_channel = {} # key: client sock, value: client channel
        self.clients_buffer = {} # key: client sock, value: client buffer
        self.commands  = {
            'join': (1, utils.SERVER_JOIN_REQUIRES_ARGUMENT),
            'create': (1, utils.SERVER_CREATE_REQUIRES_ARGUMENT),
            'list': (0, '')
        }

        try:
            self.server_socket = socket.socket()
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.address, self.port))
            self.server_socket.listen(5)
        except:
            print("Failed creating server socket.\n")
            sys.exit()

        self.fdList = [self.server_socket]

        while True:
            # set timeout=none, never run out
            ready_to_read, ready_to_write, in_error = select.select(self.fdList, [], [])
            for sock in ready_to_read:
                if sock == self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    self.fdList.append(client_socket)
                else:
                    try:
                        data = sock.recv(utils.MESSAGE_LENGTH).decode('utf-8')
                        if data:
                            self.write_buffer(sock, data)
                            if self.has_buffer(sock):
                                self.read_buffer(sock)
                        else:
                            if sock in self.fdList:
                                self.fdList.remove(sock)
                            self.leave_channel(sock)
                    except Exception as debug1:
                        continue

    def get_client_name(self, client):
        if client not in self.clients_name:
            return ''
        return self.clients_name[client]

    def channel_broadcast(self, channel, client, msg):
        for sock in self.channels[channel]:
            if sock != self.server_socket and sock != client:
                try:
                    self.server_send(sock, msg)
                except:
                    sock.close()
                    if sock in self.fdList:
                        self.fdList.remove(sock)

    def server_send(self, sock, msg):
        try:
            sock.send(msg.ljust(utils.MESSAGE_LENGTH).encode())
        except Exception as debug2:
            sock.close()
            if sock in self.fdList:
                self.fdList.remove(sock)

    def command_check(self, command, argument):
        """
        To create and join, valid format is "/create|join channel"
        To list, valid format is "/list"
        :param command: create | join | list
        :param argument: a list with a single element
        :return: (is_valid, err_msg)
        """
        try:
            if len(argument) != self.commands[command][0]:
                return (False, self.commands[command][1])
        except:
            return (False, utils.SERVER_INVALID_CONTROL_MESSAGE.format(command))
        return (True, '')

    def write_buffer(self, sock, data):
        if sock in self.clients_buffer:
            self.clients_buffer[sock] += data
        else:
            self.clients_buffer[sock] = data

    def has_buffer(self, sock):
        return len(self.clients_buffer[sock]) >= utils.MESSAGE_LENGTH

    def read_buffer(self, sock):
        msg = self.clients_buffer[sock].strip()
        if msg[0] == '/':
            msg = msg.split()
            msg_type = msg[0][1:]
            argument = msg[1:]
            is_valid, error_msg = self.command_check(msg_type, argument)
            if not is_valid:
                self.server_send(sock, error_msg)
                del self.clients_buffer[sock]
                return
            argument = ' '.join(argument)
            if msg_type == 'join':
                self.join_channel(sock, argument)
            elif msg_type == 'create':
                self.create_channel(sock, argument)
            elif msg_type == 'list':
                self.list_channel(sock)
        else:
            if sock not in self.clients_name:
                self.clients_name[sock] = msg
            else:
                self.send_msg(sock, msg)
        del self.clients_buffer[sock]

    def send_msg(self, sock, msg):
        if sock in self.clients_channel:
            self.channel_broadcast(self.clients_channel[sock], sock, "[{0}] {1}".format(self.get_client_name(sock), msg))
        else:
            self.server_send(sock, utils.SERVER_CLIENT_NOT_IN_CHANNEL)

    def create_channel(self, sock, channel):
        if channel in self.channels:
            self.server_send(sock, utils.SERVER_CHANNEL_EXISTS.format(channel))
        else:
            self.channels[channel] = []
            self.join_channel(sock, channel)

    def join_channel(self, sock, channel):
        if channel not in self.channels:
            self.server_send(sock, utils.SERVER_NO_CHANNEL_EXISTS.format(channel))
        else:
            self.leave_channel(sock)
            self.clients_channel[sock] = channel
            self.channel_broadcast(channel, sock, utils.SERVER_CLIENT_JOINED_CHANNEL.format(self.get_client_name(sock))+'\n')
            self.channels[channel].append(sock)

    def leave_channel(self, sock):
        if sock in self.clients_channel:
            self.channels[self.clients_channel[sock]].remove(sock)
            self.channel_broadcast(self.clients_channel[sock], sock, utils.SERVER_CLIENT_LEFT_CHANNEL.format(self.get_client_name(sock))+'\n')
            del self.clients_channel[sock]

    def list_channel(self, sock):
        self.server_send(sock, '\n'.join(self.channels.keys()))

if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        print("Usage: python server.py port")
        sys.exit()
    server = Server(args[1])
