#!/usr/bin/env python3
#
# Um *servidor de favoritos* ou encurtador de URI.

import http.server
import requests
import os
from urllib.parse import unquote, parse_qs

memory = {}

form = '''<!DOCTYPE html>
<title>Servidor de Favoritos</title>
<form method="POST">
    <label>URI Longa:
        <input name="longuri">
    </label>
    <br>
    <label>Nome Pequeno:
        <input name="shortname">
    </label>
    <br>
    <button type="submit">Salvar!</button>
</form>
<p>URIs que conheço:
<pre>
{}
</pre>
'''


def CheckURI(uri, timeout=5):
    '''Verificando se este URI é alcançável, ou seja, ele retorna um 200 OK
    
    Esta função retorna True se uma solicitação GET para uri retornar um 200 OK e
    False se essa solicitação GET retornar qualquer outra resposta ou não retornar
    (ou seja, tempo limite).
    '''
    try:
        r = requests.get(uri, timeout=timeout)
        # Se a solicitação GET retornar, foi um 200 OK
        return r.status_code == 200
    except requests.RequestException:
        # Se a solicitação GET gerou uma exceção, não está tudo bem.
        return False


class Shortener(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # A GET request será para / (the root path) ou para /some-name.
        # Retire o / e teremos uma string vazia ou um nome.
        name = unquote(self.path[1:])

        if name:
            if name in memory:
                # Enviando um redirecionamento.
                self.send_response(303)
                self.send_header('Location', memory[name])
                self.end_headers()
            else:
                # Não conhecemos esse nome! Envie um erro 404.
                self.send_response(404)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write("I don't know '{}'.".format(name).encode())
        else:
            # Root path. Envie o formulário.
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Liste as associações conhecidas no formulário.
            known = "\n".join("{} : {}".format(key, memory[key])
                              for key in sorted(memory.keys()))
            self.wfile.write(form.format(known).encode())

    def do_POST(self):
        # Decodifique os dados do formulário.
        length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)
        longuri = params["longuri"][0]
        shortname = params["shortname"][0]

        if CheckURI(longuri):
            # Este URI é bom! Lembre-o com o nome especificado.
            memory[shortname] = longuri

            # Servir um redirecionamento para o formulário.
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            # Não foi possível buscar o URI longo.
            self.send_response(404)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(
                "Couldn't fetch URI '{}'. Sorry!".format(longuri).encode())

if __name__ == '__main__':
    server_address = ('', int(os.environ.get('PORT', '8000')))
    httpd = http.server.HTTPServer(server_address, Shortener)
    httpd.serve_forever()
