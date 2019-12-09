#!/usr/bin/env python3
import asyncio
from camadafisica import ZyboSerialDriver
from myip import CamadaRede      # copie o arquivo da Etapa 3
from myslip import CamadaEnlace  # copie o arquivo da Etapa 4


driver = ZyboSerialDriver()

serial1 = driver.obter_porta(2)
pty1 = driver.expor_porta_ao_linux(3)

serial2 = driver.obter_porta(4)
pty2 = driver.expor_porta_ao_linux(5)

serial3 = driver.obter_porta(6)
pty3 = driver.expor_porta_ao_linux(7)


print('Conecte o RX da porta 2 com o TX da porta 3 e vice-versa.')
print('Conecte o RX da porta 4 com o TX da porta 5 e vice-versa.')
print('Conecte o RX da porta 6 com o TX da porta 7 e vice-versa.')
print()
print('Execute os seguintes comandos:')
print()
print('sudo slattach -vLp slip {}'.format(pty1.pty_name))
print('sudo slattach -vLp slip {}'.format(pty2.pty_name))
print('sudo slattach -vLp slip {}'.format(pty3.pty_name))
print()
print('sudo ifconfig sl0 192.168.123.1 pointopoint 192.168.122.1 mtu 1500')
print('sudo ip route add 192.168.124.0/24 via 192.168.122.1')
print('sudo ip route add 192.168.125.0/24 via 192.168.122.1')
print()
print('sudo ip netns add ns1')
print('sudo ip link set sl1 netns ns1')
print('sudo ip netns exec ns1 ifconfig sl1 192.168.124.1 pointopoint 192.168.122.1 mtu 1500')
print('sudo ip netns exec ns1 ip route add 0.0.0.0/0 via 192.168.122.1')
print()
print('sudo ip netns add ns2')
print('sudo ip link set sl2 netns ns2')
print('sudo ip netns exec ns2 ifconfig sl2 192.168.125.1 pointopoint 192.168.122.1 mtu 1500')
print('sudo ip netns exec ns2 ip route add 0.0.0.0/0 via 192.168.122.1')


# Os endereços IP que especificamos abaixo são os endereços da outra ponta do
# enlace. No caso do teste montado de acordo as mensagens acima, são os
# endereços atribuídos às interface de rede do Linux.
enlace = CamadaEnlace({'192.168.123.1': serial1,
                       '192.168.124.1': serial2,
                       '192.168.125.1': serial3})

rede = CamadaRede(enlace)

# Este é o endereço IP do nosso roteador. Como os enlaces são ponto-a-ponto,
# ele não precisa estar em uma mesma subrede que os endereços IP atribuídos
# às interfaces do Linux.
rede.definir_endereco_host('192.168.122.1')

# A tabela de encaminhamento define através que qual enlace o nosso
# roteador pode alcançar cada faixa de endereços IP.
rede.definir_tabela_encaminhamento([
    ('192.168.123.0/24', '192.168.123.1'),
    ('192.168.124.0/24', '192.168.124.1'),
    ('192.168.125.0/24', '192.168.125.1'),
])

asyncio.get_event_loop().run_forever()
