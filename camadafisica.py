import os
import mmap
import errno
import fcntl
import struct
import termios
import asyncio
import traceback
from collections import defaultdict


class ZyboSerialDriver:
    """ Driver para o hardware de https://github.com/thotypous/zybo-z7-20-uart """

    def __init__(self, device='/dev/uio/user_io'):
        self.fd = os.open(device, os.O_RDWR)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, os.O_NONBLOCK)
        self.mm = mmap.mmap(self.fd, 0x1000)
        asyncio.get_event_loop().add_reader(self.fd, self.__irq_handler)
        self.__irq_unmask()
        self.callbacks = defaultdict(lambda: lambda _: None)

    def obter_porta(self, port):
        """ Obtém uma porta para controlar a partir do software em Python """
        return ZyboSerialPort(self, port)

    def expor_porta_ao_linux(self, port):
        """ Conecta uma porta a uma PTY para expô-la ao Linux """
        pty = PTY()
        pty.registrar_recebedor(lambda dados: self.enviar(port, dados))
        self.registrar_recebedor(port, pty.enviar)
        return pty

    def enviar(self, port, data):
        #print('send', port, data)
        for b in data:
            self.mm[port*4:port*4+4] = struct.pack('I', b)

    def registrar_recebedor(self, port, callback):
        self.callbacks[port] = callback

    def __irq_handler(self):
        os.read(self.fd, 4)   # diz ao SO que coletamos a irq
        buffers = defaultdict(lambda: bytearray())
        while True:
            elem, = struct.unpack('i', self.mm[0:4])  # retira da fila do hardware
            if elem == -1: break                      # fila vazia
            port, b = elem>>8, elem&0xff
            buffers[port].append(b)
        for port, dados in buffers.items():
            try:
                #print('recv', port, dados)
                self.callbacks[port](bytes(dados))
            except:
                traceback.print_exc()
        self.__irq_unmask()

    def __irq_unmask(self):
        os.write(self.fd, b'\x01\x00\x00\x00')


class ZyboSerialPort:
    def __init__(self, driver, port):
        self.driver = driver
        self.port = port
    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando vierem dados da linha serial
        """
        self.driver.registrar_recebedor(self.port, callback)
    def enviar(self, dados):
        """
        Envia dados para a linha serial
        """
        self.driver.enviar(self.port, dados)


class PTY:
    def __init__(self):
        pty, slave_fd = os.openpty()
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(pty)
        ispeed = termios.B115200
        ospeed = termios.B115200
        # cfmakeraw
        iflag &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK | termios.ISTRIP |
                   termios.INLCR | termios.IGNCR | termios.ICRNL | termios.IXON)
        oflag &= ~termios.OPOST
        lflag &= ~(termios.ECHO | termios.ECHONL | termios.ICANON |
                   termios.ISIG | termios.IEXTEN)
        cflag &= ~(termios.CSIZE | termios.PARENB)
        cflag |= termios.CS8
        #
        termios.tcsetattr(pty, termios.TCSANOW, [iflag, oflag, cflag, lflag,
                                                 ispeed, ospeed, cc])
        fcntl.fcntl(pty, fcntl.F_SETFL, os.O_NONBLOCK)
        pty_name = os.ttyname(slave_fd)
        os.close(slave_fd)
        self.pty = pty
        self.pty_name = pty_name
        asyncio.get_event_loop().add_reader(pty, self.__raw_recv)

    def __raw_recv(self):
        try:
            dados = os.read(self.pty, 2048)
            if self.callback:
                self.callback(dados)
        except OSError as e:
            if e.errno == errno.EIO:
                pass      # a outra ponta está fechada
            else:
                raise e

    def registrar_recebedor(self, callback):
        """
        Registra uma função para ser chamada quando vierem dados da linha serial
        """
        self.callback = callback

    def enviar(self, dados):
        """
        Envia dados para a linha serial
        """
        os.write(self.pty, dados)

