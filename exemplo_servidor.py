#!/usr/bin/env python3
# Este é um exemplo de um programa que faz eco, ou seja, envia de volta para
# o cliente tudo que for recebido em uma conexão.

import asyncio
from camadafisica import ZyboSerialDriver
from mytcp import Servidor       # copie o arquivo da Etapa 2
from myip import CamadaRede      # copie o arquivo da Etapa 3
from myslip import CamadaEnlace  # copie o arquivo da Etapa 4

# Implemenetação da camada de aplicação

def dados_recebidos(conexao, dados):
    if dados == b'':
        conexao.fechar()
    else:
        conexao.enviar(dados)   # envia de volta

def conexao_aceita(conexao):
    conexao.registrar_recebedor(dados_recebidos)   # usa esse mesmo recebedor para toda conexão aceita


# Integração com as demais camadas

driver = ZyboSerialDriver()
linha_serial = driver.obter_porta(4)
pty = driver.expor_porta_ao_linux(5)
outra_ponta = '192.168.123.1'
nossa_ponta = '192.168.123.2'
porta_tcp = 7000

print('Conecte o RX da porta 4 com o TX da porta 5 e vice-versa.')
print('Para conectar a outra ponta da camada física, execute:')
print()
print('sudo slattach -vLp slip {}'.format(pty.pty_name))
print('sudo ifconfig sl0 {} pointopoint {} mtu 1500'.format(outra_ponta, nossa_ponta))
print()
print('Acesse o serviço com o comando: nc {} {}'.format(nossa_ponta, porta_tcp))
print()

enlace = CamadaEnlace({outra_ponta: linha_serial})
rede = CamadaRede(enlace)
rede.definir_endereco_host(nossa_ponta)
rede.definir_tabela_encaminhamento([
    ('0.0.0.0/0', outra_ponta)
])
servidor = Servidor(rede, porta_tcp)
servidor.registrar_monitor_de_conexoes_aceitas(conexao_aceita)
asyncio.get_event_loop().run_forever()
